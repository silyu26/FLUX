import os
import io
import json
import base64
import psutil
from datetime import datetime
from PIL import Image
import paho.mqtt.client as mqtt
from ultralytics import YOLO

# === SQL + Models ===
from SQL import crud, db
import model

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "image_stream/test"

# Load YOLO model
model = YOLO("yolo11n.pt")
expId = 0

# === Optional Resource Limit ===
def limit_resources():
    process = psutil.Process(os.getpid())
    # Example: limit to 1 GB RAM or one CPU core
    # process.cpu_affinity([0])
    # max_memory_bytes = 1024 * 1024 * 1024
    # process.rlimit(psutil.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

# === MQTT Callback ===
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        batch = payload.get("batch", [])

        # Measure pre-inference system stats
        memory_usage_before = psutil.virtual_memory().percent
        print(f" Received batch of {len(batch)} images")
        print(f"Memory usage before inference: {memory_usage_before}%")

        # Decode images
        images = []
        req_id = None
        gen_at = None
        fps = None
        for item in batch:
            img_data = base64.b64decode(item["data"])
            image = Image.open(io.BytesIO(img_data))
            images.append(image)
            req_id = item.get("req_id")
            gen_at = item.get("gen_at")
            fps = item.get("fps")

        # Run YOLO inference
        model_in = datetime.now()
        results = model.predict(source=images, batch=len(images))
        model_out = datetime.now()

        # Record metrics in SQL
        exp = model.Experiment(
            gen_at=gen_at,
            exp_id=expId,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(interval=0),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            fps=fps,
        )
        crud.create_experiment_with_weather(db.SessionLocal(), exp)

        # Print or log results
        print(f" Processed req_id={req_id} | fps={fps}")
        print(f"Model in: {model_in}, Model out: {model_out}")
        print(f"Detected objects: {len(results[0].boxes)}")

    except Exception as e:
        print(f" Error processing MQTT message: {e}")

# === MQTT Setup ===
def main():
    limit_resources()
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    print(f"Subscribed to MQTT topic '{MQTT_TOPIC}' on {MQTT_BROKER}:{MQTT_PORT}")
    client.loop_forever()

if __name__ == "__main__":
    main()
