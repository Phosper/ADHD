"""Run deterministic checks with an isolated, workspace-owned temporary directory."""
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def main():
    root = Path(__file__).resolve().parents[1]
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    temp = runtime / ("tests-" + uuid4().hex)
    # A new UUID path is supplied; pytest never cleans another developer's work.
    commands = [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "pytest", "-q", "--tb=short", f"--basetemp={temp}"],
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
