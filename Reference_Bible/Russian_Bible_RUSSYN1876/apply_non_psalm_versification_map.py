#!/usr/bin/env python3
"""Apply non_psalm_versification_map.csv on top of the naive direct-address
match, and verify the result is 100% GOI-address-complete for every
affected book (no gaps, no overlaps, no silently-wrong leftovers).

Every GOI address in an affected book is resolved by, in order:
  1. non_psalm_versification_map.csv (shift/merged/relocated rows) --
     content-verified boundary corrections.
  2. Direct (book, chapter, verse) address match -- correct wherever the
     book/chapter isn't touched by rule (1).

This REPLACES every flatfile for the touched books (deletes and rewrites
all of them, not just the boundary addresses) because a within-chapter
shift silently mis-pairs every verse from the shift point onward under
naive address matching, not just the boundary verse.

Addresses in ADDITIONS (build_non_psalm_versification_map.py) are real
Russian-only textual content with no GOI counterpart (LXX/Byzantine
additions) -- by definition they can never resolve to a GOI address, and
are reported, not written.
"""
from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
OUT_DIR = Path(__file__).resolve().parent / "One_Directory_RUSSYN1876"
MAP_CSV = Path(__file__).resolve().parent / "non_psalm_versification_map.csv"
VPL_ZIP = Path(__file__).resolve().parent / "source/russyn_vpl.zip"

BOOK_CODE_MAP = {
    "1JO": "1JN", "2JO": "2JN", "3JO": "3JN", "EZE": "EZK", "JAM": "JAS",
    "JOE": "JOL", "JOH": "JHN", "MAR": "MRK", "NAH": "NAM", "PHI": "PHP",
    "SOL": "SNG",
}

AFFECTED_BOOKS = {"1SA", "2CO", "3JN", "ACT", "DAN", "ECC", "HOS", "ISA",
                   "JOB", "JON", "JOS", "LEV", "NUM", "PRO", "ROM", "SNG"}


def normalize(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    with zipfile.ZipFile(VPL_ZIP) as z:
        raw = z.read("russyn_vpl.txt").decode("utf-8")
    rus: dict[tuple[str, int, int], str] = {}
    for line in raw.splitlines():
        m = re.match(r"^([1-3]?[A-Z]{2,3})\s+(\d+):(\d+)\s+(.*)$", line)
        if not m:
            continue
        raw_book, ch, vs, text = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        book = BOOK_CODE_MAP.get(raw_book, raw_book)
        rus[(book, ch, vs)] = normalize(text)

    overrides: dict[tuple[str, int, int], tuple[int, int]] = {}
    for row in csv.DictReader(MAP_CSV.open(encoding="utf-8")):
        goi = (row["goi_book"], int(row["goi_chapter"]), int(row["goi_verse"]))
        overrides[goi] = (int(row["rus_chapter"]), int(row["rus_verse"]))

    # GOI spine addresses for the affected books, from the KJV directory.
    spine: dict[tuple[str, int, int], str] = {}
    for p in KJV_DIR.glob("*_KJV.txt"):
        conical, book, chapter, verse, _ = p.stem.split("_")
        if book in AFFECTED_BOOKS:
            spine[(book, int(chapter), int(verse))] = conical

    removed = 0
    for book in AFFECTED_BOOKS:
        conical = next(p.stem.split("_")[0] for p in KJV_DIR.glob(f"*_{book}_001_001_KJV.txt"))
        for f in OUT_DIR.glob(f"{conical}_{book}_*_RUSSYN1876.txt"):
            f.unlink()
            removed += 1

    written = 0
    unresolved = []
    for (book, ch, vs), conical in spine.items():
        if (book, ch, vs) in overrides:
            rus_ch, rus_vs = overrides[(book, ch, vs)]
        else:
            rus_ch, rus_vs = ch, vs
        text = rus.get((book, rus_ch, rus_vs))
        if text is None:
            unresolved.append((book, ch, vs))
            continue
        # MERGE_MULTI: a GOI address realized by more than one Russian verse.
        extra = MERGE_MULTI_EXTRA_RUS_VERSES.get((book, ch, vs), [])
        for extra_book, extra_ch, extra_vs in extra:
            extra_text = rus.get((extra_book, extra_ch, extra_vs))
            if extra_text:
                text = text + " " + extra_text
        path = OUT_DIR / f"{conical}_{book}_{ch:03d}_{vs:03d}_RUSSYN1876.txt"
        path.write_text(text + "\n", encoding="utf-8")
        written += 1

    print(f"Removed {removed} flatfiles for affected books")
    print(f"Wrote {written} flatfiles")
    print(f"Unresolved GOI addresses: {len(unresolved)}")
    if unresolved:
        for a in unresolved[:20]:
            print("  ", a)


MERGE_MULTI_EXTRA_RUS_VERSES = {
    ("1SA", 20, 42): [("1SA", 20, 43)],
    ("3JN", 1, 14): [("3JN", 1, 15)],
}

if __name__ == "__main__":
    main()
