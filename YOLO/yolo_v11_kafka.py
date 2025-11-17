from kafka import KafkaConsumer
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import base64
import json
from datetime import datetime
import psutil
import logging
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer

# --- Logging setup ---
log_filename = "yolo_kafka.log"
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

# --- Load YOLO model ---
model = YOLO("yolo11n.pt")

# --- Kafka Consumer Setup ---
consumer = KafkaConsumer(
    "yolo-images",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="yolo-inference-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

logging.info("✅ YOLO Kafka consumer started and waiting for messages...")

# --- Main loop ---
for msg in consumer:
    data = msg.value
    try:
        req_id = data["req_id"]
        expId = data["expId"]
        fps = data["fps"]
        gen_at = data["gen_at"]
        image_base64 = data["image_base64"]

        image = Image.open(BytesIO(base64.b64decode(image_base64)))
        model_in = datetime.now()

        logging.info(f"Running YOLO inference | req_id={req_id} | expId={expId}")
        results = model.predict(source=[image], batch=1)
        model_out = datetime.now()

        exp = Experiment(
            gen_at=gen_at,
            exp_id=expId,
            req_id=req_id,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(interval=0),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            fps=fps
        )
        save_experiment_to_buffer(exp)
        logging.info(f"Inference completed | req_id={req_id} | time={(model_out - model_in).total_seconds():.2f}s")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
