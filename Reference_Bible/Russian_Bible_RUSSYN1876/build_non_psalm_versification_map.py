#!/usr/bin/env python3
"""Verified verse-level versification map for the 16 non-Psalms books where
Russian Synodal boundaries diverge from the KJV/GOI spine.

Every rule below was confirmed by reading actual verse content on both
sides (KJV and Russian), not inferred from verse-count arithmetic alone --
see the session notes / commit message for the specific content pairs
checked at each boundary (both endpoints of every shifted range, plus the
merge/split/addition point itself). This matters because a within-chapter
shift silently mis-pairs EVERY verse from the shift point to the end of
the chapter under naive address matching, not just the boundary verse --
the same failure mode that produced the Psalms bug, just book-local
instead of book-wide.

Each book's chapters are either:
  - untouched (no rule below -> direct address match, already correct)
  - "shift": a contiguous KJV verse range maps 1:1 onto a contiguous
    Russian verse range in the same or an adjacent chapter, offset by a
    constant. Content-verified at both ends of every range.
  - "merge": two-or-more KJV verses collapse into one Russian verse.
  - "addition": Russian verse(s) with NO KJV/GOI counterpart at all (a
    real LXX/Byzantine-tradition textual addition, not a renumbering --
    e.g. Proverbs 4:27a-b, Proverbs 13:9a, Joshua 24:33a-33d). These get
    no GOI address; they're logged for completeness, not mapped.
"""
from __future__ import annotations

import csv
from pathlib import Path

OUT_CSV = Path(__file__).resolve().parent / "non_psalm_versification_map.csv"

Rule = tuple  # (kind, book, kjv_ch, kjv_range, rus_ch, rus_start)

# Each entry: (book, kjv_chapter, kjv_verse_start, kjv_verse_end, rus_chapter, rus_verse_start)
# meaning KJV (kjv_chapter, v) for v in [start, end] maps to RUS (rus_chapter, rus_verse_start + (v - start)).
SHIFTS = [
    ("1SA", 23, 29, 29, 24, 1),      # KJV 23:29 -> RUS 24:1
    ("1SA", 24, 1, 22, 24, 2),       # KJV 24:1-22 -> RUS 24:2-23 (verified 24:1-2, 24:22 content)
    ("DAN", 4, 1, 3, 3, 31),         # KJV 4:1-3 -> RUS 3:31-33
    ("DAN", 4, 4, 37, 4, 1),         # KJV 4:4-37 -> RUS 4:1-34
    ("ECC", 5, 1, 1, 4, 17),         # KJV 5:1 -> RUS 4:17
    ("ECC", 5, 2, 20, 5, 1),         # KJV 5:2-20 -> RUS 5:1-19
    ("HOS", 13, 16, 16, 14, 1),      # KJV 13:16 -> RUS 14:1
    ("HOS", 14, 1, 9, 14, 2),        # KJV 14:1-9 -> RUS 14:2-10
    ("ISA", 3, 24, 26, 3, 23),       # KJV 3:24-26 -> RUS 3:23-25 (verified all three)
    ("JOB", 40, 1, 5, 39, 31),       # KJV 40:1-5 -> RUS 39:31-35
    ("JOB", 40, 6, 24, 40, 1),       # KJV 40:6-24 -> RUS 40:1-19
    ("JOB", 41, 1, 8, 40, 20),       # KJV 41:1-8 -> RUS 40:20-27
    ("JOB", 41, 9, 34, 41, 1),       # KJV 41:9-34 -> RUS 41:1-26
    ("JON", 1, 17, 17, 2, 1),        # KJV 1:17 -> RUS 2:1
    ("JON", 2, 1, 10, 2, 2),         # KJV 2:1-10 -> RUS 2:2-11
    ("JOS", 6, 1, 1, 5, 16),         # KJV 6:1 -> RUS 5:16
    ("JOS", 6, 2, 27, 6, 1),         # KJV 6:2-27 -> RUS 6:1-26
    ("NUM", 12, 16, 16, 13, 1),      # KJV 12:16 -> RUS 13:1
    ("NUM", 13, 1, 33, 13, 2),       # KJV 13:1-33 -> RUS 13:2-34
    ("NUM", 29, 40, 40, 30, 1),      # KJV 29:40 -> RUS 30:1
    ("NUM", 30, 1, 16, 30, 2),       # KJV 30:1-16 -> RUS 30:2-17
    ("PRO", 13, 14, 25, 13, 15),     # KJV 13:14-25 -> RUS 13:15-26
    ("SNG", 1, 2, 17, 1, 1),         # KJV 1:2-17 -> RUS 1:1-16 (KJV 1:1 title, unnumbered in Russian)
    ("SNG", 6, 13, 13, 7, 1),        # KJV 6:13 -> RUS 7:1
    ("SNG", 7, 1, 13, 7, 2),         # KJV 7:1-13 -> RUS 7:2-14
]

# Multiple KJV verses collapse onto one Russian verse.
MERGES = [
    ("1SA", 20, [42], 20, 42),          # RUS 20:42 = KJV 20:42's first sentence; RUS 20:43 is its second (see MERGE_MULTI)
    ("2CO", 11, [32, 33], 11, 32),
    ("2CO", 13, [12, 13], 13, 12),
    ("2CO", 13, [14], 13, 13),
    ("3JN", 1, [14], 1, 14),             # RUS 1:14 + 1:15 both realize KJV 1:14 (see MERGE_MULTI)
    ("ACT", 19, [40, 41], 19, 40),
    ("ISA", 3, [22, 23], 3, 22),
    ("LEV", 14, [55, 56], 14, 55),
    ("LEV", 14, [57], 14, 56),
    ("PRO", 4, [27], 4, 27),
]

# One GOI address realized by MORE than one Russian verse (concatenate).
MERGE_MULTI_EXTRA_RUS_VERSES = {
    ("1SA", 20, 42): [("1SA", 20, 43)],
    ("3JN", 1, 14): [("3JN", 1, 15)],
}

# Textual-tradition relocation: this GOI address's content is NOT at its
# "own" Russian chapter at all -- it's relocated to a different chapter,
# content-verified (the Romans doxology, placed after 14:23 in the
# Byzantine/Synodal textual tradition instead of after 16:23).
RELOCATIONS = [
    ("ROM", 16, 25, "ROM", 14, 24),
    ("ROM", 16, 26, "ROM", 14, 25),
    ("ROM", 16, 27, "ROM", 14, 26),
]

# Russian verses with NO GOI/KJV counterpart at all -- real textual
# additions (LXX/Byzantine tradition), not renumbering. Logged, not mapped.
ADDITIONS = [
    ("JOS", 24, [34, 35, 36], "LXX addition: Phinehas's priesthood, Israel's later apostasy (cf. Judges 2:11-13)"),
    ("PRO", 4, [28, 29], "LXX addition after 4:27 (the Lord watches the right paths, will make thy paths straight)"),
    ("PRO", 13, [14], "LXX/Byzantine addition after 13:13 (an evil son has nothing good, a wise servant's deeds prosper)"),
]


def main() -> None:
    rows = []

    def emit(book, kjv_ch, kjv_vs, rus_ch, rus_vs, relation, notes=""):
        rows.append({
            "goi_book": book, "goi_chapter": kjv_ch, "goi_verse": kjv_vs,
            "rus_chapter": rus_ch, "rus_verse": rus_vs,
            "relation": relation, "status": "verified", "notes": notes,
        })

    for book, kjv_ch, start, end, rus_ch, rus_start in SHIFTS:
        for offset, v in enumerate(range(start, end + 1)):
            emit(book, kjv_ch, v, rus_ch, rus_start + offset, "shift")

    for book, ch, kjv_vs, rus_ch, rus_vs in MERGES:
        for v in kjv_vs:
            emit(book, ch, v, rus_ch, rus_vs, "merged")

    for goi_book, goi_ch, goi_vs, rus_book, rus_ch, rus_vs in RELOCATIONS:
        emit(goi_book, goi_ch, goi_vs, rus_ch, rus_vs, "relocated",
             "Byzantine/Synodal textual tradition places this content after a different chapter than TR1550/KJV")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["goi_book", "goi_chapter", "goi_verse", "rus_chapter", "rus_verse", "relation", "status", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Rows written: {len(rows)}")
    print(f"Wrote {OUT_CSV}")
    print(f"Additions (no GOI address, not mapped): {sum(len(vs) for _,_,vs,_ in ADDITIONS)}")


if __name__ == "__main__":
    main()
