# GitHub 检索：中文客服情绪对抗语音库

- 检索日期：2026-11-09，Asia/Taipei
- 检索范围：GitHub 仓库搜索（name/description）、Hugging Face 数据集 API、arXiv
- 目标：确认是否存在“中文 + 客服通话 + 情绪/对抗标签 + 音频”的公开仓库

## 结论

**没有找到。** 截至 2026-11-09，没有发现同时满足以下条件的公开 GitHub 仓库：

1. 中文普通话；
2. 真实客服/呼叫中心通话；
3. 有愤怒、焦虑、冲突强度或安抚策略等情绪对抗标签；
4. 能下载到音频或视频音轨。

命中的中文客服数据全部是文本；命中的客服语音数据是法语、阿拉伯语、俄语等非中文语料。公开的中文语音情绪语料（EmotionTalk、M3ED、MER2023/2024、ESD、EMOVIE、CSEU-Bench）都不是客服域。

## 零结果/近似零结果的精确查询

以下查询使用 GitHub Search API 的 `in:name,description`，结果数为检索时返回值：

| 查询 | 结果数 | 说明 |
| --- | ---: | --- |
| `"Chinese Customer Service Speech"` | 0 | 没有中文客服语音数据集 |
| `"Chinese call center"` | 0 | 没有中文呼叫中心语料 |
| `"Mandarin call center"` | 0 | 没有普通话音呼叫中心语料 |
| `"客服" "语音库"` | 0 | 没有客服语音库 |
| `"客服语音数据集"` | 0 | 没有客服语音数据集 |
| `"中文客服" "语音"` | 0 | 没有中文客服语音 |
| `"呼叫中心" "语音" "数据集"` | 0 | 没有呼叫中心语音数据集 |
| `"坐席" "语音" "数据集"` | 0 | 没有坐席语音数据集 |
| `"Customer Service Speech"` | 3 | 阿拉伯语客服语音样本、两个客服语音评测项目；无中文 |
| `"Call Center Speech"` | 7 | 俄语/法语商业语料、ASR 项目；无中文 |
| `"customer service" "speech dataset"` | 1 | 只有 Nexdata 的阿拉伯语客服语音 |

宽泛查询 `客服 语音 数据集` 会返回 8 条左右，但都是客服系统、ASR 工具或通用 NLP 资源，不是带情绪标签的中文客服语音库。

## 命中的中文客服文本资源

| 资源 | 类型 | 规模/标签 | 数据状态 | 判断 |
| --- | --- | --- | --- | --- |
| [CCSE-CS](https://github.com/haimianxing/CCSE-CS-Empathetic-Culture-AI) | 中文客服共情对话，合成/生成 | README 称 9,478 段对话、76,847 轮、4 行业、6 类 18 子策略（含 De-escalation） | 公开策略本体、生成脚本、评测代码；`data/raw/` 仅 `.gitkeep`，未见对话数据或 LICENSE 文件 | 最接近“中文客服降级策略”，但**无音频、数据未公开、论文未正式发表** |
| [CSDS](https://github.com/xiaolinAndy/CSDS) | 中文客服对话摘要 | EMNLP 2021 | 仓库含代码/说明，数据走 Google Drive | 文本摘要，无情绪标签、无音频 |
| [Chinese-Ambiguous-Reference](https://github.com/ygan/Chinese-Ambiguous-Reference) | 中文客服澄清对话 | 1,000+ 段 | 仓库公开 `All Conversation.json` | 澄清/追问话术，无情绪标签、无音频 |
| [JDDC 1.0](https://github.com/SimonJYang/JDDC-Baseline-Seq2Seq) / [JDDC 2.1](https://github.com/hrlinlp/jddc2.1) | 京东电商客服 | 100 万+/24.6 万会话 | 1.0 仅第三方小样本；2.1 需单位申请 | 最贴客服域，但无音频、无情绪标签 |

## 命中的非中文客服语音

| 资源 | 语言 | 规模 | 获取 | 判断 |
| --- | --- | --- | --- | --- |
| [CusEmo](https://arxiv.org/abs/2310.02281) | 法语 | 5,548 通、375.39 小时 | 未公开 | 真实呼叫中心，只能学标注设计 |
| [Nexdata Arabic Customer Service Speech](https://github.com/Nexdata-AI/268-Hours-Arabic-Saudi-Full-Duplex-Multi-Channel-Customer-Service-Speech-Dataset) | 阿拉伯语 | 268 小时 | 商业样本 | 不是中文 |
| [MaratDV/russian-call-center-speech-ru](https://github.com/MaratDV/russian-call-center-speech-ru) | 俄语 | 约 832 小时 | 商业使用 | 不是中文 |
| [MaratDV/french-call-center-speech-fr](https://github.com/MaratDV/french-call-center-speech-fr) | 法语 | 约 164 小时 | 商业使用 | 不是中文 |
| [Rekktech/emotion-customer-service-processed](https://huggingface.co/datasets/Rekktech/emotion-customer-service-processed) | 未标注 | 7,027/1,506/1,506 条，3 类情感 | 公开 parquet | 有音频张量，但无语言/来源说明，不能确认是中文，不计入 |

## 检索限制

- GitHub 仓库搜索只索引仓库名和描述；真正存放在代码/数据目录里的语料可能搜不到。
- GitHub 代码搜索需要登录，本次未能使用；grep.app 和 Sourcegraph 也因限流/权限不可用。
- 私有仓库、企业内网数据、商业授权语料不会出现在公开搜索里。
- 商业厂商（MagicData、Nexdata、Speechocean 等）可能出售中文客服语音，但本次没有找到可公开下载的 GitHub 仓库。
- “没搜到”不等于“绝对不存在”；如果团队有供应商或企业渠道，仍需单独询价和做法务复核。

## 建议

- **语音预训练/评测**：继续用 EmotionTalk + M3ED，MER2023/2024 做鲁棒性，ESD/EMOVIE 做声学与语速。
- **中文客服降级策略**：可参考 CCSE-CS 的 18 子策略分类和 ESConv 的 8 类策略，但不要把文本策略当成语音语料。
- **真实阈值**：仍需 200—500 通获准脱敏的真实客服通话做标定；公开数据无法替代。
