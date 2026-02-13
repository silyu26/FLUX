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
from confluent_kafka import Consumer, Producer, KafkaError

# Assuming these exist in your environment
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer

# --- Configuration ---
# REPLACE WITH YOUR SERVER LAPTOP IP
BOOTSTRAP_SERVERS = "192.168.2.106:9092"
#BOOTSTRAP_SERVERS = "https://paternal-astrid-nondiagonally.ngrok-free.dev/"
TOPIC_REQUEST = "yolo-requests"
TOPIC_RESPONSE = "yolo-responses"
CONSUMER_GROUP = "yolo-inference-group"

# --- Setup logging ---
log_filename = "yolo_wf28.log"
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
#uvicorn YOLO.yolo_v11_kafka:app --reload --host 0.0.0.0 --port 5000
# --- Load YOLO ---
try:
    model = YOLO("yolo11l.pt")
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    logging.info("YOLO model loaded successfully")
except Exception as e:
    logging.error(f"Failed to load model/GPU: {e}")
    exit(1)

# --- Kafka Setup ---
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'group.id': CONSUMER_GROUP,
    'auto.offset.reset': 'latest'
}
consumer = Consumer(consumer_conf)
consumer.subscribe([TOPIC_REQUEST])

producer_conf = {'bootstrap.servers': BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)

logging.info(f"Kafka Consumer started. Subscribed to {TOPIC_REQUEST}")

try:
    while True:
        # Poll for messages (timeout 1.0s)
        msg = consumer.poll(1.0)

        # 1. CAPTURE DPSE_OUT
        # The moment we hold the message, it has "left" Kafka
        #dpse_out = datetime.now()

        if msg is None:
            continue
        if msg.error():
            # ... error handling ...
            continue

        try:
            # 2. CAPTURE DPSE_IN
            # msg.timestamp() returns a tuple: (timestamp_type, timestamp_value_ms)
            # We convert milliseconds to a proper datetime object
            model_in = datetime.now()
            ts_type, ts_val = msg.timestamp()
            dpse_in = datetime.fromtimestamp(ts_val / 1000.0).isoformat()

            # Parse Message
            payload = json.loads(msg.value().decode('utf-8'))
            req_id = payload.get("req_id")
            expId = payload.get("expId")
            fps = payload.get("fps")
            gen_at = payload.get("gen_at")
            acq_start = payload.get("acq_start")
            
            logging.info(f"Received message | req_id={req_id} | expId={expId}")

            # Decode image
            
            tmp = time.time()
            image_data = base64.b64decode(payload["image"])
            image = Image.open(io.BytesIO(image_data))
            tmp2 = time.time()
            logging.info(f"Image decoded in {tmp2 - tmp:.4f} seconds")

            # Inference
            results = model.predict(source=[image], batch=1, device='cuda')
            model_out = datetime.now()
            
            # Metrics
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000   # watts
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            util_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)

            logging.info(f"Inference done | req_id={req_id} | duration={(model_out - model_in).total_seconds():.2f}s")

            # Save to SQL (Existing logic)
            exp = Experiment(
                gen_at=gen_at,
                acq_start=acq_start,
                exp_id=expId,
                req_id=req_id,
                model_in=model_in,
                model_out=model_out,
                dpse_in=dpse_in,
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

            # Prepare Response
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

            # Send Response back to Kafka
            producer.produce(
                TOPIC_RESPONSE, 
                value=json.dumps(response)
            )
            producer.poll(0) # Trigger callbacks
            
            logging.info(f"Sent response to {TOPIC_RESPONSE} | req_id={req_id}")

        except Exception as e:
            logging.error(f"Error processing message: {e}")

except KeyboardInterrupt:
    logging.info("Stopping...")
finally:
    consumer.close()
    producer.flush()