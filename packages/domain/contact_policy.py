from dataclasses import dataclass

from packages.domain.models import Case


@dataclass(frozen=True)
class ContactDecision:
    channel: str
    followup: bool
    reason: str


def contact_policy(case: Case, *, connected: bool, retry_attempt: bool = False) -> ContactDecision:
    if not case.reviewed:
        return ContactDecision("human", True, "资料尚未核对，不自动关单")
    if case.callback_requested or case.complaint_risk:
        return ContactDecision("phone", not connected, "明确回电要求或投诉风险优先")
    if case.default_channel == "written" or case.submission_count >= 3:
        return ContactDecision("written", False, "按已核对场景或重复提交规则站内处理")
    if connected:
        return ContactDecision("phone", False, "电话说明整改事项")
    if case.submission_count == 2 and not retry_attempt:
        return ContactDecision("phone", True, "第二次错误且未接通，登记预约回访")
    return ContactDecision("written", False, "本次未接通，站内说明原因")
