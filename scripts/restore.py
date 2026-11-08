"""Restore to a NEW isolated database. Never overwrite live state or replay tools."""
import argparse
import sqlite3
from pathlib import Path


def restore(source: Path, destination: Path):
    if not source.is_file():
        raise ValueError("Backup not found")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass  # Atomic exclusive reservation; existing databases cannot be overwritten.
    uri = source.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as src, sqlite3.connect(destination) as dst:
            if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Invalid backup")
            if src.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise ValueError("Unsupported database schema")
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Restore integrity check failed")
    except Exception:
        # Keep failed artifact for diagnosis; never silently replace another path.
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print("Isolated restore verified; no tools executed:", restore(args.source, args.destination))


if __name__ == "__main__":
    main()
