import hashlib
import json
import os
from pathlib import Path

from packages.domain.models import utcnow
from packages.observability.source_identity import source_identity

ROOT = Path(__file__).resolve().parents[2]


def file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def build_manifest(mode: str, knowledge_path: Path | None = None) -> dict:
    source = source_identity(ROOT)
    commit, dirty = source['code_commit'], source['dirty']
    models = {"status": "mock" if mode == "mock" else "unverified"}
    model_manifest = os.getenv('ZHIYU_MODEL_MANIFEST')
    if mode == 'real' and model_manifest:
        models = json.loads(Path(model_manifest).read_text(encoding='utf-8'))
    return {"schema_version": "1.0", "release_id": commit[:12] + ("-dirty" if dirty else ""),
            **source, "mode": mode,
            "created_at": utcnow(), "database_schema": 1,
            "dependency_lock_sha256": file_hash(ROOT / "uv.lock"),
            "knowledge_sha256": file_hash(knowledge_path) if knowledge_path else None,
            "models": models,
            "frontend_lock_sha256": file_hash(ROOT / 'apps/web/package-lock.json'),
            "voice_lock_sha256": file_hash(ROOT / 'deploy/voice-windows.lock'),
            "prompt_sha256": file_hash(ROOT / 'services/api/model_client.py'),
            "intent_guard_sha256": file_hash(ROOT / 'packages/domain/intent_guard.py'),
            "official_evaluation": False}
