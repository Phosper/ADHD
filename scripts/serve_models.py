"""Project-owned model supervisor. Never touches processes belonging to other jobs."""
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    for name in ('llm', 'asr', 'tts'):
        if not (root / 'models' / f'{name}-manifest.json').is_file():
            raise RuntimeError(f'{name} model download/hash is incomplete')
    for port in (18081, 18082, 18083):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(f'Port {port} in use; leaving existing process untouched')
    env = os.environ.copy()
    vendor = root / 'vendor/CosyVoice'
    env.update({
        'ZHIYU_LLM_PATH': str(root / 'models/llm'),
        'ZHIYU_ASR_PATH': str(root / 'models/asr'),
        'ZHIYU_TTS_PATH': str(root / 'models/tts'),
        'ZHIYU_TTS_REFERENCE': str(vendor / 'asset/zero_shot_prompt.wav'),
        'ZHIYU_TTS_REFERENCE_TEXT': '希望你以后能够做的比我还好呦。',
        'PYTHONPATH': os.pathsep.join([str(root), str(vendor), str(vendor / 'third_party/Matcha-TTS')]),
        'OMP_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4', 'TOKENIZERS_PARALLELISM': 'false',
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
    })
    children, logs = [], []
    stopping = False

    def stop(signum=None, frame=None):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for name, port in [('llm', 18081), ('asr', 18082), ('tts', 18083)]:
            log = (runtime / f'{name}-service.log').open('ab')
            logs.append(log)
            process = subprocess.Popen([sys.executable, '-m', 'uvicorn',
                f'services.inference.{name}:create_app', '--factory', '--host', '127.0.0.1',
                '--port', str(port)], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
            children.append(process)
        (runtime / 'models-supervisor.pid').write_text(str(os.getpid()))
        started = time.monotonic()
        ready = False
        while not stopping:
            if any(p.poll() is not None for p in children):
                raise RuntimeError('One model service exited; inspect runtime/*-service.log')
            if not ready:
                states = []
                for port in (18081, 18082, 18083):
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as response:
                            states.append(json.load(response).get('ready') is True)
                    except OSError:
                        states.append(False)
                if all(states):
                    ready = True
                    print('All three real model services ready', flush=True)
                elif time.monotonic() - started > 300:
                    raise RuntimeError('Model startup timeout')
            time.sleep(2)
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
        for process in children:
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()  # Only direct children created by this supervisor.
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
