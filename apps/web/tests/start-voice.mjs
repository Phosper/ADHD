import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const root = resolve('../..');
const python = resolve(root, process.platform === 'win32' ? '.voice/Scripts/python.exe' : '.voice/bin/python');
const env = { ...process.env, ZHIYU_MODE: 'real', ZHIYU_VOICE_ENABLED: '1', ZHIYU_API_TOKEN: '',
  ZHIYU_LLM_URL: 'http://127.0.0.1:18092/v1', ZHIYU_ASR_URL: 'http://127.0.0.1:18092', ZHIYU_TTS_URL: 'http://127.0.0.1:18092',
  ZHIYU_DB: resolve(root, `runtime/voice-fixture-${Date.now()}.sqlite`) };
const fixture = spawn(python, ['-m','uvicorn','tests.voice_fixture:app','--host','127.0.0.1','--port','18092'], {cwd:root,stdio:'inherit',env});
const api = spawn(python, ['-m','uvicorn','services.api.app:create_app','--factory','--host','127.0.0.1','--port','18091'], {cwd:root,stdio:'inherit',env});
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => { fixture.kill(signal); api.kill(signal); });
api.on('exit', code => {fixture.kill();process.exit(code ?? 1);});
