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

# Standard book names by OSIS code, for editions whose book titles must not
# fall back to the English `books.long_name` column.
BOOK_NAMES_ZH_HANT = {
    "GEN": "創世記", "EXO": "出埃及記", "LEV": "利未記", "NUM": "民數記",
    "DEU": "申命記", "JOS": "約書亞記", "JDG": "士師記", "RUT": "路得記",
    "1SA": "撒母耳記上", "2SA": "撒母耳記下", "1KI": "列王紀上", "2KI": "列王紀下",
    "1CH": "歷代志上", "2CH": "歷代志下", "EZR": "以斯拉記", "NEH": "尼希米記",
    "EST": "以斯帖記", "JOB": "約伯記", "PSA": "詩篇", "PRO": "箴言",
    "ECC": "傳道書", "SNG": "雅歌", "ISA": "以賽亞書", "JER": "耶利米書",
    "LAM": "耶利米哀歌", "EZK": "以西結書", "DAN": "但以理書", "HOS": "何西阿書",
    "JOL": "約珥書", "AMO": "阿摩司書", "OBA": "俄巴底亞書", "JON": "約拿書",
    "MIC": "彌迦書", "NAM": "那鴻書", "HAB": "哈巴谷書", "ZEP": "西番雅書",
    "HAG": "哈該書", "ZEC": "撒迦利亞書", "MAL": "瑪拉基書",
    "MAT": "馬太福音", "MRK": "馬可福音", "LUK": "路加福音", "JHN": "約翰福音",
    "ACT": "使徒行傳", "ROM": "羅馬書", "1CO": "哥林多前書", "2CO": "哥林多後書",
    "GAL": "加拉太書", "EPH": "以弗所書", "PHP": "腓立比書", "COL": "歌羅西書",
    "1TH": "帖撒羅尼迦前書", "2TH": "帖撒羅尼迦後書", "1TI": "提摩太前書",
    "2TI": "提摩太後書", "TIT": "提多書", "PHM": "腓利門書", "HEB": "希伯來書",
    "JAS": "雅各書", "1PE": "彼得前書", "2PE": "彼得後書", "1JN": "約翰一書",
    "2JN": "約翰二書", "3JN": "約翰三書", "JUD": "猶大書", "REV": "啟示錄",
}

BOOK_NAMES_ZH_HANS = {
    "GEN": "创世记", "EXO": "出埃及记", "LEV": "利未记", "NUM": "民数记",
    "DEU": "申命记", "JOS": "约书亚记", "JDG": "士师记", "RUT": "路得记",
    "1SA": "撒母耳记上", "2SA": "撒母耳记下", "1KI": "列王纪上", "2KI": "列王纪下",
    "1CH": "历代志上", "2CH": "历代志下", "EZR": "以斯拉记", "NEH": "尼希米记",
    "EST": "以斯帖记", "JOB": "约伯记", "PSA": "诗篇", "PRO": "箴言",
    "ECC": "传道书", "SNG": "雅歌", "ISA": "以赛亚书", "JER": "耶利米书",
    "LAM": "耶利米哀歌", "EZK": "以西结书", "DAN": "但以理书", "HOS": "何西阿书",
    "JOL": "约珥书", "AMO": "阿摩司书", "OBA": "俄巴底亚书", "JON": "约拿书",
    "MIC": "弥迦书", "NAM": "那鸿书", "HAB": "哈巴谷书", "ZEP": "西番雅书",
    "HAG": "哈该书", "ZEC": "撒迦利亚书", "MAL": "玛拉基书",
    "MAT": "马太福音", "MRK": "马可福音", "LUK": "路加福音", "JHN": "约翰福音",
    "ACT": "使徒行传", "ROM": "罗马书", "1CO": "哥林多前书", "2CO": "哥林多后书",
    "GAL": "加拉太书", "EPH": "以弗所书", "PHP": "腓立比书", "COL": "歌罗西书",
    "1TH": "帖撒罗尼迦前书", "2TH": "帖撒罗尼迦后书", "1TI": "提摩太前书",
    "2TI": "提摩太后书", "TIT": "提多书", "PHM": "腓利门书", "HEB": "希伯来书",
    "JAS": "雅各书", "1PE": "彼得前书", "2PE": "彼得后书", "1JN": "约翰一书",
    "2JN": "约翰二书", "3JN": "约翰三书", "JUD": "犹大书", "REV": "启示录",
}

BOOK_NAME_OVERRIDES_BY_EDITION = {
    "GOI_Zh_Hant": BOOK_NAMES_ZH_HANT,
    "GOI_Zh_Hans": BOOK_NAMES_ZH_HANS,
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
        "SELECT conical, osis, long_name FROM books ORDER BY conical"
    ).fetchall()
    overrides = BOOK_NAME_OVERRIDES_BY_EDITION.get(edition.edition_id)
    book_name_by_order = {
        conical: (overrides[osis] if overrides else long_name)
        for conical, osis, long_name in book_rows
    }

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
