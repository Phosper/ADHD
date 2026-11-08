"""Deterministic development interpreter, not a production language model."""
import re
from packages.domain.models import Intent, IntentKind, Session, Stage
from packages.domain.intent_guard import guard_intent


def interpret_mock(text: str, session: Session) -> Intent:
    t = re.sub(r"[\s，,。！!]", "", text)
    if any(x in t for x in ("不是本人", "打错", "不是这家", "我不是")):
        kind = IntentKind.IDENTITY_NO
    elif any(x in t for x in ("不要再打", "不想沟通", "不需要", "拒绝", "不愿意")):
        kind = IntentKind.REFUSE
    elif any(x in t for x in ("人工", "投诉")):
        kind = IntentKind.HUMAN
    elif any(x in t for x in ("不方便", "忙", "稍后")):
        kind = IntentKind.BUSY
    elif any(x in t for x in ("更正", "说错", "不是这个材料")):
        kind = IntentKind.CORRECTION
    elif any(x in t for x in ("吗", "？", "?", "怎么", "哪里", "为什么", "保证", "一定")):
        kind = IntentKind.QUESTION
    elif t in ("是的", "我是负责人", "是本人", "我是", "是") and session.stage == Stage.IDENTITY:
        kind = IntentKind.IDENTITY_YES
    elif t in ("方便", "可以说明", "可以", "请说", "方便沟通", "方便请说") and session.stage == Stage.CONSENT:
        kind = IntentKind.CONSENT
    elif re.fullmatch(r"(确认|明白了|了解了)?(同意整改|愿意重新提交|我会补齐重新提交)", t) or (t == "确认" and session.stage == Stage.CONFIRM):
        kind = IntentKind.RESULT_YES
    else:
        kind = IntentKind.UNKNOWN
    return guard_intent(text, Intent(kind=kind, query=text))


def safe_answer(text: str) -> str | None:
    if any(x in text for x in ("保证", "一定", "通过")):
        return "补齐材料后仍需按标准重新审核，不能保证审核通过。"
    if any(x in text for x in ("号码", "电话", "隐私")):
        return "不能提供第三方完整联系方式或其他隐私信息。"
    return None
