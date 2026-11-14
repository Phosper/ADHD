import struct

import pytest

from services.voice.segmentation import SpeechSegmenter
from services.voice.speech_gate import SpeechStartGate


def frame(value=2000, ms=20):
    return struct.pack('<hh', value, -value) * (16 * ms // 2)


def test_rejected_noise_does_not_start_asr_or_cancel_playback():
    segmenter = SpeechSegmenter()
    for _ in range(30):
        update = segmenter.feed(frame(10), speaking=True, quiet=False)
        assert not update.started and not update.chunks
    assert not segmenter.feed(frame(), speaking=True, quiet=False).started
    update = segmenter.feed(frame(0), speaking=False, quiet=True)
    assert not update.started and not update.ended and not update.chunks


def test_onset_confirmation_preserves_pcm_and_chunk_sequence_without_duplication():
    segmenter = SpeechSegmenter()
    submitted = []
    updates = []
    # The retained 300 ms consists of 200 ms context plus 80 ms confirmation.
    for i in range(10):
        part = frame(100 + i)
        submitted.append(part)
        updates.append(segmenter.feed(part, speaking=False, quiet=True))
    for i in range(34):
        part = frame(1000 + i)
        submitted.append(part)
        updates.append(segmenter.feed(part, speaking=True, quiet=False))
    trailing = frame(0)
    submitted.append(trailing)
    updates.append(segmenter.feed(trailing, speaking=False, quiet=True))
    chunks = [chunk for update in updates for chunk in update.chunks]
    assert sum(update.started for update in updates) == 1
    assert sum(update.ended for update in updates) == 1
    assert b''.join(chunk.pcm for chunk in chunks) == b''.join(submitted)
    assert all(len(chunk.pcm) == 19200 for chunk in chunks[:-1])
    assert [chunk.final for chunk in chunks] == [False] * (len(chunks) - 1) + [True]


def test_preroll_is_bounded_and_following_utterance_does_not_reuse_old_audio():
    segmenter = SpeechSegmenter(SpeechStartGate(confirm_ms=20))
    for _ in range(100):
        segmenter.feed(frame(10), speaking=False, quiet=True)
    assert len(segmenter.preroll) == 9600
    assert segmenter.feed(frame(2000), speaking=True, quiet=False).started
    first = segmenter.feed(frame(0), speaking=False, quiet=True)
    assert first.ended
    assert segmenter.feed(frame(3000), speaking=True, quiet=False).started
    second = segmenter.feed(frame(0), speaking=False, quiet=True)
    assert b''.join(chunk.pcm for chunk in second.chunks) == frame(3000) + frame(0)


def test_long_input_is_bounded_even_when_caller_delivers_a_large_pcm_frame():
    segmenter = SpeechSegmenter(SpeechStartGate(confirm_ms=20))
    assert segmenter.feed(frame(), speaking=True, quiet=False).started
    update = segmenter.feed(frame(ms=31000), speaking=True, quiet=False)
    assert update.too_long and len(update.chunks) == 50
    assert not segmenter.feed(frame(), speaking=True, quiet=False).chunks


def test_invalid_pcm_and_conflicting_vad_states_fail_explicitly():
    segmenter = SpeechSegmenter()
    with pytest.raises(ValueError):
        segmenter.feed(b'x', speaking=True, quiet=False)
    with pytest.raises(ValueError):
        segmenter.feed(frame(), speaking=True, quiet=True)
