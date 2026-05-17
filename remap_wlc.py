#!/usr/bin/env python3
"""
remap_wlc.py — Remap WLC flatfiles and DB to KJV GPS alignment.

Two categories of misalignment:
  CHAPTER_BOUNDARY — content exists in KJV, just under a different address
  SUPERSCRIPTION   — Psalm titles, no KJV equivalent → apparatus (not remapped here)

Operations:
  1. Rename flatfiles to KJV-aligned addresses
  2. Update DB verse records to match
  3. Write forensics log of every action
  4. Leave SUPERSCRIPTION verses untouched (handled by apparatus pipeline)

Usage:
  python3 remap_wlc.py --dry-run     # show all renames, touch nothing
  python3 remap_wlc.py --apply       # execute renames + DB updates
"""

import argparse
import csv
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR  = Path("/home/albert/projects/bible")
DB_PATH   = BASE_DIR / "atomic_bible.sqlite3"
WLC_DIR   = BASE_DIR / "Hebrew_Bible_WLC/One_Directory_WLC"
FORENSICS = BASE_DIR / f"remap_wlc_forensics_{datetime.now():%Y%m%d_%H%M%S}.csv"

# ── COMPLETE REMAP TABLE ──────────────────────────────────────────────────────
# Derived from verify_alignment.py Tier 1 + NULL GOI analysis.
# Format: (book, wlc_chapter, wlc_verse) → (kjv_chapter, kjv_verse)
#
# Two remap types:
#   TRAILING OVERFLOW  — WLC ch N has extra verses at the end
#                        that belong in KJV ch N+1 (or N-1 for JOL/1KI)
#   LEADING ABSORPTION — WLC ch N started with KJV prev chapter's last verse,
#                        so WLC ch N's last verse maps to same chapter in KJV
#                        (HOS 14, JON 2, NAM 2)

def build_remap_table() -> dict:
    """
    Returns {(book, wlc_ch, wlc_v): (kjv_ch, kjv_v)}
    """
    remap = {}

    def trailing(book, wlc_ch, kjv_ch, wlc_verses: list, kjv_v_start: int = 1):
        """Trailing overflow: WLC ch overflow verses → KJV ch starting at kjv_v_start."""
        for i, wlc_v in enumerate(wlc_verses):
            remap[(book, wlc_ch, wlc_v)] = (kjv_ch, kjv_v_start + i)

    def same_chapter(book, wlc_ch, kjv_ch, wlc_v, kjv_v):
        """Single verse same-chapter remap."""
        remap[(book, wlc_ch, wlc_v)] = (kjv_ch, kjv_v)

    # ── 1 Chronicles ─────────────────────────────────────────────────────────
    # 1CH 5:27-41 → 1CH 6:1-15  (Hebrew ch5 bleeds into KJV ch6)
    trailing("1CH", 5, 6, list(range(27, 42)), kjv_v_start=1)
    # 1CH 12:41 → 1CH 13:1
    trailing("1CH", 12, 13, [41], kjv_v_start=1)

    # ── 1 Kings ──────────────────────────────────────────────────────────────
    # WLC 1KI ch5 is actually KJV ch4 (Hebrew split differs entirely)
    # WLC 1KI 5:1-18  = KJV 1KI 4:21-38  (first 18 verses align to KJV ch4)
    # WLC 1KI 5:19-32 = KJV 1KI 5:1-14   (overflow becomes KJV ch5)
    # The NULL GOI verses are 1KI 5:19-32 — they belong in KJV 5:1-14
    trailing("1KI", 5, 5, list(range(19, 33)), kjv_v_start=1)
    # 1KI 22:54 → 1KI 23:1
    trailing("1KI", 22, 23, [54], kjv_v_start=1)

    # ── 1 Samuel ─────────────────────────────────────────────────────────────
    trailing("1SA", 21, 22, [16], kjv_v_start=1)
    trailing("1SA", 24, 25, [23], kjv_v_start=1)

    # ── 2 Chronicles ─────────────────────────────────────────────────────────
    trailing("2CH", 1, 2, [18], kjv_v_start=1)
    trailing("2CH", 13, 14, [23], kjv_v_start=1)

    # ── 2 Kings ──────────────────────────────────────────────────────────────
    trailing("2KI", 12, 13, [22], kjv_v_start=1)

    # ── 2 Samuel ─────────────────────────────────────────────────────────────
    trailing("2SA", 19, 20, [44], kjv_v_start=1)

    # ── Daniel ───────────────────────────────────────────────────────────────
    # DAN 3:31-33 → DAN 4:1-3  (Aramaic section boundary)
    trailing("DAN", 3, 4, [31, 32, 33], kjv_v_start=1)
    # DAN 6:29 → DAN 7:1
    trailing("DAN", 6, 7, [29], kjv_v_start=1)

    # ── Deuteronomy ──────────────────────────────────────────────────────────
    trailing("DEU", 13, 14, [19], kjv_v_start=1)
    trailing("DEU", 23, 24, [26], kjv_v_start=1)
    trailing("DEU", 28, 29, [69], kjv_v_start=1)

    # ── Ecclesiastes ─────────────────────────────────────────────────────────
    trailing("ECC", 4, 5, [17], kjv_v_start=1)

    # ── Exodus ───────────────────────────────────────────────────────────────
    trailing("EXO", 7, 8, [26, 27, 28, 29], kjv_v_start=1)
    trailing("EXO", 21, 22, [37], kjv_v_start=1)

    # ── Ezekiel ──────────────────────────────────────────────────────────────
    trailing("EZK", 21, 22, [33, 34, 35, 36, 37], kjv_v_start=1)

    # ── Genesis ──────────────────────────────────────────────────────────────
    trailing("GEN", 32, 33, [33], kjv_v_start=1)

    # ── Hosea ────────────────────────────────────────────────────────────────
    # HOS 2:24-25 → HOS 3:1-2
    trailing("HOS", 2, 3, [24, 25], kjv_v_start=1)
    # HOS 12:15 → HOS 13:1 -- wait: KJV HOS 12 delta=-1, HOS 13 delta=+1... 
    # NULL GOI is HOS 12:15 → KJV HOS 13:1? Actually:
    # WLC HOS 11 delta=-1, HOS 12 delta=+1 -- from Tier1
    # HOS 12:15 NULL → KJV 13:1 (trailing overflow)
    trailing("HOS", 12, 13, [15], kjv_v_start=1)
    # HOS 14:10 — leading absorption case (same chapter remap)
    # WLC HOS 13 delta=-1, HOS 14 delta=+1
    # WLC 14:1 = KJV 13:16, so WLC 14:2-10 = KJV 14:1-9
    # WLC 14:10 → KJV 14:9
    same_chapter("HOS", 14, 14, 10, 9)

    # ── Isaiah ───────────────────────────────────────────────────────────────
    trailing("ISA", 8, 9, [23], kjv_v_start=1)

    # ── Jeremiah ─────────────────────────────────────────────────────────────
    trailing("JER", 8, 9, [23], kjv_v_start=1)

    # ── Job ──────────────────────────────────────────────────────────────────
    # JOB 40:25-32 → JOB 41:1-8
    trailing("JOB", 40, 41, list(range(25, 33)), kjv_v_start=1)

    # ── Joel ─────────────────────────────────────────────────────────────────
    # WLC has 4 chapters; KJV has 3.
    # WLC JOL 4:1-21 = KJV JOL 3:1-21  (entire chapter renumber)
    trailing("JOL", 4, 3, list(range(1, 22)), kjv_v_start=1)

    # ── Jonah ────────────────────────────────────────────────────────────────
    # Leading absorption: WLC JON 2:1 = KJV JON 1:17
    # WLC JON 2:2-11 = KJV JON 2:1-10
    # WLC JON 2:11 → KJV JON 2:10 (same chapter)
    same_chapter("JON", 2, 2, 11, 10)

    # ── Leviticus ────────────────────────────────────────────────────────────
    trailing("LEV", 5, 6, list(range(20, 27)), kjv_v_start=1)

    # ── Malachi ──────────────────────────────────────────────────────────────
    # WLC MAL 3:19-24 → KJV MAL 4:1-6
    trailing("MAL", 3, 4, list(range(19, 25)), kjv_v_start=1)

    # ── Micah ────────────────────────────────────────────────────────────────
    trailing("MIC", 4, 5, [14], kjv_v_start=1)

    # ── Nahum ────────────────────────────────────────────────────────────────
    # Leading absorption: WLC NAM 2:1 = KJV NAM 1:15
    # WLC NAM 2:2-14 = KJV NAM 2:1-13
    # WLC NAM 2:14 → KJV NAM 2:13 (same chapter)
    same_chapter("NAM", 2, 2, 14, 13)

    # ── Nehemiah ─────────────────────────────────────────────────────────────
    trailing("NEH", 3, 4, list(range(33, 39)), kjv_v_start=1)
    trailing("NEH", 10, 11, [40], kjv_v_start=1)

    # ── Numbers ──────────────────────────────────────────────────────────────
    trailing("NUM", 17, 18, list(range(14, 29)), kjv_v_start=1)
    trailing("NUM", 25, 26, [19], kjv_v_start=1)
    trailing("NUM", 30, 31, [17], kjv_v_start=1)

    # ── Song of Songs ────────────────────────────────────────────────────────
    trailing("SNG", 7, 8, [14], kjv_v_start=1)

    # ── Zechariah ────────────────────────────────────────────────────────────
    trailing("ZEC", 2, 3, [14, 15, 16, 17], kjv_v_start=1)

    return remap


# ── FILENAME HELPERS ──────────────────────────────────────────────────────────

def parse_wlc_filename(fname: str):
    """019_PSA_003_001_WLC.txt → (canonical, book, chapter, verse)"""
    stem = fname.replace(".txt", "")
    parts = stem.split("_")
    return int(parts[0]), parts[1], int(parts[2]), int(parts[3])


def make_wlc_filename(canonical: int, book: str, chapter: int, verse: int) -> str:
    return f"{canonical:03d}_{book}_{chapter:03d}_{verse:03d}_WLC.txt"


def make_filename_key(canonical: int, book: str, chapter: int, verse: int) -> str:
    """DB filename_key format (no extension)."""
    return f"{canonical:03d}_{book}_{chapter:03d}_{verse:03d}_WLC"


# ── BOOK CANONICAL LOOKUP ─────────────────────────────────────────────────────

def load_canonical(conn) -> dict:
    """Returns {osis: canonical}"""
    cur = conn.cursor()
    cur.execute("SELECT osis, canonical FROM books")
    return {osis: canonical for osis, canonical in cur.fetchall()}


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Remap WLC flatfiles to KJV GPS alignment")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Show all renames, touch nothing")
    group.add_argument("--apply",   action="store_true",
                       help="Execute renames and DB updates")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "APPLY"

    print(f"\n{'='*60}")
    print(f"  WLC REMAP — {mode}")
    print(f"  WLC dir : {WLC_DIR}")
    print(f"  DB      : {DB_PATH}")
    print(f"{'='*60}\n")

    remap = build_remap_table()
    print(f"  Remap table entries: {len(remap)}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    canonical_map = load_canonical(conn)

    # Scan all WLC flatfiles
    wlc_files = sorted(WLC_DIR.glob("*.txt"))
    print(f"  WLC flatfiles found: {len(wlc_files)}\n")

    forensics_rows = []
    rename_count   = 0
    skip_count     = 0
    error_count    = 0
    conflict_count = 0

    for fpath in wlc_files:
        try:
            canonical, book, wlc_ch, wlc_v = parse_wlc_filename(fpath.name)
        except Exception as e:
            print(f"  [ERROR] Cannot parse: {fpath.name}: {e}")
            error_count += 1
            continue

        key = (book, wlc_ch, wlc_v)
        if key not in remap:
            skip_count += 1
            continue

        kjv_ch, kjv_v = remap[key]

        # Build new filename
        new_fname = make_wlc_filename(canonical, book, kjv_ch, kjv_v)
        new_path  = WLC_DIR / new_fname
        new_key   = make_filename_key(canonical, book, kjv_ch, kjv_v)

        action = "RENAME"
        note   = ""

        # Check for conflicts
        if new_path.exists() and new_path != fpath:
            action = "CONFLICT"
            note   = f"Target {new_fname} already exists"
            conflict_count += 1
            print(f"  [CONFLICT] {fpath.name} → {new_fname}: target exists")
        else:
            rename_count += 1
            if not args.dry_run:
                # Rename flatfile
                fpath.rename(new_path)

                # Update DB
                try:
                    conn.execute("""
                        UPDATE verses
                        SET chapter      = ?,
                            verse        = ?,
                            filename_key = ?
                        WHERE version = 'WLC'
                          AND book    = ?
                          AND chapter = ?
                          AND verse   = ?
                    """, (kjv_ch, kjv_v, new_key, book, wlc_ch, wlc_v))
                except Exception as e:
                    action = "DB_ERROR"
                    note   = str(e)
                    error_count += 1
                    print(f"  [DB ERROR] {book} {wlc_ch}:{wlc_v} → {e}")

        print(f"  [{action}] {fpath.name:40s} → {new_fname}  {note}")

        forensics_rows.append({
            "timestamp":  datetime.now().isoformat(),
            "action":     action,
            "book":       book,
            "wlc_ch":     wlc_ch,
            "wlc_v":      wlc_v,
            "kjv_ch":     kjv_ch,
            "kjv_v":      kjv_v,
            "old_file":   fpath.name,
            "new_file":   new_fname,
            "note":       note,
            "dry_run":    args.dry_run,
        })

    if not args.dry_run:
        conn.commit()

        # Reassign GOI for remapped WLC verses
        print(f"\n  Reassigning GOI for remapped WLC verses...")
        conn.execute("""
            UPDATE verses
            SET goi = (
                SELECT k.goi FROM verses k
                WHERE k.version = 'KJV'
                  AND k.book    = verses.book
                  AND k.chapter = verses.chapter
                  AND k.verse   = verses.verse
            )
            WHERE version = 'WLC'
              AND goi IS NULL
              AND book NOT IN (SELECT DISTINCT book FROM verses
                               WHERE version='WLC' AND verse = 0)
        """)
        conn.commit()

        # Report remaining NULLs (should be only superscriptions)
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM verses
            WHERE version = 'WLC' AND goi IS NULL
        """)
        remaining_nulls = cur.fetchone()[0]
        print(f"  Remaining NULL GOI after remap: {remaining_nulls} "
              f"(should equal superscription count ~66)")

    conn.close()

    # ── FORENSICS LOG ─────────────────────────────────────────────────────────
    with open(FORENSICS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "action", "book",
            "wlc_ch", "wlc_v", "kjv_ch", "kjv_v",
            "old_file", "new_file", "note", "dry_run"
        ])
        writer.writeheader()
        writer.writerows(forensics_rows)

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY ({mode})")
    print(f"    Remapped    : {rename_count}")
    print(f"    Skipped     : {skip_count}  (aligned or PSA superscription)")
    print(f"    Conflicts   : {conflict_count}")
    print(f"    Errors      : {error_count}")
    print(f"    Forensics   : {FORENSICS}")
    print(f"{'='*60}\n")

    if conflict_count:
        print("  ⚠ Resolve conflicts before running --apply")
    if error_count:
        print("  ⚠ Review errors in forensics log")
    if rename_count and args.dry_run:
        print("  Run with --apply to execute")


if __name__ == "__main__":
    main()
