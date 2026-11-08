"""Optional per-session PCM evidence; private runtime only, no implicit Git publication."""
import hashlib
import json
from pathlib import Path


class AudioArchive:
    def __init__(self, root: Path, session_id: str):
        self.path = root / session_id
        self.path.mkdir(parents=True, exist_ok=False)
        self.files = {}
        self.closed = False

    def append(self, name: str, pcm: bytes, sample_rate: int):
        if self.closed:
            return
        if name not in self.files:
            stream = (self.path / (name + '.pcm')).open('xb')
            self.files[name] = (stream, sample_rate, hashlib.sha256(), 0)
        stream, rate, digest, count = self.files[name]
        if rate != sample_rate or len(pcm) % 2:
            raise ValueError('Audio archive format mismatch')
        stream.write(pcm)
        digest.update(pcm)
        self.files[name] = (stream, rate, digest, count + len(pcm))

    def close(self):
        if self.closed:
            return
        self.closed = True
        manifest = {}
        for name, (stream, rate, digest, count) in self.files.items():
            stream.close()
            manifest[name] = {'file': name + '.pcm', 'sample_rate': rate, 'channels': 1,
                              'format': 's16le', 'bytes': count, 'sha256': digest.hexdigest(),
                              'meaning': 'received microphone' if name == 'microphone' else 'generated output, not playback proof'}
        (self.path / 'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
