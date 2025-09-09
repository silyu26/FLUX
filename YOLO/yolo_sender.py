import requests
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000/yolo/"
IMAGE_PATHS = ["./imgs/cat1.jpg"]
# tasks with different images
for i in range(30):
    img_path = IMAGE_PATHS[0]
    with open(img_path, "rb") as f:
        files = {"file": (img_path, f, "image/jpeg")}
        data = {"gen_at": datetime.now().isoformat(), "req_id" : i}
        response = requests.post(API_URL, files=files, data=data)
        print(f"Sent {img_path}, got:", response.json())
    #time.sleep(2)  