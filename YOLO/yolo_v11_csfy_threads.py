from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io
import os
import psutil
import torch
import pynvml
from datetime import datetime
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer
import logging
import threading
import queue
import time

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
#uvicorn YOLO.yolo_v11_csfy_threads:app --reload --host 0.0.0.0 --port 5000
# --- Setup logging ---
log_filename = "yolo_wf01.log"
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

# --- Load YOLO model ---
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

image_queue = queue.Queue(maxsize=5) 
NUM_WORKERS = 6
#model = YOLO("yolo11n.pt")
# --- Background inference worker ---
def inference_worker(worker_id: int):
    # IMPORTANT: each worker gets its own YOLO model instance
    model = YOLO("yolo11n.pt")
    #model.to('cuda')  # Move model to GPU

    logging.info(f"[Worker-{worker_id}] Started")

    while True:
        try:
            item = image_queue.get()
            if item is None:  # Graceful shutdown
                logging.info(f"[Worker-{worker_id}] Shutdown signal received")
                break

            req_id, gen_at, expId, fps, server_in, image_bytes = item
            model_in = datetime.now()

            image = Image.open(io.BytesIO(image_bytes))

            logging.info(f"[Worker-{worker_id}] Running inference | req_id={req_id}")

            #results = model.predict(source=[image], batch=1)
            results = model.predict(source=[image], batch=1, device='cpu')
            #results = model.predict(source=[image], batch=1, device='cuda:0')
            device = next(model.parameters()).device
            print(f"Model is on: {device}")
            print(f"YOLO model device is: {model.device}")
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)

            model_out = datetime.now()

            exp = Experiment(
                gen_at=gen_at,
                exp_id=expId,
                req_id=req_id,
                model_in=model_in,
                model_out=model_out,
                cpu_usage=psutil.cpu_percent(interval=0),
                gpu_usage=mem.used / mem.total * 100 if mem.total > 0 else 0,
                memory_usage=psutil.virtual_memory().percent,
                process_count=len(psutil.pids()),
                fps=fps,
                server_in=server_in
            )

            #save_experiment_to_buffer(exp)

            logging.info(
                f"[Worker-{worker_id}] Done | req_id={req_id} | Time={(model_out - model_in).total_seconds():.2f}s"
            )

        except Exception as e:
            logging.error(f"[Worker-{worker_id}] Error: {str(e)}")

        finally:
            image_queue.task_done()



# Start multiple worker threads
for i in range(NUM_WORKERS):
    t = threading.Thread(target=inference_worker, args=(i,), daemon=True)
    t.start()
    logging.info(f"[System] Started inference worker thread #{i}")


@app.post("/yolo/")
async def predict(
    file: UploadFile = File(...),
    req_id: int = Form(...),
    gen_at: str = Form(...),
    expId: int = Form(...),
    fps: int = Form(...)
):
    try:
        server_in = datetime.now().isoformat()
        contents = await file.read()
        # Push image into the queue for async processing
        image_queue.put((req_id, gen_at, expId, fps, server_in, contents))
        logging.info(f"[Receiver] Received image | req_id={req_id} | Queue size={image_queue.qsize()}")

        # Respond immediately (without waiting for inference)cd 
        return {
            "status": "received",
            "req_id": req_id,
            "queued_items": image_queue.qsize()
        }

    except Exception as e:
        logging.error(f"[Receiver] Error receiving image | req_id={req_id} | {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
