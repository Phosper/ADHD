import json
import tempfile
from pathlib import Path

from packages.domain.models import ClientEvent, CreateSession, Event, Outcome, Session, UserTurn, VoiceOffer
from services.api.app import create_app


def main():
    target = Path("contracts")
    target.mkdir(exist_ok=True)
    for model in (Event, Outcome, Session, UserTurn, CreateSession, ClientEvent, VoiceOffer):
        (target / f"{model.__name__}.schema.json").write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scratch = Path("runtime/contract-export")
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as folder:
        app = create_app(Path(folder) / "contracts.sqlite", recover=False)
        (target / "openapi.json").write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")


if __name__ == "__main__":
    main()
