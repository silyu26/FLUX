import socket
import time
import json
import base64
import struct
import threading
import os
from datetime import datetime

# --- Configuration ---
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5006
PAYLOAD_SIZE = 60000  # Max bytes per packet (UDP MTU safe-ish)

IMAGE_PATH = "./Senders/imgs/cat1_m.jpg"
FPS_LIST = [1, 5, 10, 20]
NUM_ITERATIONS = 60

# --- RTP State Variables ---
SEQ_NUM = 0
TIMESTAMP = 0
SSRC = 12345678  # Random ID for this source
PAYLOAD_TYPE = 96  # Dynamic payload type

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def create_rtp_header(seq, ts, ssrc, marker):
    """
    Constructs a 12-byte RTP header.
    Format: !BBHII (Network Endian, 1B, 1B, 2B, 4B, 4B)
    """
    # Byte 0: Version (2 bits), Padding (1), Extension (1), CSRC Count (4)
    # V=2 (10), P=0, X=0, CC=0 -> 10000000 -> 0x80
    byte0 = 0x80
    
    # Byte 1: Marker (1 bit), Payload Type (7 bits)
    # M=1 if last chunk, else 0
    byte1 = (marker << 7) | PAYLOAD_TYPE
    
    return struct.pack("!BBHII", byte0, byte1, seq, ts, ssrc)

def send_frame_rtp(req_id, json_payload):
    global SEQ_NUM, TIMESTAMP
    
    data_bytes = json_payload.encode('utf-8')
    total_len = len(data_bytes)
    offset = 0
    
    # Increment timestamp for this new frame (arbitrary step, e.g., 3000 ticks)
    TIMESTAMP += 3000 
    
    while offset < total_len:
        # Determine chunk size
        chunk_size = min(PAYLOAD_SIZE, total_len - offset)
        chunk = data_bytes[offset : offset + chunk_size]
        offset += chunk_size
        
        # Is this the last chunk?
        is_last = (offset >= total_len)
        marker_bit = 1 if is_last else 0
        
        # Create Header
        header = create_rtp_header(SEQ_NUM, TIMESTAMP, SSRC, marker_bit)
        
        # Send Packet
        sock.sendto(header + chunk, (TARGET_IP, TARGET_PORT))
        
        # Increment Sequence (wraps at 65535)
        SEQ_NUM = (SEQ_NUM + 1) % 65535

def response_listener():
    """Simple listener for completion signals"""
    s_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_listen.bind(("0.0.0.0", 5007)) # Listen port for Ack
    while True:
        try:
            data, _ = s_listen.recvfrom(1024)
            print(f"[{datetime.now().time()}] ACK Received: {data.decode()}")
        except:
            pass

# Start ACK listener
t = threading.Thread(target=response_listener, daemon=True)
t.start()

print(f"RTP Sender targeting {TARGET_IP}:{TARGET_PORT}")

# --- Main Loop ---
for fps in FPS_LIST:
    print(f"\n=== Starting RTP Stream at {fps} FPS ===")
    for i in range(NUM_ITERATIONS):
        req_id = i + (FPS_LIST.index(fps) * 1000)
        
        # Load Image
        with open(IMAGE_PATH, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        msg = {
            "req_id": req_id,
            "fps": fps,
            "image": image_b64
        }
        
        send_frame_rtp(req_id, json.dumps(msg))
        print(f"Sent Frame {i} via RTP (TS={TIMESTAMP})")
        
        time.sleep(1/fps)

print("RTP Stream Finished.")