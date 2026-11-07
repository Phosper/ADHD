import argparse
import json
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Read-only event replay; never invokes tools")
    parser.add_argument("database", type=Path)
    parser.add_argument("session_id")
    args = parser.parse_args()
    uri = args.database.resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        for row in db.execute("SELECT body FROM events WHERE session_id=? ORDER BY seq", (args.session_id,)):
            print(json.dumps(json.loads(row[0]), ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
