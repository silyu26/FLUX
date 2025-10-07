import cv2
import psutil
import time
from datetime import datetime
from ultralytics import YOLO
from SQL import crud, db
import model
import os

# --- Settings ---
RECEIVER_IP = "0.0.0.0"  # Listen on all available network interfaces
RTP_PORT = 5000
expId = 11 # Using a new experiment ID

# --- Model and DB Setup ---
print("Loading YOLO model...")
model = YOLO("yolo11n.pt")
db_session = db.SessionLocal()
print("Model loaded and DB session created.")

def main():
    # GStreamer pipeline for receiving an H.264 encoded RTP stream over UDP
    # This pipeline listens on the specified port, depacketizes the RTP stream,
    # decodes the H.264 video, converts the color space, and sends it to the app.
    pipeline = (
        f"udpsrc port={RTP_PORT} caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! "
        "rtph264depay ! "
        "decodebin ! "
        "videoconvert ! "
        "appsink"
    )

    # Use CAP_GSTREAMER to tell OpenCV to use the GStreamer backend
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: VideoCapture not opened. Check GStreamer installation and the pipeline.")
        return

    print(f"Listening for RTP stream on port {RTP_PORT}...")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or error reading frame.")
            break
        
        # --- Start of Inference and Logging Logic (from your original FastAPI endpoint) ---
        model_in = datetime.now()

        # Run YOLO inference
        results = model.predict(source=frame, verbose=False) # verbose=False to keep logs clean

        model_out = datetime.now()
        frame_count += 1

        # Calculate processing FPS (how fast this receiver is processing frames)
        # This is an approximation. For more accuracy, use a rolling average.
        processing_time = (model_out - model_in).total_seconds()
        current_processing_fps = 1 / processing_time if processing_time > 0 else float('inf')

        # Create experiment record
        exp = model.Experiment(
            gen_at=model_in.isoformat(), # We use model_in as the generation time at receiver
            exp_id=expId,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            fps=int(current_processing_fps) # Log the actual processing FPS
        )
        crud.create_experiment_with_weather(db_session, exp)
        
        print(
            f"Frame {frame_count}: "
            f"Processed in {processing_time*1000:.2f} ms "
            f"(~{current_processing_fps:.2f} FPS) | "
            f"CPU: {exp.cpu_usage}% | "
            f"Mem: {exp.memory_usage}%"
        )
        
        # Optionally, display the video feed with bounding boxes
        # annotated_frame = results[0].plot()
        # cv2.imshow('YOLO Inference', annotated_frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    # --- Cleanup ---
    cap.release()
    # cv2.destroyAllWindows()
    db_session.close()
    print("Stream finished.")


if __name__ == "__main__":
    main()