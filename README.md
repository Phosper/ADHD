# 智语外呼

赛道二基线工程。已实现可审计业务闭环、网页工作台、WebRTC、A800 三模型和资料导入；真实模型合成语音四轮与回写已通过。人声、声学时延、独立业务复核及比赛网络/接口尚未验收，B0 尚未冻结。实测与限制见 [基线自测报告](docs/基线自测报告.md)。

## 启动文本演示

Python 3.10—3.13、Node 24、uv 0.11.21。执行 `uv sync --frozen`，在 `apps/web` 执行 `npm ci`、`npm run build`，回到根目录运行 `uv run uvicorn services.api.app:create_app --factory --host 127.0.0.1 --port 18080`，浏览器访问 http://127.0.0.1:18080 。默认使用合成数据与 Mock 意图解析，不调用真实号码。

完整文本路径：我是负责人 → 方便，请说 → 我会补齐重新提交 → 确认。结果区应有四项确认及回写回执。运行 `uv run python -m scripts.verify` 检查后端；网页目录运行 `npx playwright test` 检查浏览器（本机需要 Chrome）。

## 团队入口

- [基线设计](docs/赛道二基线设计文档.md)：已确认的业务与技术方向。
- [项目文件规划](docs/项目文件规划.md)：目录、模块边界、接口与落地顺序。
- [团队协作规范](CONTRIBUTING.md)：分支、评审、验证与合并要求。
- [日志与回退](docs/日志与回退.md)：开发对话记录、运行会话日志、版本恢复。
- [实施任务](docs/任务看板.md)：按依赖推进，领取时填写实际负责人。
- [开发日志](docs/devlogs/README.md)：每次开发对话的变更依据与验证记录。
- [架构决策](docs/decisions/0001-module-boundaries.md)：已确定的工程边界。

## 已确认条件

服务器实际核验为 A800 80GB，通过校园网 SSH 访问，不开放公网；比赛网络路径尚未确认。开发机用浏览器通话。技术主线为 Pipecat、FunASR、Qwen3-8B、CosyVoice2，先完成文本业务闭环，再接实时语音。

业务资料放在被忽略的 `data/`，不上传公开仓库。资审关单工作簿只导入可见表“场景汇总”；隐藏表不自动参与规则决策。

开始工作前阅读根目录 `AGENTS.md` 与 `CONTRIBUTING.md`。目录 README 中列出的待建文件是规划，不代表已实现能力。
