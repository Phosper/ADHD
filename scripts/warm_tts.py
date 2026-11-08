"""Pre-synthesize deterministic policy phrases, independent of evaluation case IDs."""
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

from packages.domain.models import Case, Intent, IntentKind, Session, Stage
from packages.domain.state_machine import advance, opening
from services.api.interpreter import safe_answer


def main():
    root = Path(__file__).resolve().parents[1]
    cases = [Case.model_validate(c) for c in json.loads((root/'configs/synthetic_cases.json').read_text(encoding='utf-8'))]
    phrases = set()
    for case in cases:
        if case.default_channel != 'phone':
            continue
        session = Session(case=case)
        phrases.add(opening(session))
        for stage in [Stage.IDENTITY, Stage.CONSENT, Stage.EXPLAIN, Stage.CONFIRM]:
            for kind in IntentKind:
                for retries in [0, 2]:
                    state = session.model_copy(deep=True)
                    state.stage, state.retries = stage, retries
                    state.identity_status = 'confirmed' if stage != Stage.IDENTITY else 'unknown'
                    state.consent = stage in [Stage.EXPLAIN, Stage.CONFIRM]
                    phrases.add(advance(state, Intent(kind=kind)).response)
                    if kind == IntentKind.QUESTION:
                        for question in ['保证通过吗', '能提供电话号码吗']:
                            phrases.add(advance(state, Intent(kind=kind), safe_answer(question)).response)
    results = []
    for i, text in enumerate(sorted(phrases)):
        start = time.monotonic()
        with urlopen(Request('http://127.0.0.1:18083/speak', json.dumps({'text':text}).encode(),
                            headers={'Content-Type':'application/json'}), timeout=120) as response:
            data = response.read()
            source = response.headers.get('X-Audio-Source')
        results.append({'text':text, 'seconds':time.monotonic()-start, 'bytes':len(data), 'source':source})
        print(f'{i+1}/{len(phrases)} {source} {len(data)} bytes', flush=True)
    destination = root / 'runtime/tts-warmup.json'
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
