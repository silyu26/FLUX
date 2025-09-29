from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
from typing import List
import io
import os
import psutil
from datetime import datetime
from SQL.crud import create_experiment_with_weather
from SQL.db import SessionLocal
from model import Experiment, WeatherData

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
#uvicorn YOLO.yolo_v11_csfy:app --reload --host 0.0.0.0 --port 5000
model = YOLO("yolo11m.pt")
expId = 15

def limit_resources():
    process = psutil.Process(os.getpid())

    #process.cpu_affinity([16])  # Restrict to first CPU core (0-based index)

    #max_memory_bytes = 1024 * 1024 * 1024  
    #process.rlimit(psutil.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

@app.post("/yolo/")
async def predict(files: List[UploadFile] = File(...),
                  req_id: int = Form(...),
                  gen_at: str = Form(...),
                  fps: int = Form(...)):
    #limit_resources()
    memory_usage_b=psutil.virtual_memory().percent
    print(f"Memory Usage Before Inference: {memory_usage_b}%")
    try:
        model_in = datetime.now()
        images = []
        for file in files:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            images.append(image)

        # Run YOLO inference
        results = model.predict(source=images, batch=len(images))
        model_out = datetime.now()
        exp = Experiment(
          gen_at=gen_at,
          exp_id=expId,
          model_in=model_in,
          model_out=model_out,
          cpu_usage=psutil.cpu_percent(interval=0),
          memory_usage=psutil.virtual_memory().percent,
          process_count=len(psutil.pids()),
          fps=fps,
          #server_in=server_in,
          #model_out=datetime.now()
        )
        create_experiment_with_weather(SessionLocal(), exp)
        return {
            "predictions": results[0].boxes.xyxy.tolist(),  # Bounding boxes
            "scores": results[0].boxes.conf.tolist(),      # Confidence scores
            "classes": results[0].boxes.cls.tolist(),      # Class IDs
            "model_in": model_in.isoformat(),
            "model_out": model_out.isoformat(),
            "req_id": req_id,
            "gen_at": gen_at,
            "fps": fps
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


#results = model.train(data="coco8.yaml", epochs=100, imgsz=640)


#results = model("./imgs/cat1.jpg")