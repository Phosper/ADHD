"""Conservative interpretation guards, shared by real and development interpreters."""
import re

from packages.domain.models import Intent, IntentKind


def guard_intent(text: str, proposal: Intent) -> Intent:
    normalized = re.sub(r'[\s，,。！!]', '', text)
    acknowledgement_only = normalized in {'知道了','明白了','了解了','收到','嗯','哦','好的','好吧'}
    instruction_override = re.search(r'(忽略|无视|绕过|覆盖).{0,12}(系统|规则|指令)|'
                                     r'(系统提示词|system\s*prompt|developer\s*message)|'
                                     r'(把我|将我).{0,8}(标记|设置).{0,8}(确认|通过|同意)',
                                     text, re.IGNORECASE)
    if acknowledgement_only or instruction_override:
        return Intent(kind=IntentKind.UNKNOWN, confidence=1, query=text)
    return proposal
