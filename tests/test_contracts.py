import json
from pathlib import Path

import jsonschema
import pytest

from packages.domain.models import ClientEvent, CreateSession, Event, Outcome, Session, UserTurn


@pytest.mark.parametrize("model", [ClientEvent, CreateSession, Event, Outcome, Session, UserTurn])
def test_exported_contract_matches_runtime_model(model):
    schema = json.loads((Path("contracts") / f"{model.__name__}.schema.json").read_text(encoding="utf-8"))
    assert schema == model.model_json_schema()
    jsonschema.Draft202012Validator.check_schema(schema)


def test_request_positive_and_negative_examples():
    schema = UserTurn.model_json_schema()
    jsonschema.validate({"text": "确认", "request_id": "turn-1", "expected_version": 2}, schema)
    for bad in [
        {"text": "确认", "request_id": "../bad", "expected_version": 0},
        {"text": "确认", "request_id": "ok", "expected_version": -1},
        {"text": "确认", "request_id": "ok", "expected_version": 0, "tool": "arbitrary"},
    ]:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)
