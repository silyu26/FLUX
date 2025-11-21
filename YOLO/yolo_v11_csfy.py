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
#from SQL.crud import create_experiment_with_weather
#from SQL.db import SessionLocal
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer
#from save_data import push_buffer_to_db
import logging

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
#uvicorn YOLO.yolo_v11_csfy:app --reload --host 0.0.0.0 --port 5000

# --- Setup logging ---
log_filename = "yolo_wf9.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Load model
model = YOLO("yolo11l.pt")
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

@app.post("/yolo/")
async def predict(
    file: UploadFile = File(...),
    req_id: int = Form(...),
    gen_at: str = Form(...),
    expId: int = Form(...),
    fps: int = Form(...)
):

    try:
        model_in = datetime.now()
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        logging.info(f"Running YOLO inference | req_id={req_id} | expId={expId}")
        results = model.predict(source=[image], batch=1, device='cuda')
        #results = model.predict(source=[image], batch=1, device='cpu')
        model_out = datetime.now()
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000   # watts
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        util_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)

        #results = model.predict(source=[image], batch=1)
        
        logging.info(f"Inference completed | Time taken: {(model_out - model_in).total_seconds():.2f}s")

        # Save experiment data
        exp = Experiment(
            gen_at=gen_at,
            exp_id=expId,
            req_id=req_id,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(interval=0,percpu=False),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            gpu_usage=util_rates.gpu,
            gpu_vram_usage=mem.used / mem.total * 100 if mem.total > 0 else 0,
            gpu_temperature=temp,
            gpu_power=power,
            fps=fps
        )
        save_experiment_to_buffer(exp)
        return {
            "predictions": results[0].boxes.xyxy.tolist(),
            "scores": results[0].boxes.conf.tolist(),
            "classes": results[0].boxes.cls.tolist(),
            "model_in": model_in.isoformat(),
            "model_out": model_out.isoformat(),
            "req_id": req_id,
            "gen_at": gen_at,
            "fps": fps
        }

    except Exception as e:
        logging.error(f"Error in prediction | req_id={req_id} | {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
