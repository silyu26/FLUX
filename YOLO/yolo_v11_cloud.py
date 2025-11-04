from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io
import os
import psutil
from datetime import datetime
#from SQL.crud import create_experiment_with_weather
#from SQL.db import SessionLocal
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer
#from save_data import push_buffer_to_db
import logging

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
#uvicorn YOLO.yolo_v11_cloud:app --reload --host 0.0.0.0 --port 5000

# --- Setup logging ---
log_filename = "yolo_wf34.log"
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
model = YOLO("yolo11n.pt")

def limit_resources():
    process = psutil.Process(os.getpid())
    # Example: limit CPU or memory if needed
    #process.cpu_affinity([19])
    # max_memory_bytes = 1024 * 1024 * 1024  
    # process.rlimit(psutil.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

@app.post("/yolo/")
async def predict(
    file: UploadFile = File(...),
    req_id: int = Form(...),
    gen_at: str = Form(...),
    expId: int = Form(...),
    fps: int = Form(...),
    server_in: str = Form(...),
    minio_in: str = Form(...),
    db_in: str = Form(...),
    minio_out: str = Form(...),
    db_out: str = Form(...),
    server_out: str = Form(...),
):
    #limit_resources()
    #memory_usage_b = psutil.virtual_memory().percent
    #logging.info(f"Memory Usage Before Inference: {memory_usage_b}% | exp_id={req_id}")

    try:
        model_in = datetime.now()
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        logging.info(f"Running YOLO inference | req_id={req_id} | expId={expId}")
        #results = model.predict(source=[image], batch=1, device='cuda')
        results = model.predict(source=[image], batch=1)
        model_out = datetime.now()
        logging.info(f"Inference completed | Time taken: {(model_out - model_in).total_seconds():.2f}s")

        # Save experiment data
        exp = Experiment(
            gen_at=gen_at,
            exp_id=expId,
            req_id=req_id,
            model_in=model_in,
            model_out=model_out,
            server_in=server_in,
            minio_in=minio_in,
            db_in=db_in,
            minio_out=minio_out,
            db_out=db_out,
            server_out=server_out,
            cpu_usage=psutil.cpu_percent(interval=0),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            fps=fps
        )
        save_experiment_to_buffer(exp)

        return {
            "predictions": results[0].boxes.xyxy.tolist(),
            "scores": results[0].boxes.conf.tolist(),
            "classes": results[0].boxes.cls.tolist(),
        }

    except Exception as e:
        logging.error(f"Error in prediction | req_id={req_id} | {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)