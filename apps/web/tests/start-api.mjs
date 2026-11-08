import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const root = resolve('../..');
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const child = spawn(python, ['-m', 'uvicorn', 'services.api.app:create_app', '--factory', '--host', '127.0.0.1', '--port', '18090'], {
  cwd: root, stdio: 'inherit', env: { ...process.env, ZHIYU_MODE: 'mock', ZHIYU_API_TOKEN: '',
    ZHIYU_DB: resolve(root, `runtime/browser-${Date.now()}-${process.pid}.sqlite`) },
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('exit', code => process.exit(code ?? 1));
child.on('error', error => { console.error(error); process.exit(1); });
