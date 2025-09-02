# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from .knn import moving_average_predict, knn_predict, markov_predict, df
from datetime import datetime
from SQL.crud import create_experiment_with_weather
from SQL.db import SessionLocal
from model import Experiment, WeatherData
import pandas as pd
import time


# ---------------------------
# Define input schema
# ---------------------------
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Maybe make some fields optional
class Input(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precipitation: float
    wind: float
    weather: str
    gen_at: datetime

# ---------------------------
# Start FastAPI
# uvicorn KNN.main:app --reload --host 0.0.0.0 --port 5000

# ---------------------------
app = FastAPI(title="Weather Prediction API")

@app.post("/predict")
def predict_weather(data: Input):
    print("Received data:", data)
    server_in = datetime.now()
    
    # Convert input to dataframe for moving average
    new_df = pd.concat([df, pd.DataFrame([data.dict()])], ignore_index=True)

    # Moving Average
    #model_in = datetime.now()
    #ma_pred = moving_average_predict(new_df)
    #model_out = datetime.now()
    
    # KNN
    kmodel_in = datetime.now()
    knn_pred = knn_predict([data.temp_max, data.precipitation, data.wind])
    kmodel_out = datetime.now()
    
    # Markov Chain
    #model_in = datetime.now()
    #markov_pred = markov_predict(data.temp_max)
    #model_out = datetime.now()
    
    # Save and send to sql
    exp = Experiment(
        gen_at=data.gen_at,
        exp_id=1,
        model_in=kmodel_in,
        model_out=kmodel_out,
        server_in=server_in,
        #model_out=datetime.now()
    )
    #weather = WeatherData(
    #    date=data.date,
    #    precipitation=data.precipitation,
    #    temp_max=data.temp_max,
    #    temp_min=data.temp_min,
    #    wind=data.wind,
    #)
    #exp.weather = weather
    create_experiment_with_weather(SessionLocal(), exp)
    
    return {
        "predictions": {
    #        "moving_average": ma_pred,
            "knn": knn_pred,
    #        "markov_chain": markov_pred
        },
        "received_data": exp
    #    "timing": {
    #        "moving_average_time": ma_time,
    #        "knn_time": knn_time,
    #        "markov_time": markov_time,
    #        "total_time": total_time
    #    }
    }
