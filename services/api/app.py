import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from packages.domain.models import (
    Case, CaseResult, ClientEvent, CreateSession, DomainError, ErrorResponse, Session,
    UserTurn, VoiceOffer, NoAnswer,
)
from packages.domain.state_machine import advance
from packages.observability.manifest import ROOT, build_manifest
from packages.observability.report import report
from packages.storage.sqlite import Store
from services.api.interpreter import interpret_mock, safe_answer
from services.api.model_client import ModelClient


def create_app(db_path: str | Path | None = None, token: str | None = None,
               recover: bool = True) -> FastAPI:
    db_path = db_path or os.getenv("ZHIYU_DB", "runtime/zhiyu.sqlite")
    token = token if token is not None else os.getenv("ZHIYU_API_TOKEN", "")
    mode = os.getenv("ZHIYU_MODE", "mock")
    store = Store(db_path)
    store.seed([Case.model_validate(v) for v in json.loads(
        (ROOT / "configs/synthetic_cases.json").read_text(encoding="utf-8"))])
    knowledge_path = Path(os.environ["ZHIYU_KNOWLEDGE"]) if os.getenv("ZHIYU_KNOWLEDGE") else None
    manifest = build_manifest(mode, knowledge_path)
    model = ModelClient(os.getenv("ZHIYU_LLM_URL", "http://127.0.0.1:18081/v1"),
                        os.getenv("ZHIYU_LLM_MODEL", "Qwen3-8B"), knowledge_path)
    if mode not in ("mock", "real"):
        raise ValueError("ZHIYU_MODE must be mock or real")
    voice = None
    if mode == "real" and os.getenv("ZHIYU_VOICE_ENABLED") == "1":
        from services.voice.runtime import VoiceManager
        from services.api.voice_gateway import Gateway
        voice = VoiceManager(Gateway(store), model)

    @asynccontextmanager
    async def lifespan(app):
        if recover:
            store.recover()
        yield
        if voice:
            await voice.close()

    app = FastAPI(title="智语外呼业务 API", version="0.1.0", lifespan=lifespan)
    app.state.store = store

    async def authenticate(request: Request, authorization: str | None = Header(default=None)):
        if token:
            if not secrets.compare_digest(authorization or "", f"Bearer {token}"):
                raise DomainError("unauthorized", "请填写有效访问令牌", 401)
        elif request.client and request.client.host not in ("127.0.0.1", "::1", "testclient"):
            raise DomainError("token_required", "远程访问必须配置服务端令牌", 403)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(status_code=exc.status, content=ErrorResponse(
            code=exc.code, message=exc.message).model_dump())

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": mode, "voice_ready": bool(voice and await voice.ready()), "version": "0.1.0"}

    auth = [Depends(authenticate)]

    @app.get("/api/cases", response_model=list[Case], dependencies=auth)
    def cases():
        return store.cases()

    @app.get("/api/cases/{case_id}/result", response_model=CaseResult, dependencies=auth)
    def case_result(case_id: str):
        return store.case_result(case_id)

    @app.get("/api/sessions", response_model=list[Session], dependencies=auth)
    def sessions():
        return store.sessions()

    @app.post("/api/sessions", response_model=Session, dependencies=auth)
    def create(body: CreateSession):
        return store.create(body.case_id, body.request_id, manifest)

    @app.get("/api/sessions/{session_id}", response_model=Session, dependencies=auth)
    def session(session_id: str):
        return store.session(session_id)

    @app.post("/api/sessions/{session_id}/turns", response_model=Session, dependencies=auth)
    async def turn(session_id: str, body: UserTurn):
        if voice and voice.active and not voice.active.closed and voice.active.sid == session_id:
            raise DomainError("voice_active", "语音通话中不接受文字轮次，请先断开语音")
        cached = store.cached_turn(session_id, body.request_id, body.model_dump())
        if cached:
            return cached
        s = store.session(session_id)
        if body.expected_version != s.version:
            raise DomainError("version_conflict", "会话已变化，请刷新后重试")
        if mode == "real":
            intent, answer = await model.interpret(body.text, s)
            return store.turn(session_id, body.request_id, body.model_dump(),
                              lambda current: advance(current, intent, answer))
        return store.turn(session_id, body.request_id, body.model_dump(),
                          lambda s: advance(s, interpret_mock(body.text, s), safe_answer(body.text)))

    @app.post("/api/sessions/{session_id}/events", response_model=Session, dependencies=auth)
    def client_event(session_id: str, body: ClientEvent):
        return store.client_event(session_id, body)

    @app.post("/api/sessions/{session_id}/no-answer", response_model=Session, dependencies=auth)
    async def no_answer(session_id: str, body: NoAnswer):
        if voice and voice.active and not voice.active.closed and voice.active.sid == session_id:
            raise DomainError("voice_active", "已接通语音不能标记未接通")
        return store.no_answer(session_id, body.model_dump())

    @app.get("/api/sessions/{session_id}/events", dependencies=auth)
    def events(session_id: str, after: int = Query(default=0, ge=0)):
        return store.events(session_id, after)

    @app.post("/api/sessions/{session_id}/end", response_model=Session, dependencies=auth)
    async def end(session_id: str):
        if voice:
            await voice.close(session_id)
        return store.abort(session_id)

    @app.post("/api/sessions/{session_id}/offer", dependencies=auth)
    async def offer(session_id: str, body: VoiceOffer):
        if not voice:
            raise DomainError("voice_unavailable", "当前未启用真实语音", 503)
        answer = await voice.offer(session_id, body.sdp)
        return {"sdp": answer["sdp"], "type": answer["type"]}

    @app.post("/api/sessions/{session_id}/disconnect", dependencies=auth)
    async def disconnect(session_id: str):
        if voice:
            await voice.close(session_id)
        return store.session(session_id)

    @app.get("/api/sessions/{session_id}/report", dependencies=auth)
    def quality(session_id: str):
        return report(store.session(session_id), store.events(session_id))

    @app.get("/api/operations/{operation_id}", dependencies=auth)
    def operation(operation_id: str):
        return store.operation(operation_id)

    web = ROOT / "apps/web/dist"
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="web")
    return app


# Factory entry: uvicorn services.api.app:create_app --factory --host 127.0.0.1
