import pandas as pd
import time
import requests
from datetime import datetime

df = pd.read_csv('weather.csv')

receiver_ip = "192.168.2.100"
url = f"http://{receiver_ip}:5000/receive"

for _, row in df.iterrows():
    data = row.to_dict()
    req_time = datetime.now()
    response = requests.post(url, json=data)
    print(f"Data sent at {req_time.isoformat()}| Response: {response.status_code}")
    time.sleep(1)