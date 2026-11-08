"""Stop only this project's verified model supervisor; never kill by a broad name."""
import os
import signal
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'runtime/models-supervisor.pid'
    if not path.exists():
        print('No supervisor PID file')
        return
    pid = int(path.read_text())
    proc = Path('/proc') / str(pid)
    if not proc.exists():
        print('Supervisor already stopped')
        return
    args = (proc / 'cmdline').read_bytes().split(b'\0')
    if b'scripts.serve_models' not in args or (proc / 'cwd').resolve() != root:
        raise RuntimeError('PID no longer belongs to this project; refusing stop')
    os.kill(pid, signal.SIGTERM)
    print('Stop requested for verified project supervisor')


if __name__ == '__main__':
    main()
