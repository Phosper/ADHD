import math
import struct

import pytest

from services.voice.speech_gate import SpeechStartGate, ac_level_dbfs


def pcm(ms=20, amplitude=2000, rate=16000, dc=0):
    samples = [round(dc + amplitude * math.sin(2 * math.pi * 440 * i / rate))
               for i in range(round(rate * ms / 1000))]
    return struct.pack('<' + 'h' * len(samples), *samples)


def test_short_impulse_does_not_interrupt_but_continuous_voice_can():
    gate = SpeechStartGate()
    assert not gate.accept(pcm(), 16000, True)
    assert not gate.accept(pcm(amplitude=0), 16000, False)
    assert all(not gate.accept(pcm(), 16000, True) for _ in range(3))
    assert gate.accept(pcm(), 16000, True)


def test_low_noise_and_dc_do_not_open_gate_even_with_vad_false_positive():
    gate = SpeechStartGate()
    for _ in range(100):
        assert not gate.accept(pcm(amplitude=10, dc=6000), 16000, True)
    assert ac_level_dbfs(pcm(amplitude=0, dc=6000)) == -math.inf
    # Soft speech above the conservative floor must still be able to interrupt.
    assert not gate.accept(pcm(ms=40, amplitude=200), 16000, True)
    assert gate.accept(pcm(ms=40, amplitude=200), 16000, True)


def test_frame_duration_controls_confirmation_and_reset_starts_new_utterance():
    gate = SpeechStartGate()
    assert not gate.accept(pcm(ms=30), 16000, True)
    assert not gate.accept(pcm(ms=30), 16000, True)
    assert gate.accept(pcm(ms=20), 16000, True)
    gate.reset()
    assert not gate.accept(pcm(ms=20), 16000, True)
    assert not gate.accept(pcm(ms=100), 16000, False)


@pytest.mark.parametrize('confirm,threshold', [(0,-50),(151,-50),(80,float('nan')),
                                              (float('inf'),-50),(80,-100)])
def test_invalid_gate_configuration_is_rejected(confirm, threshold):
    with pytest.raises(ValueError):
        SpeechStartGate(confirm, threshold)


def test_gate_environment_overrides(monkeypatch):
    monkeypatch.setenv('ZHIYU_SPEECH_CONFIRM_MS', '40')
    monkeypatch.setenv('ZHIYU_SPEECH_MIN_DBFS', '-60')
    gate = SpeechStartGate.from_env()
    assert gate.accept(pcm(ms=40), 16000, True)
    with pytest.raises(ValueError):
        ac_level_dbfs(b'x')
