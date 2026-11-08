import json
import subprocess
import tarfile

import pytest

from packages.observability.source_identity import digest, source_identity
from scripts.package_source import create_archive


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


def test_actual_git_archive_carries_verified_identity(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    (repo / 'main.py').write_text('print(1)\n')
    subprocess.run(['git', 'add', 'main.py'], cwd=repo, check=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'fixture'], cwd=repo, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo).decode().strip()
    output = tmp_path / 'source.tar'
    create_archive(repo, commit, output)
    release = tmp_path / 'release'
    release.mkdir()
    with tarfile.open(output) as archive:
        for member in archive.getmembers():
            if member.isfile():
                (release / member.name).write_bytes(archive.extractfile(member).read())
    identity = source_identity(release)
    assert identity['code_commit'] == commit and identity['dirty'] is False
    with pytest.raises(FileExistsError):
        create_archive(repo, commit, output)
