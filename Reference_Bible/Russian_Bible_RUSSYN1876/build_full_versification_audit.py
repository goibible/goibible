#!/usr/bin/env python3
"""Exhaustive chapter/verse-count audit: Hebrew WLC vs Russian (OT), Greek
TR1550 vs Russian (NT) -- every book, every chapter, no sampling.

This project's WLC and TR1550 reference trees are already fully realigned
onto the GOI/KJV address spine (23,145 + 7,957 = 31,102 files, one per
spine address -- see memory: WLC GOI realignment). That means comparing
Russian against WLC/TR1550 addresses is address-for-address identical to
comparing it against the KJV spine; there is no separate "native Hebrew/
Greek versification" left to check beyond that spine, because these
source trees no longer carry native Hebrew/Greek verse numbers -- they
were remapped onto KJV's during that realignment. This script still does
the comparison directly against WLC/TR1550 (not just KJV) so that claim
is verified here, not assumed, and so the source-language file counts are
the audited authority, not a proxy.

Output:
  full_versification_audit.csv     -- one row per (testament, book, chapter):
                                       source_verses, russian_verses, match
  full_versification_audit_summary.md -- human-readable rollup
"""
from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WLC_DIR = ROOT / "Reference_Bible/Hebrew_Bible_WLC/One_Directory_WLC_KJV"
TR_DIR = ROOT / "Reference_Bible/Greek_Bible_TR1550/One_Directory_TR1550"
VPL_ZIP = Path(__file__).resolve().parent / "source/russyn_vpl.zip"
OUT_CSV = Path(__file__).resolve().parent / "full_versification_audit.csv"
OUT_MD = Path(__file__).resolve().parent / "full_versification_audit_summary.md"

# eBible/SIL source code -> this project's KJV/WLC/TR1550 spine code,
# for every book where they differ (same table as atomize_russian_synodal.py).
BOOK_CODE_MAP = {
    "1JO": "1JN", "2JO": "2JN", "3JO": "3JN", "EZE": "EZK", "JAM": "JAS",
    "JOE": "JOL", "JOH": "JHN", "MAR": "MRK", "NAH": "NAM", "PHI": "PHP",
    "SOL": "SNG",
}
# reverse map: spine code -> raw eBible code used in the Russian source
RUS_SOURCE_CODE = {v: k for k, v in BOOK_CODE_MAP.items()}


def spine_counts(directory: Path, suffix: str) -> dict[tuple[str, int], set[int]]:
    counts: dict[tuple[str, int], set[int]] = defaultdict(set)
    for p in directory.glob(f"*_{suffix}.txt"):
        _, book, chapter, verse, _ = p.stem.split("_")
        counts[(book, int(chapter))].add(int(verse))
    return counts


def russian_counts() -> dict[tuple[str, int], set[int]]:
    with zipfile.ZipFile(VPL_ZIP) as z:
        raw = z.read("russyn_vpl.txt").decode("utf-8")
    counts: dict[tuple[str, int], set[int]] = defaultdict(set)
    for line in raw.splitlines():
        m = re.match(r"^([1-3]?[A-Z]{2,3})\s+(\d+):(\d+)\s+", line)
        if not m:
            continue
        raw_book, chapter, verse = m.group(1), int(m.group(2)), int(m.group(3))
        book = BOOK_CODE_MAP.get(raw_book, raw_book)
        counts[(book, chapter)].add(verse)
    return counts


def main() -> None:
    wlc = spine_counts(WLC_DIR, "WLC")
    tr = spine_counts(TR_DIR, "TR1550")
    rus = russian_counts()

    wlc_total = sum(len(v) for v in wlc.values())
    tr_total = sum(len(v) for v in tr.values())
    assert wlc_total == 23145, f"WLC total {wlc_total} != 23145 -- spine not fully realigned"
    assert tr_total == 7957, f"TR1550 total {tr_total} != 7957 -- spine not fully realigned"

    rows = []
    ot_books = sorted({b for b, _ in wlc}, key=lambda b: min(c for bk, c in wlc if bk == b))
    nt_books = sorted({b for b, _ in tr}, key=lambda b: min(c for bk, c in tr if bk == b))

    def audit(testament, source_label, source_counts, books):
        for book in books:
            chapters = sorted({c for b, c in source_counts if b == book})
            for ch in chapters:
                src_n = len(source_counts[(book, ch)])
                rus_n = len(rus.get((book, ch), set()))
                rows.append({
                    "testament": testament, "book": book, "chapter": ch,
                    "source": source_label, "source_verses": src_n,
                    "russian_verses": rus_n, "match": src_n == rus_n,
                })

    audit("OT", "WLC", wlc, ot_books)
    audit("NT", "TR1550", tr, nt_books)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["testament", "book", "chapter", "source", "source_verses", "russian_verses", "match"])
        writer.writeheader()
        writer.writerows(rows)

    total_chapters = len(rows)
    mismatches = [r for r in rows if not r["match"]]
    by_book = defaultdict(list)
    for r in mismatches:
        by_book[r["book"]].append(r)

    lines = [
        "# Full Hebrew/Russian (OT) and Greek/Russian (NT) chapter-count audit",
        "",
        f"Every chapter in every book, source-language spine (WLC for OT, TR1550 for NT) vs Russian Synodal.",
        f"Books checked: {len(ot_books)} OT + {len(nt_books)} NT = {len(ot_books) + len(nt_books)}.",
        f"Chapters checked: {total_chapters}.",
        f"Chapters with matching verse count: {total_chapters - len(mismatches)}.",
        f"Chapters with mismatched verse count: {len(mismatches)}.",
        "",
        "## Mismatched chapters by book",
        "",
        "| Book | Chapters | Detail |",
        "|---|---|---|",
    ]
    for book in sorted(by_book):
        chs = by_book[book]
        detail = "; ".join(f"ch{r['chapter']} ({r['source']}={r['source_verses']}, ru={r['russian_verses']})" for r in chs)
        lines.append(f"| {book} | {len(chs)} | {detail} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Books: {len(ot_books)} OT + {len(nt_books)} NT")
    print(f"Chapters checked: {total_chapters}")
    print(f"Mismatched chapters: {len(mismatches)}")
    print(f"Books with at least one mismatch: {len(by_book)}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
