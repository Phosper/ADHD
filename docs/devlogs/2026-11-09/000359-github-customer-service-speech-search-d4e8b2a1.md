# 开发对话记录：GitHub 检索中文客服情绪对抗语音库

- 记录 ID：20261109-000359-github-cs-speech-d4e8b2a1
- 时间：2026-11-09T00:03:59+08:00 开始；2026-11-09T00:08:00+08:00 结束
- 参与者：本次助手
- 任务与分支：`Lruy-work`；检索是否存在公开的中文客服情绪对抗语音库
- 起始 commit：b170bae `docs: add emotion dataset catalog`
- 起始工作区：干净
- 状态：检索完成；补充数据集文档与日志；本地提交待建立，未推送

## 需求与决定

用户要求去 GitHub 搜索有没有“中文客服情绪对抗语音库”。检索目标是同时满足：中文普通话、客服/呼叫中心通话、情绪或对抗/安抚标签、能拿到音频。

结论：**没有找到符合条件的公开 GitHub 仓库**。命中的中文客服数据全部是文本；命中的客服语音数据是法语、阿拉伯语、俄语等非中文语料。

## 实际变更

- 新增 `datasets/github-search-2026-11-09.md`：检索日期、查询、零结果、命中项、限制和建议。
- `datasets/README.md`：补充 GitHub 检索结论和报告入口。
- `datasets/text-support.md`：新增“中文客服文本资源（非语音）”，记录 CCSE-CS、CSDS、Chinese-Ambiguous-Reference。
- 本日志。
- 无业务代码、契约、数据库、提示词或部署配置变化。

## 检索证据

GitHub Search API（`in:name,description`）检索结果：

- `"Chinese Customer Service Speech"`：0
- `"Chinese call center"`：0
- `"Mandarin call center"`：0
- `"客服" "语音库"`：0
- `"客服语音数据集"`：0
- `"中文客服" "语音"`：0
- `"呼叫中心" "语音" "数据集"`：0
- `"坐席" "语音" "数据集"`：0
- `"Customer Service Speech"`：3，只有阿拉伯语客服语音样本和两个评测项目
- `"Call Center Speech"`：7，俄语/法语商业语料和 ASR 项目，无中文
- `"customer service" "speech dataset"`：1，只有 Nexdata 阿拉伯语客服语音

命中的中文客服文本资源：

- `haimianxing/CCSE-CS-Empathetic-Culture-AI`：README 称 9,478 段对话、76,847 轮、4 行业、6 类 18 子策略（含 De-escalation）；仓库公开策略本体、生成脚本、评测代码，但 `data/raw/` 只有 `.gitkeep`，`data/dialogues.json` 404，未见 LICENSE 文件；README 标 MIT、目标 EMNLP 2026。
- `xiaolinAndy/CSDS`：EMNLP 2021 中文客服对话摘要；数据通过 Google Drive 分发，仓库含代码/说明。
- `ygan/Chinese-Ambiguous-Reference`：1,000+ 段中文客服澄清对话；仓库公开 `All Conversation.json`。
- JDDC 1.0/2.1：中文客服文本，无音频、无情绪标签。

命中的非中文客服语音：

- CusEmo：法语真实呼叫中心，未公开。
- Nexdata Arabic 268h：阿拉伯语，商业样本。
- MaratDV 俄语约 832h、法语约 164h：商业使用。
- Hugging Face `Rekktech/emotion-customer-service-processed`：有音频张量和 3 类情感，但无语言/来源说明，不能确认是中文，不计入。

## 验证与限制

- 使用 GitHub Search API 和 Hugging Face 数据集 API；用 raw.githubusercontent.com 核对 README 与数据文件是否存在。
- GitHub 代码搜索需要登录，未使用；grep.app 和 Sourcegraph 因限流/权限不可用。
- 未执行：没有下载任何音频；没有联系作者；没有做许可法律意见；没有运行应用测试（本次仅文档变更）。
- “没搜到”不等于绝对不存在；私有仓库、企业内网和商业授权语料不在公开检索范围内。

## 交付与回退

- 交付文件：`datasets/github-search-2026-11-09.md`、`datasets/README.md`、`datasets/text-support.md` 与本日志。
- 提交：本地分支 `Lruy-work`，提交信息 `docs: record GitHub search for Chinese service speech corpus`；未推送。
- 查询：`git log --all -- docs/devlogs/2026-11-09/000359-github-customer-service-speech-search-d4e8b2a1.md`。
- 回退：revert 本次提交即可；不涉及业务代码、数据库、模型或外部工具副作用。

## 待办与交接

- 如果团队有 MagicData、Nexdata、Speechocean 等供应商渠道，单独询价并确认中文客服语音的授权范围。
- 真实阈值仍需 200—500 通获准脱敏客服通话；公开数据无法替代。
- 若要继续找，可让有 GitHub 登录权限的成员用代码搜索查 `wav`/`mp3` 文件与“客服”路径组合。
