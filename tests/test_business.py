from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest
from fastapi.testclient import TestClient

from packages.domain.models import Case, ClientEvent, DomainError, Intent, IntentKind, Stage
from packages.domain.state_machine import advance
from packages.storage.sqlite import Store
from services.api.app import create_app


@pytest.fixture
def store(tmp_path):
    db = Store(tmp_path / "state.sqlite")
    db.seed([Case(case_id="one", company="示例公司", brand="保密品牌", scene_id="missing",
                  reason="材料不完整", required_actions=["补齐盖章页"], reviewed=True)])
    return db


def step(store, s, kind, key=None):
    body = {"expected_version": s.version, "text": kind.value}
    return store.turn(s.session_id, key or f"turn-{s.version}", body,
                      lambda current: advance(current, Intent(kind=kind)))


def complete(store, s):
    for kind in [IntentKind.IDENTITY_YES, IntentKind.CONSENT, IntentKind.RESULT_YES, IntentKind.RESULT_YES]:
        s = step(store, s, kind)
    return s


def test_complete_task_and_receipt(store):
    s = complete(store, store.create("one", "create", {"mode": "mock"}))
    assert s.stage == Stage.CLOSED
    assert s.outcome.merchant_response == "will_resubmit"
    assert store.operation(s.outcome.operation_id) == s.outcome
    assert [e.session_seq for e in store.events(s.session_id)] == list(range(1, len(store.events(s.session_id)) + 1))
    assert store.cases()[0].version == 2


def test_identity_denial_never_discloses_case(store):
    s = store.create("one", "create", {})
    assert "保密品牌" not in s.last_response
    s = step(store, s, IntentKind.QUESTION)
    assert "保密品牌" not in s.last_response
    s = step(store, s, IntentKind.IDENTITY_NO)
    assert s.outcome.identity_status == "denied"
    assert not s.outcome.required_actions


def test_silence_or_ambiguous_acceptance_does_not_confirm(store):
    s = store.create("one", "create", {})
    for _ in range(3):
        s = step(store, s, IntentKind.UNKNOWN)
    assert s.stage == Stage.CLOSED and s.needs_human
    assert not s.result_confirmed


def test_correction_requires_reconfirmation(store):
    s = store.create("one", "create", {})
    for k in [IntentKind.IDENTITY_YES, IntentKind.CONSENT, IntentKind.RESULT_YES, IntentKind.CORRECTION]:
        s = step(store, s, k)
    assert s.stage == Stage.EXPLAIN and s.outcome is None
    s = step(store, s, IntentKind.RESULT_YES)
    assert s.outcome is None


def test_create_idempotency_and_conflicting_payload(store):
    a = store.create("one", "same", {})
    assert store.create("one", "same", {}).session_id == a.session_id
    with pytest.raises(DomainError, match="不同内容"):
        store.create("other", "same", {})


def test_turn_retry_returns_original_without_second_write(store):
    s = store.create("one", "create", {})
    for k in [IntentKind.IDENTITY_YES, IntentKind.CONSENT, IntentKind.RESULT_YES]:
        s = step(store, s, k)
    before = s
    first = step(store, before, IntentKind.RESULT_YES, "final")
    repeat = step(store, before, IntentKind.RESULT_YES, "final")
    assert first.outcome.operation_id == repeat.outcome.operation_id
    assert sum(e.event_type == "tool.committed" for e in store.events(s.session_id)) == 1


def test_concurrent_duplicate_turn(store):
    s = store.create("one", "create", {})
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: step(store, s, IntentKind.IDENTITY_YES, "same"), range(8)))
    assert all(r.version == 1 for r in results)
    assert sum(e.event_type == "user.text" for e in store.events(s.session_id)) == 1


def test_stale_version_rejected(store):
    s = store.create("one", "create", {})
    step(store, s, IntentKind.IDENTITY_YES)
    with pytest.raises(DomainError, match="会话已变化"):
        step(store, s, IntentKind.IDENTITY_NO, "other")


def test_two_sessions_cannot_overwrite_same_case(store):
    a, b = store.create("one", "a", {}), store.create("one", "b", {})
    complete(store, a)
    with pytest.raises(DomainError, match="单据已被"):
        complete(store, b)
    assert store.session(b.session_id).outcome is None


def test_audit_failure_rolls_back_business_state(store, monkeypatch):
    s = store.create("one", "create", {})
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("disk full")
    monkeypatch.setattr(store, "event", fail)
    with pytest.raises(sqlite3.OperationalError):
        step(store, s, IntentKind.IDENTITY_YES)
    assert store.session(s.session_id).version == 0


def test_interrupt_invalidates_old_playback(store):
    s = store.create("one", "create", {})
    speech = ClientEvent(event_id="speech", event_type="speech.started", generation_id=0, client_time_ms=1)
    updated = store.client_event(s.session_id, speech)
    assert updated.generation_id == 1
    assert store.client_event(s.session_id, speech).version == updated.version
    with pytest.raises(DomainError, match="已经取消"):
        store.client_event(s.session_id, ClientEvent(event_id="late", event_type="playback.completed",
                                                    generation_id=0, client_time_ms=2))


def test_recover_and_backup_without_side_effects(store, tmp_path):
    s = store.create("one", "create", {})
    assert store.recover() == 1
    assert store.session(s.session_id).stage == Stage.ABORTED
    assert store.recover() == 0
    destination = tmp_path / "backup.sqlite"
    store.backup(destination)
    clone = Store(destination)
    assert clone.events(s.session_id) == store.events(s.session_id)
    assert clone.cases()[0].version == 1
    with pytest.raises(ValueError):
        store.backup(destination)


def test_api_auth_errors_and_full_text_flow(tmp_path):
    with TestClient(create_app(tmp_path / "api.sqlite", token="test-key")) as c:
        assert c.get("/api/cases").status_code == 401
        c.headers["Authorization"] = "Bearer test-key"
        assert c.post("/api/sessions", json={"case_id": "demo-written", "request_id": "w"}).status_code == 409
        response = c.post("/api/sessions", json={"case_id": "demo-authorization", "request_id": "s"})
        assert response.status_code == 200
        s = response.json()
        for index, text in enumerate(["我是负责人", "方便", "补齐一定通过吗？", "确认"]):
            response = c.post(f"/api/sessions/{s['session_id']}/turns", json={
                "text": text, "request_id": f"q{index}", "expected_version": s["version"]})
            assert response.status_code == 200, response.text
            s = response.json()
        assert s["stage"] == "closed"
        report = c.get(f"/api/sessions/{s['session_id']}/report").json()
        assert report["checks"]["writeback_committed"]
        assert report["checks"]["playback_evidence"] == "insufficient"
        assert report["timing"]["end_to_end_p50_ms"] is None
        assert c.post(f"/api/sessions/{s['session_id']}/turns", json={
            "text": " ", "request_id": "empty", "expected_version": s["version"]}).status_code == 422
