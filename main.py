import subprocess
import numpy as np
import cv2
import time
import json
import os
import base64
import litellm
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

save_interval = 1  # seconds

def get_stream_resolution(rtsp_url):
    ffprobe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", rtsp_url
    ]
    ffprobe_output = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    info = json.loads(ffprobe_output.stdout)
    stream_info = info['streams'][0]
    return int(stream_info['width']), int(stream_info['height'])

def capture_frame(name, url, width, height):
    frame_size = width * height * 3
    ffmpeg_cmd = [
        "ffmpeg", "-rtsp_transport", "tcp",
        "-i", url,
        "-frames:v", "1",
        "-f", "image2pipe",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo", "-"
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_frame = process.stdout.read(frame_size)
    process.terminate()

    if len(raw_frame) < frame_size:
        print(f"[{name}] Incomplete frame read. Got {len(raw_frame)} bytes, expected {frame_size}.")
        return None

    frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
    filename = f"{name}_frame.jpg"
    cv2.imwrite(filename, frame)
    print(f"[{name}] Saved {filename}")
    return filename

def encode_image_to_data_url(path):
    with open(path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_image}"

def send_single_image_to_ollama(cam_name, image_path):
    image_url = encode_image_to_data_url(image_path)

    prompt = (
        """You are an expert computer vision assistant.

    Your ONLY task is:
    - Determine the number of people currently using the kiosk (directly interacting).
    - Determine the number of people queuing (waiting in line, not yet using).

    STRICTLY return ONLY a single line JSON object in the following format:
    {"using": <number>, "queue": <number>}

    DO NOT include any explanation, text, or commentary outside the JSON.
    """
    )



    response = litellm.completion(
        model="ollama/gemma3",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            }
        ]
    )

    content = response["choices"][0]["message"]["content"].strip()

    return cam_name, content

if __name__ == "__main__":
    cam_name, rtsp_url = list(streams.items())[0]

    print(f"[INFO] Processing single stream: {cam_name} ({rtsp_url})")
    width, height = get_stream_resolution(rtsp_url)
    print(f"[INFO] Resolution for {cam_name}: {width}x{height}")

    while True:
        start_time = time.time()

        image_path = capture_frame(cam_name, rtsp_url, width, height)
        if image_path:
            try:
                name, content = send_single_image_to_ollama(cam_name, image_path)
                result = {name: content}
                print("Ollama result:", json.dumps(result))
                
                produce_queue_count("localhost:9092", "people-count", "retail", result)
            except Exception as e:
                print("Error during analysis:", e)

        # Wait until next interval
        elapsed = time.time() - start_time
        sleep_time = save_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
