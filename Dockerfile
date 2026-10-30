FROM ghcr.io/remsky/kokoro-fastapi-cpu:latest

ENV HOST=0.0.0.0 \
    PORT=10000 \
    USE_GPU=false \
    DEVICE_TYPE=cpu \
    DEFAULT_VOICE=pm_alex \
    API_LOG_LEVEL=INFO \
    ENABLE_WEB_PLAYER=false

EXPOSE 10000
