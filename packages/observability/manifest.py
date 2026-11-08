import hashlib
import json
import os
import subprocess
from pathlib import Path

from packages.domain.models import utcnow

ROOT = Path(__file__).resolve().parents[2]


def file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def build_manifest(mode: str, knowledge_path: Path | None = None) -> dict:
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL,
                                           timeout=3).decode().strip()
        except (OSError, subprocess.SubprocessError):
            return "unknown"
    commit = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain") != ""
    models = {"status": "mock" if mode == "mock" else "unverified"}
    model_manifest = os.getenv('ZHIYU_MODEL_MANIFEST')
    if mode == 'real' and model_manifest:
        models = json.loads(Path(model_manifest).read_text(encoding='utf-8'))
    return {"schema_version": "1.0", "release_id": commit[:12] + ("-dirty" if dirty else ""),
            "code_commit": commit, "dirty": dirty, "mode": mode,
            "created_at": utcnow(), "database_schema": 1,
            "dependency_lock_sha256": file_hash(ROOT / "uv.lock"),
            "knowledge_sha256": file_hash(knowledge_path) if knowledge_path else None,
            "models": models,
            "frontend_lock_sha256": file_hash(ROOT / 'apps/web/package-lock.json'),
            "voice_lock_sha256": file_hash(ROOT / 'deploy/voice-windows.lock'),
            "prompt_sha256": file_hash(ROOT / 'services/api/model_client.py'),
            "official_evaluation": False}
