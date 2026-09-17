#!/usr/bin/env python3
"""Definitive output verification: for every book and every chapter of the
GOI/KJV spine, does One_Directory_RUSSYN1876 contain exactly the expected
verse files -- no more, no fewer, no wrong addresses? This checks the
actual written output, not the raw source counts (that's
build_full_versification_audit.py, which audits the INPUT).

Exits nonzero and prints every discrepancy if anything is off.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
OUT_DIR = Path(__file__).resolve().parent / "One_Directory_RUSSYN1876"
OUT_REPORT = Path(__file__).resolve().parent / "output_alignment_by_chapter.csv"


def main() -> None:
    spine = defaultdict(set)   # (book, chapter) -> {verse,...}
    book_order = []
    for p in sorted(KJV_DIR.glob("*_KJV.txt")):
        conical, book, chapter, verse, _ = p.stem.split("_")
        if book not in book_order:
            book_order.append(book)
        spine[(book, int(chapter))].add(int(verse))

    output = defaultdict(set)
    for p in OUT_DIR.glob("*_RUSSYN1876.txt"):
        conical, book, chapter, verse, _ = p.stem.split("_")
        output[(book, int(chapter))].add(int(verse))

    import csv
    rows = []
    total_chapters = 0
    total_expected = 0
    total_actual = 0
    mismatches = []
    for book in book_order:
        chapters = sorted(c for b, c in spine if b == book)
        for ch in chapters:
            total_chapters += 1
            expected = spine[(book, ch)]
            actual = output.get((book, ch), set())
            total_expected += len(expected)
            total_actual += len(actual)
            ok = expected == actual
            rows.append({
                "book": book, "chapter": ch,
                "expected_verses": len(expected), "actual_verses": len(actual),
                "match": ok,
            })
            if not ok:
                missing = expected - actual
                extra = actual - expected
                mismatches.append((book, ch, sorted(missing), sorted(extra)))

    with OUT_REPORT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["book", "chapter", "expected_verses", "actual_verses", "match"])
        w.writeheader()
        w.writerows(rows)

    print(f"Books: {len(book_order)}")
    print(f"Chapters: {total_chapters}")
    print(f"Expected verses (full GOI/KJV spine): {total_expected}")
    print(f"Actual verses written: {total_actual}")
    print(f"Chapters with exact match: {total_chapters - len(mismatches)}/{total_chapters}")
    print(f"Wrote {OUT_REPORT}")
    if mismatches:
        print(f"\n{len(mismatches)} MISMATCHED CHAPTERS:")
        for book, ch, missing, extra in mismatches:
            print(f"  {book} {ch}: missing={missing} extra={extra}")
        raise SystemExit(1)
    print("\n100% MATCH: every book, every chapter, every verse address present exactly once.")


if __name__ == "__main__":
    main()
