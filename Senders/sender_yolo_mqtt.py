import paho.mqtt.client as mqtt
import time
import json
import base64
import speedtest
from datetime import datetime
from ping3 import ping
import sys
import os

if len(sys.argv) < 3:
    print("Usage: python mqtt_sender.py <workflow> <expId>")
    sys.exit(1)

workflow = sys.argv[1]
exp = sys.argv[2]
log_filename = f"workflow_{workflow}_expId_{exp}.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

BROKER = "127.0.0.1"
PORT = 1883
TOPIC_REQUEST = "yolo/requests"
TOPIC_RESPONSE = f"yolo/responses/{exp}"

IMAGE_PATH = "./Senders/imgs/cat1_m.jpg"
FPS_LIST = [1, 5, 10, 20, 40, 60]
NUM_ITERATIONS = 30

# --- Setup MQTT ---
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    log(f"Connected to MQTT broker with code {rc}")
    client.subscribe(TOPIC_RESPONSE)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    log(f"Response received | req_id={payload.get('req_id')} | status=ok")

client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# --- Network check ---
host = "8.8.8.8"
log("=== Starting network test ===")
latency = ping(host)
st = speedtest.Speedtest(secure=True)
st.get_best_server()
download_speed = st.download() / 1_000_000
upload_speed = st.upload() / 1_000_000

log(f"Ping to {host}: {latency*1000:.2f} ms")
log(f"Download Speed: {download_speed:.2f} Mbps")
log(f"Upload Speed: {upload_speed:.2f} Mbps")

# --- Send images ---
for fps in FPS_LIST:
    index = FPS_LIST.index(fps)
    log(f"\n=== Starting test at {fps} FPS ===")
    start_time = time.time()

    for i in range(NUM_ITERATIONS):
        try:
            with open(IMAGE_PATH, "rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            message = {
                "gen_at": datetime.now().isoformat(),
                "req_id": i + index * 30,
                "fps": fps,
                "expId": exp,
                "image": image_b64,
                "filename": os.path.basename(IMAGE_PATH)
            }

            client.publish(TOPIC_REQUEST, json.dumps(message))
            log(f"Published frame {i+1}/{NUM_ITERATIONS} at {fps} FPS")

        except Exception as e:
            log(f"Error sending frame {i+1}: {e}")

        time.sleep(1 / fps)

    elapsed = time.time() - start_time
    log(f"Finished test at {fps} FPS in {elapsed:.2f} seconds")

log("=== All tests completed ===")
client.loop_stop()
client.disconnect()
log_file.close()
