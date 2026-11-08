import json
import hashlib

import pytest

from packages.observability.audio_archive import AudioArchive


def test_private_archive_preserves_format_hash_and_rejects_overwrite(tmp_path):
    archive = AudioArchive(tmp_path,'session')
    archive.append('microphone',b'\0\0'*160,16000)
    archive.append('output-2',b'\1\0'*240,24000)
    archive.close()
    manifest = json.loads((tmp_path/'session/manifest.json').read_text())
    assert manifest['microphone']['bytes']==320
    assert manifest['output-2']['sha256']==hashlib.sha256(b'\1\0'*240).hexdigest()
    assert 'not playback' in manifest['output-2']['meaning']
    with pytest.raises(FileExistsError):
        AudioArchive(tmp_path,'session')
