import os
import time
import logging
from datetime import datetime
from ping3 import ping
import psutil
import torch
import pynvml
import speedtest
from PIL import Image
from ultralytics import YOLO

from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer


# ------------------ CONFIG ------------------
IMAGE_PATH = "./Senders/imgs/cat1_m.jpg"   # single image for repeated runs
MODEL_PATH = "yolo11l.pt"
DEVICE = "cpu"  # or 'cuda' if GPU is available

FPS_LIST = [1, 5, 10, 20, 40, 60]
NUM_ITERATIONS = 60

HOST = "8.8.8.8"
GEN_AT = datetime.now().isoformat()
EXP_ID = 2
# -------------------------------------------


# ------------------ LOGGING -----------------
log_filename = "yolo_wf1.2.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

def log(msg):
    logging.info(msg)
# -------------------------------------------


# ---------------- NETWORK TEST --------------
log("=== Starting network test ===")

latency = ping(HOST)
st = speedtest.Speedtest(secure=True)
st.get_best_server()
download_speed = st.download() / 1_000_000  # Mbps
upload_speed = st.upload() / 1_000_000      # Mbps

log(f"Ping to {HOST}: {latency*1000:.2f} ms")
log(f"Download Speed: {download_speed:.2f} Mbps")
log(f"Upload Speed: {upload_speed:.2f} Mbps")
# -------------------------------------------


# ------------------ INIT --------------------
log("Initializing YOLO model...")
model = YOLO(MODEL_PATH)

pynvml.nvmlInit()
gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

#image = Image.open(IMAGE_PATH)
#req_id = REQ_START_ID
# -------------------------------------------


# ------------------ MAIN LOOP ---------------
for fps in FPS_LIST:
    log(f"=== Starting FPS={fps} experiment ===")

    sleep_time = 1.0 / fps

    for i in range(NUM_ITERATIONS):
        try:
            log(f"Running iteration {i+1}/{NUM_ITERATIONS} | FPS={fps}")

            GEN_AT = datetime.now().isoformat()
            image = Image.open(IMAGE_PATH)
            req_id = i + FPS_LIST.index(fps) * NUM_ITERATIONS

            model_in = datetime.now()

            results = model.predict(
                source=[image],
                batch=1,
                device=DEVICE
            )

            model_out = datetime.now()

            # GPU stats
            mem = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
            power = pynvml.nvmlDeviceGetPowerUsage(gpu_handle) / 1000
            temp = pynvml.nvmlDeviceGetTemperature(
                gpu_handle, pynvml.NVML_TEMPERATURE_GPU
            )
            util_rates = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)

            exp = Experiment(
                gen_at=GEN_AT,
                exp_id=EXP_ID,
                req_id=req_id,
                model_in=model_in,
                model_out=model_out,
                cpu_usage=psutil.cpu_percent(interval=0, percpu=False),
                memory_usage=psutil.virtual_memory().percent,
                process_count=len(psutil.pids()),
                gpu_usage=util_rates.gpu,
                gpu_vram_usage=(
                    mem.used / mem.total * 100 if mem.total > 0 else 0
                ),
                gpu_temperature=temp,
                gpu_power=power,
                fps=fps
            )

            save_experiment_to_buffer(exp)

            time.sleep(sleep_time)
            req_id += 1

        except Exception as e:
            log(f"ERROR | FPS={fps} | iter={i} | {str(e)}")

log("All experiments completed.")
# -------------------------------------------
