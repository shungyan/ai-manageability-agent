from kafka import KafkaConsumer
import json
import time

# Create Kafka consumer
consumer = KafkaConsumer(
    'people-count',  # Topic name
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',          # Start from beginning
    enable_auto_commit=True,
    group_id='dummy-group',                # Consumer group name
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Decode JSON
)

print("Kafka dummy consumer started. Waiting for messages...")

try:
    while True:
        msg_pack = consumer.poll(timeout_ms=1000)  # Wait 1 second
        for tp, messages in msg_pack.items():
            for message in messages:
                print(f"[{message.timestamp}] Received:", message.value)
        time.sleep(1)  # Throttle to 1s
except KeyboardInterrupt:
    print("Exiting consumer.")
finally:
    consumer.close()
