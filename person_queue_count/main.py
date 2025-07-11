from flask import Flask, Response, render_template
from ultralytics import YOLO
import cv2
import time
import collections
import numpy as np
import torch
import openvino as ov
from kafka import KafkaProducer
import json
from types import SimpleNamespace
from quixstreams import Application

app = Flask(__name__)

def produce_queue_count(
    broker_address: str, topic_name: str, consumer_group: str, count: int
):
    """
    Produces a single queue count event to the specified Kafka topic.
    """
    app = Application(broker_address=broker_address, consumer_group=consumer_group)
    topic = app.topic(name=topic_name, value_serializer="json")

    with app.get_producer() as producer:
        message = topic.serialize(key="queue", value={"queue_count": count})
        producer.produce(topic=topic.name, value=message.value, key=message.key)
        print(f"Produced queue count: {count}")

# Set parameters
source = "rtsp://localhost:8554/cam0"  # or 'video.mp4'
device = SimpleNamespace(value="NPU")  # or "CPU", "AUTO"
det_model_path = "yolov8n_openvino_model/yolov8n.xml"

# Load and prepare model once
core = ov.Core()
det_ov_model = core.read_model(det_model_path)
ov_config = {}

if device.value != "CPU":
    det_ov_model.reshape({0: [1, 3, 640, 640]})

if "GPU" in device.value or ("AUTO" in device.value and "CPU" in core.available_devices):
    ov_config = {"GPU_DISABLE_WINOGRAD_CONVOLUTION": "YES"}

compiled_model = core.compile_model(det_ov_model, device.value, ov_config)

det_model = YOLO("yolov8n.pt")

# Patch YOLO inference
def infer(*args):
    result = compiled_model(args)
    return torch.from_numpy(result[0])

_ = det_model.predict(np.zeros((640, 640, 3), dtype=np.uint8))
det_model.predictor.inference = infer
det_model.predictor.model.pt = False



def generate_frames():
    cap = cv2.VideoCapture(source)
    assert cap.isOpened(), "Error reading video source."

    area = [(900, 300), (1500, 300), (1500, 1500), (900, 1500)]
    processing_times = collections.deque(maxlen=200)

    SEND_INTERVAL = 2.0  # seconds
    last_send_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        start_time = time.time()
        results = det_model(frame)[0]
        people_inside_area = 0

        for det in results.boxes:
            cls_id = int(det.cls)
            if results.names[cls_id] == 'person':
                x1, y1, x2, y2 = map(int, det.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                if cv2.pointPolygonTest(np.array(area, dtype=np.int32), (cx, cy), False) >= 0:
                    people_inside_area += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        current_time = time.time()
        if current_time - last_send_time >= SEND_INTERVAL:
            produce_queue_count("localhost:9092", "people-count", "retail", people_inside_area)
            last_send_time = current_time

        cv2.polylines(frame, [np.array(area, dtype=np.int32)], isClosed=True, color=(255, 255, 0), thickness=2)

        # Draw FPS and count
        stop_time = time.time()
        processing_times.append(stop_time - start_time)
        processing_time = np.mean(processing_times) * 1000
        fps = 1000 / processing_time

        cv2.putText(frame, f"Inference time: {processing_time:.1f}ms ({fps:.1f} FPS)",
                    (20, 40), cv2.FONT_HERSHEY_COMPLEX, frame.shape[1] / 1000, (0, 0, 255), 2)

        count_text = f"Count: {people_inside_area}"
        (text_width, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_COMPLEX, 1.5, 3)
        top_right = (frame.shape[1] - text_width - 20, 80)
        cv2.putText(frame, count_text, top_right, cv2.FONT_HERSHEY_COMPLEX, 0.75, (0, 0, 255), 2)

        display_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
        ret, jpeg = cv2.imencode('.jpg', display_frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()


@app.route('/')
def index():
    return (
        "<html><body><h2>Live People Count</h2>"
        "<img src='/video_feed' width='720'></body></html>"
    )


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4896)
