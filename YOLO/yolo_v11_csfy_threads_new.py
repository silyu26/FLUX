from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io
import psutil
import pynvml
from datetime import datetime
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import uuid

app = FastAPI(title="YOLOv11 API - no-queue, backpressure")

# ---------- logging ----------
log_filename = "yolo_wf30.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# ---------- GPU init ----------
pynvml.nvmlInit()
gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

# ---------- workers / models ----------
NUM_WORKERS = 2

# preload one model per worker (each worker gets its own model instance)
logging.info("[System] Loading YOLO models...")
models = []
for i in range(NUM_WORKERS):
    m = YOLO("yolo11l.pt")   # adjust path/name as needed
    models.append(m)
    logging.info(f"[System] Loaded model for worker {i}")

# executor to run inference in background
executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)

# semaphore enforces at-most-N concurrent inferences
worker_semaphore = threading.Semaphore(NUM_WORKERS)

# busy flags to select a free worker index; protected by a lock
busy_flags = [False] * NUM_WORKERS
busy_lock = threading.Lock()


def find_and_mark_free_worker():
    """Find an index of a free worker and mark it busy. Return index or None."""
    with busy_lock:
        for idx, busy in enumerate(busy_flags):
            if not busy:
                busy_flags[idx] = True
                return idx
    return None


def mark_worker_free(idx):
    with busy_lock:
        busy_flags[idx] = False


def run_inference_background(worker_id, image_bytes, acq_start, req_id, gen_at, expId, fps, server_in, job_id):
    """
    Background worker function. This must release the semaphore and
    clear the busy flag when finished (even on exception).
    """
    try:
        model = models[worker_id]
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        model_in = datetime.now()
        logging.info(f"[Worker-{worker_id}] Starting inference job_id={job_id} req_id={req_id}")

        # run inference (adjust params as required)
        results = model.predict(source=[image], batch=1, device="cuda")

        model_out = datetime.now()

        # GPU / system stats
        try:
            mem = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
            temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(gpu_handle) / 1000.0
            util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle).gpu
            vram_pct = mem.used / mem.total * 100 if mem.total else 0
        except Exception as e:
            # If NVML fails, set sensible defaults
            logging.warning(f"[Worker-{worker_id}] NVML read failed: {e}")
            temp = power = util = vram_pct = 0

        # Build Experiment object (your SQL model)
        exp = Experiment(
            gen_at=gen_at,
            acq_start=acq_start,
            exp_id=expId,
            req_id=req_id,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(interval=0),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            gpu_usage=util,
            gpu_vram_usage=vram_pct,
            gpu_temperature=temp,
            gpu_power=power,
            fps=fps,
            server_in=server_in
        )

        save_experiment_to_buffer(exp)   

        elapsed = (model_out - model_in).total_seconds()
        logging.info(f"[Worker-{worker_id}] Finished job_id={job_id} req_id={req_id} time={elapsed:.2f}s")

    except Exception as e:
        logging.exception(f"[Worker-{worker_id}] Error in job_id={job_id} req_id={req_id}: {e}")

    finally:
        # mark worker free and release semaphore so new requests can be accepted
        mark_worker_free(worker_id)
        worker_semaphore.release()


@app.post("/yolo/")
async def predict(
    file: UploadFile = File(...),
    req_id: int = Form(...),
    gen_at: str = Form(...),
    expId: int = Form(...),
    fps: int = Form(...)
):
    """
    Accept request only if a worker slot is available right now.
    If accepted, assign a free worker, start inference in background,
    and return immediately with assigned worker & job id.

    If no worker is free, return 429 (Too Many Requests) and tell client to retry later.
    """
    # try to acquire a worker permit without blocking
    acquired = worker_semaphore.acquire(blocking=False)
    if not acquired:
        # all workers busy — no queueing
        logging.info(f"[Receiver] Busy: no worker available for req_id={req_id}")
        raise HTTPException(status_code=429, detail={"server_busy": True, "message": "All workers busy; try again later"})

    # we have a permit — find a free worker index and mark it busy
    worker_id = find_and_mark_free_worker()
    if worker_id is None:
        # This should not normally happen because of semaphore, but handle gracefully
        worker_semaphore.release()
        logging.error("[Receiver] Inconsistent state: semaphore acquired but no free worker found")
        raise HTTPException(status_code=500, detail={"error": "internal server error"})

    # read file content
    contents = await file.read()
    server_in = datetime.now().isoformat()
    job_id = str(uuid.uuid4())

    # submit background task (non-blocking)
    executor.submit(
        run_inference_background,
        worker_id,
        contents,
        req_id,
        gen_at,
        expId,
        fps,
        server_in,
        job_id
    )

    logging.info(f"[Receiver] Accepted req_id={req_id} -> worker-{worker_id} job_id={job_id}")

    # return immediately; client may send next data once it receives this acceptance
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "req_id": req_id,
            "assigned_worker": worker_id,
            "job_id": job_id,
            "server_busy": False
        }
    )
