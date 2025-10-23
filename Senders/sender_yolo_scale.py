import requests
import time
import speedtest
from datetime import datetime
from ping3 import ping
#from SQL.save_data import push_buffer_to_db
import sys
import threading # Import the threading module

# --- Settings (Global) ---
HOST = '8.8.8.8'
API_URL = "http://127.0.0.1:5001/yolo/"
IMAGE_PATHS = ["./Senders/imgs/cat1_m.jpg"]
FPS_LIST = [1, 5, 10, 20, 40, 60]
NUM_ITERATIONS = 2

def run_sender(sender_id, workflow_n, exp_id):
    """
    This function contains the logic for a single sender.
    It will be executed in its own thread.
    """
    
    # --- Logging setup for this specific sender ---
    log_filename = f"workflow_{workflow_n}_expId_{exp_id}_sender_{sender_id}.txt"
    try:
        log_file = open(log_filename, "a", encoding="utf-8")
    except Exception as e:
        print(f"[Sender {sender_id}] ERROR: Could not open log file {log_filename}. {e}")
        return # Stop this thread if logging fails

    def log(msg):
        """Helper function to log messages with timestamp to this sender's file"""
        try:
            log_file.write(f"[{datetime.now().isoformat()}] [Sender {sender_id}] {msg}\n")
            log_file.flush()
        except Exception as e:
            print(f"[Sender {sender_id}] ERROR writing to log: {e}")

    log(f"=== Sender thread {sender_id} started ===")

    # Calculate a unique ID offset for this sender
    # This ensures req_id is unique across all senders
    total_reqs_per_sender = len(FPS_LIST) * NUM_ITERATIONS
    id_offset = (sender_id - 1) * total_reqs_per_sender

    # --- Network check ---
    log("=== Starting network test ===")
    try:
        latency = ping(HOST)
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # in Mbps
        upload_speed = st.upload() / 1_000_000      # in Mbps

        log(f"Ping to {HOST}: {latency*1000:.2f} ms" if latency is not None else f"Ping to {HOST}: FAILED")
        log(f"Download Speed: {download_speed:.2f} Mbps")
        log(f"Upload Speed: {upload_speed:.2f} Mbps")
    except Exception as e:
        log(f"Network test failed: {e}")

    # --- Run tests for each FPS ---
    for fps in FPS_LIST:
        index = FPS_LIST.index(fps)
        log(f"\n=== Starting test at {fps} FPS ===")
        start_time = time.time()

        for i in range(NUM_ITERATIONS):
            img_path = IMAGE_PATHS[0]
            files = []

            try:
                # Note: 'open()' should be inside the loop if the server closes it.
                # But for 'requests', it's better to open/close each time.
                files.append(("file", (f"{img_path}", open(img_path, "rb"), "image/jpeg")))
            except Exception as e:
                log(f"Error opening image: {e}")
                continue # Skip this iteration

            # Calculate unique req_id
            current_req_id = id_offset + (index * NUM_ITERATIONS) + i
            data = {"gen_at": datetime.now().isoformat(), "req_id": current_req_id, "fps": fps, "expId": exp_id, "device": f"sender_{sender_id}"}
            
            try:
                # The 'with' statement for files is handled by requests.post
                response = requests.post(API_URL, files=files, data=data)
                log(f"Iteration {i+1}/{NUM_ITERATIONS} | FPS={fps} | ReqID={current_req_id} | Status={response.status_code}")
            except Exception as e:
                log(f"Request failed on iteration {i+1} (ReqID={current_req_id}): {e}")
            finally:
                # Ensure file handles are closed
                for _, file_tuple in files:
                    file_tuple[1].close()

            # Sleep to maintain the target FPS
            time.sleep(1/fps)

        elapsed = time.time() - start_time
        log(f"Finished test at {fps} FPS in {elapsed:.2f} seconds")

    log(f"=== Sender {sender_id} tests completed ===")
    log_file.close()

# --- Main execution ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <n_workflow> <expId> <num_senders>")
        print("Example: python script.py 1 exp_A 4")
        sys.exit(1)

    n = sys.argv[1]       # workflow
    exp = sys.argv[2]     # expId
    try:
        num_senders = int(sys.argv[3]) # Number of concurrent senders
        if num_senders <= 0:
            raise ValueError("Number of senders must be greater than 0")
    except ValueError as e:
        print(f"Error: Invalid number of senders. Must be an integer > 0. {e}")
        sys.exit(1)

    print(f"--- Starting {num_senders} concurrent sender(s) ---")
    print(f"Workflow: {n}, Experiment ID: {exp}")
    print("Each sender will write to its own log file.")

    threads = []
    for i in range(num_senders):
        sender_id = i + 1 # Use 1-based ID for clarity (sender_1, sender_2)
        # Create a new thread targeting the run_sender function
        t = threading.Thread(target=run_sender, args=(sender_id, n, exp))
        threads.append(t)
        t.start() # Start the thread
        print(f"Started sender {sender_id}...")

    # Wait for all threads to complete their execution
    for t in threads:
        t.join()

    print(f"\n--- All {num_senders} senders have completed their tasks. ---")