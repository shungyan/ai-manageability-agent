from ultralytics import YOLO
import cv2
import time
import collections
import numpy as np
import torch
import openvino as ov
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def run_inference(source, device, det_model_path):
    core = ov.Core()

    # Load OpenVINO model
    det_ov_model = core.read_model(det_model_path)
    ov_config = {}

    if device.value != "CPU":
        det_ov_model.reshape({0: [1, 3, 640, 640]})

    if "GPU" in device.value or ("AUTO" in device.value and "GPU" in core.available_devices):
        ov_config = {"GPU_DISABLE_WINOGRAD_CONVOLUTION": "YES"}

    compiled_model = core.compile_model(det_ov_model, device.value, ov_config)

    # Load YOLO model and patch inference with OpenVINO
    det_model = YOLO("yolov8n.pt")
    def infer(*args):
        result = compiled_model(args)
        return torch.from_numpy(result[0])

    _ = det_model.predict(np.zeros((640, 640, 3), dtype=np.uint8))  
    det_model.predictor.inference = infer
    det_model.predictor.model.pt = False

    try:
        cap = cv2.VideoCapture(source)
        assert cap.isOpened(), "Error reading video source."

        # Polygonal area
        area = [
            (900, 300),  
            (1500, 300),
            (1500, 1500),  
            (900, 1500)
        ]


        processing_times = collections.deque(maxlen=200)

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Video frame is empty or video processing has been successfully completed.")
                break

            start_time = time.time()

            # Run YOLO inference (returns Results object)
            results = det_model(frame)[0]
            people_inside_area = 0

            for det in results.boxes:
                cls_id = int(det.cls)
                if results.names[cls_id] == 'person':
                    x1, y1, x2, y2 = map(int, det.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    # Check if center is in polygonal area
                    if cv2.pointPolygonTest(np.array(area, dtype=np.int32), (cx, cy), False) >= 0:
                        people_inside_area += 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    #else:
                        #cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            print(people_inside_area)
            producer.send("people-count", value=people_inside_area)
            producer.flush()
            # Draw polygonal area
            cv2.polylines(frame, [np.array(area, dtype=np.int32)], isClosed=True, color=(255, 255, 0), thickness=2)

            # Timing
            stop_time = time.time()
            processing_times.append(stop_time - start_time)
            processing_time = np.mean(processing_times) * 1000
            fps = 1000 / processing_time

            # Show timing and count
            f_height, f_width = frame.shape[:2]
            cv2.putText(frame, f"Inference time: {processing_time:.1f}ms ({fps:.1f} FPS)",
                        (20, 40), cv2.FONT_HERSHEY_COMPLEX, f_width / 1000, (0, 0, 255), 2, cv2.LINE_AA)

            count_text = f"Count: {people_inside_area}"
            (text_width, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_COMPLEX, 1.5, 3)
            top_right = (frame.shape[1] - text_width - 20, 80)
            cv2.putText(frame, count_text, top_right, cv2.FONT_HERSHEY_COMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

            # Display
            display_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
            cv2.imshow("People Counter", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


    except KeyboardInterrupt:
        print("Interrupted.")

    cap.release()
    cv2.destroyAllWindows()


from types import SimpleNamespace

source = "rtsp://localhost:8554/cam0"  # or 'video.mp4' or RTSP stream
device = SimpleNamespace(value="NPU")  # or "CPU", "AUTO"
det_model_path = "yolov8n_openvino_model/yolov8n.xml"

run_inference(source, device, det_model_path)