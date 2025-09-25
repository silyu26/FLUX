from ultralytics import YOLO

#uvicorn YOLO.yolo_v11_csfy:app --reload --host 0.0.0.0 --port 5000
model = YOLO("yolo11s.pt")

results = model.train(data="coco8.yaml", epochs=100, imgsz=640)

results = model("../Senders/imgs/cat1.jpg")