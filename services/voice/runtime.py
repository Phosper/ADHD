"""Pipecat input pipeline with generation-labelled WebRTC PCM output."""
import asyncio
import base64
import os
import time
from pathlib import Path

import httpx
from contracts.voice_gateway import VoiceGateway
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams, VADState
from pipecat.frames.frames import InputAudioRawFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

from packages.domain.models import DomainError, Stage, new_id
from packages.domain.state_machine import advance
from packages.observability.audio_archive import AudioArchive


class AudioInput(FrameProcessor):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.vad = SileroVADAnalyzer(sample_rate=16000,
                                   params=VADParams(start_secs=.12, stop_secs=.35))
        self.vad.set_sample_rate(16000)
        self.speaking = False
        self.preroll = b''
        self.buffer = b''
        self.stream_id = ''
        self.seq = 0

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if not isinstance(frame, InputAudioRawFrame):
            await self.push_frame(frame, direction)
            return
        if frame.sample_rate != 16000 or frame.num_channels != 1:
            await self.owner.fail("unexpected_audio_format")
            return
        if self.owner.archive:
            self.owner.archive.append('microphone', frame.audio, 16000)
        state = await self.vad.analyze_audio(frame.audio)
        if not self.speaking:
            self.preroll = (self.preroll + frame.audio)[-9600:]
            if state == VADState.SPEAKING:
                if self.owner.store.session(self.owner.sid).stage in (Stage.CLOSED, Stage.ABORTED):
                    return
                await self.owner.interrupt()
                self.speaking = True
                self.buffer, self.preroll = self.preroll, b''
                self.stream_id, self.seq = new_id(), 0
        else:
            self.buffer += frame.audio
        if self.speaking:
            while len(self.buffer) >= 19200:
                self.enqueue(self.buffer[:19200], False)
                self.buffer = self.buffer[19200:]
            if state == VADState.QUIET:
                self.enqueue(self.buffer, True)
                self.buffer, self.speaking = b'', False
                self.owner.record("speech.ended", {"stream_id": self.stream_id,
                                  "measurement": "server_vad_endpoint"})
            elif self.seq >= 50:
                await self.owner.fail("utterance_too_long")

    def enqueue(self, pcm, final):
        self.owner.audio_queue.put_nowait((self.owner.epoch, self.stream_id, self.seq, pcm, final))
        self.seq += 1

    async def cleanup(self):
        await self.vad.cleanup()
        await super().cleanup()


class VoiceSession:
    def __init__(self, sid, store: VoiceGateway, model):
        self.sid, self.store, self.model = sid, store, model
        self.conn = SmallWebRTCConnection(ice_servers=[])
        self.epoch = 0
        self.audio_queue = asyncio.Queue(maxsize=80)
        self.response_task = None
        self.closed = False
        self.archive = AudioArchive(Path('runtime/audio'), sid) if os.getenv('ZHIYU_RECORD_AUDIO') == '1' else None
        self.http = httpx.AsyncClient(timeout=30, trust_env=False)
        self.asr_url = os.getenv("ZHIYU_ASR_URL", "http://127.0.0.1:18082")
        self.tts_url = os.getenv("ZHIYU_TTS_URL", "http://127.0.0.1:18083")
        self.transport = SmallWebRTCTransport(self.conn, TransportParams(
            audio_in_enabled=True, audio_in_sample_rate=16000, audio_out_enabled=False))
        self.processor = AudioInput(self)
        self.worker = PipelineWorker(Pipeline([self.transport.input(), self.processor]),
            params=PipelineParams(audio_in_sample_rate=16000), enable_rtvi=False,
            idle_timeout_secs=None)
        self.runner = WorkerRunner(handle_sigint=False)
        self.jobs = []

        @self.transport.event_handler("on_client_connected")
        async def connected(transport, client):
            self.record("voice.connected", {"transport": "webrtc", "output": "pcm_datachannel"})
            self.response_task = asyncio.create_task(self.speak(self.store.session(sid), self.epoch))

        @self.transport.event_handler("on_client_disconnected")
        async def disconnected(transport, client):
            await self.close("voice_disconnected")

    def record(self, kind, payload):
        self.store.record(self.sid, kind, payload)

    def send(self, **message):
        if not self.closed:
            self.conn.send_app_message(message)

    async def start(self, sdp):
        await self.conn.initialize(sdp=sdp, type="offer")
        await self.runner.add_workers(self.worker)
        self.jobs = [asyncio.create_task(self.runner.run()), asyncio.create_task(self.consume())]
        for task in self.jobs:
            task.add_done_callback(self.task_finished)
        return self.conn.get_answer()

    def task_finished(self, task):
        if not task.cancelled() and task.exception() and not self.closed:
            asyncio.create_task(self.fail("voice_pipeline_failed"))

    async def interrupt(self):
        self.epoch += 1
        if self.response_task:
            self.response_task.cancel()
        s = self.store.session(self.sid)
        self.send(type="interrupt", generation_id=s.generation_id)
        self.store.interrupt(self.sid)

    async def consume(self):
        texts = {}
        while True:
            epoch, stream, seq, pcm, final = await asyncio.wait_for(self.audio_queue.get(), 60)
            response = await self.http.post(self.asr_url + "/chunk", json={
                "stream_id": stream, "seq": seq, "pcm": base64.b64encode(pcm).decode(), "final": final})
            response.raise_for_status()
            text = response.json()["text"]
            texts[stream] = texts.get(stream, '') + text
            if text:
                self.send(type="asr.partial", text=text)
            if final:
                transcript = texts.pop(stream, '').replace(' ', '').strip()
                if transcript and epoch == self.epoch:
                    self.response_task = asyncio.create_task(self.respond(transcript, epoch))

    async def respond(self, text, epoch):
        try:
            s = self.store.session(self.sid)
            started = time.monotonic()
            intent, answer = await self.model.interpret(text, s)
            if epoch != self.epoch or self.closed:
                return
            self.record("intent.validated", {"kind": intent.kind.value, "confidence": intent.confidence,
                        "pipeline": "model_then_deterministic_guard",
                        "duration_ms": (time.monotonic() - started) * 1000})
            request_id = new_id()
            result = self.store.turn(self.sid, request_id, {"expected_version": s.version,
                       "text": text, "source": "voice", "request_id": request_id},
                       lambda current: advance(current, intent, answer))
            await self.speak(result, epoch)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.fail("voice_turn_failed")

    async def speak(self, s, epoch):
        try:
            self.send(type="audio-start", generation_id=s.generation_id, text=s.last_response)
            count = 0
            async with self.http.stream("POST", self.tts_url + "/speak", json={"text": s.last_response}) as response:
                response.raise_for_status()
                rate = int(response.headers["X-Sample-Rate"])
                source = response.headers.get('X-Audio-Source', 'unspecified')
                if rate not in (16000, 22050, 24000, 48000):
                    raise ValueError("Unsupported TTS sample rate")
                pending = b''
                async for part in response.aiter_bytes(chunk_size=4800):
                    pending += part
                    end = len(pending) // 2 * 2
                    if not end:
                        continue
                    part, pending = pending[:end], pending[end:]
                    if epoch != self.epoch or self.closed:
                        return
                    if self.archive:
                        self.archive.append(f'output-{s.generation_id}', part, rate)
                    self.send(type="audio-chunk", generation_id=s.generation_id, seq=count,
                              sample_rate=rate, pcm=base64.b64encode(part).decode())
                    count += 1
                    # Bound reliable-channel buffering to avoid seconds of old audio queued.
                    await asyncio.sleep(len(part) / (rate * 2) * .9)
            self.record("tts.generated", {"generation_id": s.generation_id, "chunks": count,
                                         "audio_source": source})
            self.send(type="audio-end", generation_id=s.generation_id, chunks=count)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.fail("tts_failed")

    async def fail(self, reason):
        if self.closed:
            return
        try:
            self.record("voice.error", {"code": reason})
        finally:
            self.send(type="error", message="语音服务异常，本次已停止，请查看会话记录。")
            await self.close(reason)

    async def close(self, reason="user_disconnected"):
        if self.closed:
            return
        self.closed = True
        self.epoch += 1
        current = asyncio.current_task()
        try:
            self.store.abort(self.sid, reason)
        finally:
            for task in [*self.jobs, self.response_task]:
                if task and task is not current:
                    task.cancel()
            await self.http.aclose()
            await self.conn.disconnect()
            if self.archive:
                self.archive.close()


class VoiceManager:
    def __init__(self, store, model):
        self.store, self.model, self.active = store, model, None
        self.lock = asyncio.Lock()

    async def ready(self):
        try:
            urls = [os.getenv("ZHIYU_LLM_URL", "http://127.0.0.1:18081/v1").removesuffix('/v1'),
                    os.getenv("ZHIYU_ASR_URL", "http://127.0.0.1:18082"),
                    os.getenv("ZHIYU_TTS_URL", "http://127.0.0.1:18083")]
            async with httpx.AsyncClient(timeout=2, trust_env=False) as client:
                results = await asyncio.gather(*(client.get(url + '/health') for url in urls))
            return all(r.status_code == 200 and r.json().get('ready') for r in results)
        except (httpx.HTTPError, ValueError):
            return False

    async def offer(self, sid, sdp):
        async with self.lock:
            if self.active and not self.active.closed:
                raise DomainError("voice_busy", "基线仅支持单通语音，请先结束当前通话")
            if self.store.session(sid).stage in (Stage.CLOSED, Stage.ABORTED):
                raise DomainError("session_closed", "请创建新会话后连接语音")
            if not await self.ready():
                raise DomainError("model_not_ready", "三项模型服务尚未全部就绪", 503)
            self.active = VoiceSession(sid, self.store, self.model)
            try:
                return await self.active.start(sdp)
            except Exception:
                await self.active.close("negotiation_failed")
                raise

    async def close(self, sid=None):
        if self.active and (sid is None or self.active.sid == sid):
            await self.active.close()
