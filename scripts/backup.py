import argparse
from pathlib import Path

from packages.storage.sqlite import Store


def main():
    parser = argparse.ArgumentParser(description="Create a consistent SQLite backup without overwriting")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("source database does not exist")
    Store(args.source).backup(args.destination)
    print("Backup verified:", args.destination)


if __name__ == "__main__":
    main()
