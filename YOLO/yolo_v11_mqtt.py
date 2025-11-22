import paho.mqtt.client as mqtt
import json
import base64
import time
import io
import psutil
import pynvml
from datetime import datetime
from PIL import Image
from ultralytics import YOLO
import logging
import os
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer

BROKER = "127.0.0.1"
PORT = 1883
TOPIC_REQUEST = "yolo/requests"
TOPIC_RESPONSE_BASE = "yolo/responses/"

#uvicorn YOLO.yolo_v11_mqtt:app --host 0.0.0.0 --port 5001

# --- Setup logging ---
log_filename = "yolo_wf4.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# --- Load YOLO ---
model = YOLO("yolo11l.pt")
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
logging.info("YOLO model loaded successfully")

# --- MQTT setup ---
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker (code={rc})")
    client.subscribe(TOPIC_REQUEST, qos=2)
    logging.info(f"Subscribed to topic: {TOPIC_REQUEST}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        req_id = payload["req_id"]
        expId = payload["expId"]
        fps = payload["fps"]
        gen_at = payload["gen_at"]
        filename = payload.get("filename", "unknown.jpg")

        logging.info(f"Received message | req_id={req_id} | expId={expId}")

        # Decode image
        model_in = datetime.now()
        tmp = time.time()
        image_data = base64.b64decode(payload["image"])
        image = Image.open(io.BytesIO(image_data))
        tmp2 = time.time()
        logging.info(f"Image decoded in {tmp2 - tmp:.4f} seconds")

        
        results = model.predict(source=[image], batch=1, device='cuda')
        model_out = datetime.now()
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000   # watts
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        util_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)

        logging.info(f"Inference done | req_id={req_id} | duration={(model_out - model_in).total_seconds():.2f}s")

        exp = Experiment(
            gen_at=gen_at,
            exp_id=expId,
            req_id=req_id,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(interval=0),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            gpu_usage=util_rates.gpu,
            gpu_vram_usage=mem.used / mem.total * 100 if mem.total > 0 else 0,
            gpu_temperature=temp,
            gpu_power=power,
            fps=fps
        )
        save_experiment_to_buffer(exp)

        response = {
            "req_id": req_id,
            "expId": expId,
            "fps": fps,
            "predictions": results[0].boxes.xyxy.tolist(),
            "scores": results[0].boxes.conf.tolist(),
            "classes": results[0].boxes.cls.tolist(),
            "model_in": model_in.isoformat(),
            "model_out": model_out.isoformat()
        }

        topic_response = TOPIC_RESPONSE_BASE + str(expId)
        client.publish(topic_response, json.dumps(response))
        logging.info(f"Sent response to {topic_response} | req_id={req_id}")

    except Exception as e:
        logging.error(f"Error processing message: {e}")

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()
