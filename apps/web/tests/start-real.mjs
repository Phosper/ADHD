import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const root = resolve('../..');
const python = resolve(root, process.platform === 'win32' ? '.voice/Scripts/python.exe' : '.voice/bin/python');
const env = { ...process.env, LOGURU_LEVEL: 'WARNING', ZHIYU_MODE: 'real', ZHIYU_VOICE_ENABLED: '1', ZHIYU_API_TOKEN: '',
  ZHIYU_MODEL_MANIFEST: resolve(root, 'runtime/model-manifest.json'),
  ZHIYU_DB: resolve(root, `runtime/real-voice-${Date.now()}.sqlite`) };
const api = spawn(python, ['-m','uvicorn','services.api.app:create_app','--factory','--host','127.0.0.1','--port','18093'], {cwd:root,stdio:'inherit',env});
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => api.kill(signal));
api.on('exit', code => process.exit(code ?? 1));
