import time
import json
import base64
import speedtest
from datetime import datetime
from ping3 import ping
import sys
import os
import threading
from confluent_kafka import Producer, Consumer, KafkaError

if len(sys.argv) < 3:
    print("Usage: python sender_yolo_kafka.py <workflow> <expId>")
    sys.exit(1)

workflow = sys.argv[1]
exp = sys.argv[2]

# Logging setup
log_filename = f"workflow_{workflow}_expId_{exp}.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# --- Kafka Configuration ---
# REPLACE WITH YOUR SERVER LAPTOP IP
BOOTSTRAP_SERVERS = "192.168.2.101:9092" 
TOPIC_REQUEST = "yolo-requests"
TOPIC_RESPONSE = "yolo-responses"

IMAGE_PATH = "./Senders/imgs/cat1_m.jpg"
FPS_LIST = [1, 5, 10, 20, 40, 60]
NUM_ITERATIONS = 60

# --- Kafka Producer Setup ---
producer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'message.max.bytes': 10485760  # Allow sending up to 10 MB
}
producer = Producer(producer_conf)

# --- Kafka Consumer Setup (for responses) ---
# Running consumer in a separate thread to mimic Paho's loop_start()
def response_listener():
    consumer_conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': f'sender-group-{exp}',
        'auto.offset.reset': 'latest'
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([TOPIC_RESPONSE])

    log("Response listener thread started.")
    
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            log(f"Consumer error: {msg.error()}")
            continue
            
        try:
            payload = json.loads(msg.value().decode('utf-8'))
            # Filter responses for this specific experiment
            if str(payload.get('expId')) == str(exp):
                log(f"Response received | req_id={payload.get('req_id')} | status=ok")
        except Exception as e:
            log(f"Error decoding response: {e}")

# Start listener in background
t = threading.Thread(target=response_listener, daemon=True)
t.start()

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        log(f'Message delivery failed: {err}')
    # else:
    #     log(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# --- Network check ---
host = "8.8.8.8"
log("=== Starting network test ===")
try:
    latency = ping(host)
    st = speedtest.Speedtest(secure=True)
    st.get_best_server()
    download_speed = st.download() / 1_000_000
    upload_speed = st.upload() / 1_000_000
    log(f"Ping to {host}: {latency*1000:.2f} ms")
    log(f"Download Speed: {download_speed:.2f} Mbps")
    log(f"Upload Speed: {upload_speed:.2f} Mbps")
except Exception as e:
    log(f"Network test failed: {e}")

# --- Send images ---
for fps in FPS_LIST:
    index = FPS_LIST.index(fps)
    log(f"\n=== Starting test at {fps} FPS ===")
    start_time = time.time()

    for i in range(NUM_ITERATIONS):
        try:
            tmp = time.time()
            acq_start = datetime.now().isoformat()
            with open(IMAGE_PATH, "rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            tmp2 = time.time()
            log(f"Image read and encoded in {tmp2 - tmp:.4f} seconds")

            message = {
                "acq_start": acq_start,
                "gen_at": datetime.now().isoformat(),
                "req_id": i + index * 60,
                "fps": fps,
                "expId": exp,
                "image": image_b64,
                "filename": os.path.basename(IMAGE_PATH)
            }

            # Produce to Kafka
            # trigger delivery_report callback to confirm receipt
            producer.produce(
                TOPIC_REQUEST, 
                key=str(message['req_id']), 
                value=json.dumps(message), 
                on_delivery=delivery_report
            )
            
            # Serve delivery reports (async)
            producer.poll(0)
            
            log(f"Published frame {i+1}/{NUM_ITERATIONS} at {fps} FPS")

        except Exception as e:
            log(f"Error sending frame {i+1}: {e}")

        # Maintain the simulated FPS rate
        time.sleep(1 / fps)

    elapsed = time.time() - start_time
    log(f"Finished test at {fps} FPS in {elapsed:.2f} seconds")

    # Ensure all messages are sent before moving to next FPS block
    producer.flush()

log("=== All tests completed ===")
log_file.close()