"""Single-session self-hosted Qwen3 adapter. Runs in the isolated model environment."""
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class Chat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    messages: list[dict[str, str]] = Field(min_length=1, max_length=8)
    max_tokens: int = Field(default=160, ge=1, le=256)
    temperature: float = Field(default=0, ge=0, le=1)
    chat_template_kwargs: dict = Field(default_factory=dict)


def create_app():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    path = os.environ["ZHIYU_LLM_PATH"]
    gate = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable; refusing silent CPU fallback")
        if torch.cuda.mem_get_info()[0] < 22 * 1024**3:
            raise RuntimeError("Need at least 22 GiB free; do not stop other GPU jobs")
        torch.set_num_threads(4)
        app.state.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True,
                                                            trust_remote_code=False)
        app.state.model = AutoModelForCausalLM.from_pretrained(
            path, local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
        app.state.model.eval()
        yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"ready": hasattr(app.state, "model"), "model": "Qwen3-8B",
                "backend": "transformers", "thinking": False}

    @app.post("/v1/chat/completions")
    def completion(body: Chat):
        if body.model != "Qwen3-8B":
            raise HTTPException(400, "Unexpected model")
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "Single-session model busy")
        try:
            if any(set(m) != {"role", "content"} or m["role"] not in ("system", "user", "assistant") for m in body.messages):
                raise HTTPException(422, "Invalid message")
            tokenizer = app.state.tokenizer
            prompt = tokenizer.apply_chat_template(body.messages, tokenize=False,
                         add_generation_prompt=True, enable_thinking=False)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            if inputs.input_ids.shape[1] > 2048:
                raise HTTPException(413, "Context limit exceeded")
            with torch.inference_mode():
                output = app.state.model.generate(**inputs, max_new_tokens=body.max_tokens,
                    do_sample=False, pad_token_id=tokenizer.eos_token_id)
            completion_ids = output[0][inputs.input_ids.shape[1]:]
            return {"model": body.model, "choices": [{"message": {"role": "assistant",
                    "content": tokenizer.decode(completion_ids, skip_special_tokens=True)}}],
                    "usage": {"prompt_tokens": inputs.input_ids.shape[1],
                              "completion_tokens": len(completion_ids)}}
        finally:
            gate.release()

    return app
