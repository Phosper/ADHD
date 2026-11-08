"""CosyVoice2 streams 24 kHz mono int16 PCM; reference is a licensed project sample."""
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


class Speech(BaseModel):
    text: str = Field(min_length=1, max_length=1500)


def create_app():
    from cosyvoice.cli.cosyvoice import CosyVoice2
    gate = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        reference = Path(os.environ["ZHIYU_TTS_REFERENCE"])
        if not reference.is_file():
            raise RuntimeError("Missing authorized reference audio")
        app.state.model = CosyVoice2(os.environ["ZHIYU_TTS_PATH"], load_jit=False,
                                     load_trt=False, fp16=True)
        app.state.model.add_zero_shot_spk(os.environ["ZHIYU_TTS_REFERENCE_TEXT"],
                                         str(reference), 'baseline_reference')
        yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"ready": hasattr(app.state, "model"), "model": "CosyVoice2-0.5B",
                "sample_rate": app.state.model.sample_rate if hasattr(app.state, "model") else None}

    @app.post("/speak")
    def speak(body: Speech):
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "Single-session TTS busy")

        def generate():
            try:
                for part in app.state.model.inference_zero_shot(body.text, '', '',
                    zero_shot_spk_id='baseline_reference', stream=True, text_frontend=False):
                    audio = part['tts_speech'].detach().cpu().numpy().reshape(-1)
                    yield (audio.clip(-1, 1) * 32767).astype('<i2').tobytes()
            finally:
                gate.release()
        return StreamingResponse(generate(), media_type="application/octet-stream",
                                 headers={"X-Sample-Rate": str(app.state.model.sample_rate)})

    return app
