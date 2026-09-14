#!/usr/bin/env python3
"""Verify canonical flatfiles, published download DBs, and their manifest.

This is deliberately read-only. Run it before every release and in CI. It
rejects zero-byte verses, malformed/duplicate coordinates, catalog/manifest
status drift, stale checksums, and text drift between a canonical flatfile and
its downloadable SQLite database.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "Meta_Bible_Data/sqlite/editions.json"
MANIFEST_PATH = ROOT / "Meta_Bible_Data/goi_db_download/manifest.json"
DOWNLOAD_DIR = MANIFEST_PATH.parent


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def corpus(config: dict[str, object]) -> dict[tuple[int, str, int, int], str]:
    edition_id = str(config["edition_id"])
    suffix = str(config.get("filename_suffix", edition_id))
    directory = ROOT / str(config["flatfile_dir"])
    pattern = re.compile(rf"(\d{{3}})_([123]?[A-Z]{{2,3}})_(\d{{3}})_(\d{{3}})_{re.escape(suffix)}\.txt$")
    allowed_empty = set(config.get("allowed_empty_coordinates", []))
    problems: list[str] = []
    verses: dict[tuple[int, str, int, int], str] = {}
    for path in sorted(directory.glob("*.txt")):
        match = pattern.fullmatch(path.name)
        if not match:
            problems.append(f"malformed filename {path.relative_to(ROOT)}")
            continue
        key = (int(match.group(1)), match.group(2), int(match.group(3)), int(match.group(4)))
        coordinate = "_".join((match.group(1), match.group(2), match.group(3), match.group(4)))
        text = path.read_text(encoding="utf-8").strip()
        if not text and coordinate not in allowed_empty:
            problems.append(f"empty verse {path.relative_to(ROOT)}")
            continue
        if key in verses:
            problems.append(f"duplicate coordinate {key} in {directory.relative_to(ROOT)}")
        verses[key] = text
    expected = config.get("expected_verse_count")
    if not isinstance(expected, int) or expected <= 0:
        problems.append(f"{edition_id}: missing positive expected_verse_count in catalog")
    elif len(verses) != expected:
        problems.append(f"{edition_id}: {len(verses)} coordinates, expected {expected}")
    if problems:
        raise ValueError("\n  ".join(problems))
    return verses


def database_verses(path: Path, edition_id: str) -> dict[tuple[int, str, int, int], str]:
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT conical, book, chapter, verse, verse_text FROM verses WHERE edition_id=?",
            (edition_id,),
        ).fetchall()
    result: dict[tuple[int, str, int, int], str] = {}
    for conical, book, chapter, verse, text in rows:
        key = (int(conical), str(book), int(chapter), int(verse))
        if key in result:
            raise ValueError(f"{edition_id}: duplicate DB coordinate {key}")
        result[key] = str(text).strip()
    return result


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = {entry["edition_id"]: entry for entry in manifest["editions"]}
    failures: list[str] = []
    checked = 0
    for config in catalog:
        if config.get("status") != "active":
            continue
        edition_id = str(config["edition_id"])
        try:
            flat = corpus(config)
            entry = entries.get(edition_id)
            if entry is None:
                raise ValueError("missing from download manifest")
            if entry.get("status") != "active":
                raise ValueError(f"manifest status is {entry.get('status')!r}, expected active")
            db_path = DOWNLOAD_DIR / str(entry["file"])
            if not db_path.is_file() or db_path.stat().st_size == 0:
                raise ValueError(f"missing or empty download DB {db_path.relative_to(ROOT)}")
            if entry.get("sha256") != digest(db_path):
                raise ValueError("download DB checksum differs from manifest")
            db = database_verses(db_path, edition_id)
            if flat != db:
                missing = len(set(flat) - set(db))
                extra = len(set(db) - set(flat))
                changed = sum(1 for key in set(flat) & set(db) if flat[key] != db[key])
                raise ValueError(f"flatfile/DB drift: missing={missing}, extra={extra}, changed={changed}")
            if entry.get("verse_count") != len(flat):
                raise ValueError(f"manifest verse_count {entry.get('verse_count')} != {len(flat)}")
            print(f"OK {edition_id}: {len(flat)} canonical verses match download DB")
            checked += 1
        except (OSError, ValueError, sqlite3.Error, UnicodeError) as exc:
            failures.append(f"{edition_id}: {exc}")
    if failures:
        print("RELEASE INTEGRITY FAILED", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"RELEASE INTEGRITY OK: {checked} active editions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
