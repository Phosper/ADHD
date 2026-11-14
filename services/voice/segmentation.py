"""PCM segmentation shared by the live adapter and hardware-free replay tests."""
from dataclasses import dataclass

from services.voice.speech_gate import SpeechStartGate


@dataclass(frozen=True)
class AudioChunk:
    pcm: bytes
    final: bool


@dataclass(frozen=True)
class SegmentUpdate:
    started: bool = False
    ended: bool = False
    chunks: tuple[AudioChunk, ...] = ()
    too_long: bool = False


class SpeechSegmenter:
    """Accept mono int16 LE at 16 kHz; VAD decisions come from the caller."""

    def __init__(self, gate: SpeechStartGate | None = None):
        self.gate = gate if gate is not None else SpeechStartGate()
        self.speaking = False
        self.preroll = b''
        self.buffer = b''
        self.chunks_sent = 0
        self.exhausted = False

    def feed(self, pcm: bytes, *, speaking: bool, quiet: bool) -> SegmentUpdate:
        if len(pcm) % 2:
            raise ValueError('Expected mono int16 PCM')
        if speaking and quiet:
            raise ValueError('Conflicting VAD states')
        if self.exhausted:
            return SegmentUpdate(too_long=True)
        started = False
        if not self.speaking:
            # 300 ms includes the audio observed while confirming speech onset.
            self.preroll = (self.preroll + pcm)[-9600:]
            if not self.gate.accept(pcm, 16000, speaking):
                return SegmentUpdate()
            self.speaking, started = True, True
            self.buffer, self.preroll = self.preroll, b''
            self.chunks_sent = 0
        else:
            self.buffer += pcm
        chunks = []
        while len(self.buffer) >= 19200:
            chunks.append(AudioChunk(self.buffer[:19200], False))
            self.buffer = self.buffer[19200:]
            self.chunks_sent += 1
            if self.chunks_sent >= 50:
                self.exhausted = True
                self.buffer = b''
                return SegmentUpdate(started=started, chunks=tuple(chunks), too_long=True)
        if quiet:
            chunks.append(AudioChunk(self.buffer, True))
            self.buffer, self.speaking = b'', False
            self.gate.reset()
        return SegmentUpdate(started=started, ended=quiet, chunks=tuple(chunks))
