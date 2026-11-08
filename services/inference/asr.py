"""Bounded streaming Paraformer service; one request per 600 ms PCM block."""
import base64
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    stream_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    seq: int = Field(ge=0, le=100)
    pcm: str = Field(max_length=30000)
    final: bool = False


def create_app():
    import numpy as np
    from funasr import AutoModel
    lock, streams = threading.Lock(), {}

    @asynccontextmanager
    async def lifespan(app):
        app.state.model = AutoModel(model=os.environ["ZHIYU_ASR_PATH"], device="cuda:0",
                                   disable_update=True, trust_remote_code=False)
        yield
        streams.clear()

    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"ready": hasattr(app.state, "model"), "model": "paraformer-streaming",
                "sample_rate": 16000, "chunk_samples": 9600}

    @app.post("/chunk")
    def chunk(body: Chunk):
        try:
            pcm = base64.b64decode(body.pcm, validate=True)
        except ValueError:
            raise HTTPException(422, "Invalid PCM")
        if len(pcm) > 19200 or len(pcm) % 2 or (not body.final and len(pcm) != 19200):
            raise HTTPException(422, "Expected 600 ms mono int16 at 16 kHz")
        with lock:
            for key in list(streams):
                if time.monotonic() - streams[key]["last"] > 60:
                    del streams[key]
            if body.stream_id not in streams:
                if body.seq != 0 or len(streams) >= 2:
                    raise HTTPException(409, "Unknown stream or capacity reached")
                streams[body.stream_id] = {"cache": {}, "seq": 0, "last": time.monotonic()}
            state = streams[body.stream_id]
            if body.seq != state["seq"]:
                raise HTTPException(409, "ASR chunk sequence mismatch; restart utterance")
            samples = np.frombuffer(pcm, dtype='<i2').astype(np.float32) / 32768
            if not len(samples):
                samples = np.zeros(1, dtype=np.float32)
            try:
                result = app.state.model.generate(input=samples, cache=state["cache"],
                    is_final=body.final, chunk_size=[0, 10, 5], encoder_chunk_look_back=4,
                    decoder_chunk_look_back=1, disable_pbar=True)
                state["seq"] += 1
                state["last"] = time.monotonic()
                return {"text": ''.join(r.get("text", '') for r in result), "final": body.final}
            finally:
                if body.final:
                    streams.pop(body.stream_id, None)

    return app
