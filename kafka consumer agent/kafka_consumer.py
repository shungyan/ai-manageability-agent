from quixstreams import Application
import time
import json
from confluent_kafka import Consumer, TopicPartition


# Configure an Application.
# The config params will be used for the Consumer instance too.
app = Application(
    broker_address="localhost:9092",
    consumer_group="retail",
    auto_offset_reset="latest",
)
# topic = app.topic(name="queue_topic", value_deserializer="json")

latest = 0


def get_latest_queue_count() -> int:
    global latest
    # Create a consumer and start a polling loop
    with app.get_consumer() as consumer:
        # consumer.subscribe(topics=["queue_topic"])

        topic = "people-count"  # specify the topic name
        partition = 0  # adjust if multiple partitions

        # Get the latest offset (high watermark)
        low, high = consumer.get_watermark_offsets(TopicPartition(topic, partition))

        if high > latest:
            latest = high
        elif high == 0 or high == latest:
            return -2

        print(f"High: {high}, Latest: {latest}")

        # Assign consumer to the latest offset (start consuming new messages only)
        consumer.assign([TopicPartition(topic, partition, high - 1)])

        msg = consumer.poll(0.1)
        if msg is None:
            return -2
        elif msg.error():
            print("Kafka error:", msg.error())
            return -1

        value = json.loads(msg.value().decode("utf-8"))
        print("Received:", value)
        # Do some work with the value here ...
        # Store the offset of the processed message on the Consumer
        # for the auto-commit mechanism.
        # It will send it to Kafka in the background.
        # Storing offset only after the message is processed enables at-least-once delivery
        # guarantees.
        consumer.store_offsets(message=msg)
        consumer.close()
        return value["queue_count"]


def main():
    while True:
        count = get_latest_queue_count()
        print(f"Consumed: {count}")
        time.sleep(2)

    # count = get_latest_queue_count()
    # print(f"Consumed: {count}")


if __name__ == "__main__":
    main()
