#!/usr/bin/env python3
"""Atomize the RV1909 USFM reference into GOI-style one-verse files."""
from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
USFM_DIR = ROOT / "SOURCE" / "usfm"
OUT_DIR = ROOT / "One_Directory_RV1909"

OLD_TESTAMENT = [
    ("GEN", "001", "02-GENspaRV1909.usfm"),
    ("EXO", "002", "03-EXOspaRV1909.usfm"),
    ("LEV", "003", "04-LEVspaRV1909.usfm"),
    ("NUM", "004", "05-NUMspaRV1909.usfm"),
    ("DEU", "005", "06-DEUspaRV1909.usfm"),
    ("JOS", "006", "07-JOSspaRV1909.usfm"),
    ("JDG", "007", "08-JDGspaRV1909.usfm"),
    ("RUT", "008", "09-RUTspaRV1909.usfm"),
    ("1SA", "009", "10-1SAspaRV1909.usfm"),
    ("2SA", "010", "11-2SAspaRV1909.usfm"),
    ("1KI", "011", "12-1KIspaRV1909.usfm"),
    ("2KI", "012", "13-2KIspaRV1909.usfm"),
    ("1CH", "013", "14-1CHspaRV1909.usfm"),
    ("2CH", "014", "15-2CHspaRV1909.usfm"),
    ("EZR", "015", "16-EZRspaRV1909.usfm"),
    ("NEH", "016", "17-NEHspaRV1909.usfm"),
    ("EST", "017", "18-ESTspaRV1909.usfm"),
    ("JOB", "018", "19-JOBspaRV1909.usfm"),
    ("PSA", "019", "20-PSAspaRV1909.usfm"),
    ("PRO", "020", "21-PROspaRV1909.usfm"),
    ("ECC", "021", "22-ECCspaRV1909.usfm"),
    ("SNG", "022", "23-SNGspaRV1909.usfm"),
    ("ISA", "023", "24-ISAspaRV1909.usfm"),
    ("JER", "024", "25-JERspaRV1909.usfm"),
    ("LAM", "025", "26-LAMspaRV1909.usfm"),
    ("EZK", "026", "27-EZKspaRV1909.usfm"),
    ("DAN", "027", "28-DANspaRV1909.usfm"),
    ("HOS", "028", "29-HOSspaRV1909.usfm"),
    ("JOL", "029", "30-JOLspaRV1909.usfm"),
    ("AMO", "030", "31-AMOspaRV1909.usfm"),
    ("OBA", "031", "32-OBAspaRV1909.usfm"),
    ("JON", "032", "33-JONspaRV1909.usfm"),
    ("MIC", "033", "34-MICspaRV1909.usfm"),
    ("NAM", "034", "35-NAMspaRV1909.usfm"),
    ("HAB", "035", "36-HABspaRV1909.usfm"),
    ("ZEP", "036", "37-ZEPspaRV1909.usfm"),
    ("HAG", "037", "38-HAGspaRV1909.usfm"),
    ("ZEC", "038", "39-ZECspaRV1909.usfm"),
    ("MAL", "039", "40-MALspaRV1909.usfm"),
]

NEW_TESTAMENT = [
    ("MAT", "040", "70-MATspaRV1909.usfm"),
    ("MRK", "041", "71-MRKspaRV1909.usfm"),
    ("LUK", "042", "72-LUKspaRV1909.usfm"),
    ("JHN", "043", "73-JHNspaRV1909.usfm"),
    ("ACT", "044", "74-ACTspaRV1909.usfm"),
    ("ROM", "045", "75-ROMspaRV1909.usfm"),
    ("1CO", "046", "76-1COspaRV1909.usfm"),
    ("2CO", "047", "77-2COspaRV1909.usfm"),
    ("GAL", "048", "78-GALspaRV1909.usfm"),
    ("EPH", "049", "79-EPHspaRV1909.usfm"),
    ("PHP", "050", "80-PHPspaRV1909.usfm"),
    ("COL", "051", "81-COLspaRV1909.usfm"),
    ("1TH", "052", "82-1THspaRV1909.usfm"),
    ("2TH", "053", "83-2THspaRV1909.usfm"),
    ("1TI", "054", "84-1TIspaRV1909.usfm"),
    ("2TI", "055", "85-2TIspaRV1909.usfm"),
    ("TIT", "056", "86-TITspaRV1909.usfm"),
    ("PHM", "057", "87-PHMspaRV1909.usfm"),
    ("HEB", "058", "88-HEBspaRV1909.usfm"),
    ("JAS", "059", "89-JASspaRV1909.usfm"),
    ("1PE", "060", "90-1PEspaRV1909.usfm"),
    ("2PE", "061", "91-2PEspaRV1909.usfm"),
    ("1JN", "062", "92-1JNspaRV1909.usfm"),
    ("2JN", "063", "93-2JNspaRV1909.usfm"),
    ("3JN", "064", "94-3JNspaRV1909.usfm"),
    ("JUD", "065", "95-JUDspaRV1909.usfm"),
    ("REV", "066", "96-REVspaRV1909.usfm"),
]

VERSE_MARKER = re.compile(r"\\v\s+(\d+)\s+")
CHAPTER_MARKER = re.compile(r"\\c\s+(\d+)")
STRIP_MARKERS = re.compile(r"\\[a-z0-9*]+")
STRIP_WORD_ATTRS = re.compile(r"\|[^\\]*")


def clean_verse(text: str) -> str:
    # \w word|strong="G0976"\w* -> word (drop the |attr= payload before \w*)
    text = STRIP_WORD_ATTRS.sub("", text)
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
        out = OUT_DIR / f"{conical}_{book_code}_{current_chapter:03d}_{current_verse:03d}_RV1909.txt"
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
        help="Delete existing RV1909 atomized files for the selected books before writing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    requested_books = {book.upper() for book in args.book}
    books = selected_books(args.scope, requested_books)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for book_code, conical, _filename in books:
            for old in OUT_DIR.glob(f"{conical}_{book_code}_*_RV1909.txt"):
                old.unlink()

    total = 0
    for book_code, conical, filename in books:
        count = atomize_book(book_code, conical, filename)
        print(f"{book_code}: {count}")
        total += count
    print(f"TOTAL: {total}")


if __name__ == "__main__":
    main()
