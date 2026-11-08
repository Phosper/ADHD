# GEPA 的来源与用途

**GEPA 是提示词优化框架，适合作为智语外呼项目的第一套自动优化对照。** 它读取任务执行轨迹，分析失败原因，提出提示词修改，再通过评测比较候选。

## 原始来源

- 论文：[GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457)；本目录附有 [PDF 原文](../论文/GEPA_2507.19457.pdf)。
- 作者公开代码：[gepa-ai/gepa](https://github.com/gepa-ai/gepa)。
- 本次适配分析参考的代码版本：[cb7674c8b231](https://github.com/gepa-ai/gepa/commit/cb7674c8b231270134b8e5ea8b9db1a62ed8d081)。
- 下载方式：进入代码网页选择 `Code → Download ZIP`，或按上述提交取得固定版本。许可证与安装说明见上游仓库。

## 在我们项目中做什么

ADHD 当前由 Qwen3-8B 分类商家意图，状态机控制业务流程。可以把分类提示词作为 GEPA 的候选文本，由自定义执行器将候选真正送入 Qwen，再评价分类与最终业务结果。失败的训练案例和对应结果可作为反思材料。

这能建立“原始提示词、人工修订、自动优化”的基础比较。后续研究诊断性测试选择时，可以固定 GEPA 产生的候选，单独比较验证方法，避免把候选生成能力和选择能力混在一起。

## 需要适配什么

主要接口是 [`GEPAAdapter`](https://github.com/gepa-ai/gepa/blob/cb7674c8b231270134b8e5ea8b9db1a62ed8d081/src/gepa/core/adapter.py)：负责执行候选、输出评分和轨迹，并整理反思数据。现有规则模拟评测不会调用候选提示词，需要另接真实模型评测入口。

GEPA 不会自动理解本项目的业务正确性，也不自带外呼场景真值；评分函数、业务守卫和独立测试仍需我们提供。优化分类提示词不等于完整沟通 Skill 已经演化成功。当前为适配参考，尚未接入或运行。
