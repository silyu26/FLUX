import requests
import time
import speedtest
from datetime import datetime
from ping3 import ping
import sys

# --- Logging setup ---
log_filename = "run_logs.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file  # Redirect all print() output to file
sys.stderr = log_file

def log(msg):
    """Helper function to log messages with timestamp"""
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# --- Settings ---
host = '8.8.8.8'
API_URL = "http://127.0.0.1:5000/yolo/"
IMAGE_PATHS = ["./imgs/cat1.jpg"]
FPS_LIST = [1, 5, 10, 20, 40]
NUM_ITERATIONS = 50

# --- Network check ---
log("=== Starting network test ===")
latency = ping(host)
st = speedtest.Speedtest()
st.get_best_server()
download_speed = st.download() / 1_000_000  # in Mbps
upload_speed = st.upload() / 1_000_000      # in Mbps

log(f"Ping to {host}: {latency*1000:.2f} ms")
log(f"Download Speed: {download_speed:.2f} Mbps")
log(f"Upload Speed: {upload_speed:.2f} Mbps")

# --- Run tests for each FPS ---
for fps in FPS_LIST:
    log(f"\n=== Starting test at {fps} FPS ===")
    start_time = time.time()

    for i in range(NUM_ITERATIONS):
        img_path = IMAGE_PATHS[0]
        files = []

        for j in range(fps):
            try:
                files.append(("files", (f"{img_path}_copy{j}", open(img_path, "rb"), "image/jpeg")))
            except Exception as e:
                log(f"Error opening image: {e}")
                continue

        data = {"gen_at": datetime.now().isoformat(), "req_id": i, "fps": fps}
        try:
            response = requests.post(API_URL, files=files, data=data)
            log(f"Iteration {i+1}/{NUM_ITERATIONS} | FPS={fps} | Status={response.status_code}")
        except Exception as e:
            log(f"Request failed on iteration {i+1}: {e}")

        # Optional small delay between iterations to avoid flooding
        time.sleep(0.05)

    elapsed = time.time() - start_time
    log(f"Finished test at {fps} FPS in {elapsed:.2f} seconds")

log("=== All tests completed ===")
log_file.close()
