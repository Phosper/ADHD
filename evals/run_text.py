"""Deterministic development evaluation, no LLM judge or official score claims."""
import json
import tempfile
from pathlib import Path

from packages.domain.models import Case, new_id
from packages.domain.state_machine import advance
from packages.observability.manifest import build_manifest, file_hash
from packages.storage.sqlite import Store
from services.api.interpreter import interpret_mock, safe_answer


def run():
    root = Path(__file__).resolve().parents[1]
    path = root / 'evals/cases/development.json'
    suite = json.loads(path.read_text(encoding='utf-8'))
    runtime = root / 'runtime/evals'
    runtime.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=runtime) as temp:
        store = Store(Path(temp) / 'eval.sqlite')
        for case in suite['cases']:
            record = Case(case_id=case['id'], company='合成公司', brand='合成品牌', scene_id='synthetic',
                          reason='授权材料缺少盖章页', required_actions=['补齐盖章页并重新提交'], reviewed=True)
            store.seed([record])
            session = store.create(record.case_id, new_id(), build_manifest('mock'))
            responses = []
            for text in case['turns']:
                session = store.turn(session.session_id, new_id(), {'text': text, 'expected_version': session.version},
                    lambda s: advance(s, interpret_mock(text, s), safe_answer(text)))
                responses.append(session.last_response)
            checks = {'result': session.outcome is not None and session.outcome.merchant_response == case['result']}
            if 'identity' in case:
                checks['identity'] = session.identity_status == case['identity']
            if 'needs_human' in case:
                checks['needs_human'] = session.needs_human == case['needs_human']
            if 'must_contain' in case:
                checks['required_phrase'] = any(case['must_contain'] in text for text in responses)
            checks['receipt'] = session.outcome is not None and store.operation(session.outcome.operation_id) == session.outcome
            results.append({'case_id': case['id'], 'checks': checks, 'passed': all(checks.values())})
    output = {'suite_sha256': file_hash(path), 'split': suite['split'], 'mode': 'mock',
              'cases': results, 'passed': all(r['passed'] for r in results),
              'official_evaluation': False, 'independent_holdout': False}
    target = runtime / f'text-{new_id()}.json'
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(target)
    print(f"{sum(r['passed'] for r in results)}/{len(results)} development cases passed")
    if not output['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    run()
