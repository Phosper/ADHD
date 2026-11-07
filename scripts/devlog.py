import argparse
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="短主题，仅使用英文、数字和连字符")
    args = parser.parse_args()
    if not args.topic or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in args.topic):
        parser.error("topic must use lowercase letters, digits and hyphens")
    root = Path(__file__).resolve().parents[1]
    now = datetime.now(timezone(timedelta(hours=8)))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    path = root / "docs/devlogs" / now.strftime("%Y-%m-%d") / f"{now:%H%M%S}-{args.topic}-{uuid4().hex[:8]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(f"# {args.topic}\n\n- 开始：{now.isoformat()}\n- 起始提交：{head}\n- 状态：进行中\n\n"
                     "## 需求与实际变更\n\n待记录。\n\n## 验证\n\n未执行。\n\n## 回退与交接\n\n待记录。\n")
    print(path)


if __name__ == "__main__":
    main()
