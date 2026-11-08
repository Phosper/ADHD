# 中文带语音情绪语料

筛选标准：**中文、能拿到音频或视频音轨、有情绪或对话行为标签**。纯文本、无音频、非中文的数据不进本表。

## 结论

- 没有找到可公开下载的“中文客服情绪对抗 / 降级”语音库。
- 最接近的是 **EmotionTalk、M3ED、MER2023 / MER2024**。
- 声学、韵律和语速用 **ESD、EMOVIE**；细粒度语音情绪理解用 **CSEU-Bench**。
- 影视/表演/朗读域与真实客服差距很大，不能直接拿公开数据分数宣称客服效果。

## 可直接获取的语料

| 语料 | 论文 | 仓库 / 数据入口 | 规模与标签 | 获取与许可 | 对情绪对抗的用途 |
| --- | --- | --- | --- | --- | --- |
| [EmotionTalk](https://huggingface.co/datasets/BAAI/Emotiontalk) | [arXiv 2505.23018](https://arxiv.org/abs/2505.23018) | [NKU-HLT/EmotionTalk](https://github.com/NKU-HLT/EmotionTalk)；[HF BAAI/Emotiontalk](https://huggingface.co/datasets/BAAI/Emotiontalk) | 23.6 小时、19,250 句、19 人、7 类情绪（anger 3,698）；含 WAV/文本/视频 | HF 登录并同意 CC BY-NC-SA 4.0，gated auto；总文件约 36.1 GB | **最接近“冲突对话”**：双人对话、真实语音、愤怒样本多；无安抚策略标签，需自行标注策略/强度 |
| [M3ED](https://github.com/AIM3-RUC/RUCM3ED) | [arXiv 2205.10237](https://arxiv.org/abs/2205.10237) | [AIM3-RUC/RUCM3ED](https://github.com/AIM3-RUC/RUCM3ED) | 990 段对话、9,082 轮、24,449 句、56 部电视剧、7 类情绪 | 标注/文本/语音信息在仓库；音频在百度网盘（链接见 README，提取码 `6b5q`）；视觉特征因版权未放；仓库未声明 LICENSE | 多轮上下文 + 愤怒；影视剧，不是客服；适合上下文情绪建模和预训练 |
| [MER2023](https://huggingface.co/datasets/MERChallenge/MER2023) | [arXiv 2304.08981](https://arxiv.org/abs/2304.08981) | [MERTools/MER2023](https://github.com/zeroQiaoba/MERTools/tree/master/MER2023)；[HF MER2023](https://huggingface.co/datasets/MERChallenge/MER2023) | 5,030 条标注片段（含 MER-SEMI 的 834 条）+ 73,148 条无标注；CHEAVD 扩展；离散 + 维度情绪 | HF 填 EULA，gated auto；CC BY-NC 4.0；仅学术 | 中文影视、噪声/半监督；适合鲁棒性评测，不是客服对抗数据 |
| [MER2024](https://huggingface.co/datasets/MERChallenge/MER2024) | [arXiv 2404.17113](https://arxiv.org/abs/2404.17113) | [MERTools/MER2024](https://github.com/zeroQiaoba/MERTools/tree/master/MER2024)；[HF MER2024](https://huggingface.co/datasets/MERChallenge/MER2024) | 5,030 条标注 + 20,000 条无标注；中英字幕；开放词表 | HF 填 EULA，gated auto；CC BY-NC 4.0；仅学术 | 噪声、开放词表、跨域评测；不是客服 |
| [ESD](https://github.com/HLTSingapore/Emotional-Speech-Data) | [ICASSP 2021](https://doi.org/10.1109/ICASSP39728.2021.9413391)；[Speech Communication 2022](https://www.sciencedirect.com/science/article/pii/S0167639321001308) | [HLTSingapore/Emotional-Speech-Data](https://github.com/HLTSingapore/Emotional-Speech-Data) | 10 位普通话 + 10 位英语说话人，每人 350 句；neutral/happy/angry/sad/surprise | Google Drive；需签 License 并发给作者；仅研究 | 声学情绪、韵律、TTS 语速/情感控制；单人朗读，不是对话 |
| [EMOVIE](https://viem-ccy.github.io/EMOVIE/dataset_release) | [arXiv 2106.09317](https://arxiv.org/abs/2106.09317) | [官方数据页](https://viem-ccy.github.io/EMOVIE/dataset_release)；[ViEm-ccy/EMOVIE](https://github.com/ViEm-ccy/EMOVIE) | 9,724 条普通话电影语音 + 人工情绪标注 | 数据页 Google Drive 直接下 tar.gz（约 600 MB）；CC BY-NC-SA 2.0 | 情感 TTS/声学；电影台词，不是对话/客服 |
| [CSEU-Bench](https://huggingface.co/datasets/smart9/CSEU-Bench) | 未检索到正式论文；见 [HF 数据卡](https://huggingface.co/datasets/smart9/CSEU-Bench) | [qiuchili/CSEU-Bench](https://github.com/qiuchili/CSEU-Bench) | 1K–10K 条中文语音；83 类心理语言学情绪标签；单音节/双音节/短句/语篇 | HF 直接下载；CC BY 4.0；无需申请 | 细粒度中文语音情绪理解；不是客服、不含对话策略 |
| [Chinese Speech Emotion Datasets](https://github.com/AkishinoShiame/Chinese-Speech-Emotion-Datasets) | [MMSys 2017](http://dl.acm.org/citation.cfm?id=3083220) | [AkishinoShiame/Chinese-Speech-Emotion-Datasets](https://github.com/AkishinoShiame/Chinese-Speech-Emotion-Datasets) | 652 条台湾普通话；positive/natural/negative；wav + 频谱图 | GitHub 直接下载；Apache-2.0 | 小型三类声学基线；来源混杂、样本少，不作为主训练集 |

## 论文可查、但没有找到公开仓库

| 语料 | 论文 | 仓库状态 | 说明 |
| --- | --- | --- | --- |
| CHEAVD | [2014 ICOSP](https://doi.org/10.1109/ICOSP.2014.7015071)；[2016 JAIHC](https://doi.org/10.1007/s12652-016-0406-z) | 未找到公开仓库 | 中文自然情绪音视频库；MER2023 使用其扩展版，实际获取走 MER2023 EULA |
| CH-MEAD | [DOI 10.1109/APSIPAASC58517.2023.10317512](https://doi.org/10.1109/APSIPAASC58517.2023.10317512) | 未找到公开仓库/HF | 中文多模态对话情绪、细粒度情绪分类；需向作者确认音频与授权 |
| NNIME | [DOI 10.1109/ACII.2017.8273615](https://doi.org/10.1109/ACII.2017.8273615) | 未找到公开仓库 | NTHU-NTUA 中文交互式多模态情绪语料；需向作者确认音频与授权 |
| MES-P | [arXiv 1808.10095](https://arxiv.org/abs/1808.10095) | 未找到公开仓库 | 普通话；intended/perceived 标签；joy/anger/sadness 强度；论文无公开下载链接，需联系作者 |
| MASC | [DOI 10.1109/ODYSSEY.2006.248084](https://doi.org/10.1109/ODYSSEY.2006.248084) | 未找到公开仓库 | 普通话情绪分析与情感说话人识别；较早的基准语料，需联系作者 |

## 获取步骤

以下命令只写入被忽略的 `data/datasets/`，不要提交到 Git。

### EmotionTalk

需要 Hugging Face 账号并接受 CC BY-NC-SA 4.0：

```powershell
huggingface-cli login
huggingface-cli download BAAI/Emotiontalk --repo-type dataset --local-dir data/datasets/EmotionTalk
```

总文件约 36.1 GB，先确认磁盘空间。下载后记录实际文件数和哈希。

### M3ED

```powershell
git clone --depth 1 https://github.com/AIM3-RUC/RUCM3ED data/datasets/M3ED
```

音频按仓库 README 的百度网盘链接下载，提取码 `6b5q`。仓库未声明 LICENSE，使用前向作者确认。

### MER2023 / MER2024

先在 Hugging Face 数据页填写 EULA 并接受条款，再下载：

```powershell
huggingface-cli download MERChallenge/MER2023 --repo-type dataset --local-dir data/datasets/MER2023
huggingface-cli download MERChallenge/MER2024 --repo-type dataset --local-dir data/datasets/MER2024
```

仅学术用途，CC BY-NC 4.0。

### ESD

1. 打开 [HLTSingapore/Emotional-Speech-Data](https://github.com/HLTSingapore/Emotional-Speech-Data)。
2. 按 README 下载 License，签署后发给作者。
3. 获得 Google Drive 权限后再下载；仅研究用途。

### EMOVIE

1. 打开 [官方数据页](https://viem-ccy.github.io/EMOVIE/dataset_release)。
2. 从 Google Drive 下载 `EMOVIE DATASET.tar.gz`，约 600 MB。
3. 许可为 CC BY-NC-SA 2.0，不能商用再分发。

### CSEU-Bench

```powershell
huggingface-cli download smart9/CSEU-Bench --repo-type dataset --local-dir data/datasets/CSEU-Bench
```

CC BY 4.0，可直接下载。

### Chinese Speech Emotion Datasets

```powershell
git clone --depth 1 https://github.com/AkishinoShiame/Chinese-Speech-Emotion-Datasets data/datasets/Chinese-Speech-Emotion-Datasets
```

Apache-2.0；样本少，只适合做小型基线。

## 推荐组合

- **对话/冲突情绪**：EmotionTalk + M3ED。前者是双人真实语音，后者有多轮上下文和较多愤怒样本；两者都不是客服。
- **鲁棒性与跨域评测**：MER2023 / MER2024。用于验证噪声、跨剧集、开放词表下的退化，不能拿分数直接宣称客服效果。
- **声学情绪、韵律、语速**：ESD + EMOVIE。用于验证 SER 模型、TTS `speed` 和韵律特征；不提供对话策略。
- **细粒度中文语音情绪理解**：CSEU-Bench。83 类标签适合做标签映射和模型诊断。
- **备选/需申请**：CHEAVD、CH-MEAD、NNIME、MES-P、MASC。拿不到授权就不要阻塞项目。
- **客服域**：没有公开中文客服情绪对抗语音库；先用上述数据做预训练/评测，再用 200—500 通自有脱敏通话做阈值和策略标定。

## 明确剔除

- **JDDC / JDDC 2.1**：没有音频；2.1 是文本 + 图片。
- **CPED**：公开仓库只有文本、标注和人脸框坐标，没有 wav/mp4。
- **MELD / ESConv / EmpatheticDialogues / EmoTwiCS**：非中文或纯文本，不满足“中文带语音”。
- **CusEmo**：法语真实呼叫中心，且未公开。
- **CH-SIMS**：标签是情感极性而非 13 类情绪；`thuiar/CH-SIMS` 当前 404，HF 只有第三方镜像。
