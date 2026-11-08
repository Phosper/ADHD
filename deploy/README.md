# 部署与恢复

当前可运行：本机 Mock 文本工作台；A800 上 Qwen3-8B/FunASR/CosyVoice2 三服务。浏览器媒体管道已通过合成音测试，真实多轮与时延结果见开发日志，不以本文件代替验收。

## 本机文字模式

1. Python 3.10—3.13，Node 24；安装 uv 0.11.21。
2. 根目录 `uv sync --frozen`。
3. `apps/web` 下 `npm ci`、`npm run build`。
4. 根目录 `uv run python -m scripts.launch`，访问 `http://127.0.0.1:18080`。

只监听本机。若由团队运维改为远程监听，必须设置随机 ZHIYU_API_TOKEN，并提供受控 HTTPS。不要把访问令牌写入 Git 或链接参数。

## 真实模型（Linux A800）

独立目录：`/home/liuph/zhiyu-outbound`。`.core` 是业务 Python 3.10，`.models-env` 是模型 Python 3.10；不修改服务器其他环境。实际依赖为 `models-linux.lock`，安装时带 `--build-constraint deploy/build-constraints.txt`。这是当前实测平台锁，不宣称适用于任意显卡和驱动。

1. 获取官方 CosyVoice 源码提交 `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` 至 vendor/CosyVoice，子模块 Matcha-TTS 提交 `dd9105b34bf2be2230f4aa1e4769fb586a3c824e`。
2. 以模型环境执行 `python -m scripts.download_models`，下载指定公开仓库；生成每文件 SHA-256 清单。后续部署应复用已验收权重及清单，不能默默用最新权重覆盖。
3. `python -m scripts.serve_models` 以前台监督方式启动 18081/18082/18083，均仅环回监听。任何一个服务退出会停止这次启动的其他子进程；不会停止其他项目。常驻运行可交由团队现有进程管理器，不能把临时 SSH 会话当可靠服务。
4. `python -m scripts.doctor --health` 检查三项服务。`python -m scripts.smoke_models` 生成合成录音、流式转写和推理结果；保存 runtime/model-smoke。
5. 业务环境执行 `python -m scripts.warm_tts`，从状态机生成固定话术缓存。冷/热/缓存测量须分开。`python -m scripts.model_manifest` 输出会话绑定清单。
6. 停止本项目使用 `python -m scripts.stop_models`，它核对 PID 的命令及工作目录。不要广泛 kill Python/GPU 进程。

## 浏览器真实语音（研发路径）

本机独立 `.voice` 环境安装 `deploy/voice-windows.lock`（实测 Windows Python 3.13），然后用 `.voice/Scripts/python.exe -m scripts.launch --real`。

设置 `ZHIYU_MODEL_MANIFEST` 指向已下载的 runtime/model-manifest.json。模型 URL 默认 127.0.0.1:18081/v1、18082、18083；校园研发通过已授权 SSH 本地端口转发连接服务器环回服务。浏览器与本机 Pipecat 使用 WebRTC；模型推理在 A800。无第三方穿透、无公网开放、无真实电话号码外呼。

上述 SSH 方案未取得赛场许可，只能称研发路径。用户已确认赛场网络方式与官方 Mock 接口都未确认，不能据此标记比赛就绪。

## 验证、日志和回退

- 后端：`python -m scripts.verify`；开发集：`python -m evals.run_text`。
- 浏览器文字：apps/web 下 `npx playwright test`；合成音传输：`npx playwright test --config playwright.voice.config.ts`。
- 真实模型合成语音：准备 runtime/real-input/0.wav—3.wav 后执行 `npx playwright test --config playwright.real.config.ts`。这是合成输入联调，不是人声、噪声或官方最终验收。
- 每通记录在 ZHIYU_DB SQLite 中，页面可导出会话、事件、版本与报告。运行日志/数据库/模型/音频不进入 Git。
- 经授权测试时可设置 ZHIYU_RECORD_AUDIO=1，录音保存在 runtime/audio/<session_id>，每份有采样率、长度和 SHA-256。输出 PCM 是生成证据，不能替代播放回执。默认关闭录音。
- 备份：`python -m scripts.backup <当前库> <新备份路径>`；恢复：`python -m scripts.restore <备份> <全新隔离库路径>`。恢复不会覆盖运行库、执行工具或重发回执。
- 回放：`python -m scripts.replay <数据库> <session_id>`，只读。
- 代码用新 revert 提交保留审计，模型切换回已锁定文件；数据库与外部工具补偿独立处理。

Dockerfile.mock 已提供，当前 Docker 构建未执行；镜像基础标签未冻结 digest，不能标成已验证的容器发布包。使用本机/服务器上述实测环境运行。

## 源码交付与版本追溯

干净 Git 检出中执行 `python -m scripts.package_source runtime/source-<版本>.tar`，得到源码归档和旁置 SHA-256 元数据。解压到新的独立目录，不覆盖运行实例；包内 .source-manifest.json 逐文件绑定提交。运行会话会检查源码变化，不会把父目录 Git 提交冒充当前版本。归档不包含模型、vendor、网页构建产物或私密运行数据，安装和前端构建仍按上述步骤执行。

将服务器现有权重用于新源码副本前，核对模型清单；不要复制旧数据库或重放工具回执来模拟新一次成功。更换运行副本、数据库恢复、模型回退分别留记录。
