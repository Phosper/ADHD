# ADR 0003 模型隔离与执行边界

日期：2026-11-08。状态：实施中，实际语音性能待测。

Qwen3-8B 使用 Transformers 4.51.3 的非思考模式，初期单会话 BF16 + SDPA，以兼容服务器现有驱动并减少多模型显存预留。与语音环境隔离，不替换其他项目依赖；推理服务只监听环回地址。模型启动检查空闲显存，不能抢占或停止其他任务。

模型只生成严格 Intent JSON；身份、意愿、结果确认与回写仍由纯领域状态机控制。解析失败或超时返回可见错误，不把 Mock 当真实模型。检索仅采用已核对、且属于当前场景白名单的来源原文；无依据转人工。

依据：[Qwen3-8B 模型卡](https://huggingface.co/Qwen/Qwen3-8B)、[CosyVoice 官方示例](https://github.com/QwenAudio/CosyVoice/blob/main/example.py)、[FunASR](https://github.com/modelscope/FunASR)。模型下载后记录所有文件 SHA-256；只有完成下载和小测后才能记录为已部署。仓库地址发生官方重定向，CosyVoice 由 FunAudioLLM 转到 QwenAudio，仍使用原设计 CosyVoice2 权重。

开发阶段可在本机运行 WebRTC 服务并通过已授权校园网 SSH 使用远程推理。此路径仅用于研发，不能冒充已获许可的比赛现场网络方案。
