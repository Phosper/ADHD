"""Versioned, strict contracts shared by HTTP, voice and persistence adapters."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=4000)]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid4().hex


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Stage(str, Enum):
    IDENTITY = "identity"
    CONSENT = "consent"
    EXPLAIN = "explain"
    CONFIRM = "confirm"
    CLOSED = "closed"
    ABORTED = "aborted"


class IntentKind(str, Enum):
    IDENTITY_YES = "identity_yes"
    IDENTITY_NO = "identity_no"
    CONSENT = "consent"
    REFUSE = "refuse"
    BUSY = "busy"
    RESULT_YES = "result_yes"
    CORRECTION = "correction"
    QUESTION = "question"
    HUMAN = "human"
    UNKNOWN = "unknown"


class Intent(Contract):
    kind: IntentKind
    confidence: float = Field(default=1, ge=0, le=1)
    query: str = Field(default="", max_length=4000)


class Source(Contract):
    file: str
    sheet: str
    row: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class KnowledgeEntry(Contract):
    entry_id: Identifier
    category: list[str]
    question: str
    answer: str
    channel: Literal["phone", "written", "unknown"] = "unknown"
    source: Source
    review_status: Literal["pending", "approved", "rejected"] = "pending"


class Case(Contract):
    case_id: Identifier
    version: int = Field(default=1, ge=1)
    company: ShortText
    brand: ShortText
    scene_id: Identifier
    reason: ShortText
    required_actions: list[ShortText] = Field(min_length=1, max_length=20)
    knowledge_refs: list[Identifier] = Field(default_factory=list)
    default_channel: Literal["phone", "written"] = "phone"
    submission_count: int = Field(default=1, ge=1)
    callback_requested: bool = False
    complaint_risk: bool = False
    reviewed: bool = False
    synthetic: bool = True


class Outcome(Contract):
    case_id: Identifier
    session_id: Identifier
    identity_status: Literal["unknown", "confirmed", "denied"]
    contact_status: Literal["connected", "no_answer", "wrong_person", "declined", "aborted"]
    scene_id: Identifier
    required_actions: list[str]
    merchant_response: Literal["will_resubmit", "declined", "needs_human", "unknown"]
    needs_human: bool
    knowledge_refs: list[str]
    writeback_status: Literal["committed"] = "committed"
    operation_id: Identifier
    recommended_channel: Literal["phone", "written", "human"] = "phone"
    followup_id: Identifier | None = None


class CaseResult(Contract):
    case_id: Identifier
    case_version: int = Field(ge=1)
    task_status: Literal["pending", "processed", "needs_human"]
    latest_outcome: Outcome | None = None


class Session(Contract):
    session_id: Identifier = Field(default_factory=new_id)
    trace_id: Identifier = Field(default_factory=new_id)
    case: Case
    stage: Stage = Stage.IDENTITY
    version: int = Field(default=0, ge=0)
    turn_id: int = Field(default=0, ge=0)
    generation_id: int = Field(default=0, ge=0)
    identity_status: Literal["unknown", "confirmed", "denied"] = "unknown"
    consent: bool = False
    result_confirmed: bool = False
    retries: int = Field(default=0, ge=0)
    needs_human: bool = False
    last_response: str = ""
    outcome: Outcome | None = None
    created_at: str = Field(default_factory=utcnow)
    ended_at: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)


class CreateSession(Contract):
    case_id: Identifier
    request_id: Identifier


class UserTurn(Contract):
    text: ShortText
    request_id: Identifier
    expected_version: int = Field(ge=0)

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("empty text")
        return value.strip()


class ClientEvent(Contract):
    event_id: Identifier
    event_type: Literal["playback.started", "playback.stopped", "playback.completed", "speech.started"]
    generation_id: int = Field(ge=0)
    client_time_ms: float = Field(ge=0)
    played_chars: int = Field(default=0, ge=0, le=4000)


class VoiceOffer(Contract):
    sdp: str = Field(min_length=1, max_length=100000)
    type: Literal["offer"]


class NoAnswer(Contract):
    request_id: Identifier
    expected_version: int = Field(ge=0)
    retry_attempt: bool = False


class Event(Contract):
    schema_version: Literal["1.0"] = "1.0"
    event_id: Identifier = Field(default_factory=new_id)
    event_type: str
    session_id: Identifier
    trace_id: Identifier
    session_seq: int = Field(ge=1)
    turn_id: int = Field(ge=0)
    generation_id: int = Field(ge=0)
    timestamp_utc: str = Field(default_factory=utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(Contract):
    code: str
    message: str
    retryable: bool = False
    operation_id: str | None = None


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)
