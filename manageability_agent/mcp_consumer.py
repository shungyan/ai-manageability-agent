import json
import time
from mcp.server.fastmcp import Context, FastMCP
from kafka import KafkaConsumer, TopicPartition
from kafka.structs import OffsetAndMetadata
import json
import time

latest = 0

mcp = FastMCP("Kafka MCP Server")

# Create Kafka consumer
consumer = KafkaConsumer(
    'people-count',  # Topic name
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',          # Start from beginning
    enable_auto_commit=True,
    group_id='dummy-group',                # Consumer group name
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Decode JSON
)


@mcp.tool()
def get_latest_queue_count():
    global latest

    topic = 'people-count'
    partition = 0

    consumer = KafkaConsumer(
        bootstrap_servers='localhost:9092',
        group_id='dummy-group',
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest'
    )

    tp = TopicPartition(topic, partition)
    

    end_offsets = consumer.end_offsets([tp])
    high = end_offsets[tp]

    if high > latest:
        latest = high
    elif high == 0 or high == latest:
        return -2

    print(f"High: {high}, Latest: {latest}")


    consumer.assign([tp])
    consumer.seek(tp, high - 1)
    msg_pack = consumer.poll(timeout_ms=100)

    if msg_pack is None:
        return -2

    for tp, messages in msg_pack.items():
        for message in messages:
            consumer.commit(offsets={
                TopicPartition(topic, partition): OffsetAndMetadata(message.offset + 1, None,-1)
            })
            consumer.close()
            return message.value

    return -2



if __name__ == "__main__":
    # Run the server
    mcp.run()