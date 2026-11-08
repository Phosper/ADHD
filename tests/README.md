# 自动化测试

状态：已提供领域、API、事务、并发、契约、资料导入、模型输出防护、恢复、音频归档和发布门槛检查。入口 python -m scripts.verify。浏览器用例在 apps/web/tests；fixture 不能视为真实模型验收。

建议负责角色：各模块作者与独立评审者。实际领取人见 docs/任务看板.md。

范围：unit/contract/integration/e2e 逐步建立；重点覆盖状态、幂等、故障、打断、日志和恢复，避免只重复实现。

对应任务：P01—P10。

目标文件、依赖方向与验收条件以根目录 docs/项目文件规划.md、docs/日志与回退.md、CONTRIBUTING.md 为准。
