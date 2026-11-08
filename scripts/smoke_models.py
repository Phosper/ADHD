"""Real self-hosted smoke test; synthetic speech is not human microphone acceptance."""
import base64
import json
import time
import wave
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4


def post(url, body):
    return urlopen(Request(url, json.dumps(body, ensure_ascii=False).encode(),
                          headers={'Content-Type': 'application/json'}), timeout=120)


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / 'runtime/model-smoke' / uuid4().hex
    target.mkdir(parents=True)
    results = {'kind': 'real_models_synthetic_speech', 'official_acceptance': False, 'utterances': []}
    for index, text in enumerate(['我是这家公司的负责人。', '现在方便，请您说明。',
                                  '我会补齐盖章页，然后重新提交材料。', '是的，我确认愿意整改重新提交。']):
        started = time.monotonic()
        with post('http://127.0.0.1:18083/speak', {'text': text}) as response:
            rate = int(response.headers['X-Sample-Rate'])
            first = response.read(4800)
            first_ms = (time.monotonic() - started) * 1000
            pcm = first + response.read()
        with wave.open(str(target / f'{index}.wav'), 'wb') as wav:
            wav.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
            wav.writeframes(pcm)
        import numpy as np
        from scipy.signal import resample_poly
        samples = np.frombuffer(pcm, dtype='<i2')
        audio = resample_poly(samples.astype(np.float32), 16000, rate).clip(-32768, 32767).astype('<i2').tobytes()
        audio += bytes(16000)  # Flush end of speech as streaming clients do.
        stream_id, recognized = uuid4().hex, ''
        asr_started = time.monotonic()
        for seq, offset in enumerate(range(0, len(audio), 19200)):
            block = audio[offset:offset + 19200]
            with post('http://127.0.0.1:18082/chunk', {'stream_id': stream_id, 'seq': seq,
                      'pcm': base64.b64encode(block).decode(), 'final': offset + 19200 >= len(audio)}) as response:
                recognized += json.load(response)['text']
        results['utterances'].append({'text': text, 'asr': recognized,
            'tts_first_chunk_ms': first_ms, 'asr_batch_total_ms': (time.monotonic()-asr_started)*1000,
            'audio_seconds': len(pcm)/(rate*2)})
        print(json.dumps(results['utterances'][-1], ensure_ascii=False), flush=True)
    with post('http://127.0.0.1:18081/v1/chat/completions', {
        'model': 'Qwen3-8B', 'messages': [{'role':'system','content':'只输出 JSON：{"kind":"identity_yes","confidence":1,"query":"我是负责人"}。'},
            {'role':'user','content':'我是负责人'}], 'max_tokens':100, 'temperature':0}) as response:
        results['llm_smoke'] = json.load(response)
    (target/'result.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(target, flush=True)


if __name__ == '__main__':
    main()
