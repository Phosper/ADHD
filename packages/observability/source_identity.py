"""Identify a checkout or a verified source archive without inheriting a parent Git repo."""
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_identity(root: Path) -> dict:
    root = root.resolve()
    packaged = root / '.source-manifest.json'
    if packaged.is_file():
        manifest = json.loads(packaged.read_text(encoding='utf-8'))
        commit = manifest['code_commit']
        if not re.fullmatch(r'[0-9a-f]{40}', commit) or not manifest['files']:
            raise ValueError('Invalid packaged source identity')
        changed = []
        for name, expected in manifest['files'].items():
            relative = PurePosixPath(name)
            path = root.joinpath(*relative.parts)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
                raise ValueError('Invalid packaged source path')
            if not path.resolve().is_relative_to(root):
                raise ValueError('Packaged source escapes root')
            if not path.is_file() or digest(path.read_bytes()) != expected:
                changed.append(name)
        # Detect extra importable code as well as edits/deletions of tracked files.
        for directory in ('packages', 'services', 'scripts', 'apps/web/src'):
            for path in (root / directory).rglob('*'):
                if path.is_file() and path.suffix in ('.py', '.js', '.ts', '.tsx'):
                    name = path.relative_to(root).as_posix()
                    if name not in manifest['files']:
                        changed.append(name)
        return {'code_commit': commit, 'dirty': bool(changed), 'source_kind': 'archive',
                'source_manifest_sha256': digest(packaged.read_bytes()),
                'source_changes': sorted(set(changed))}
    try:
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=root,
                                           stderr=subprocess.DEVNULL, timeout=5)
        if Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
            raise ValueError('Parent Git repository is not this release')
        commit = git('rev-parse', 'HEAD').decode().strip()
        dirty = bool(git('status', '--porcelain').strip())
        # Hash tracked bytes too: a dirty commit ID alone cannot reconstruct source.
        files = {}
        for raw in git('ls-files', '-z').split(b'\0'):
            if raw:
                name = raw.decode('utf-8')
                path = root / name
                files[name] = digest(path.read_bytes()) if path.is_file() else None
        return {'code_commit': commit, 'dirty': dirty, 'source_kind': 'git',
                'tracked_source_sha256': digest(json.dumps(files, sort_keys=True).encode())}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {'code_commit': 'unknown', 'dirty': True, 'source_kind': 'unverified'}
