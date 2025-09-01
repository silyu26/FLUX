# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from knn import moving_average_predict, knn_predict, markov_predict, df
import pandas as pd
import time

# ---------------------------
# Define input schema
# ---------------------------
class WeatherData(BaseModel):
    temp_max: float
    precipitation: float
    wind: float

# ---------------------------
# Start FastAPI
# ---------------------------
app = FastAPI(title="Weather Prediction API")

@app.post("/predict")
def predict_weather(data: WeatherData):
    start_time = time.time()
    
    # Convert input to dataframe for moving average
    new_df = pd.concat([df, pd.DataFrame([data.dict()])], ignore_index=True)

    # Moving Average
    ma_start = time.time()
    ma_pred = moving_average_predict(new_df)
    ma_time = time.time() - ma_start
    
    # KNN
    knn_start = time.time()
    knn_pred = knn_predict([data.temp_max, data.precipitation, data.wind])
    knn_time = time.time() - knn_start
    
    # Markov Chain
    markov_start = time.time()
    markov_pred = markov_predict(data.temp_max)
    markov_time = time.time() - markov_start
    
    total_time = time.time() - start_time
    
    return {
        "predictions": {
            "moving_average": ma_pred,
            "knn": knn_pred,
            "markov_chain": markov_pred
        },
        "timing": {
            "moving_average_time": ma_time,
            "knn_time": knn_time,
            "markov_time": markov_time,
            "total_time": total_time
        }
    }
