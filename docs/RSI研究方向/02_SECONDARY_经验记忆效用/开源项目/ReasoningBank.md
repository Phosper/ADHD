# ReasoningBank 的来源与用途

**ReasoningBank 将任务经历整理成可复用的处理经验，用于帮助后续任务。** 它适合参考经验记忆副线中的“存什么、如何提炼”。

## 原始来源

- 论文：[ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory](https://arxiv.org/abs/2509.25140)；本目录附有 [PDF 原文](../论文/ReasoningBank_2509.25140.pdf)。
- 作者公开代码：[google-research/reasoning-bank](https://github.com/google-research/reasoning-bank)。
- 本次适配分析参考的代码版本：[ed8061178829](https://github.com/google-research/reasoning-bank/commit/ed80611788292ea739f1effd31f16c53823b8a0d)。
- 下载方式：进入代码网页选择 `Code → Download ZIP`，或取得上述固定提交。依赖与许可证见仓库说明。

## 在我们项目中做什么

智语外呼已经能记录会话事件和最终结果。可以从训练组提炼“在某种阶段和条件下，怎样理解商家表达或处理疑问”的经验，而不是原样保存全部聊天。

例如，一条经验应解释“单独说知道了为什么不足以证明整改意愿，适用于哪些上下文”，而不是只保存某一次成功对话。成功和失败都可提供材料；本项目应优先用已复核的业务结果判断经验是否可靠，不照搬模型自评作为唯一依据。

## 需要适配什么

原仓库包含 WebArena 和 SWE-Bench 等任务的实现。经验提炼、管理和注入思路可参考，但需要改为本项目的场景、状态、业务证据和结果格式。

当前基线没有经验注入接口。初期可将少量经验用于意图分类；完整沟通经验还需要受控策略接口。经验不能覆盖业务规则，测试组也不能用于反向提炼训练经验。当前未实现或验证此适配。
