import json
from datetime import datetime
import paho.mqtt.client as mqtt

broker_ip = "192.168.1.42"  # Same as in sender
topic = "sensor/weather"

def on_connect(client, userdata, flags, rc):
    client.subscribe(topic)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"Received at {datetime.now().isoformat()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, 1883, 60)
print("Listening for MQTT messages...")
client.loop_forever()