import os
import time
import json
import base64
import asyncio
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from ping3 import ping
from SQL.save_data import push_buffer_to_db
import speedtest
import sys

if len(sys.argv) < 3:
    print("Usage: python script.py <n>")
    sys.exit(1)

n = sys.argv[1] #workflow
exp = sys.argv[2] #expId
# ------------------ Logging ------------------
log_filename = f"workflow_{n}_expId_{exp}.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file  # Redirect all print() output to file
sys.stderr = log_file

def log(msg):
    """Helper function to log messages with timestamp"""
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# ------------------ Params ------------------
host = '8.8.8.8'
receiver_ip = "192.169.2.100"
HTTP_URL = f"http://{receiver_ip}:5000/yolo/"
MQTT_BROKER = receiver_ip
MQTT_TOPIC = "image_stream/test"

IMAGE_PATHS = ["./imgs/cat1.jpg"]
FPS_LIST = [1, 5, 10, 20, 40, 60]  # automatically loop over these
TOTAL_REQUESTS = 30

# ------------------ Network Check ------------------
def network_test():
    log("=== Starting network check ===")
    try:
        latency = ping(host)
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Mbps
        upload_speed = st.upload() / 1_000_000      # Mbps

        log(f"Ping to {host}: {latency*1000:.2f} ms")
        log(f"Download Speed: {download_speed:.2f} Mbps")
        log(f"Upload Speed: {upload_speed:.2f} Mbps")
    except Exception as e:
        log(f"Network check failed: {e}")

# ------------------ HTTP ------------------
def send_http(fps):
    log(f"=== Starting HTTP test at {fps} FPS ===")
    for i in range(TOTAL_REQUESTS):
        img_path = IMAGE_PATHS[0]
        files = []

        for j in range(fps):
            try:
                acq_start = datetime.now().isoformat()
                files.append(("file", (f"{img_path}", open(img_path, "rb"), "image/jpeg")))
            except Exception as e:
                log(f"Error opening image: {e}")
                continue

        data = {"acq_start": acq_start, "gen_at": datetime.now().isoformat(), "req_id": i + index*30, "fps": fps, "expId": exp}
        try:
            response = requests.post(HTTP_URL, files=files, data=data, timeout=60)
            log(f"HTTP request {i+1}/{TOTAL_REQUESTS} | FPS={fps} | Status={response.status_code}")
        except Exception as e:
            log(f"HTTP request {i+1} failed: {e}")

        time.sleep(0.05)
    log(f"=== Finished HTTP test at {fps} FPS ===")

# ------------------ MQTT ------------------
def send_mqtt(fps):
    log(f"=== Starting MQTT test at {fps} FPS ===")
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)

    img_path = IMAGE_PATHS[0]
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    try:
        for i in range(TOTAL_REQUESTS):
            batch = []
            for j in range(fps):
                batch.append({
                    "filename": f"{os.path.basename(img_path)}_copy{j}",
                    "data": base64.b64encode(img_bytes).decode("utf-8"),
                    "gen_at": datetime.now().isoformat(),
                    "req_id": i,
                    "fps": fps
                })
            client.publish(MQTT_TOPIC, json.dumps({"batch": batch}))
            log(f"MQTT request {i+1}/{TOTAL_REQUESTS} published with {fps} frames")
            time.sleep(0.05)
    except Exception as e:
        log(f"MQTT test failed at FPS={fps}: {e}")
    finally:
        client.disconnect()
        log(f"=== Finished MQTT test at {fps} FPS ===")

# ------------------ Main ------------------
if __name__ == "__main__":
    log("=== Starting multi-FPS sender test ===")
    network_test()
    for fps in FPS_LIST:
        
        start = time.time()
        #send_http(fps)
        # send_mqtt(fps)
        elapsed = time.time() - start
        log(f"Completed all tests at {fps} FPS in {elapsed:.2f} seconds\n")

    log_file.close()