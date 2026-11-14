"""Confirm VAD speech before cancelling playback; this does not denoise PCM."""
import math
import os
import sys
from array import array


def ac_level_dbfs(pcm: bytes) -> float:
    """Measure int16 mono energy without allowing a DC offset to open the gate."""
    if len(pcm) % 2:
        raise ValueError("Expected signed int16 PCM")
    samples = array('h', pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples:
        return -math.inf
    mean = sum(samples) / len(samples)
    power = max(0.0, sum(value * value for value in samples) / len(samples) - mean * mean)
    return 10 * math.log10(power / (32768 ** 2)) if power else -math.inf


class SpeechStartGate:
    def __init__(self, confirm_ms: float = 80, min_dbfs: float = -50):
        # Keep the added confirmation shorter than the existing 300 ms pre-roll.
        if not math.isfinite(confirm_ms) or not 20 <= confirm_ms <= 150:
            raise ValueError("Speech confirmation must be between 20 and 150 ms")
        if not math.isfinite(min_dbfs) or not -96 <= min_dbfs <= -10:
            raise ValueError("Speech threshold must be between -96 and -10 dBFS")
        self.confirm_ms, self.min_dbfs = confirm_ms, min_dbfs
        self.active_ms = 0.0

    @classmethod
    def from_env(cls):
        return cls(float(os.getenv('ZHIYU_SPEECH_CONFIRM_MS', '80')),
                   float(os.getenv('ZHIYU_SPEECH_MIN_DBFS', '-50')))

    def accept(self, pcm: bytes, sample_rate: int, vad_speaking: bool) -> bool:
        if sample_rate <= 0:
            raise ValueError("Invalid sample rate")
        if not vad_speaking or ac_level_dbfs(pcm) < self.min_dbfs:
            self.active_ms = 0.0
            return False
        self.active_ms += len(pcm) / (2 * sample_rate) * 1000
        return self.active_ms >= self.confirm_ms

    def reset(self):
        self.active_ms = 0.0
