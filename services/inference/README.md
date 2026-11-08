# 模型推理服务

状态：已实现 Qwen3-8B、Paraformer streaming、CosyVoice2 服务，A800 上已实际加载并完成中文生成与转写小测。按 deploy/README.md 使用独立环境；缓存与实时生成分开记录。

建议负责角色：实时与模型负责人。实际领取人见 docs/任务看板.md。

范围：ASR、LLM、TTS 独立进程和依赖；模型权重不进 Git，真实 revision 与硬件结果写入 manifest。

对应任务：P07。

目标文件、依赖方向与验收条件以根目录 docs/项目文件规划.md、docs/日志与回退.md、CONTRIBUTING.md 为准。
