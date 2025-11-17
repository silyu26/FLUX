import time
import base64
import json
from datetime import datetime
from ping3 import ping
import speedtest
from kafka import KafkaProducer
import sys
import os

if len(sys.argv) < 3:
    print("Usage: python script.py <n> <expId>")
    sys.exit(1)

n = sys.argv[1]  # workflow
exp = sys.argv[2]  # expId

log_filename = f"workflow_{n}_expId_{exp}.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# --- Settings ---
host = '8.8.8.8'
IMAGE_PATHS = ["./Senders/imgs/cat1_m.jpg"]
FPS_LIST = [1, 5, 10, 20, 40, 60]
NUM_ITERATIONS = 30

# --- Network check ---
log("=== Starting network test ===")
latency = ping(host)
st = speedtest.Speedtest(secure=True)
st.get_best_server()
download_speed = st.download() / 1_000_000
upload_speed = st.upload() / 1_000_000

log(f"Ping to {host}: {latency*1000:.2f} ms")
log(f"Download Speed: {download_speed:.2f} Mbps")
log(f"Upload Speed: {upload_speed:.2f} Mbps")

# --- Run tests for each FPS ---
for fps in FPS_LIST:
    index = FPS_LIST.index(fps)
    log(f"\n=== Starting test at {fps} FPS ===")
    start_time = time.time()

    for i in range(NUM_ITERATIONS):
        img_path = IMAGE_PATHS[0]
        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            log(f"Error opening image: {e}")
            continue

        message = {
            "gen_at": datetime.now().isoformat(),
            "req_id": i + index * 30,
            "fps": fps,
            "expId": exp,
            "image_base64": img_base64
        }

        try:
            producer.send("yolo-images", message)
            log(f"Sent message {i+1}/{NUM_ITERATIONS} | FPS={fps}")
        except Exception as e:
            log(f"Kafka send failed on iteration {i+1}: {e}")

        time.sleep(1 / fps)

    elapsed = time.time() - start_time
    log(f"Finished test at {fps} FPS in {elapsed:.2f} seconds")

log("=== All tests completed ===")
log_file.close()
