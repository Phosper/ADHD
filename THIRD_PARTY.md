# 基线组件与来源

实际 Python 全量依赖见 uv.lock、deploy/models-linux.lock、deploy/voice-windows.lock；前端见 apps/web/package-lock.json。模型逐文件哈希保存在私有 models/*-manifest.json，简表在 runtime/model-manifest.json，不能仅凭仓库名重建相同权重。

| 组件 | 本次版本/身份 | 用途 | 来源与许可记录 |
|---|---|---|---|
| Pipecat | 1.15.0 | WebRTC 管线、Silero 接入 | https://github.com/pipecat-ai/pipecat ，BSD-2-Clause，发行包包含许可 |
| aiortc | 1.16.0 | WebRTC 协商及音频输入 | https://github.com/aiortc/aiortc ，BSD-3-Clause，上游依赖另有许可 |
| Qwen3 | Qwen/Qwen3-8B，15 个文件哈希 | 非思考意图分类 | https://huggingface.co/Qwen/Qwen3-8B ，模型包包含 Apache-2.0 LICENSE |
| FunASR | 1.2.6 | 600ms Paraformer 流式识别 | https://github.com/modelscope/FunASR ，代码 MIT；具体 iic 在线模型条款需随模型卡复核 |
| Paraformer 模型 | iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online | 中文 ASR | https://modelscope.cn/models/iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online ，下载文件没有独立 LICENSE，禁止据代码许可推定权重再分发权 |
| CosyVoice | 074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc | 流式 TTS | https://github.com/QwenAudio/CosyVoice ，源码 Apache-2.0 |
| CosyVoice2 权重 | iic/CosyVoice2-0.5B，20 个文件哈希 | 中文发声 | https://modelscope.cn/models/iic/CosyVoice2-0.5B ，具体模型卡条款与参考音频再分发条件待交付前复核，不随源码包分发 |
| Matcha-TTS | dd9105b34bf2be2230f4aa1e4769fb586a3c824e | CosyVoice 子模块 | https://github.com/shivammehta25/Matcha-TTS ，保留原仓库 LICENSE |
| PyTorch / Transformers | 2.6.0 / 4.51.3 | GPU 推理 | https://github.com/pytorch/pytorch 、https://github.com/huggingface/transformers ，保留安装包许可 |
| Whisper 特征函数 | 20240930 | CosyVoice 音频特征 | https://github.com/openai/whisper ，MIT；不是本项目 ASR 主模型 |
| React / Vite | 19.3.1 / 8.3.6 | 网页工作台 | https://github.com/facebook/react 、https://github.com/vitejs/vite ，MIT |

本项目没有重新发布模型权重、企业资料、音色样本或第三方源码。官方公共参考音频只用于研发小测，最终比赛演示音色使用权需要团队按模型卡核对，不能以仓库公开下载等同任意用途授权。

技术论文与选择理由已在 docs/赛道二基线设计文档.md 中列出；这些论文不提供本工程的实测成绩。
