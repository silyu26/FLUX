import socket
import struct
import json
import base64
import io
from collections import defaultdict
from ultralytics import YOLO
from PIL import Image
from datetime import datetime
import logging

# --- Config ---
BIND_IP = "0.0.0.0"
BIND_PORT = 5006
SENDER_ACK_PORT = 5007

# --- Logging & Model ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(INFO)s] %(message)s")
model = YOLO("yolo11l.pt")
logging.info("YOLO Loaded.")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((BIND_IP, BIND_PORT))
logging.info(f"RTP Receiver listening on {BIND_PORT}")

# Buffers
# Buffer structure: { timestamp: { seq_num: payload_bytes } }
rtp_buffer = defaultdict(dict)

while True:
    try:
        packet, addr = sock.recvfrom(65535)
        
        # --- Parse RTP Header (12 Bytes) ---
        if len(packet) < 12:
            continue

        header = packet[:12]
        payload = packet[12:]
        
        # Unpack !BBHII
        b0, b1, seq_num, timestamp, ssrc = struct.unpack("!BBHII", header)
        
        # Extract flags
        version = (b0 >> 6) & 0x03
        marker_bit = (b1 >> 7) & 0x01
        payload_type = b1 & 0x7F
        
        # Store payload in buffer grouped by TIMESTAMP
        rtp_buffer[timestamp][seq_num] = payload
        
        # --- Check for End of Frame ---
        if marker_bit == 1:
            # Sort chunks by sequence number to ensure correct order
            sorted_seq = sorted(rtp_buffer[timestamp].keys())
            
            # Reassemble
            full_data = b"".join([rtp_buffer[timestamp][seq] for seq in sorted_seq])
            
            try:
                # Decode JSON
                json_str = full_data.decode('utf-8')
                data = json.loads(json_str)
                req_id = data.get('req_id', 'unknown')
                
                logging.info(f"Reassembled Frame (TS={timestamp}). Running Inference...")
                
                # Inference
                img_bytes = base64.b64decode(data['image'])
                image = Image.open(io.BytesIO(img_bytes))
                results = model.predict(image, verbose=False)
                
                logging.info(f"Inference Done for req_id={req_id}")
                
                # Send simple ACK back to sender
                ack_msg = f"Done {req_id}".encode()
                sock.sendto(ack_msg, (addr[0], SENDER_ACK_PORT))
                
            except Exception as e:
                logging.error(f"Failed to process frame: {e}")
            
            # Cleanup buffer
            del rtp_buffer[timestamp]
            
            # Optional: Garbage collect old timestamps if buffer gets too big
            if len(rtp_buffer) > 10:
                rtp_buffer.clear()

    except Exception as e:
        logging.error(f"Socket Error: {e}")