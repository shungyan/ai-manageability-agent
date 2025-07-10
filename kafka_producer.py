from quixstreams import Application
import time
import random

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


def main():
    while True:
        count = random.randint(0, 5)  # Random number between 0 and 5
        produce_queue_count("localhost:9092", "queue_topic", "retail", count)
        time.sleep(100)


if __name__ == "__main__":
    main()
