import cv2
import psutil
import time
from datetime import datetime
from ultralytics import YOLO
from SQL import crud, db
import model
import os

# --- Settings ---
IMAGE_PATH = "./imgs/cat1.jpg"   # Example static image (can be replaced with real frame source)
FPS = 10                         # Simulated streaming FPS
TOTAL_FRAMES = 100               # How many frames to simulate
expId = 0                        # Experiment ID

# --- Model and DB Setup ---
print("Loading YOLO model...")
yolo_model = YOLO("yolo11n.pt")
db_session = db.SessionLocal()
print("Model loaded and DB session created.")

def main():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        return

    print(f"Simulating image stream from {IMAGE_PATH} at {FPS} FPS...")

    frame_count = 0
    frame_interval = 1.0 / FPS  # seconds per frame

    while frame_count < TOTAL_FRAMES:
        frame = cv2.imread(IMAGE_PATH)
        if frame is None:
            print("Error loading image. Check path or format.")
            break

        # --- YOLO Inference ---
        model_in = datetime.now()
        results = yolo_model.predict(source=frame, verbose=False)
        model_out = datetime.now()

        # --- Performance and Resource Metrics ---
        frame_count += 1
        processing_time = (model_out - model_in).total_seconds()
        current_processing_fps = 1 / processing_time if processing_time > 0 else float('inf')

        exp = model.Experiment(
            gen_at=model_in.isoformat(),
            exp_id=expId,
            model_in=model_in,
            model_out=model_out,
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            process_count=len(psutil.pids()),
            fps=int(current_processing_fps)
        )

        crud.create_experiment_with_weather(db_session, exp)

        print(
            f"Frame {frame_count}/{TOTAL_FRAMES}: "
            f"Processed in {processing_time*1000:.2f} ms "
            f"(~{current_processing_fps:.2f} FPS) | "
            f"CPU: {exp.cpu_usage}% | "
            f"Mem: {exp.memory_usage}%"
        )

        # Optional: visualize results
        # annotated = results[0].plot()
        # cv2.imshow("YOLO Stream", annotated)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        # Wait so the loop matches the target FPS
        time.sleep(frame_interval)

    db_session.close()
    print("Stream simulation finished.")

if __name__ == "__main__":
    main()
