import sqlite3

import pytest
from fastapi.testclient import TestClient

from packages.domain.models import Case, DomainError, Intent, IntentKind
from packages.domain.state_machine import advance
from packages.storage.sqlite import Store
from services.api.app import create_app


def prepared(tmp_path):
    store = Store(tmp_path/'task.sqlite')
    store.seed([Case(case_id='task', company='合成公司', brand='合成品牌', scene_id='missing',
                     reason='缺页', required_actions=['补齐盖章页'], reviewed=True)])
    return store


def turn(store, session, kind, request_id):
    return store.turn(session.session_id, request_id,
                      {'expected_version':session.version, 'text':kind.value},
                      lambda current: advance(current, Intent(kind=kind)))


def before_commit(store, request_id='start'):
    session = store.create('task', request_id, {})
    for i, kind in enumerate([IntentKind.IDENTITY_YES, IntentKind.CONSENT, IntentKind.RESULT_YES]):
        session = turn(store, session, kind, f'{request_id}-{i}')
    return session


def test_task_receipt_survives_restart_and_retry_does_not_replace_it(tmp_path):
    store = prepared(tmp_path)
    assert store.case_result('task').task_status == 'pending'
    s = before_commit(store)
    assert store.case_result('task').latest_outcome is None
    first = turn(store, s, IntentKind.RESULT_YES, 'final')
    repeat = turn(store, s, IntentKind.RESULT_YES, 'final')
    result = Store(store.path).case_result('task')
    assert result.task_status == 'processed' and result.case_version == 2
    assert result.latest_outcome == first.outcome == repeat.outcome
    assert result.latest_outcome.merchant_response == 'will_resubmit'


def test_task_readback_uses_latest_persisted_session_not_old_receipt(tmp_path):
    store = prepared(tmp_path)
    first = turn(store, before_commit(store), IntentKind.RESULT_YES, 'first-final')
    second = store.create('task', 'second', {})
    second = turn(store, second, IntentKind.HUMAN, 'human')
    result = store.case_result('task')
    assert result.task_status == 'needs_human' and result.case_version == 3
    assert result.latest_outcome == second.outcome
    assert result.latest_outcome.operation_id != first.outcome.operation_id


def test_write_failure_after_insert_leaves_no_receipt_and_can_retry(tmp_path, monkeypatch):
    store = prepared(tmp_path)
    s = before_commit(store)
    event = store.event
    def fail_after_write(db, session, kind, *args, **kwargs):
        if kind == 'tool.committed':
            raise sqlite3.OperationalError('simulated audit storage failure')
        return event(db, session, kind, *args, **kwargs)
    monkeypatch.setattr(store, 'event', fail_after_write)
    with pytest.raises(sqlite3.OperationalError):
        turn(store, s, IntentKind.RESULT_YES, 'final')
    result = store.case_result('task')
    assert result.task_status == 'pending' and result.case_version == 1
    assert result.latest_outcome is None
    assert store.session(s.session_id) == s
    monkeypatch.setattr(store, 'event', event)
    committed = turn(store, s, IntentKind.RESULT_YES, 'final')
    assert store.case_result('task').latest_outcome == committed.outcome
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM operations').fetchone()[0] == 1


def test_task_result_api_is_authenticated_and_matches_committed_receipt(tmp_path):
    with TestClient(create_app(tmp_path/'api.sqlite', token='test-key')) as client:
        assert client.get('/api/cases/demo-authorization/result').status_code == 401
        client.headers['Authorization'] = 'Bearer test-key'
        pending = client.get('/api/cases/demo-authorization/result').json()
        assert pending['task_status'] == 'pending' and pending['latest_outcome'] is None
        s = client.post('/api/sessions', json={
            'case_id':'demo-authorization', 'request_id':'start'}).json()
        for i, text in enumerate(['我是负责人', '方便', '我会补齐重新提交', '确认']):
            response = client.post(f"/api/sessions/{s['session_id']}/turns", json={
                'request_id':f'turn-{i}', 'text':text, 'expected_version':s['version']})
            assert response.status_code == 200
            s = response.json()
        result = client.get('/api/cases/demo-authorization/result').json()
        assert result['latest_outcome'] == s['outcome']
        assert client.get('/api/cases/not-found/result').status_code == 404


def test_unknown_task_has_no_fabricated_result(tmp_path):
    with pytest.raises(DomainError, match='单据不存在'):
        prepared(tmp_path).case_result('not-found')
