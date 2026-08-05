#!/usr/bin/env python3
"""Build app-facing SQLite DB downloads from sqlite/versions/*.sql."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
META = REPO_ROOT / "Meta_Bible_Data"
SQLITE_DIR = META / "sqlite"
SOURCE_DIR = SQLITE_DIR / "versions"
SHELL_DB = SQLITE_DIR / "goi_bible_shell.db"
OUT_DIR = META / "goi_db_download"
MANIFEST = OUT_DIR / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_scalar(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> object:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql, params).fetchone()[0]


def sqlite_row(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> tuple[object, ...]:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql, params).fetchone()


def build_db(edition_id: str, sql_path: Path, out_path: Path) -> None:
    if out_path.exists():
        out_path.unlink()

    shutil.copyfile(SHELL_DB, out_path)
    with sql_path.open("rb") as sql_file:
        subprocess.run(["sqlite3", str(out_path)], stdin=sql_file, check=True)
    with sqlite3.connect(out_path) as conn:
        conn.execute("DELETE FROM editions WHERE edition_id <> ?", (edition_id,))
    subprocess.run(["sqlite3", str(out_path), "VACUUM;"], check=True)

    verse_count = sqlite_scalar(
        out_path,
        "SELECT count(*) FROM verses WHERE edition_id = ?",
        (edition_id,),
    )
    if not isinstance(verse_count, int) or verse_count <= 0:
        raise RuntimeError(f"{edition_id} built with no verses")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("editions", nargs="*", help="optional edition_id list; default builds every sqlite/versions/*.sql")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    sql_paths = sorted(SOURCE_DIR.glob("*.sql"))
    requested = set(args.editions)
    if args.editions:
        found = {path.stem for path in sql_paths if path.stem in requested}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(f"missing sqlite/versions SQL for: {', '.join(missing)}")

    for sql_path in sql_paths:
        edition_id = sql_path.stem
        out_path = OUT_DIR / f"{edition_id}.db"
        if not requested or edition_id in requested or not out_path.exists():
            build_db(edition_id, sql_path, out_path)

        bcp47_tag, language_subtag, display_name, status = sqlite_row(
            out_path,
            (
                "SELECT bcp47_tag, language_subtag, display_name, status "
                "FROM editions WHERE edition_id = ?"
            ),
            (edition_id,),
        )
        verse_count = sqlite_scalar(
            out_path,
            "SELECT count(*) FROM verses WHERE edition_id = ?",
            (edition_id,),
        )

        entries.append(
            {
                "edition_id": edition_id,
                "display_name": display_name,
                "bcp47_tag": bcp47_tag,
                "language_subtag": language_subtag,
                "status": status,
                "file": f"{edition_id}.db",
                "size_bytes": out_path.stat().st_size,
                "sha256": sha256(out_path),
                "verse_count": verse_count,
            }
        )

    manifest = {
        "format": "goi-sqlite-edition-db",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "shell_db": "Meta_Bible_Data/sqlite/goi_bible_shell.db",
            "sql_dir": "Meta_Bible_Data/sqlite/versions",
        },
        "editions": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    for entry in entries:
        print(f"{entry['file']}: {entry['verse_count']} verses")
    print(f"Wrote {MANIFEST.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
