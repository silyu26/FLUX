import socket
import json
import base64
import time
import io
import struct
import psutil
import pynvml
from datetime import datetime
from PIL import Image
from ultralytics import YOLO
import logging
from collections import defaultdict
import os # Added for file operations
from SQL.model import Experiment
from SQL.buffer_data import save_experiment_to_buffer

# --- Configuration ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5000
MAX_DGRAM = 65000  # Safe buffer size for recv
EXPERIMENT_DATA_FILE = "udp_experiment_data.jsonl" # New file for metrics

# --- Setup Logging & Model ---
log_filename = "yolo_wf5.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
model = YOLO("yolo11l.pt")
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
logging.info("YOLO model loaded.")

# --- UDP Socket Setup ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
logging.info(f"UDP Receiver listening on port {UDP_PORT}")
#uvicorn YOLO.yolo_v11_udp:app --reload --host 0.0.0.0 --port 5000
# Buffer to hold chunks: { req_id: { seq_num: data } }
frame_buffer = defaultdict(dict)
frame_meta = {} # { req_id: total_chunks }

while True:
    try:
        # 1. Receive Chunk
        packet, addr = sock.recvfrom(MAX_DGRAM)
        
        # 2. Parse Header (First 8 bytes)
        req_id, seq_num, total_chunks = struct.unpack("!IHH", packet[:8])
        chunk_data = packet[8:]

        # 3. Store Chunk
        frame_buffer[req_id][seq_num] = chunk_data
        frame_meta[req_id] = total_chunks

        # 4. Check if Frame is Complete
        if len(frame_buffer[req_id]) == total_chunks:
            logging.info(f"Reassembled frame {req_id} from {total_chunks} chunks.")
            
            # Reconstruct Full Data
            full_data = b"".join([frame_buffer[req_id][i] for i in range(total_chunks)])
            payload = json.loads(full_data.decode('utf-8'))
            
            # Clean up buffer to save memory
            del frame_buffer[req_id]
            del frame_meta[req_id]

            # --- INFERENCE LOGIC ---
            time.sleep(0.5)
            model_in = datetime.now()
            image_data = base64.b64decode(payload["image"])
            image = Image.open(io.BytesIO(image_data))
            
            results = model.predict(source=[image], batch=1, device='cuda', verbose=False)
            r = results[0]

            if len(r.boxes) > 0:
                best = r.boxes[r.boxes.conf.argmax()]  # highest-confidence detection
                cls_id = int(best.cls[0])
                class_name = model.names[cls_id]
                logging.info(f"Best detection for req_id={req_id}: {class_name}")
            else:
                logging.info(f"No detections for req_id={req_id}")
            model_out = datetime.now()

            # --- METRICS COLLECTION (New) ---
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000   # watts
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            util_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Get experiment details from payload (assuming they exist or setting defaults)
            exp_id = payload.get("expId", 0) # Assuming expId is now sent in the payload
            gen_at = payload.get("gen_at", 0)
            fps = payload.get("fps", 0)

            # --- SAVE EXPERIMENT DATA (New) ---
            exp = Experiment(
                gen_at=gen_at,
                exp_id=exp_id,
                req_id=req_id,
                model_in=model_in,
                model_out=model_out,
                cpu_usage=psutil.cpu_percent(interval=0,percpu=False),
                memory_usage=psutil.virtual_memory().percent,
                process_count=len(psutil.pids()),
                gpu_usage=util_rates.gpu,
                gpu_vram_usage=mem.used / mem.total * 100 if mem.total > 0 else 0,
                gpu_temperature=temp,
                gpu_power=power,
                fps=fps
            )
            save_experiment_to_buffer(exp)
            
            logging.info(f"Experiment data saved for req_id={req_id}")


            # --- PREPARE & SEND RESPONSE ---
            response = {
                "req_id": req_id,
                "fps": fps, # Use the potentially updated FPS value
                "predictions": results[0].boxes.xyxy.tolist(),
                "classes": results[0].boxes.cls.tolist(),
                "model_out": model_out.isoformat()
            }
            
            # Send Response back to Sender
            resp_bytes = json.dumps(response).encode('utf-8')
            sock.sendto(resp_bytes, addr)
            logging.info(f"Sent response for req_id={req_id} to {addr}")

    except Exception as e:
        logging.error(f"Error: {e}")