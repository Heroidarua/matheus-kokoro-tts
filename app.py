import asyncio
import base64
import gc
import io
import json
import logging
import os
from contextlib import asynccontextmanager

import soundfile as sf
import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from qwen_tts import Qwen3TTSModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ada-m-voice")

VOICE_DESIGN_MODEL = os.getenv("VOICE_DESIGN_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign")
VOICE_CLONE_MODEL = os.getenv("VOICE_CLONE_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-Base")
VOICE_NAME = "ada-m-original-ptbr"
API_KEY = os.getenv("TTS_API_KEY", "").strip()
DEVICE = os.getenv("TTS_DEVICE", "cuda:0")
LANGUAGE = "Portuguese"
VOICE_INSTRUCTION = (
    "A completely original adult Brazilian Portuguese male voice, around 30 years old. "
    "Natural, warm and human conversational delivery, medium-low pitch, smooth but "
    "slightly textured resonance, clear articulation, relaxed breathing, friendly "
    "and thoughtful tone. Speak like a helpful person talking naturally to one person, "
    "with subtle expressive intonation and realistic pauses. Use authentic Brazilian "
    "Portuguese pronunciation. Avoid a radio announcer style, exaggerated bass, "
    "robotic rhythm, theatrical acting or excessive enthusiasm."
)
REFERENCE_TEXT = (
    "Oi, eu sou a ADA-M. Estou aqui para conversar com você de um jeito natural, "
    "claro e tranquilo. Pode me contar o que precisa; vou pensar com cuidado e "
    "ajudar no que estiver ao meu alcance."
)

tts_model = None
voice_clone_prompt = None
model_ready = False
synthesis_lock = asyncio.Lock()


def _load_models():
    global tts_model, voice_clone_prompt, model_ready
    if not torch.cuda.is_available():
        raise RuntimeError(
            "Qwen3-TTS VoiceDesign precisa de uma GPU NVIDIA CUDA. "
            "Render Free não oferece os recursos necessários."
        )

    logger.info("Loading voice-design model: %s", VOICE_DESIGN_MODEL)
    design_model = Qwen3TTSModel.from_pretrained(
        VOICE_DESIGN_MODEL, device_map=DEVICE, dtype=torch.float16
    )
    ref_wavs, sample_rate = design_model.generate_voice_design(
        text=REFERENCE_TEXT,
        language=LANGUAGE,
        instruct=VOICE_INSTRUCTION,
        do_sample=True,
        temperature=0.7,
        top_p=0.85,
    )
    reference_audio = ref_wavs[0]
    del design_model, ref_wavs
    gc.collect()
    torch.cuda.empty_cache()

    logger.info("Loading reusable voice model: %s", VOICE_CLONE_MODEL)
    tts_model = Qwen3TTSModel.from_pretrained(
        VOICE_CLONE_MODEL, device_map=DEVICE, dtype=torch.float16
    )
    voice_clone_prompt = tts_model.create_voice_clone_prompt(
        ref_audio=(reference_audio, sample_rate),
        ref_text=REFERENCE_TEXT,
        x_vector_only_mode=False,
    )
    del reference_audio
    gc.collect()
    model_ready = True
    logger.info("ADA-M original Brazilian Portuguese voice is ready.")


def _synthesize(text: str) -> bytes:
    if not model_ready or tts_model is None or voice_clone_prompt is None:
        raise RuntimeError("A voz original da ADA-M ainda está carregando.")
    wavs, sample_rate = tts_model.generate_voice_clone(
        text=text,
        language=LANGUAGE,
        voice_clone_prompt=voice_clone_prompt,
        do_sample=True,
        temperature=0.7,
        top_p=0.85,
        repetition_penalty=1.05,
        max_new_tokens=2048,
    )
    output = io.BytesIO()
    sf.write(output, wavs[0], sample_rate, format="WAV", subtype="PCM_16")
    return output.getvalue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_ready
    model_ready = False
    await asyncio.to_thread(_load_models)
    yield
    model_ready = False


app = FastAPI(
    title="ADA-M Original Voice",
    description="Original synthetic Brazilian Portuguese voice designed for ADA-M using Qwen3-TTS.",
    version="1.0.0",
    lifespan=lifespan,
)


class SpeechRequest(BaseModel):
    model: str = "ada-m-original"
    input: str = Field(min_length=1, max_length=3000)
    voice: str = VOICE_NAME
    response_format: str = "wav"
    speed: float = Field(default=1.0, ge=0.7, le=1.3)


def _authorize(authorization: str):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/")
def home():
    return {
        "service": "ADA-M Original Voice",
        "engine": "Qwen3-TTS VoiceDesign + Base",
        "voice": VOICE_NAME,
        "language": "pt-BR",
        "profile": "original-male-natural-conversational",
    }


@app.get("/health")
def health():
    return {
        "status": "ok" if model_ready else "loading",
        "engine": "qwen3-tts",
        "voice": VOICE_NAME,
        "language": "pt-BR",
        "device": DEVICE,
    }


@app.post("/v1/audio/speech")
async def generate_speech(data: SpeechRequest, authorization: str = Header(default="")):
    _authorize(authorization)
    if data.voice not in (VOICE_NAME, "ada-m-original", "alloy"):
        raise HTTPException(status_code=400, detail=f"Voz indisponível. Use {VOICE_NAME}.")
    if not model_ready:
        raise HTTPException(status_code=503, detail="A voz original ainda está carregando.")
    try:
        async with synthesis_lock:
            audio = await asyncio.to_thread(_synthesize, data.input.strip())
        return Response(
            content=audio,
            media_type="audio/wav",
            headers={"Cache-Control": "no-store", "Content-Disposition": 'inline; filename="ada-m.wav"'},
        )
    except Exception:
        logger.exception("Voice synthesis failed")
        raise HTTPException(status_code=500, detail="Não foi possível sintetizar a voz original da ADA-M.")


@app.post("/v1/audio/speech/stream")
async def generate_speech_stream(data: SpeechRequest, authorization: str = Header(default="")):
    _authorize(authorization)
    if data.voice not in (VOICE_NAME, "ada-m-original", "alloy"):
        raise HTTPException(status_code=400, detail=f"Voz indisponível. Use {VOICE_NAME}.")
    if not model_ready:
        raise HTTPException(status_code=503, detail="A voz original ainda está carregando.")

    async def audio_events():
        try:
            async with synthesis_lock:
                audio = await asyncio.to_thread(_synthesize, data.input.strip())
            encoded = base64.b64encode(audio).decode("ascii")
            yield "data: " + json.dumps({"audio": encoded}, separators=(",", ":")) + "\n\n"
            yield "event: done\ndata: {}\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Streaming voice synthesis failed")
            yield "event: error\ndata: {\"detail\":\"Falha ao sintetizar a voz original da ADA-M.\"}\n\n"

    return StreamingResponse(
        audio_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
