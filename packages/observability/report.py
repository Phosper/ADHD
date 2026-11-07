from packages.domain.models import Event, Session


def report(session: Session, events: list[Event]) -> dict:
    kinds = [e.event_type for e in events]
    played = [e for e in events if e.event_type == "playback.completed"]
    proposals = {e.generation_id: e.payload.get("text", "") for e in events
                 if e.event_type == "response.validated"}
    played_text = [proposals.get(e.generation_id, "") for e in played]
    return {
        "session_id": session.session_id, "trace_id": session.trace_id,
        "mode": session.manifest.get("mode"), "stage": session.stage.value,
        "turn_count": session.turn_id, "outcome": session.outcome.model_dump(mode="json") if session.outcome else None,
        "manifest": session.manifest,
        "checks": {
            "identity_confirmed": session.identity_status == "confirmed",
            "consent_confirmed": session.consent,
            "result_confirmed": session.result_confirmed,
            "writeback_committed": "tool.committed" in kinds,
            "ended": "session.ended" in kinds or "session.aborted" in kinds,
            "event_sequence_complete": [e.session_seq for e in events] == list(range(1, len(events) + 1)),
            "playback_evidence": "available" if played else "insufficient",
        },
        "played_text": played_text,
        "timing": {"end_to_end_p50_ms": None, "end_to_end_p95_ms": None,
                   "status": "requires_client_audio_measurement"},
        "limitations": ["规则检查不等同于完整人工合规审查", "文本测试不证明实时语音达标"],
    }
