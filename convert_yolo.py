from ultralytics import YOLO

DET_MODEL_NAME = "yolov8n"

det_model = YOLO(f"{DET_MODEL_NAME}.pt")
label_map = det_model.model.names

# Need to make en empty call to initialize the model
res = det_model()
det_model.export(format="openvino", dynamic=True, half=True)