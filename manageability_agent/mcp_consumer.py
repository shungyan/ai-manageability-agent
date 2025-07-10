from kafka import KafkaConsumer
import json
import time
from mcp.server.fastmcp import Context, FastMCP

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
def consume(**kwargs):
    try:
        msg_pack = consumer.poll(timeout_ms=1000)  # Wait 1 second
        for tp, messages in msg_pack.items():
            for message in messages:
                print("[RECEIVED]", message.value)
                return message.value

    except KeyboardInterrupt:
        print("Exiting consumer.")


if __name__ == "__main__":
    # Run the server
    mcp.run()