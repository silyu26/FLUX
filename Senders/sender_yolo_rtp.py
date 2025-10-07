import cv2
import time
from datetime import datetime
import sys

# --- Logging setup ---
log_filename = "run_logs_rtp.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

def log(msg):
    """Helper function to log messages with timestamp"""
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

# --- Settings ---
RECEIVER_IP = '127.0.0.1'  # IP address of the receiver
RTP_PORT = 5000
IMAGE_PATH = "./imgs/cat1.jpg"
FPS_LIST = [1, 5, 10, 20, 40]
DURATION_PER_FPS = 10  # Stream for 10 seconds at each FPS setting

# --- Run tests for each FPS ---
for fps in FPS_LIST:
    log(f"\n=== Starting stream at {fps} FPS for {DURATION_PER_FPS} seconds ===")
    
    # Read the source image
    frame = cv2.imread(IMAGE_PATH)
    if frame is None:
        log(f"Error: Could not read image at {IMAGE_PATH}")
        continue
    
    frame_height, frame_width, _ = frame.shape

    # GStreamer pipeline for encoding the stream to H.264 and sending via RTP
    # This pipeline takes frames from the app (appsrc), converts them,
    # encodes them using x264enc with a zero-latency profile, packetizes for RTP,
    # and sends them over UDP.
    pipeline = (
        "appsrc ! "
        "videoconvert ! "
        f"video/x-raw,format=I420,width={frame_width},height={frame_height},framerate={fps}/1 ! "
        "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
        "rtph264pay ! "
        f"udpsink host={RECEIVER_IP} port={RTP_PORT}"
    )

    # Create the VideoWriter object
    writer = cv2.VideoWriter(pipeline, cv2.CAP_GSTREAMER, 0, fps, (frame_width, frame_height))

    if not writer.isOpened():
        log(f"Error: VideoWriter not opened for FPS={fps}. Check GStreamer installation.")
        continue

    start_time = time.time()
    frames_sent = 0
    total_frames_to_send = DURATION_PER_FPS * fps

    log(f"Streaming {total_frames_to_send} frames...")
    
    while frames_sent < total_frames_to_send:
        # Write the same frame repeatedly to the stream
        writer.write(frame)
        frames_sent += 1
        # Sleep to maintain the target FPS
        time.sleep(1 / fps) 

    elapsed = time.time() - start_time
    log(f"Finished streaming at {fps} FPS. Sent {frames_sent} frames in {elapsed:.2f} seconds.")
    
    # Release the writer to close the stream for this FPS
    writer.release()
    # Small delay before starting the next stream
    time.sleep(2)


log("\n=== All streaming tests completed ===")
log_file.close()