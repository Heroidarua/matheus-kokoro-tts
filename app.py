import io
import logging
import os
import threading
import wave
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from piper import PiperVoice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matheus-piper-tts")

VOICE_NAME = "pt_BR-faber-medium"
MODEL_PATH = Path(os.getenv(
    "PIPER_MODEL_PATH",
    "/app/voices/pt_BR-faber-medium.onnx"
))
API_KEY = os.getenv("PIPER_API_KEY")

voice = None
synthesis_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global voice
    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Modelo Piper não encontrado: {MODEL_PATH}")
    logger.info("Carregando voz %s em CPU", VOICE_NAME)
    voice = PiperVoice.load(str(MODEL_PATH), use_cuda=False)
    logger.info("Voz %s carregada", VOICE_NAME)
    yield
    voice = None


app = FastAPI(
    title="Matheus Piper TTS",
    description="API de síntese de voz em português brasileiro usando Piper.",
    version="1.0.0",
    lifespan=lifespan,
)


class SpeechRequest(BaseModel):
    model: str = "piper"
    input: str = Field(min_length=1, max_length=4000)
    voice: str = VOICE_NAME
    response_format: str = "wav"


@app.get("/")
def home():
    return {
        "service": "Matheus Piper TTS",
        "engine": "Piper",
        "voice": VOICE_NAME,
        "format": "wav",
    }


@app.get("/health")
def health():
    return {
        "status": "ok" if voice is not None else "loading",
        "engine": "piper",
        "voice": VOICE_NAME,
    }


@app.post("/v1/audio/speech")
def generate_speech(
    data: SpeechRequest,
    authorization: str = Header(default=""),
):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not data.input.strip():
        raise HTTPException(status_code=400, detail="Texto vazio.")

    if data.voice != VOICE_NAME:
        raise HTTPException(
            status_code=400,
            detail=f"Voz não disponível. Use {VOICE_NAME}.",
        )

    if data.response_format.lower() not in ("wav",):
        raise HTTPException(
            status_code=400,
            detail="Formato ainda não suportado. Use response_format=wav.",
        )

    if voice is None:
        raise HTTPException(status_code=503, detail="Modelo ainda está carregando.")

    audio_buffer = io.BytesIO()
    try:
        # Piper/espeak não deve sintetizar requisições simultâneas neste serviço.
        with synthesis_lock:
            with wave.open(audio_buffer, "wb") as wav_file:
                voice.synthesize_wav(data.input.strip(), wav_file)

        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )
    except Exception:
        logger.exception("Falha ao sintetizar áudio")
        raise HTTPException(status_code=500, detail="Falha ao gerar áudio.")
