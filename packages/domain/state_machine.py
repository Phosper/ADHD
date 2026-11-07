"""Deterministic business transitions. Model proposals never write to tools directly."""

from dataclasses import dataclass

from packages.domain.models import DomainError, Intent, IntentKind, Session, Stage


@dataclass(frozen=True)
class Decision:
    session: Session
    response: str
    close_reason: str | None = None


def opening(session: Session) -> str:
    return f"您好，我是商家资质审核智能助手。请问您是{session.case.company}的相关负责人吗？"


def explanation(session: Session) -> str:
    actions = "；".join(session.case.required_actions)
    return f"您申请的{session.case.brand}需要补充核实：{session.case.reason}。请{actions}。您有什么需要我说明的吗？"


def advance(state: Session, intent: Intent, answer: str | None = None) -> Decision:
    s = state.model_copy(deep=True)
    if s.stage in (Stage.CLOSED, Stage.ABORTED):
        raise DomainError("session_closed", "会话已结束")
    s.turn_id += 1
    s.generation_id += 1
    s.version += 1
    kind = intent.kind if intent.confidence >= 0.8 else IntentKind.UNKNOWN

    def reply(text: str, reason: str | None = None) -> Decision:
        s.last_response = text
        if reason:
            s.stage = Stage.CLOSED
        return Decision(s, text, reason)

    if kind == IntentKind.REFUSE:
        return reply("好的，本次不再打扰您，感谢接听，再见。", "declined")
    if kind == IntentKind.IDENTITY_NO:
        s.identity_status = "denied"
        return reply("抱歉打扰，我们会核对联系信息。再见。", "wrong_person")
    if kind in (IntentKind.HUMAN, IntentKind.BUSY):
        s.needs_human = True
        return reply("好的，我会登记人工跟进请求，本次先不打扰您。", "needs_human")
    if s.stage == Stage.IDENTITY:
        if kind == IntentKind.IDENTITY_YES:
            s.identity_status = "confirmed"
            s.stage = Stage.CONSENT
            s.retries = 0
            return reply("感谢确认。现在方便听我说明本次资质材料需要调整的事项吗？")
        s.retries += 1
        if s.retries >= 3:
            s.needs_human = True
            return reply("暂时无法确认身份，本次先结束，后续由人工核对。", "needs_human")
        return reply("为保护申请信息，需要先确认您是否为该公司的相关负责人。")
    if s.stage == Stage.CONSENT:
        if kind == IntentKind.CONSENT:
            s.consent = True
            s.stage = Stage.EXPLAIN
            s.retries = 0
            return reply(explanation(s))
        s.retries += 1
        if s.retries >= 3:
            s.needs_human = True
            return reply("本次先不继续说明，后续请人工跟进。", "needs_human")
        return reply("请确认您现在是否方便沟通资质材料整改事项。")
    if kind == IntentKind.CORRECTION:
        s.result_confirmed = False
        s.stage = Stage.EXPLAIN
        return reply("收到您的更正。请说明哪一项需要核实，我不会把未确认的信息记为已同意。")
    if kind == IntentKind.QUESTION:
        if answer:
            s.stage = Stage.CONFIRM
            return reply(answer + " 请确认您是否了解整改事项，并愿意补齐后重新提交？")
        s.needs_human = True
        return reply("目前没有足够的已核对依据回答这个问题，我会登记人工核实。", "needs_human")
    if kind == IntentKind.RESULT_YES:
        if s.stage == Stage.CONFIRM:
            s.result_confirmed = True
            return reply("感谢确认，我会记录本次沟通结果。材料重新提交后仍需审核，不保证通过。再见。", "will_resubmit")
        s.stage = Stage.CONFIRM
        return reply("我再确认一下：您已了解整改事项，并愿意补齐材料后重新提交，对吗？")
    s.retries += 1
    if s.retries >= 3:
        s.needs_human = True
        return reply("这部分需要进一步核实，我会登记人工跟进，本次通话先结束。", "needs_human")
    s.stage = Stage.CONFIRM
    return reply("请明确确认是否愿意按上述事项整改，或告诉我需要核实的问题。")
