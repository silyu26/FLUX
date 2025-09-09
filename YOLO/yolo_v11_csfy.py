from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io
import psutil
from datetime import datetime
from SQL.crud import create_experiment_with_weather
from SQL.db import SessionLocal
from model import Experiment, WeatherData

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
 #uvicorn YOLO.yolo_v11_csfy:app --reload --host 0.0.0.0 --port 5000
model = YOLO("yolo11n.pt")

@app.post("/yolo/")
async def predict(file: UploadFile = File(...),
                  req_id: int = Form(...),
                  gen_at: str = Form(...)):
    try:
        model_in = datetime.now()
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Run YOLO inference
        results = model(image)
        model_out = datetime.now()
        exp = Experiment(
          gen_at=gen_at,
          exp_id=2,
          model_in=model_in,
          model_out=model_out,
          cpu_usage=psutil.cpu_percent(interval=0),
          memory_usage=psutil.virtual_memory().percent,
          process_count=len(psutil.pids()),
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
            "gen_at": gen_at
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


#results = model.train(data="coco8.yaml", epochs=100, imgsz=640)


#results = model("./imgs/cat1.jpg")