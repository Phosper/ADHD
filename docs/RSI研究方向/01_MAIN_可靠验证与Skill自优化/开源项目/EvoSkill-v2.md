# EvoSkill v2 的来源与用途

**EvoSkill v2 是通过反复改写技能说明来改善 Agent 的项目。** 它保留演化器跨轮状态，并让演化器读取多次训练轨迹，适合比较技能更新与评测波动处理方式。

## 原始来源

- 论文：[EvoSkill v2: Fully Agentic Skill Evolution from Benchmark Adaptation to a Stateful Evolver](https://arxiv.org/abs/2610.25931v2)；本目录附有 [PDF 原文](../论文/EvoSkill-v2_2610.25931v2.pdf)。
- 作者公开代码：[sentient-agi/EvoSkill 的 v2 分支](https://github.com/sentient-agi/EvoSkill/tree/v2)。`main` 分支对应另一版，不能混用。
- 本次适配分析参考的代码版本：[331ac10aac04](https://github.com/sentient-agi/EvoSkill/commit/331ac10aac04d179942d1dfdd88732d4a52a869f)。
- 下载方式：在代码网页切换到 `v2` 后选择 `Code → Download ZIP`，或取得上述固定提交。依赖与许可证见上游仓库。

## 在我们项目中做什么

原方法让演化器持续利用训练尝试和历史技能，每轮采用更新后的技能，而不是根据波动分数反复选择。它可以作为 GEPA、RRSI 式流程之外的对照，帮助研究“优化器应该如何使用历史失败，以及怎样处理不稳定评测”。

本项目可先借鉴多次训练轨迹反馈和保留演化历史；如果研究完整沟通技能，则需要让 ADHD 真正读取并执行技能策略。当前 Qwen 主要输出意图分类，状态机固定生成回复，放入一个 `SKILL.md` 文件不会自动改变这些行为。

## 需要适配什么

原实现使用 Claude Code 技能执行和容器编排，不是直接调用 Qwen 聊天接口的插件。更换执行器、技能格式或每轮更新规则后，需要说明差异，不能声称严格复现。

“每轮采用更新”是隔离实验中的算法选择；实际部署仍需统一业务与发布验收。若研究对照也额外拒绝其更新，应明确该实验已经修改原方法。当前未运行该框架。
