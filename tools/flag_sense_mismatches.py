#!/usr/bin/env python3
"""Deterministic scan for likely wrong-sense noun renderings in GOI_Bible_English (OT).

Mirrors the project's established approach (per CLAUDE.md / prior sessions):
"shove it into sqlite and SELECT where mismatch" rather than spot-checking
verse by verse. This drives a per-category WATCH_LIST of suspect English words
against the DB's noun-category ground truth, and reports every verse where a
noun's resolved category and its English rendering plausibly disagree — e.g.
Elohim (category=GOD) rendered as "angels" instead of "God"/"the LORD"
(observed live in Genesis 1:22).

This does NOT auto-fix anything — it produces a reviewable flag list so sense
mismatches across the whole corpus can be triaged in one batch instead of
discovered one verse at a time.

Usage:
  python3 flag_sense_mismatches.py            # scan all translated OT verses
  python3 flag_sense_mismatches.py --book GEN # scan one book
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "Meta_Bible_Data" / "Bible_Noun_Extraction" / "bible_noun.sqlite3"
ENGLISH_DIR = ROOT / "GOI_Bible" / "GOI_Bible_English"
REPORT_PATH = ROOT / "Meta_Bible_Data" / "logs" / "ot_sense_mismatch_flags.csv"

# category_code -> (acceptable words/phrases, suspect words/phrases, note)
# A verse is flagged when its English rendering contains a SUSPECT term and
# none of the ACCEPTABLE terms — i.e. the model picked a divergent dictionary
# sense for a noun whose category we already know from the extraction pass.
WATCH_LIST = {
    "GOD": (
        {"god", "gods", "lord", "almighty", "shaddai", "el "},
        {"angel", "angels", "judge", "judges", "mighty one", "mighty ones"},
        "Elohim/El/Adonai/Shaddai family is polysemous in KJV-style lexicon "
        "glosses (god/gods/angels/judges/mighty) — the model can pick the "
        "wrong sense without context grounding.",
    ),
}

FILENAME_RE = re.compile(r"^(\d{3})_([A-Z0-9]{3})_(\d{3})_(\d{3})\.txt$")


def ot_book_codes(cur: sqlite3.Cursor) -> set[str]:
    return {code for (code,) in cur.execute("SELECT book_code FROM books WHERE book_id BETWEEN 28 AND 66")}


def verse_categories(cur: sqlite3.Cursor, book_id: int, chapter: int, verse: int) -> list[tuple[str, str]]:
    """[(surface_form, category_code), ...] for every noun occurrence in this verse."""
    return cur.execute(
        """
        SELECT o.surface_form, c.category_code
        FROM verse_noun_occurrences o
        JOIN verses v ON v.verse_id = o.verse_id
        JOIN noun_categories c ON c.category_id = o.category_id
        WHERE v.book_id = ? AND v.chapter_number = ? AND v.verse_number = ?
        """,
        (book_id, chapter, verse),
    ).fetchall()


def scan_verse(english: str, categories: list[tuple[str, str]]) -> list[dict]:
    flags = []
    text_lower = english.lower()
    seen_categories = {cat for _surface, cat in categories}
    for category_code in seen_categories:
        rule = WATCH_LIST.get(category_code)
        if not rule:
            continue
        acceptable, suspect, note = rule
        has_acceptable = any(term in text_lower for term in acceptable)
        hit_suspects = [term for term in suspect if term in text_lower]
        if hit_suspects and not has_acceptable:
            flags.append({
                "category": category_code,
                "suspect_terms": ", ".join(hit_suspects),
                "note": note,
            })
    return flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="3-letter OT book code, e.g. GEN — omit to scan the whole OT")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ot_codes = ot_book_codes(cur)
    book_id_by_code = dict(cur.execute("SELECT book_code, book_id FROM books WHERE book_id BETWEEN 28 AND 66"))

    if args.book and args.book not in ot_codes:
        conn.close()
        return f"{args.book} is not an OT book code" and 1

    files = sorted(ENGLISH_DIR.glob("*.txt"))
    rows = []
    scanned = 0
    for f in files:
        m = FILENAME_RE.match(f.name)
        if not m:
            continue
        _num, book_code, chapter_s, verse_s = m.groups()
        if book_code not in ot_codes:
            continue
        if args.book and book_code != args.book:
            continue

        chapter, verse = int(chapter_s), int(verse_s)
        book_id = book_id_by_code[book_code]
        english = f.read_text(encoding="utf-8").strip()
        categories = verse_categories(cur, book_id, chapter, verse)
        scanned += 1

        for flag in scan_verse(english, categories):
            rows.append({
                "file": f.name,
                "ref": f"{book_code} {chapter}:{verse}",
                "category": flag["category"],
                "suspect_terms": flag["suspect_terms"],
                "english": english,
                "note": flag["note"],
            })

    conn.close()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["file", "ref", "category", "suspect_terms", "english", "note"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Scanned {scanned} translated OT verse(s).")
    print(f"Flagged {len(rows)} likely sense mismatch(es) -> {REPORT_PATH}")
    for row in rows:
        print(f"  [{row['category']}] {row['ref']} ({row['suspect_terms']}): {row['english']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
