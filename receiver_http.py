from flask import Flask, request
from datetime import datetime
import requests

app = Flask(__name__)

@app.route('/receive', methods=['POST'])

def receive_data():
    data = request.get_json()
    res_time = datetime.now()
    print("Received Data at",res_time.isoformat())
    forward_to_n8n(data)
    return {'status': 'success'}, 200

def forward_to_n8n(data):
    try:
        data["received_at"] = datetime.now().isoformat()
        #requests.post("http://localhost:5678/webhook-test/http_data", json=data)
        requests.post("http://localhost:5678/webhook/http_data", json=data)
    except Exception as e:
        print(f"Error sending to n8n: {e}")

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)