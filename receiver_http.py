from flask import Flask, request
from datetime import datetime, timezone
import requests
#from . import crud, model, db
from model import Experiment, WeatherData
from crud import create_experiment_with_weather
from db import SessionLocal


app = Flask(__name__)

@app.route('/receive', methods=['POST'])

def receive_data():
    data = request.get_json()
    res_time = datetime.now()
    #print("Received Data at",res_time.isoformat())
    #forward_to_n8n(data)
    exp = Experiment(
        gen_at=data['gen_at'],
        exp_id=1,
        model_in=datetime.now(),
        model_out=datetime.now(),
        server_in=res_time,
        #model_out=datetime.now()
    )
    weather = WeatherData(
        date=data['date'],
        precipitation=data['precipitation'],
        temp_max=data['temp_max'],
        temp_min=data['temp_min'],
        wind=data['wind'],
    )
    exp.weather = weather

    create_experiment_with_weather(SessionLocal(), exp)
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