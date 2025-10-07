import os
import time
import json
import base64
import asyncio
import requests
import websockets
import paho.mqtt.client as mqtt
from datetime import datetime
from ping3 import ping
import speedtest

# ------------------ Params ------------------
host = '8.8.8.8'
receiver_ip = "127.0.0.1"
HTTP_URL = f"http://{receiver_ip}:5000/yolo/"
WS_URL = f"ws://{receiver_ip}:5000/yolo/"
MQTT_BROKER = receiver_ip
MQTT_TOPIC = "sensor/yolo"

IMAGE_PATHS = ["./imgs/cat1.jpg"]
fps = 1   # how many frames per request/batch
TOTAL_REQUESTS = 10

# ------------------ Network check ------------------
#latency = ping(host)
#st = speedtest.Speedtest()
#st.get_best_server()
#download_speed = st.download() / 1_000_000  # in Mbps
#upload_speed = st.upload() / 1_000_000      # in Mbps

#print(f"Ping to {host}: {latency*1000:.2f} ms")
#print("Download Speed:", download_speed, "Mbps")
#print("Upload Speed:", upload_speed, "Mbps")


# ------------------ HTTP ------------------
def send_http():
    print("Start sending frames via HTTP at", fps, "FPS")
    for i in range(TOTAL_REQUESTS):
        img_path = IMAGE_PATHS[0]
        files = []

        for j in range(fps):
            files.append(("files", (f"{os.path.basename(img_path)}_copy{j}", open(img_path, "rb"), "image/jpeg")))

        data = {"gen_at": datetime.now().isoformat(), "req_id": i, "fps": fps}
        response = requests.post(HTTP_URL, files=files, data=data)  
        print(f"HTTP request {i} | Status: {response.status_code}")


# ------------------ WebSocket ------------------
async def send_websocket():
    print("Start sending frames via WebSocket at", fps, "FPS")
    uri = WS_URL
    async with websockets.connect(uri, max_size=None) as websocket:
        img_path = IMAGE_PATHS[0]
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        for i in range(TOTAL_REQUESTS):
            batch = []
            for j in range(fps):
                batch.append({
                    "filename": f"{os.path.basename(img_path)}_copy{j}",
                    "data": base64.b64encode(img_bytes).decode("utf-8"),
                    "gen_at": datetime.now().isoformat(),
                    "req_id": i,
                    "fps": fps
                })

            await websocket.send(json.dumps({"batch": batch}))
            print(f"WebSocket request {i} sent with {fps} frames")


# ------------------ MQTT ------------------
def send_mqtt():
    print("Start sending frames via MQTT at", fps, "FPS")
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)

    img_path = IMAGE_PATHS[0]
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    try:
        for i in range(TOTAL_REQUESTS):
            batch = []
            for j in range(fps):
                batch.append({
                    "filename": f"{os.path.basename(img_path)}_copy{j}",
                    "data": base64.b64encode(img_bytes).decode("utf-8"),
                    "gen_at": datetime.now().isoformat(),
                    "req_id": i,
                    "fps": fps
                })

            client.publish(MQTT_TOPIC, json.dumps({"batch": batch}))
            print(f"MQTT request {i} published with {fps} frames")

    finally:
        client.disconnect()


# ------------------ Run examples ------------------
if __name__ == "__main__":
     send_http()
    # asyncio.run(send_websocket())
    # send_mqtt()
    #pass
