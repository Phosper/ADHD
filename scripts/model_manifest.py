import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    models = {}
    for name in ['llm','asr','tts']:
        path = root/'models'/f'{name}-manifest.json'
        source = json.loads(path.read_text())
        models[name] = {'repository':source['repository'],
                        'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'file_count':len(source['files'])}
    models['source'] = {'cosyvoice':'074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc',
                        'matcha_tts':'dd9105b34bf2be2230f4aa1e4769fb586a3c824e'}
    lock = root/'deploy/models-linux.lock'
    models['dependency_sha256'] = hashlib.sha256(lock.read_bytes()).hexdigest()
    path = root/'runtime/model-manifest.json'
    path.write_text(json.dumps(models,indent=2),encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
