FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    KOKORO_MODEL_PATH=/app/models/kokoro-v1.0.fp16.onnx \
    KOKORO_VOICES_PATH=/app/models/voices-v1.0.bin \
    KOKORO_SPEED=1.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates espeak-ng libespeak-ng1 libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/models \
    && curl -fL --retry 5 --retry-delay 2 \
      https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.fp16.onnx \
      -o /app/models/kokoro-v1.0.fp16.onnx \
    && echo "f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96  /app/models/kokoro-v1.0.fp16.onnx" | sha256sum -c - \
    && curl -fL --retry 5 --retry-delay 2 \
      https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin \
      -o /app/models/voices-v1.0.bin \
    && echo "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d  /app/models/voices-v1.0.bin" | sha256sum -c -

COPY app.py .

EXPOSE 10000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
