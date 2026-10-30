import io
import logging
import os
import threading
import wave
from contextlib import asynccontextmanager
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from misaki.espeak import EspeakG2P
from kokoro_onnx import Kokoro
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matheus-kokoro-tts")

VOICE_NAME = "pm_alex"
MODEL_PATH = Path(os.getenv("KOKORO_MODEL_PATH", "/app/models/kokoro-v1.0.fp16.onnx"))
VOICES_PATH = Path(os.getenv("KOKORO_VOICES_PATH", "/app/models/voices-v1.0.bin"))
API_KEY = os.getenv("TTS_API_KEY") or os.getenv("PIPER_API_KEY")
SPEECH_SPEED = float(os.getenv("KOKORO_SPEED", "1.0"))

kokoro = None
g2p = None
synthesis_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kokoro, g2p
    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Modelo Kokoro não encontrado: {MODEL_PATH}")
    if not VOICES_PATH.is_file():
        raise RuntimeError(f"Arquivo de vozes não encontrado: {VOICES_PATH}")

    logger.info("Carregando Kokoro FP16 e voz %s", VOICE_NAME)
    g2p = EspeakG2P(language="pt-br")
    kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    logger.info("Kokoro pronto; voz ativa: %s", VOICE_NAME)
    yield
    if kokoro is not None:
        try:
            kokoro.voices.close()
        except Exception:
            logger.exception("Falha ao liberar os arquivos de vozes")
    kokoro = None
    g2p = None


app = FastAPI(
    title="Matheus Kokoro TTS",
    description="Síntese de voz em português brasileiro com Kokoro-82M e voz masculina pm_alex.",
    version="2.0.0",
    lifespan=lifespan,
)


class SpeechRequest(BaseModel):
    model: str = "kokoro"
    input: str = Field(min_length=1, max_length=3000)
    voice: str = VOICE_NAME
    response_format: str = "wav"
    speed: float = Field(default=SPEECH_SPEED, ge=0.7, le=1.3)


@app.get("/")
def home():
    return {
        "service": "Matheus Kokoro TTS",
        "engine": "Kokoro-82M",
        "voice": VOICE_NAME,
        "language": "pt-BR",
        "model": MODEL_PATH.name,
        "format": "wav",
    }


@app.get("/health")
def health():
    return {
        "status": "ok" if kokoro is not None and g2p is not None else "loading",
        "engine": "kokoro-82m",
        "voice": VOICE_NAME,
        "language": "pt-BR",
        "model": MODEL_PATH.name,
    }


@app.post("/v1/audio/speech")
def generate_speech(data: SpeechRequest, authorization: str = Header(default="")):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not data.input.strip():
        raise HTTPException(status_code=400, detail="Texto vazio.")
    if data.voice != VOICE_NAME:
        raise HTTPException(status_code=400, detail=f"Voz não disponível. Use {VOICE_NAME}.")
    if data.response_format.lower() != "wav":
        raise HTTPException(status_code=400, detail="Formato ainda não suportado. Use wav.")
    if kokoro is None or g2p is None:
        raise HTTPException(status_code=503, detail="Modelo ainda está carregando.")

    try:
        with synthesis_lock:
            phonemes, _ = g2p(data.input.strip())
            samples, sample_rate = kokoro.create(
                phonemes,
                voice=VOICE_NAME,
                speed=data.speed,
                is_phonemes=True,
            )
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, samples, sample_rate, format="WAV", subtype="PCM_16")
            audio = audio_buffer.getvalue()

        return Response(
            content=audio,
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )
    except Exception:
        logger.exception("Falha ao sintetizar áudio com Kokoro")
        raise HTTPException(status_code=500, detail="Falha ao gerar áudio.")
