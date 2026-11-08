# 提示词

状态：当前真实意图提示词位于 services/api/model_client.py，已绑定会话 manifest 的 prompt_sha256；这里尚无重复提示词副本，避免两份漂移。

建议负责角色：业务负责人。实际领取人见 docs/任务看板.md。

范围：显式版本、证据约束、结构化提案与无依据兜底；不能将隐藏验收答案写入提示。

对应任务：P04。

目标文件、依赖方向与验收条件以根目录 docs/项目文件规划.md、docs/日志与回退.md、CONTRIBUTING.md 为准。
