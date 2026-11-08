# 纯文本辅助语料

这些资源**不满足“中文 + 带语音”**，不进入中文语音语料主表；但可用于策略标签、中文话术、文本情绪辅助和负例评测。

## ESConv

- 论文：[arXiv 2106.01144](https://arxiv.org/abs/2106.01144)
- 仓库：[thu-coai/Emotional-Support-Conversation](https://github.com/thu-coai/Emotional-Support-Conversation)
- 数据：[ESConv.json](https://raw.githubusercontent.com/thu-coai/Emotional-Support-Conversation/main/ESConv.json)（实测 9,017,487 字节）
- 镜像：[Hugging Face thu-coai/esconv](https://huggingface.co/datasets/thu-coai/esconv)
- 许可：CC BY-NC 4.0；仓库注明仅学术研究。

规模与标签：

- 1,300 段英文情绪支持对话、38,365 轮、18,376 条带策略标注的支持者发言。
- 13 个 `problem_type` 取值，头部为 ongoing depression 351、job crisis 280、breakup with partner 239、problems with friends 179、academic pressure 156。
- 情绪类型：anxiety 354、depression 334、sadness 308、anger 111、fear 95、shame 42、disgust 40、nervousness 13、guilt/jealousy/pain 各 1。
- **anger 只有 111 段**，更适合借“策略”，不适合当愤怒对抗语料。

| 策略 | 条数 | 占比 | 可借鉴的客服动作 |
| --- | ---: | ---: | --- |
| Question | 3,801 | 20.7% | 追问澄清；对抗场景最多问一次，避免连续盘问 |
| Others | 3,341 | 18.2% | 兜底：转人工、回呼、礼貌收尾 |
| Providing Suggestions | 2,954 | 16.1% | 给单一步骤，不同时抛多个方案 |
| Affirmation and Reassurance | 2,827 | 15.4% | 承认体验 + “我帮您处理”的保证；不轻易认责 |
| Self-disclosure | 1,713 | 9.3% | 用“我这边”表态已接手，不暴露客服个人信息 |
| Reflection of feelings | 1,436 | 7.8% | 命名情绪：“您这么生气是因为……” |
| Information | 1,215 | 6.6% | 解释规则/事实，先结论后原因 |
| Restatement or Paraphrasing | 1,089 | 5.9% | 复述确认，防止误解升级 |
| 合计 | 18,376 | 100% | |

失败样本：[FailedESConv.json](https://raw.githubusercontent.com/thu-coai/Emotional-Support-Conversation/main/FailedESConv.json) 含 **196 段失败对话**，可用于分析连续追问、过早给建议、空泛保证等反例。

适用边界：

- 借 8 类策略标签和失败反例，不直接照搬英文话术。
- 不能用于中文客服语音训练。
- 不能用来推导语速、音量或 TTS 参数。

## CPED

- 论文：[arXiv 2205.14727](https://arxiv.org/abs/2205.14727)
- 仓库：[scutcyr/CPED](https://github.com/scutcyr/CPED)
- 数据目录：[data/CPED](https://github.com/scutcyr/CPED/tree/main/data/CPED)
- 许可：仓库代码 Apache-2.0；论文/数据 CC BY-NC-ND 4.0；源素材是电视剧，商用和再分发需法务复核。

规模与标签：

- 40 部电视剧、11,835 段对话、132,762 句；论文称 392 名说话人，CSV 中唯一 `Speaker` 字符串为 303 个，存在统计口径差异。
- 实际 CSV 有 11 个 `Scene` 取值（论文概括为 10 类）：home 62,243、office 17,093、restaurant 15,100、other-venue 8,474、outdoor 8,314、hospital 5,786、car 5,705、entertainment-venue 3,777、school 3,281、mall 2,257、sports-venue 732。
- 13 类情绪：neutral 42,875、anger 18,039、depress 14,055、negative-other 13,978、relaxed 10,134、worried 8,292、happy 6,521、positive-other 6,466、astonished 4,176、sadness 3,021、fear 2,969、disgust 1,986、grateful 250。
- 19 类对话行为，头部为 `statement-non-opinion` 58,098、`statement-opinion` 31,178、`question` 25,358；与安抚直接相关的是 **`comfort` 806、`apology` 557**。
- **没有 wav/mp3/mp4/npy**，只有文本、人格/情绪/DA 标注和 `FacePosition_LU/RD` 人脸框坐标。

适用边界：

- `comfort` / `apology` 可做中文安抚、致歉话术的种子，但要改写成客服合规表达，不能直接照抄影视台词。
- anger / worried 可做中文文本情绪的少样本和离线评测，但要处理影视域偏移。
- 不能用于声学情绪或语速训练，不能替代真实客服语音标定。

## 中文客服文本资源（非语音）

2026-11-09 的 GitHub 检索找到几个中文客服对话数据，但**全部是文本，没有音频**，不能计入语音语料：

| 资源 | 规模与标签 | 获取状态 | 用途与限制 |
| --- | --- | --- | --- |
| [CCSE-CS](https://github.com/haimianxing/CCSE-CS-Empathetic-Culture-AI) | README 称 9,478 段对话、76,847 轮；4 个行业（电商/银行/电信/医疗）；6 类 18 子策略，含 De-escalation、Boundary Setting、Constructive Redirection | 仓库公开策略本体、生成脚本和评测代码；`data/raw/` 只有 `.gitkeep`，未见公开对话数据或 LICENSE 文件；README 标 MIT、目标 EMNLP 2026 | 最适合借“中文客服降级策略分类”；数据未公开、论文未正式发表，不能当现成训练集 |
| [CSDS](https://github.com/xiaolinAndy/CSDS) | 中文客服对话摘要数据集；EMNLP 2021 | 仓库含代码和数据处理说明，数据走 Google Drive | 客服对话摘要；不含情绪标签、不含音频 |
| [Chinese-Ambiguous-Reference](https://github.com/ygan/Chinese-Ambiguous-Reference) | 1,000+ 段中文客服对话，标注澄清问题 | 仓库公开 `All Conversation.json` | 澄清/追问话术参考；不含情绪标签、不含音频 |

结论：这些资源可用于中文客服话术和策略分类，但**不能替代“中文客服情绪对抗语音库”**；截至检索日仍未找到公开可下载的此类语音库。

## 其他文本参考

| 资源 | 语言/域 | 规模与标签 | 获取与许可 | 用途与限制 |
| --- | --- | --- | --- | --- |
| [JDDC 1.0](https://arxiv.org/abs/1911.09969) | 中文，京东电商客服 | 100 万+ 对话、2,000 万句、200+ 意图；无情绪标签 | 原官方入口已下线；仅第三方 1 万 session 小样本，无明确 LICENSE | 最贴客服话术；不能做情绪监督 |
| [JDDC 2.1](https://arxiv.org/abs/2109.12913) | 中文，京东多模态客服 | 约 24.6 万会话、300 万句、50.7 万图片 | 单位邮箱申请；以京东回复为准 | 文本+图片，无音频、无情绪主标签 |
| [EmoTwiCS](https://arxiv.org/abs/2310.06536) | 荷兰语，Twitter 客服 | 9,489 段对话；28 类情绪 + VAD + 8 类响应 | 论文称可申请；需核对条款 | 客服情绪轨迹标注设计；语言不匹配 |
| [CusEmo](https://arxiv.org/abs/2310.02281) | 法语，真实呼叫中心 | 5,548 通、375.39 小时；连续 VAD + 共情水平 | 未公开 | 只能学标注设计，不能训练 |
| [MELD](https://arxiv.org/abs/1810.02508) | 英文，电视剧 | 1,433 段对话、约 1.3 万句；7 类情绪 | GPL-3.0 | 英文影视基准，不适合中文客服部署 |
| [EmpatheticDialogues](https://arxiv.org/abs/1811.00207) | 英文，开放域共情 | 2.5 万段对话；32 类情绪情境 | CC BY-NC 4.0 | 共情表达风格参考 |
| CH-SIMS | 中文，电视剧 | 情感极性标注 | `thuiar/CH-SIMS` 404；HF 仅第三方镜像 | 极性不是 13 类情绪；不作为首选 |
