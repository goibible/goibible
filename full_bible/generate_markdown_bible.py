#!/usr/bin/env python3
"""Generate full Bible markdown files from GOI edition verse flatfiles.

The exporter uses `GOI_bible.sqlite3` for canonical ordering and edition
metadata, then reads verse text from the existing flatfile corpora:

  - GOI_En -> GOI_Bible_English/
  - GOI_Zh_Hant -> GOI_Bible_Chinese_Hant/
  - GOI_Zh_Hans -> GOI_Bible_Chinese_Hans/

Markdown format:

  # GENESIS
  
  ## Chapter 1
  
  1 In the beginning ...
  
  2 And the earth ...

Book names come from the database `books.long_name` column and are rendered in
uppercase. Verse text is normalized to a single line per verse.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import sys
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "GOI_bible.sqlite3"
OUTPUT_DIR = ROOT / "full_bible"

SUPPORTED_EDITIONS = {
    "goi_en": "GOI_En",
    "goi_zh_hant": "GOI_Zh_Hant",
    "goi_zh_hans": "GOI_Zh_Hans",
}

SOURCE_DIRS = {
    "GOI_En": ROOT / "GOI_Bible_English",
    "GOI_Zh_Hant": ROOT / "GOI_Bible_Chinese_Hant",
    "GOI_Zh_Hans": ROOT / "GOI_Bible_Chinese_Hans",
}


@dataclass(frozen=True)
class Edition:
    edition_id: str
    display_name: str
    source_dir: pathlib.Path


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def canonical_edition_id(raw: str) -> str:
    key = raw.strip().lower()
    if key in SUPPORTED_EDITIONS:
        return SUPPORTED_EDITIONS[key]
    for canonical in SOURCE_DIRS:
        if canonical.lower() == key:
            return canonical
    raise SystemExit(f"Unknown or unsupported edition: {raw!r}")


def load_edition(conn: sqlite3.Connection, edition_id: str) -> Edition:
    row = conn.execute(
        "SELECT edition_id, display_name, status FROM editions WHERE edition_id = ?",
        (edition_id,),
    ).fetchone()
    if row is None:
        raise SystemExit(f"Edition not found in GOI_bible.sqlite3: {edition_id}")
    db_edition_id, display_name, status = row
    if status != "active":
        raise SystemExit(f"Edition is not active: {edition_id} ({status})")
    source_dir = SOURCE_DIRS.get(db_edition_id)
    if source_dir is None:
        raise SystemExit(f"No flatfile source directory configured for edition: {edition_id}")
    if not source_dir.exists():
        raise SystemExit(f"Source directory does not exist: {source_dir}")
    return Edition(db_edition_id, display_name, source_dir)


def output_name_for(display_name: str, edition_id: str) -> str:
    prefix = "GOI Bible "
    if display_name.startswith(prefix):
        suffix = display_name[len(prefix) :].strip()
        if suffix:
            return f"GOI_{suffix.replace(' ', '_')}_Bible.md"
    return f"{edition_id}.md"


def export_markdown(conn: sqlite3.Connection, edition: Edition, output_dir: pathlib.Path, overwrite: bool) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name_for(edition.display_name, edition.edition_id)
    if output_path.exists() and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {output_path}")

    book_rows = conn.execute(
        "SELECT conical, long_name FROM books ORDER BY conical"
    ).fetchall()
    book_name_by_order = {conical: long_name for conical, long_name in book_rows}

    verse_rows = conn.execute(
        """
        SELECT v.conical, v.chapter, v.verse, v.filename_key
        FROM verses v
        WHERE v.edition_id = ?
        ORDER BY v.conical, v.chapter, v.verse
        """,
        (edition.edition_id,),
    )

    current_book = None
    current_chapter = None
    written_verses = 0

    with output_path.open("w", encoding="utf-8", newline="\n") as fh:
        for conical, chapter, verse, filename_key in verse_rows:
            if conical != current_book:
                if written_verses:
                    fh.write("\n")
                book_name = book_name_by_order.get(conical)
                if book_name is None:
                    raise SystemExit(f"Missing book metadata for canonical order {conical}")
                fh.write(f"# {book_name.upper()}\n\n")
                current_book = conical
                current_chapter = None

            if chapter != current_chapter:
                if current_chapter is not None:
                    fh.write("\n")
                fh.write(f"## Chapter {chapter}\n\n")
                current_chapter = chapter

            verse_path = edition.source_dir / f"{filename_key}.txt"
            if not verse_path.exists():
                raise SystemExit(f"Missing verse file: {verse_path}")
            verse_text = normalize_text(verse_path.read_text(encoding="utf-8").strip())
            fh.write(f"{verse} {verse_text}\n\n")
            written_verses += 1

    return output_path


def resolve_editions(conn: sqlite3.Connection, requested: list[str] | None, all_flag: bool) -> list[Edition]:
    if all_flag:
        requested_ids = list(SUPPORTED_EDITIONS.values())
    else:
        if not requested:
            raise SystemExit("Specify one or more --edition values, or use --all.")
        requested_ids = [canonical_edition_id(item) for item in requested]

    editions: list[Edition] = []
    seen: set[str] = set()
    for edition_id in requested_ids:
        if edition_id in seen:
            continue
        seen.add(edition_id)
        editions.append(load_edition(conn, edition_id))
    return editions


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate full Bible markdown files.")
    ap.add_argument(
        "--edition",
        action="append",
        help="Edition id to export, e.g. GOI_En. May be repeated.",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="Export all supported GOI editions.",
    )
    ap.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=OUTPUT_DIR,
        help="Directory to write markdown files into.",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing markdown files.",
    )
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        editions = resolve_editions(conn, args.edition, args.all)
        for edition in editions:
            output_path = export_markdown(conn, edition, args.output_dir, args.overwrite)
            print(f"Wrote {output_path}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
