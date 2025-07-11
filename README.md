# AI Manageability Agent

An AI-based agent to **control the power cycle of a self-service kiosk** based on the number of people queueing in front of it.  
The system leverages edge AI with Intel NPU support to provide efficient local inference and monitoring.

---

## 📋 Prerequisites

- **Ubuntu**: 22.04 or 24.10  
- **Intel Platform**: Meteor Lake and above  
- **uv** (Python package and virtual environment manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh

### 🟦 Ollama

Install Ollama by following the guide here:  
👉 https://github.com/huichuno/edge-optimized-ai-assistant

This project uses Ollama as the LLM backend optimized for edge devices.

---

### 🐳 Docker

Install Docker following the official instructions for Ubuntu:  
👉 https://docs.docker.com/engine/install/ubuntu/

Ensure Docker is running and you can execute containers.

---

## 🚀 Getting Started

Follow these steps to set up and run the AI Manageability Agent:
1.  Clone the repository
```bash
git clone https://github.com/shungyan/AI-manageability-agent
cd AI-manageability
```
2. Edit environment variables in docker compose to switch device or input source

<img width="590" height="128" alt="image" src="https://github.com/user-attachments/assets/bb498e89-6be3-4a4a-9830-371601d7f7dc" />


3. Start Docker services
```bash
docker compose build
docker compose up -d
```
4. Create kafka topic 

5. Go to http://localhost:4896/ to look at the person queue count stream (optional)

6. Set up Python environment with uv for google adk
```bash
uv venv
uv pip install -r requirements.txt 
```

7. Launch google adk web on port 5678
```bash
uv run adk web --port 5678
```
<img width="1365" height="907" alt="image" src="https://github.com/user-attachments/assets/7c0b3c2b-5f31-4a37-a6b7-6263ebe54c16" />



8. Run the google adk agent directly
```bash
uv run adk run ai-agent
```
## 🛠️ How To

### 🧵 Create Kafka Topics

Create a topic named `people-count`:

```bash
docker exec -it broker kafka-topics \
  --create \
  --topic people-count \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1
```

### 🧵 List Kafka Topics

```bash
docker exec -it broker kafka-topics \
--list \
--bootstrap-server localhost:9092
```

# 🧠 Using the Intel NPU Monitor Tool

This section explains how to install and use `intel-npu-top`, a tool for monitoring Intel NPU usage in real time.


```bash
git clone https://github.com/DMontgomery40/intel-npu-top
cd intel-npu-top
uv venv
uv pip install intel-npu-top
uv run intel-npu-top.py
```
![image](https://github.com/user-attachments/assets/347092f5-29bb-4494-9539-39ca06a8fc6c)

---
### ⚙️ Intel NPU Driver Installation (optional)

Install the NPU driver for Meteor Lake and above (Ubuntu 24.04 compatible):

```bash
sudo apt install libtbb12

wget https://github.com/intel/linux-npu-driver/releases/download/v1.13.0/intel-driver-compiler-npu_1.13.0.20250131-13074932693_ubuntu24.04_amd64.deb
wget https://github.com/intel/linux-npu-driver/releases/download/v1.13.0/intel-fw-npu_1.13.0.20250131-13074932693_ubuntu24.04_amd64.deb
wget https://github.com/intel/linux-npu-driver/releases/download/v1.13.0/intel-level-zero-npu_1.13.0.20250131-13074932693_ubuntu24.04_amd64.deb
wget https://github.com/oneapi-src/level-zero/releases/download/v1.18.5/level-zero_1.18.5+u24.04_amd64.deb

sudo dpkg -i *.deb
sudo bash -c "echo 'SUBSYSTEM==\"accel\", KERNEL==\"accel*\", GROUP=\"render\", MODE=\"0660\"' > /etc/udev/rules.d/10-intel-vpu.rules"
sudo usermod -a -G render <your-user-name>

sudo reboot
```

### ✅ Verify NPU Driver

After installing the driver and rebooting your system, verify that the NPU is available using OpenVINO:

Create a Python script (e.g., `check_npu.py`) and paste the following:

```python
import openvino as ov

core = ov.Core()
print(core.available_devices)
```


