from fastapi import WebSocket, WebSocketDisconnect
import base64
import json
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
from SQL.model import Experiment, WeatherData

app = FastAPI(title="YOLOv11 API", description="API for YOLOv11 inference", version="1.0")
#uvicorn YOLO.yolo_v11_ws:app --reload --host 0.0.0.0 --port 5000
model = YOLO("yolo11n.pt")
expId = 9

@app.websocket("/yolo/")
async def websocket_yolo(websocket: WebSocket):
    websocket._max_size = 10_485_760
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            payload = json.loads(message)

            batch = payload.get("batch", [])
            images = []
            req_id = batch[0].get("req_id") if batch else None
            gen_at = batch[0].get("gen_at") if batch else None
            fps = batch[0].get("fps") if batch else None

            model_in = datetime.now()

            for frame in batch:
                img_data = base64.b64decode(frame["data"])
                image = Image.open(io.BytesIO(img_data))
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
            )
            create_experiment_with_weather(SessionLocal(), exp)

            await websocket.send_json({
                "predictions": results[0].boxes.xyxy.tolist(),
                "scores": results[0].boxes.conf.tolist(),
                "classes": results[0].boxes.cls.tolist(),
                "model_in": model_in.isoformat(),
                "model_out": model_out.isoformat(),
                "req_id": req_id,
                "gen_at": gen_at,
                "fps": fps
            })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
