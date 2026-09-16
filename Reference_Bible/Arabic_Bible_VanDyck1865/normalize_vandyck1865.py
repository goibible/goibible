#!/usr/bin/env python3
"""Normalize the preserved Arabic Van Dyck USFM into the GOI/KJV spine.

The raw eBible archive is never modified.  This normalizer writes one UTF-8
reference file per GOI coordinate.  Van Dyck has two final-verse divisions
that differ from the GOI/KJV spine; both are deliberately merged here and in
``alignment_exceptions.csv``.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "arb-vd_usfm.zip"
OUTPUT = HERE / "One_Directory_VanDyck1865_GOI"
EDITION = "VanDyck1865"

BOOK_NUMBERS = {
    book: number
    for number, book in enumerate(
        "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV".split(),
        start=1,
    )
}
VERSE_RE = re.compile(r"^\\v\s+(\d+)\s*(.*)$")
CHAPTER_RE = re.compile(r"^\\c\s+(\d+)\s*$")
BOOK_RE = re.compile(r"^\\id\s+(\S+)")

# (source coordinate) -> target coordinate.  Values not listed are exact.
MERGES = {
    ("1TI", 6, 21): ("1TI", 6, 21),
    ("1TI", 6, 22): ("1TI", 6, 21),
    ("3JN", 1, 14): ("3JN", 1, 14),
    ("3JN", 1, 15): ("3JN", 1, 14),
}


def read_usfm() -> dict[tuple[str, int, int], str]:
    if not SOURCE.is_file() or SOURCE.stat().st_size == 0:
        raise SystemExit(f"missing preserved source archive: {SOURCE}")
    verses: dict[tuple[str, int, int], str] = {}
    with zipfile.ZipFile(SOURCE) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".usfm"):
                continue
            book = None
            chapter = None
            for raw_line in archive.read(member).decode("utf-8").splitlines():
                if match := BOOK_RE.match(raw_line):
                    book = match.group(1)
                elif match := CHAPTER_RE.match(raw_line):
                    chapter = int(match.group(1))
                elif match := VERSE_RE.match(raw_line):
                    if not book or chapter is None:
                        raise ValueError(f"verse without book/chapter in {member}")
                    key = (book, chapter, int(match.group(1)))
                    text = match.group(2).strip()
                    if not text or key in verses:
                        raise ValueError(f"empty or duplicate source verse {key}")
                    verses[key] = text
    if len(verses) != 31_104 or len({key[0] for key in verses}) != 66:
        raise ValueError(f"unexpected Arabic source inventory: {len(verses)} verses")
    return verses


def expected_spine() -> set[tuple[str, int, int]]:
    database = ROOT / "Meta_Bible_Data" / "goi_db_download" / "KJV.db"
    with sqlite3.connect(database) as connection:
        return set(connection.execute(
            "SELECT book, chapter, verse FROM verses WHERE edition_id = 'KJV'"
        ))


def normalize(source: dict[tuple[str, int, int], str]) -> dict[tuple[str, int, int], str]:
    target: dict[tuple[str, int, int], list[str]] = defaultdict(list)
    for source_key, text in source.items():
        target[MERGES.get(source_key, source_key)].append(text)
    result = {key: " ".join(parts) for key, parts in target.items()}
    spine = expected_spine()
    if set(result) != spine:
        raise ValueError(
            f"normalization does not match GOI spine: "
            f"missing={len(spine - set(result))}, extra={len(set(result) - spine)}"
        )
    if len(result) != 31_102 or any(not value.strip() for value in result.values()):
        raise ValueError("invalid normalized output")
    return result


def write_output(verses: dict[tuple[str, int, int], str], output: Path) -> None:
    staging = output.with_name(output.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for book, chapter, verse in sorted(verses, key=lambda key: (BOOK_NUMBERS[key[0]], key[1], key[2])):
        filename = f"{BOOK_NUMBERS[book]:03d}_{book}_{chapter:03d}_{verse:03d}_{EDITION}.txt"
        (staging / filename).write_text(verses[(book, chapter, verse)] + "\n", encoding="utf-8")
    if output.exists():
        shutil.rmtree(output)
    staging.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify source and existing normalized output without writing")
    args = parser.parse_args()
    normalized = normalize(read_usfm())
    if args.check:
        files = sorted(OUTPUT.glob(f"*_{EDITION}.txt"))
        if len(files) != len(normalized):
            raise SystemExit(f"expected {len(normalized)} normalized files, found {len(files)}")
        expected_names = {
            f"{BOOK_NUMBERS[book]:03d}_{book}_{chapter:03d}_{verse:03d}_{EDITION}.txt": text + "\n"
            for (book, chapter, verse), text in normalized.items()
        }
        actual_names = {path.name for path in files}
        if actual_names != set(expected_names):
            raise SystemExit("normalized filenames do not match the GOI spine")
        for path in files:
            if path.read_text(encoding="utf-8") != expected_names[path.name]:
                raise SystemExit(f"normalized text differs from reproducible output: {path.name}")
        print(f"Arabic Van Dyck scaffold OK: 66 source books, 31,104 source verses -> {len(normalized)} GOI verses")
        return
    write_output(normalized, OUTPUT)
    print(f"Arabic Van Dyck scaffold written: 66 source books, 31,104 source verses -> {len(normalized)} GOI verses")


if __name__ == "__main__":
    main()
