# 开发对话记录：数据集目录整理

- 记录 ID：20261108-234011-dataset-catalog-b3f7a1c2
- 时间：2026-11-08T23:40:11+08:00 开始；2026-11-08T23:46:00+08:00 结束
- 参与者：本次助手
- 任务与分支：从 `codex/baseline-implementation` 新开 `Lruy-work`；只整理已找到的数据集，不改 baseline 业务代码
- 起始 commit：41afa0c `docs: record successful baseline push verification`
- 起始工作区：干净
- 状态：数据集目录已整理；本地提交待建立，未推送

## 需求与决定

用户要求以 `codex/baseline-implementation` 为基础新开 `Lruy-work`，基线的事情不用处理，只提交已找到的数据集并整理好，先本地提交、不要推送。

决定：

- 从本地 `codex/baseline-implementation` 创建 `Lruy-work`，不沿用调研分支的历史。
- 只新增数据集目录和开发日志，不修改 baseline 代码、契约、配置或测试。
- **不提交原始音视频、CSV、JSON 或压缩包**：仓库约定禁止把资料和录音放入 Git；多数数据还是 CC BY-NC/ND 或影视版权数据，提交即构成再分发风险。
- 用清单、详细说明和获取命令代替原始数据；实际下载统一放 `data/datasets/`（已被忽略）。

## 实际变更

- `datasets/README.md`：数据集结论、快速选择、优先级定义、原始数据规则、复核证据和新增检查清单。
- `datasets/catalog.csv`：22 条候选的机器可读清单，含语言、域、模态、规模、标签、获取方式、许可、优先级、论文和仓库。
- `datasets/zh-speech-emotion.md`：8 个可获取的中文带语音语料、5 个仅论文可查语料、获取步骤、推荐组合和剔除清单。
- `datasets/text-support.md`：ESConv、CPED 的详细统计和使用边界，以及 JDDC、EmoTwiCS、CusEmo、MELD、EmpatheticDialogues、CH-SIMS 等文本参考。
- `datasets/.gitignore`：阻止原始音频、视频、压缩包、CSV/JSON 误入 Git，仅保留 `catalog.csv`。
- 本日志。
- 无业务代码、契约、数据库、提示词或部署配置变化。

## 验证证据

- `Import-Csv datasets/catalog.csv`：22 行、13 列，无空值；优先级分布 A=2、A-aux=2、B=5、C=13。
- `git check-ignore -v datasets/catalog.csv`：命中 `datasets/.gitignore` 的 `!catalog.csv` 例外，清单可被跟踪。
- ESConv 与 CPED 的计数沿用 2026-11-08 的实际文件核对：ESConv 1,300 段对话、38,365 轮、18,376 条策略标注、FailedESConv 196 条；CPED 132,762 句、11,835 个对话、303 个唯一 Speaker。
- 未执行：没有完整下载所有语料；没有验证 gated 申请；没有做许可法律意见；没有运行应用测试（本次仅新增数据集文档）。

## 交付与回退

- 交付文件：`datasets/` 下 5 个文件与本日志。
- 提交：本地分支 `Lruy-work`，提交信息 `docs: add emotion dataset catalog`；未推送。
- 查询：`git log --all -- docs/devlogs/2026-11-08/234011-dataset-catalog-b3f7a1c2.md`。
- 回退：revert 本次提交即可；不涉及业务代码、数据库、模型或外部工具副作用。
- 原始数据未下载进仓库；如后续下载，位置为 `data/datasets/`，不会进入 Git。

## 待办与交接

- 团队成员按 `datasets/zh-speech-emotion.md` 获取数据；先确认磁盘、HF 账号和许可。
- 法务/团队复核 EmotionTalk、MER2023/2024、ESD、EMOVIE、ESConv、CPED 的许可范围。
- 需要真实客服阈值时，另行准备 200—500 通获准脱敏通话；公开语料不能替代。
