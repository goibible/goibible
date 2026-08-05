#!/usr/bin/env python3
"""Atomize the VIE1934 USFM reference into GOI-style one-verse files."""
from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
USFM_DIR = ROOT / "SOURCE" / "usfm"
OUT_DIR = ROOT / "One_Directory_VIE1934"

OLD_TESTAMENT = [
    ("GEN", "001", "02-GENvie1934.usfm"),
    ("EXO", "002", "03-EXOvie1934.usfm"),
    ("LEV", "003", "04-LEVvie1934.usfm"),
    ("NUM", "004", "05-NUMvie1934.usfm"),
    ("DEU", "005", "06-DEUvie1934.usfm"),
    ("JOS", "006", "07-JOSvie1934.usfm"),
    ("JDG", "007", "08-JDGvie1934.usfm"),
    ("RUT", "008", "09-RUTvie1934.usfm"),
    ("1SA", "009", "10-1SAvie1934.usfm"),
    ("2SA", "010", "11-2SAvie1934.usfm"),
    ("1KI", "011", "12-1KIvie1934.usfm"),
    ("2KI", "012", "13-2KIvie1934.usfm"),
    ("1CH", "013", "14-1CHvie1934.usfm"),
    ("2CH", "014", "15-2CHvie1934.usfm"),
    ("EZR", "015", "16-EZRvie1934.usfm"),
    ("NEH", "016", "17-NEHvie1934.usfm"),
    ("EST", "017", "18-ESTvie1934.usfm"),
    ("JOB", "018", "19-JOBvie1934.usfm"),
    ("PSA", "019", "20-PSAvie1934.usfm"),
    ("PRO", "020", "21-PROvie1934.usfm"),
    ("ECC", "021", "22-ECCvie1934.usfm"),
    ("SNG", "022", "23-SNGvie1934.usfm"),
    ("ISA", "023", "24-ISAvie1934.usfm"),
    ("JER", "024", "25-JERvie1934.usfm"),
    ("LAM", "025", "26-LAMvie1934.usfm"),
    ("EZK", "026", "27-EZKvie1934.usfm"),
    ("DAN", "027", "28-DANvie1934.usfm"),
    ("HOS", "028", "29-HOSvie1934.usfm"),
    ("JOL", "029", "30-JOLvie1934.usfm"),
    ("AMO", "030", "31-AMOvie1934.usfm"),
    ("OBA", "031", "32-OBAvie1934.usfm"),
    ("JON", "032", "33-JONvie1934.usfm"),
    ("MIC", "033", "34-MICvie1934.usfm"),
    ("NAM", "034", "35-NAMvie1934.usfm"),
    ("HAB", "035", "36-HABvie1934.usfm"),
    ("ZEP", "036", "37-ZEPvie1934.usfm"),
    ("HAG", "037", "38-HAGvie1934.usfm"),
    ("ZEC", "038", "39-ZECvie1934.usfm"),
    ("MAL", "039", "40-MALvie1934.usfm"),
]

NEW_TESTAMENT = [
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


def selected_books(scope: str, requested_books: set[str]) -> list[tuple[str, str, str]]:
    if scope == "ot":
        books = OLD_TESTAMENT
    elif scope == "nt":
        books = NEW_TESTAMENT
    else:
        books = OLD_TESTAMENT + NEW_TESTAMENT

    if requested_books:
        books = [book for book in books if book[0] in requested_books]
    return books


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("ot", "nt", "all"), default="all")
    parser.add_argument(
        "--book",
        action="append",
        default=[],
        help="Limit to a USFM book code. May be repeated, e.g. --book GEN --book PSA.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing VIE1934 atomized files for the selected books before writing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    requested_books = {book.upper() for book in args.book}
    books = selected_books(args.scope, requested_books)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for book_code, conical, _filename in books:
            for old in OUT_DIR.glob(f"{conical}_{book_code}_*_VIE1934.txt"):
                old.unlink()

    total = 0
    for book_code, conical, filename in books:
        count = atomize_book(book_code, conical, filename)
        print(f"{book_code}: {count}")
        total += count
    print(f"TOTAL: {total}")


if __name__ == "__main__":
    main()
