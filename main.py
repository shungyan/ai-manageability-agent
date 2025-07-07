import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import Tracker
import cvzone
import subprocess
import numpy as np
import json
import threading
from quixstreams import Application
import time

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

# Single RTSP stream
streams = {
    "cam0": "rtsp://localhost:8554/cam0"
}

# Initialize YOLO model
model = YOLO('yolov8s.pt')

def people_counter(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print([x, y])

def load_class_list(file_path):
    with open(file_path, "r") as file:
        return file.read().split("\n")

def process_frame(frame, model, class_list, tracker, area):
    frame = cv2.resize(frame, (1020, 500))
    results = model.predict(frame)
    boxes_data = results[0].boxes.data
    px = pd.DataFrame(boxes_data).astype("float")

    detected_objects = []
    for _, row in px.iterrows():
        x1, y1, x2, y2, _, d = map(int, row)
        if 'person' in class_list[d]:
            detected_objects.append([x1, y1, x2, y2])

    objects_bbs_ids = tracker.update(detected_objects)
    detected_in_area = 0

    for bbox in objects_bbs_ids:
        x3, y3, x4, y4, obj_id = bbox
        if cv2.pointPolygonTest(np.array(area, np.int32), (x4, y4), False) >= 0:
            cv2.circle(frame, (x4, y4), 4, (0, 255, 0), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (255, 255, 255), 2)
            cvzone.putTextRect(frame, f'{obj_id}', (x3, y3), 1, 1)
            detected_in_area += 1

    return frame, detected_in_area

def get_video_resolution(rtsp_url):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',              # first video stream
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        rtsp_url
    ]

    result = subprocess.run(
        ffprobe_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print(f"ffprobe error: {result.stderr.strip()}")
        return None, None

    info = json.loads(result.stdout)
    streams = info.get('streams', [])
    if not streams:
        print("No video stream found.")
        return None, None

    width = streams[0].get('width')
    height = streams[0].get('height')
    return width, height

class RTSPStream:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        self.cap.release()

def main():
    cv2.namedWindow('people_counter')
    cv2.setMouseCallback('people_counter', people_counter)

    rtsp_url = 'rtsp://localhost:8554/cam0?buffer_size=512000,rtsp_transport=udp'

    # Initialize threaded RTSP stream
    stream = RTSPStream(rtsp_url)

    class_list = load_class_list("coco.txt")
    tracker = Tracker()

    y_offset = 100
    area = [
        (240, 40 + y_offset),
        (830, 40 + y_offset),
        (830, 565 + y_offset),
        (240, 565 + y_offset)
    ]

    delay = 30  # approximate delay

    while True:
        frame = stream.get_frame()
        if frame is None:
            continue  # wait until frames are available


        frame, detected_count = process_frame(frame, model, class_list, tracker, area)
        print(detected_count)
        produce_queue_count("localhost:9092", "people-count", "retail", detected_count)

        cv2.putText(frame, f'People in Area: {detected_count}', (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
        cv2.polylines(frame, [np.array(area, np.int32)], True, (0, 255, 0), 2)

        cv2.imshow("people_counter", frame)
        if cv2.waitKey(delay) & 0xFF == 27:
            break

    stream.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()