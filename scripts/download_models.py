"""Download public model assets only; record content identity after download."""
import hashlib
import json
from pathlib import Path


def main():
    from modelscope import snapshot_download
    root = Path(__file__).resolve().parents[1]
    specs = {
        "llm": "Qwen/Qwen3-8B",
        "asr": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
        "tts": "iic/CosyVoice2-0.5B",
    }
    for name, repo in specs.items():
        destination = root / "models" / name
        snapshot_download(repo, local_dir=str(destination))
        files = {}
        for path in sorted(destination.rglob('*')):
            if not path.is_file() or any(p.startswith('.') for p in path.relative_to(destination).parts):
                continue
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(block)
            files[path.relative_to(destination).as_posix()] = digest.hexdigest()
        manifest = {"repository": repo, "files": files, "download_policy": "resolved snapshot, content hashes locked"}
        (root / "models" / f"{name}-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"{name}: ready, {len(files)} hashed files", flush=True)


if __name__ == '__main__':
    main()
