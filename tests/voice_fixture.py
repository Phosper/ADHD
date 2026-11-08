"""TEST ONLY: synthetic tone provider, not ASR/LLM/TTS acceptance evidence."""
import math
import struct

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get("/health")
def health():
    return {"ready": True, "test_fixture": True}


@app.post("/speak")
def speak():
    pcm = b''.join(struct.pack('<h', int(2000 * math.sin(i * 2 * math.pi * 440 / 24000))) for i in range(24000))
    return StreamingResponse(iter([pcm]), media_type="application/octet-stream", headers={"X-Sample-Rate": "24000"})


@app.post("/chunk")
def chunk():
    return {"text": "", "final": False}
