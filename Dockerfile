FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    HF_HOME=/data/huggingface \
    TTS_DEVICE=cuda:0

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip libsndfile1 ffmpeg git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir --upgrade pip \
    && python3.11 -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126 \
    && python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY app.py .
EXPOSE 10000
CMD ["sh", "-c", "python3.11 -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
