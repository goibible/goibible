#!/usr/bin/env python3
"""Atomize the VIE1934 NT USFM reference into GOI-style one-verse files."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
USFM_DIR = ROOT / "SOURCE" / "usfm"
OUT_DIR = ROOT / "One_Directory_VIE1934"

BOOKS = [
    ("MAT", "040", "70-MATvie1934.usfm"),
    ("MRK", "041", "71-MRKvie1934.usfm"),
    ("LUK", "042", "72-LUKvie1934.usfm"),
    ("JHN", "043", "73-JHNvie1934.usfm"),
    ("ACT", "044", "74-ACTvie1934.usfm"),
    ("ROM", "045", "75-ROMvie1934.usfm"),
    ("1CO", "046", "76-1COvie1934.usfm"),
    ("2CO", "047", "77-2COvie1934.usfm"),
    ("GAL", "048", "78-GALvie1934.usfm"),
    ("EPH", "049", "79-EPHvie1934.usfm"),
    ("PHP", "050", "80-PHPvie1934.usfm"),
    ("COL", "051", "81-COLvie1934.usfm"),
    ("1TH", "052", "82-1THvie1934.usfm"),
    ("2TH", "053", "83-2THvie1934.usfm"),
    ("1TI", "054", "84-1TIvie1934.usfm"),
    ("2TI", "055", "85-2TIvie1934.usfm"),
    ("TIT", "056", "86-TITvie1934.usfm"),
    ("PHM", "057", "87-PHMvie1934.usfm"),
    ("HEB", "058", "88-HEBvie1934.usfm"),
    ("JAS", "059", "89-JASvie1934.usfm"),
    ("1PE", "060", "90-1PEvie1934.usfm"),
    ("2PE", "061", "91-2PEvie1934.usfm"),
    ("1JN", "062", "92-1JNvie1934.usfm"),
    ("2JN", "063", "93-2JNvie1934.usfm"),
    ("3JN", "064", "94-3JNvie1934.usfm"),
    ("JUD", "065", "95-JUDvie1934.usfm"),
    ("REV", "066", "96-REVvie1934.usfm"),
]

VERSE_MARKER = re.compile(r"\\v\s+(\d+)\s+")
CHAPTER_MARKER = re.compile(r"\\c\s+(\d+)")
STRIP_MARKERS = re.compile(r"\\[a-z0-9*]+(?:\s+)?")


def clean_verse(text: str) -> str:
    text = STRIP_MARKERS.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def atomize_book(book_code: str, conical: str, filename: str) -> int:
    raw = (USFM_DIR / filename).read_text(encoding="utf-8-sig")
    current_chapter = None
    current_verse = None
    buffer: list[str] = []
    written = 0

    def flush() -> None:
        nonlocal written
        if current_chapter is None or current_verse is None:
            return
        verse_text = clean_verse(" ".join(buffer))
        if not verse_text:
            return
        out = OUT_DIR / f"{conical}_{book_code}_{current_chapter:03d}_{current_verse:03d}_VIE1934.txt"
        out.write_text(verse_text + "\n", encoding="utf-8")
        written += 1

    for line in raw.splitlines():
        chapter_match = CHAPTER_MARKER.match(line)
        if chapter_match:
            flush()
            current_chapter = int(chapter_match.group(1))
            current_verse = None
            buffer = []
            continue

        verse_match = VERSE_MARKER.match(line)
        if verse_match:
            flush()
            current_verse = int(verse_match.group(1))
            buffer = [line[verse_match.end() :]]
            continue

        if current_verse is not None:
            buffer.append(line)

    flush()
    return written


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.txt"):
        old.unlink()
    total = 0
    for book_code, conical, filename in BOOKS:
        count = atomize_book(book_code, conical, filename)
        print(f"{book_code}: {count}")
        total += count
    print(f"TOTAL: {total}")


if __name__ == "__main__":
    main()
