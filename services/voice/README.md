# 实时语音

状态：已实现 Pipecat WebRTC 输入、Silero VAD、流式 ASR 调用、模型意图、带代号 PCM 播放和取消。真实合成输入四轮已跑通；人声、噪声与官方网络验收待完成。

建议负责角色：实时与模型负责人。实际领取人见 docs/任务看板.md。

范围：Pipecat 管线、音频格式、VAD、generation_id 取消；通过业务接口请求状态变更。

2026-11-14 候选改进：VAD 起始后增加默认 80 ms 持续确认及 -50 dBFS 去直流能量门槛，确认后才打断播报，保留 300 ms 前置音频；参数见 .env.example。该模块不修改 PCM 波形，不能当作已完成通用降噪。逻辑测试覆盖短脉冲、低能量、直流偏置、轻声及重新起始；真人、背景人声及正式声学时延仍待验收。设计与取舍见 [ADR 0009](../../docs/decisions/0009-noise-gate-and-task-result.md)。

对应任务：P07、P08。

目标文件、依赖方向与验收条件以根目录 docs/项目文件规划.md、docs/日志与回退.md、CONTRIBUTING.md 为准。
