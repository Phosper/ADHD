"""Read-only environment check. Does not inspect credentials or private inputs."""
import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', action='store_true')
    parser.add_argument('--health', action='store_true')
    args = parser.parse_args()
    result = {'python': platform.python_version(), 'platform': platform.system(), 'packages': {}}
    for name in ['torch', 'transformers', 'funasr', 'pipecat-ai', 'fastapi', 'onnxruntime', 'openai-whisper']:
        try:
            result['packages'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result['packages'][name] = None
    if args.models:
        import torch
        from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: F401
        from funasr import AutoModel  # noqa: F401
        result['cuda_available'] = torch.cuda.is_available()
        if torch.cuda.is_available():
            result['gpu'] = torch.cuda.get_device_name()
            result['memory_free_total'] = torch.cuda.mem_get_info()
        root = Path(__file__).resolve().parents[1]
        result['model_manifests'] = {k: (root / 'models' / f'{k}-manifest.json').is_file()
                                     for k in ['llm', 'asr', 'tts']}
    if args.health:
        result['services'] = {}
        for name, port in [('llm', 18081), ('asr', 18082), ('tts', 18083)]:
            try:
                with urlopen(f'http://127.0.0.1:{port}/health', timeout=3) as response:
                    result['services'][name] = json.load(response)
            except OSError:
                result['services'][name] = {'ready': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
