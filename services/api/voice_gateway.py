"""API-owned transaction boundary shared with the in-process voice adapter."""
from packages.domain.models import DomainError, Stage


class Gateway:
    def __init__(self, store):
        self.store = store

    def session(self, sid):
        return self.store.session(sid)

    def record(self, sid, kind, payload):
        with self.store.transaction() as db:
            self.store.event(db, self.store._session(db, sid), kind, payload)

    def interrupt(self, sid):
        with self.store.transaction() as db:
            s = self.store._session(db, sid)
            if s.stage in (Stage.CLOSED, Stage.ABORTED):
                raise DomainError("session_closed", "会话已结束")
            self.store.event(db, s, "response.cancelled", {"origin": "server_vad"})
            s.generation_id += 1
            s.version += 1
            self.store.event(db, s, "vad.started", {"origin": "server"})
            self.store.save(db, s)

    def abort(self, sid, reason):
        return self.store.abort(sid, reason)

    def turn(self, sid, request_id, body, decide):
        return self.store.turn(sid, request_id, body, decide)
