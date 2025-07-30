import pandas as pd
import asyncio
import json
import websockets
import time
import requests
from datetime import datetime
import paho.mqtt.client as mqtt
import random

df = pd.read_csv('weather.csv')
# Params
receiver_ip = "192.168.2.105"

# Send data via HTTP
def send_http():
    url = f"http://{receiver_ip}:5000/receive"
    for _, row in df.iterrows():
        data = row.to_dict()
        data.update({"sent_at": datetime.now().isoformat()})
        req_time = datetime.now()
        response = requests.post(url, json=data)
        print(f"Data sent at {req_time.isoformat()}| Response: {response.status_code}")
        time.sleep(1)

# Websockets
async def send_websocket():
    uri = f"ws://{receiver_ip}:5000"
    async with websockets.connect(uri) as websocket:
        for _, row in df.iterrows():
            data_raw = row.to_dict()
            data_raw.update({"sent_at": datetime.now().isoformat()})
            data = json.dumps(data_raw)
            await websocket.send(data)
            print(f"Data sent at {data_raw['sent_at']} via WebSocket")
            time.sleep(1)

# MQTT
def send_mqtt():
    # different cases
    #broker_ip = "192.168.2.100"
    broker_ip = "127.0.0.1" #localhast
    topic = "sensor/weather"
    client = mqtt.Client()
    client.connect(broker_ip, 1883, 60)

    try:
        for _, row in df.iterrows():
            data_raw = row.to_dict()
            data_raw.update({"sent_at": datetime.now().isoformat()})
            data = json.dumps(data_raw)
            client.publish(topic, data)
            print(f"Published data at {data_raw['sent_at']}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped publisher.")
        client.disconnect()

def main():
    #print("Starting HTTP sender...")
    #send_http()
    
    #print("Starting WebSocket sender...")
    #asyncio.run(send_websocket())
    
    print("Starting MQTT sender...")
    send_mqtt()

if __name__ == "__main__":
    main()