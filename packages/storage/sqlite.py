import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from packages.domain.models import (
    Case, ClientEvent, DomainError, Event, Outcome, Session, Stage, new_id, utcnow,
)
from packages.domain.state_machine import Decision, opening


def encode(value) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value) -> str:
    return hashlib.sha256(encode(value).encode()).hexdigest()


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL, body TEXT NOT NULL,
                    UNIQUE(session_id,seq), FOREIGN KEY(session_id) REFERENCES sessions(id));
                CREATE TABLE IF NOT EXISTS requests(
                    key TEXT PRIMARY KEY, hash TEXT NOT NULL, response TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS operations(
                    id TEXT PRIMARY KEY, session_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL, body TEXT NOT NULL);
                PRAGMA user_version=1;
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, factory=ManagedConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def seed(self, cases: list[Case]):
        with self.transaction() as db:
            for case in cases:
                db.execute("INSERT OR IGNORE INTO cases VALUES (?,?)", (case.case_id, encode(case)))

    def cases(self) -> list[Case]:
        with self.connect() as db:
            return [Case.model_validate_json(r[0]) for r in db.execute("SELECT body FROM cases")]

    def _session(self, db, session_id: str) -> Session:
        row = db.execute("SELECT body FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise DomainError("not_found", "会话不存在", 404)
        return Session.model_validate_json(row[0])

    def session(self, session_id: str) -> Session:
        with self.connect() as db:
            return self._session(db, session_id)

    def sessions(self) -> list[Session]:
        with self.connect() as db:
            return [Session.model_validate_json(r[0]) for r in db.execute(
                "SELECT body FROM sessions ORDER BY rowid DESC LIMIT 100"
            )]

    def save(self, db, session: Session):
        db.execute("INSERT INTO sessions VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                   (session.session_id, encode(session)))

    def event(self, db, session: Session, event_type: str, payload: dict, event_id=None):
        seq = db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE session_id=?",
                         (session.session_id,)).fetchone()[0]
        event = Event(event_id=event_id or new_id(), event_type=event_type,
                      session_id=session.session_id, trace_id=session.trace_id,
                      session_seq=seq, turn_id=session.turn_id,
                      generation_id=session.generation_id, payload=payload)
        db.execute("INSERT INTO events VALUES (?,?,?,?)",
                   (event.event_id, session.session_id, seq, encode(event)))
        return event

    def events(self, session_id: str, after: int = 0) -> list[Event]:
        with self.connect() as db:
            self._session(db, session_id)
            return [Event.model_validate_json(r[0]) for r in db.execute(
                "SELECT body FROM events WHERE session_id=? AND seq>? ORDER BY seq",
                (session_id, after))]

    def _cached(self, db, key, body):
        row = db.execute("SELECT hash,response FROM requests WHERE key=?", (key,)).fetchone()
        if row:
            if row[0] != digest(body):
                raise DomainError("idempotency_conflict", "相同请求标识对应不同内容")
            return Session.model_validate_json(row[1])

    def cached_turn(self, session_id, request_id, body):
        with self.connect() as db:
            return self._cached(db, f"turn:{session_id}:{request_id}", body)

    def _cache(self, db, key, body, response):
        db.execute("INSERT INTO requests VALUES (?,?,?)", (key, digest(body), encode(response)))

    def create(self, case_id: str, request_id: str, manifest: dict) -> Session:
        key, body = f"create:{request_id}", {"case_id": case_id}
        with self.transaction() as db:
            cached = self._cached(db, key, body)
            if cached:
                return cached
            row = db.execute("SELECT body FROM cases WHERE id=?", (case_id,)).fetchone()
            if not row:
                raise DomainError("case_not_found", "单据不存在", 404)
            case = Case.model_validate_json(row[0])
            if not case.reviewed:
                raise DomainError("unreviewed_case", "单据尚未核对，不允许自动沟通")
            from packages.domain.contact_policy import contact_policy
            if contact_policy(case, connected=True).channel != "phone":
                raise DomainError("not_phone_case", "当前策略为站内处理，请勿发起电话会话")
            s = Session(case=case, manifest=manifest)
            s.last_response = opening(s)
            self.save(db, s)
            self.event(db, s, "session.started", {"manifest": manifest})
            self.event(db, s, "response.validated", {"text": s.last_response})
            self._cache(db, key, body, s)
            return s

    def turn(self, session_id: str, request_id: str, body: dict,
             decide: Callable[[Session], Decision]) -> Session:
        key = f"turn:{session_id}:{request_id}"
        with self.transaction() as db:
            cached = self._cached(db, key, body)
            if cached:
                return cached
            old = self._session(db, session_id)
            if old.version != body["expected_version"]:
                raise DomainError("version_conflict", "会话已变化，请刷新后重试")
            decision = decide(old)
            s = decision.session
            self.event(db, old, "asr.final" if body.get("source") == "voice" else "user.text",
                       {"text": body["text"], "request_id": request_id})
            self.event(db, s, "state.changed", {"before": old.stage.value, "after": s.stage.value,
                       "previous_version": old.version, "version": s.version})
            if decision.close_reason:
                self._commit_outcome(db, s, decision.close_reason)
                s.ended_at = utcnow()
                self.event(db, s, "session.ended", {"reason": decision.close_reason})
            self.event(db, s, "response.validated", {"text": s.last_response})
            self.save(db, s)
            self._cache(db, key, body, s)
            return s

    def _commit_outcome(self, db, s: Session, reason: str):
        current = Case.model_validate_json(db.execute("SELECT body FROM cases WHERE id=?",
                                                     (s.case.case_id,)).fetchone()[0])
        if current.version != s.case.version:
            raise DomainError("case_version_conflict", "单据已被其他会话处理，需要人工核对")
        if reason == "will_resubmit" and not (s.identity_status == "confirmed" and
                                              s.consent and s.result_confirmed):
            raise DomainError("precondition_failed", "业务确认不完整")
        op_id = new_id()
        contact = {"wrong_person": "wrong_person", "declined": "declined"}.get(reason, "connected")
        s.outcome = Outcome(case_id=s.case.case_id, session_id=s.session_id,
                            identity_status=s.identity_status, contact_status=contact,
                            scene_id=s.case.scene_id,
                            required_actions=s.case.required_actions if s.identity_status == "confirmed" else [],
                            merchant_response=reason if reason in ("will_resubmit", "declined", "needs_human") else "unknown",
                            needs_human=s.needs_human, knowledge_refs=s.case.knowledge_refs,
                            operation_id=op_id)
        self.event(db, s, "tool.requested", {"name": "write_outcome", "operation_id": op_id})
        db.execute("INSERT INTO operations VALUES (?,?,?,?)",
                   (op_id, s.session_id, s.case.case_id, encode(s.outcome)))
        current.version += 1
        db.execute("UPDATE cases SET body=? WHERE id=?", (encode(current), current.case_id))
        self.event(db, s, "tool.committed", {"name": "write_outcome", "operation_id": op_id,
                                          "result": s.outcome.model_dump(mode="json")})

    def operation(self, operation_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM operations WHERE id=?", (operation_id,)).fetchone()
            if not row:
                raise DomainError("operation_not_found", "操作不存在", 404)
            return Outcome.model_validate_json(row[0])

    def client_event(self, session_id: str, incoming: ClientEvent) -> Session:
        with self.transaction() as db:
            s = self._session(db, session_id)
            row = db.execute("SELECT body FROM events WHERE id=?", (incoming.event_id,)).fetchone()
            if row:
                existing = Event.model_validate_json(row[0])
                if existing.session_id != session_id or existing.payload.get("client") != incoming.model_dump(mode="json"):
                    raise DomainError("event_conflict", "重复事件内容不一致")
                return s
            if incoming.generation_id != s.generation_id:
                raise DomainError("stale_generation", "忽略已经取消的回复事件")
            if incoming.event_type == "speech.started":
                if s.stage in (Stage.CLOSED, Stage.ABORTED):
                    raise DomainError("session_closed", "会话已结束")
                self.event(db, s, "response.cancelled", {"generation_id": s.generation_id})
                s.generation_id += 1
                s.version += 1
            self.event(db, s, incoming.event_type, {"client": incoming.model_dump(mode="json")},
                       event_id=incoming.event_id)
            self.save(db, s)
            return s

    def abort(self, session_id, reason="user_ended") -> Session:
        with self.transaction() as db:
            s = self._session(db, session_id)
            if s.stage not in (Stage.CLOSED, Stage.ABORTED):
                s.stage = Stage.ABORTED
                s.version += 1
                s.generation_id += 1
                s.ended_at = utcnow()
                self.event(db, s, "session.aborted", {"reason": reason})
                self.save(db, s)
            return s

    def recover(self) -> int:
        count = 0
        with self.connect() as db:
            all_sessions = [Session.model_validate_json(r[0]) for r in db.execute("SELECT body FROM sessions")]
        for s in all_sessions:
            if s.stage not in (Stage.CLOSED, Stage.ABORTED):
                self.abort(s.session_id, "process_restarted")
                count += 1
        return count

    def backup(self, destination: Path):
        if destination.exists():
            raise ValueError("Backup target already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as src, sqlite3.connect(destination) as dst:
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
