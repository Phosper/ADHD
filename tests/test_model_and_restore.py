import asyncio

import httpx
import pytest

from packages.domain.models import Case, DomainError, Session, Stage
from packages.storage.sqlite import Store
from scripts.restore import restore
from services.api.interpreter import interpret_mock
from services.api.model_client import ModelClient


def sample():
    return Session(case=Case(case_id="s", company="合成公司", brand="合成品牌",
                            scene_id="s", reason="缺材料", required_actions=["补材料"], reviewed=True))


@pytest.mark.parametrize("content", ['{"kind":"identity_yes","confidence":1,"query":"原话"}',
                                    '{"kind":"question","confidence":0.9,"query":"如何处理"}'])
def test_model_validates_structured_intent(content):
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    client = ModelClient("http://model/v1", "Qwen3-8B", transport=httpx.MockTransport(handler))
    intent, _ = asyncio.run(client.interpret("原话", sample()))
    assert intent.query == "原话"


@pytest.mark.parametrize("content", ['{"kind":"write_database","confidence":1}',
                                    '{"kind":"identity_yes","tool":"close"}',
                                    '已执行关单', '{"kind":"consent","confidence":2}'])
def test_untrusted_model_output_never_reaches_domain(content):
    client = ModelClient("http://model/v1", "Qwen3-8B", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"message": {"content": content}}]})))
    with pytest.raises(DomainError, match="未提交"):
        asyncio.run(client.interpret("原话", sample()))


def test_restore_isolated_no_external_effect_and_no_overwrite(tmp_path):
    store = Store(tmp_path / "live.sqlite")
    store.seed([sample().case])
    session = store.create("s", "start", {})
    store.backup(tmp_path / "backup.sqlite")
    restored = restore(tmp_path / "backup.sqlite", tmp_path / "restored.sqlite")
    clone = Store(restored)
    assert clone.session(session.session_id) == session
    assert clone.events(session.session_id) == store.events(session.session_id)
    assert clone.session(session.session_id).outcome is None
    with pytest.raises(FileExistsError):
        restore(tmp_path / "backup.sqlite", restored)


def test_mock_requires_commitment_not_acknowledgement():
    s = sample()
    s.stage = Stage.EXPLAIN
    assert interpret_mock("明白了", s).kind == "unknown"
    assert interpret_mock("明白了，我会补齐重新提交", s).kind == "result_yes"
    assert interpret_mock("我不愿意重新提交", s).kind == "refuse"
    s.stage = Stage.CONSENT
    assert interpret_mock("方便，请说", s).kind == "consent"
