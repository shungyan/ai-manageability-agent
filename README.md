prequisite:
uv
ollama
docker

1. docker compose up -d
2. create kafka topics
3. uv venv
4. uv pip install -r requirement
5. uv run main.py
6. uv run adk web --port 1234


- How to create topics in kafka
-
  ```
  docker exec -it broker kafka-topics \
    --create \
    --topic people-count \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1
  
  ```
-
-
- How to list topics in kafka
-
  ```
  docker exec -it broker kafka-topics \
    --list \
    --bootstrap-server localhost:9092
  
  ```
