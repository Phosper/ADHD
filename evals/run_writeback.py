"""Offline writeback acceptance from controlled intents, not ASR/model evaluation."""
import argparse
import json
import tempfile
from pathlib import Path

from packages.domain.models import Case, Intent, new_id
from packages.domain.state_machine import advance
from packages.observability.manifest import build_manifest, file_hash
from packages.storage.sqlite import Store
from services.api.voice_gateway import Gateway


def run_case(path: Path, item: dict, manifest: dict) -> dict:
    store = Store(path)
    case = Case(case_id=item['id'], company='合成商贸公司', brand='合成品牌',
                scene_id=item.get('scene', 'synthetic-authorization'),
                reason=item.get('reason', '合成案件：材料缺页'),
                required_actions=item.get('actions', ['补齐指定材料后重新提交']),
                reviewed=True, synthetic=True)
    store.seed([case])
    gateway = Gateway(store)
    session = store.create(case.case_id, 'create', manifest)
    trace, early_write, repeat_ok = [], False, True
    for index, value in enumerate(item['turns']):
        value = {'kind': value} if isinstance(value, str) else value
        intent = Intent(kind=value['kind'], confidence=value.get('confidence', 1))
        before = session
        body = {'expected_version': before.version,
                'text': value.get('text', intent.kind.value), 'source': 'offline_validated_intents'}
        key = f'turn-{index}'
        session = gateway.turn(session.session_id, key, body,
                               lambda current: advance(current, intent))
        # Check persistence at every step, not only the final Session response.
        persisted = store.case_result(case.case_id)
        if index < len(item['turns']) - 1 and persisted.latest_outcome:
            early_write = True
        trace.append({'index': index, 'controlled_intent': intent.model_dump(mode='json'),
                      'text': body['text'], 'stage_before': before.stage.value,
                      'stage_after': session.stage.value,
                      'result_confirmed': session.result_confirmed,
                      'task_result': persisted.model_dump(mode='json')})
        if index == len(item['turns']) - 1 and item.get('repeat_last'):
            repeat = gateway.turn(session.session_id, key, body,
                                  lambda current: advance(current, intent))
            repeat_ok = repeat == session
    if item.get('abort'):
        session = gateway.abort(session.session_id, 'offline_simulated_disconnect')
    restarted = Store(path)
    result = restarted.case_result(case.case_id)
    events = restarted.events(session.session_id)
    writes = [event for event in events if event.event_type == 'tool.committed'
              and event.payload.get('name') == 'write_outcome']
    expected = item['expected_result']
    actual = result.latest_outcome.merchant_response if result.latest_outcome else None
    checks = {'stage': session.stage.value == item['expected_stage'],
              'merchant_result': actual == expected, 'no_early_write': not early_write,
              'write_count': len(writes) == (0 if expected is None else 1),
              'case_version': result.case_version == (1 if expected is None else 2),
              'restarted_receipt': result.latest_outcome == session.outcome,
              'idempotent_retry': repeat_ok,
              'event_sequence': [e.session_seq for e in events] == list(range(1, len(events) + 1))}
    if expected is None:
        checks['not_confirmed'] = not session.result_confirmed
    if expected == 'will_resubmit':
        checks['complete_confirmation'] = (session.identity_status == 'confirmed'
                                          and session.consent and session.result_confirmed)
        checks['actions_match_case'] = result.latest_outcome.required_actions == case.required_actions
    if expected == 'needs_human':
        checks['followup_receipt'] = (result.latest_outcome.needs_human
                                     and result.latest_outcome.followup_id is not None)
    if 'expected_identity' in item:
        checks['identity'] = session.identity_status == item['expected_identity']
        checks['no_action_disclosure'] = not result.latest_outcome.required_actions
    return {'case_id': case.case_id, 'checks': checks, 'passed': all(checks.values()),
            'trace': trace, 'final_session': {
                'session_id': session.session_id, 'stage': session.stage.value,
                'identity_status': session.identity_status, 'consent': session.consent,
                'result_confirmed': session.result_confirmed, 'needs_human': session.needs_human},
            'final_result': result.model_dump(mode='json')}


def run(suite_path: Path, output_dir: Path) -> Path:
    suite = json.loads(suite_path.read_text(encoding='utf-8'))
    if suite.get('input_kind') != 'validated_intents' or suite.get('synthetic') is not True:
        raise ValueError('This runner only accepts controlled intents and synthetic cases')
    ids = [item['id'] for item in suite['cases']]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Expected nonempty, uniquely identified cases')
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest('offline_validated_intents')
    with tempfile.TemporaryDirectory(prefix='writeback-', dir=output_dir) as scratch:
        results = [run_case(Path(scratch)/f'case-{i}.sqlite', item, manifest)
                   for i, item in enumerate(suite['cases'])]
    report = {'suite_sha256': file_hash(suite_path), 'suite_version': suite['version'],
              'split': suite['split'], 'manifest': manifest, 'input_kind': suite['input_kind'],
              'real_model': False, 'real_audio': False, 'independent_holdout': False,
              'official_evaluation': False, 'passed': all(r['passed'] for r in results),
              'cases': results}
    target = output_dir/f'writeback-{new_id()}.json'
    with target.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    print(target)
    print(f"{sum(r['passed'] for r in results)}/{len(results)} controlled-intent writeback cases passed")
    if not report['passed']:
        raise SystemExit(1)
    return target


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, default=root/'evals/cases/writeback_component.json')
    parser.add_argument('--output-dir', type=Path, default=root/'runtime/evals')
    args = parser.parse_args()
    run(args.suite, args.output_dir)


if __name__ == '__main__':
    main()
