import requests
import time
import speedtest
from datetime import datetime
from ping3 import ping

host = '8.8.8.8'
API_URL = "http://127.0.0.1:5000/yolo/"
IMAGE_PATHS = ["./imgs/cat1.jpg"]
fps = 1

# network checking
latency = ping(host)
st = speedtest.Speedtest()
st.get_best_server()
download_speed = st.download() / 1_000_000  # in Mbps
upload_speed = st.upload() / 1_000_000      # in Mbps

print(f"Ping to {host}: {latency*1000:.2f} ms")
print("Download Speed:", download_speed, "Mbps")
print("Upload Speed:", upload_speed, "Mbps")

# tasks with different images
print("Start sending frames at", fps, "FPS")
i = 0
while (i < 50):
    img_path = IMAGE_PATHS[0]
    files = []

    for j in range(fps):
        files.append(("files", (f"{img_path}_copy{j}", open(img_path, "rb"), "image/jpeg")))

    data = {"gen_at": datetime.now().isoformat(), "req_id": i, "fps": fps}
    response = requests.post(API_URL, files=files, data=data)  
    i = i + 1