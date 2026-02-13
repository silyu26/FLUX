import socket
import time
import json
import base64
import struct
import threading
import sys
import os
from datetime import datetime
import speedtest
from ping3 import ping # Added for network check

if len(sys.argv) < 3:
    # Adjusted usage message to reflect the necessary arguments
    print("Usage: python script.py <n> <expId>")
    sys.exit(1)

n = sys.argv[1] # workflow ID (unused in current logic, but kept for consistency)
EXP_ID = sys.argv[2] # expId
# python -m Senders.sender_yolo_udp n exp

# --- Logging setup (Matching sender_yolo_fat.py) ---
log_filename = f"udp_workflow_{n}_expId_{EXP_ID}.txt"
# If you want to redirect all output, use the setup below:
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

def log(msg):
    """Helper function to log messages with timestamp"""
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# --- Configuration ---
TARGET_IP = "192.168.2.101"
TARGET_PORT = 5000
CHUNK_SIZE = 60000 # Leave room for header (< 65535)

IMAGE_PATH = "./Senders/imgs/cat1_m.jpg"
FPS_LIST = [1, 5, 10, 20, 40]
NUM_ITERATIONS = 60

# --- Network check (Matching sender_yolo_fat.py) ---
log("=== Starting network test ===")
host = '8.8.8.8'
latency = ping(host)
st = speedtest.Speedtest(secure=True)
st.get_best_server()
download_speed = st.download() / 1_000_000  # in Mbps
upload_speed = st.upload() / 1_000_000      # in Mbps

log(f"Ping to {host}: {latency*1000:.2f} ms")
log(f"Download Speed: {download_speed:.2f} Mbps")
log(f"Upload Speed: {upload_speed:.2f} Mbps")

# --- UDP Socket Setup ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# We set a timeout so the listener thread doesn't block forever
sock.settimeout(1.0) 

def chunk_and_send(req_id, payload_bytes):
    """Splits bytes into chunks and sends with header."""
    total_len = len(payload_bytes)
    total_chunks = (total_len // CHUNK_SIZE) + (1 if total_len % CHUNK_SIZE != 0 else 0)
    
    for i in range(total_chunks):
        start = i * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk = payload_bytes[start:end]
        
        # Header: req_id (4B), seq_num (2B), total_chunks (2B)
        # struct format "!IHH" means Network Endian, Int, Short, Short
        header = struct.pack("!IHH", req_id, i, total_chunks)
        
        sock.sendto(header + chunk, (TARGET_IP, TARGET_PORT))

def response_listener():
    """Background thread to catch UDP responses."""
    log("Listener thread started...")
    while True:
        try:
            data, _ = sock.recvfrom(65535)
            resp = json.loads(data.decode('utf-8'))
            log(f"Response received | req_id={resp.get('req_id')}")
        except socket.timeout:
            continue # Loop back
        except Exception as e:
            log(f"Listener Error: {e}")

# Start Listener
t = threading.Thread(target=response_listener, daemon=True)
t.start()

# --- Main Sending Loop ---
log(f"UDP Sender targeting {TARGET_IP}:{TARGET_PORT}")

for fps in FPS_LIST:
    log(f"\n=== Starting test at {fps} FPS ===")
    
    for i in range(NUM_ITERATIONS):
        # The req_id calculation is slightly different from the FAT sender's calculation 
        # but ensures uniqueness, which is the main goal.
        req_id = i + (FPS_LIST.index(fps) * 1000) 
        
        # Prepare Image
        try:
            acq_start = datetime.now().isoformat()
            with open(IMAGE_PATH, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            log(f"Error reading image: {e}")
            continue
        
        # --- Data Fields Updated Here ---
        message = {
            "acq_start": acq_start,
            "req_id": req_id,
            "fps": fps,
            "gen_at": datetime.now().isoformat(),
            "image": image_b64,
            "expId": EXP_ID # <<< ADDED expId
        }
        
        # Serialize and Send
        json_bytes = json.dumps(message).encode('utf-8')
        chunk_and_send(req_id, json_bytes)
        
        log(f"Sent frame {i+1}/{NUM_ITERATIONS} (req_id={req_id})")
        time.sleep(1 / fps)

log("Tests completed.")
log_file.close() # Close log file at the end