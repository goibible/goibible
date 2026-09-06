#!/usr/bin/env python3
"""Create the blank bible_video.sqlite3 database from schema.sql."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "bible_video.sqlite3"
SCHEMA = HERE / "schema.sql"


def init_db(db_path: Path = DEFAULT_DB, replace: bool = False) -> Path:
    if db_path.exists() and replace:
        db_path.unlink()
    if db_path.exists() and not replace:
        raise SystemExit(f"{db_path} already exists; pass --replace to recreate it.")

    sql = SCHEMA.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql)
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a blank bible_video.sqlite3 schema.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--replace", action="store_true", help="Delete and recreate the database.")
    args = parser.parse_args()

    db_path = init_db(args.db, args.replace)
    print(f"Initialized {db_path}")


if __name__ == "__main__":
    main()
