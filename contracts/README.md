# 共享契约

状态：已实现 JSON Schema/OpenAPI 生成与正反例检查，voice_gateway.py 为语音模块访问业务的共享边界。运行 python -m scripts.export_contracts 更新契约，禁止只改生成文件。

建议负责角色：集成负责人协调，各模块共同评审。实际领取人见 docs/任务看板.md。

范围：先定义 OpenAPI、事件、结果、工具和 manifest 的 Schema；附纯合成正反例，明确顺序、取消、重试和兼容规则。

对应任务：P01。

目标文件、依赖方向与验收条件以根目录 docs/项目文件规划.md、docs/日志与回退.md、CONTRIBUTING.md 为准。
