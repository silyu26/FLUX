<<<<<<< HEAD
# FLUX
=======
# FLUX: Feedback Latency and Utilization Examination for Real-Time Sensor-Based AI Pipelines

A master thesis in analyzing all possible factors and optimization techniques that affect the latency in a generic ML inference pipeline with sensor data streams as input.

## Structure
```
FLUX

|-KNN: Simple machine learning model that usus K-Nearest Neighbour

|-Receivers: Contains receivers used with different protocols
 |-receiver_http.py: Use http, IPV4 and TCP as 
 protocol
 |-receiver_mqtt.py: Use MQTT(IoT) as protocol
 |-receiver_ws.py: Use Websockets as protocol

|-SQL: Contains sql helper functions

|-YOLO: Contains YOLO, the computer vision model

|-model.py: Data schema in sql

|-sender.py: The sender that simulates the sensor
```
## Scenario
We categorize a machine learning inference pipeline with sensor data stream as input into the following categories
### 1. Fat Client
### 2. Remote Inference
### 3. Complex Setup

## Literatures
## External Tools
>>>>>>> origin/main
