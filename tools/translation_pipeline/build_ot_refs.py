#!/usr/bin/env python3
"""Build OT reference manifests for the Vietnamese translation pipeline."""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
WLC_DIR = ROOT / "Reference_Bible" / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"

BOOK_NUMBERS = {
    "GEN": "001",
    "EXO": "002",
    "LEV": "003",
    "NUM": "004",
    "DEU": "005",
    "JOS": "006",
    "JDG": "007",
    "RUT": "008",
    "1SA": "009",
    "2SA": "010",
    "1KI": "011",
    "2KI": "012",
    "1CH": "013",
    "2CH": "014",
    "EZR": "015",
    "NEH": "016",
    "EST": "017",
    "JOB": "018",
    "PSA": "019",
    "PRO": "020",
    "ECC": "021",
    "SNG": "022",
    "ISA": "023",
    "JER": "024",
    "LAM": "025",
    "EZK": "026",
    "DAN": "027",
    "HOS": "028",
    "JOL": "029",
    "AMO": "030",
    "OBA": "031",
    "JON": "032",
    "MIC": "033",
    "NAM": "034",
    "HAB": "035",
    "ZEP": "036",
    "HAG": "037",
    "ZEC": "038",
    "MAL": "039",
}

PRESETS = {
    "torah": ["GEN", "EXO", "LEV", "NUM", "DEU"],
    "ot": list(BOOK_NUMBERS),
}


def chapters_for_book(book: str) -> list[int]:
    conical = BOOK_NUMBERS[book]
    chapters = set()
    for path in WLC_DIR.glob(f"{conical}_{book}_*_WLC.txt"):
        match = re.match(rf"{conical}_{book}_(\d{{3}})_\d{{3}}_WLC\.txt$", path.name)
        if match:
            chapters.add(int(match.group(1)))
    if not chapters:
        raise RuntimeError(f"No WLC files found for {book}")
    return sorted(chapters)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Use a named book set.")
    parser.add_argument("--book", action="append", default=[], help="Book code to include. May repeat.")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--description", default="Vietnamese OT translation batch.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    books = [book.upper() for book in args.book]
    if args.preset:
        books = PRESETS[args.preset] + books
    books = list(dict.fromkeys(books))
    if not books:
        raise SystemExit("Pass --preset or at least one --book.")

    groups = []
    total_chapters = 0
    for book in books:
        if book not in BOOK_NUMBERS:
            raise SystemExit(f"Unknown OT book: {book}")
        refs = [f"{book} {chapter}" for chapter in chapters_for_book(book)]
        total_chapters += len(refs)
        groups.append(
            {
                "name": f"{book} full book",
                "reason": "Full-book staged OT generation from WLC; VIE1934 is QA reference only.",
                "refs": refs,
            }
        )

    payload = {
        "edition": "GOI_Bible_vi",
        "description": args.description,
        "books": books,
        "chapter_count": total_chapters,
        "groups": groups,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Books: {', '.join(books)}")
    print(f"Chapters: {total_chapters}")


if __name__ == "__main__":
    main()
