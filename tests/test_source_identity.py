import json
import subprocess

import pytest

from packages.observability.source_identity import digest, source_identity


def packaged(root):
    (root / 'services').mkdir()
    (root / 'services/main.py').write_text('x = 1\n')
    manifest = {'code_commit': 'a' * 40,
                'files': {'services/main.py': digest((root / 'services/main.py').read_bytes())}}
    (root / '.source-manifest.json').write_text(json.dumps(manifest))
    return manifest


def test_archive_detects_edit_delete_and_added_code(tmp_path):
    packaged(tmp_path)
    assert source_identity(tmp_path)['dirty'] is False
    (tmp_path / 'services/main.py').write_text('x = 2\n')
    assert source_identity(tmp_path)['source_changes'] == ['services/main.py']
    (tmp_path / 'services/main.py').unlink()
    (tmp_path / 'services/extra.py').write_text('x = 3\n')
    assert source_identity(tmp_path)['source_changes'] == ['services/extra.py', 'services/main.py']


def test_archive_rejects_outside_path(tmp_path):
    manifest = packaged(tmp_path)
    manifest['files']['../outside.py'] = '0' * 64
    (tmp_path / '.source-manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='path'):
        source_identity(tmp_path)


def test_release_never_inherits_parent_repository(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    release = tmp_path / 'release'
    release.mkdir()
    assert source_identity(release) == {'code_commit': 'unknown', 'dirty': True,
                                        'source_kind': 'unverified'}
