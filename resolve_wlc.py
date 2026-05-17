#!/usr/bin/env python3
"""
resolve_wlc.py — Final WLC alignment resolution.

Three operations derived from remap_wlc.py --dry-run analysis:

  1. DIFFERENT (112) — source file has unique Hebrew content not in KJV
                       → insert into apparatus table
                       → delete source flatfile
                       → delete source DB row

  2. IDENTICAL  (1)  — source file is exact duplicate of target
                       → delete source flatfile
                       → delete source DB row

  3. CLEAN RENAME (23) — no conflict, straightforward remap
                       → rename flatfile
                       → update DB chapter/verse
                       → reassign GOI

Usage:
  python3 resolve_wlc.py --dry-run    # show all actions, touch nothing
  python3 resolve_wlc.py --apply      # execute everything
"""

import argparse
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR = Path("/home/albert/projects/bible")
DB_PATH  = BASE_DIR / "atomic_bible.sqlite3"
WLC_DIR  = BASE_DIR / "Hebrew_Bible_WLC/One_Directory_WLC"
FORENSICS = BASE_DIR / f"resolve_wlc_forensics_{datetime.now():%Y%m%d_%H%M%S}.csv"

# ── CONFLICT PAIRS ────────────────────────────────────────────────────────────
# Source: remap_wlc.py --dry-run output + content comparison script
# Format: (source_file, target_file, resolution)
# resolution: APPARATUS | DUPLICATE | RENAME

CONFLICT_PAIRS = [
    # DIFFERENT — unique Hebrew content → apparatus
    ("001_GEN_032_033_WLC.txt", "001_GEN_033_001_WLC.txt", "APPARATUS"),
    ("002_EXO_007_026_WLC.txt", "002_EXO_008_001_WLC.txt", "APPARATUS"),
    ("002_EXO_007_027_WLC.txt", "002_EXO_008_002_WLC.txt", "APPARATUS"),
    ("002_EXO_007_028_WLC.txt", "002_EXO_008_003_WLC.txt", "APPARATUS"),
    ("002_EXO_007_029_WLC.txt", "002_EXO_008_004_WLC.txt", "APPARATUS"),
    ("002_EXO_021_037_WLC.txt", "002_EXO_022_001_WLC.txt", "APPARATUS"),
    ("003_LEV_005_020_WLC.txt", "003_LEV_006_001_WLC.txt", "DUPLICATE"),  # identical
    ("003_LEV_005_021_WLC.txt", "003_LEV_006_002_WLC.txt", "APPARATUS"),
    ("003_LEV_005_022_WLC.txt", "003_LEV_006_003_WLC.txt", "APPARATUS"),
    ("003_LEV_005_023_WLC.txt", "003_LEV_006_004_WLC.txt", "APPARATUS"),
    ("003_LEV_005_024_WLC.txt", "003_LEV_006_005_WLC.txt", "APPARATUS"),
    ("003_LEV_005_025_WLC.txt", "003_LEV_006_006_WLC.txt", "APPARATUS"),
    ("003_LEV_005_026_WLC.txt", "003_LEV_006_007_WLC.txt", "APPARATUS"),
    ("004_NUM_017_014_WLC.txt", "004_NUM_018_001_WLC.txt", "APPARATUS"),
    ("004_NUM_017_015_WLC.txt", "004_NUM_018_002_WLC.txt", "APPARATUS"),
    ("004_NUM_017_016_WLC.txt", "004_NUM_018_003_WLC.txt", "APPARATUS"),
    ("004_NUM_017_017_WLC.txt", "004_NUM_018_004_WLC.txt", "APPARATUS"),
    ("004_NUM_017_018_WLC.txt", "004_NUM_018_005_WLC.txt", "APPARATUS"),
    ("004_NUM_017_019_WLC.txt", "004_NUM_018_006_WLC.txt", "APPARATUS"),
    ("004_NUM_017_020_WLC.txt", "004_NUM_018_007_WLC.txt", "APPARATUS"),
    ("004_NUM_017_021_WLC.txt", "004_NUM_018_008_WLC.txt", "APPARATUS"),
    ("004_NUM_017_022_WLC.txt", "004_NUM_018_009_WLC.txt", "APPARATUS"),
    ("004_NUM_017_023_WLC.txt", "004_NUM_018_010_WLC.txt", "APPARATUS"),
    ("004_NUM_017_024_WLC.txt", "004_NUM_018_011_WLC.txt", "APPARATUS"),
    ("004_NUM_017_025_WLC.txt", "004_NUM_018_012_WLC.txt", "APPARATUS"),
    ("004_NUM_017_026_WLC.txt", "004_NUM_018_013_WLC.txt", "APPARATUS"),
    ("004_NUM_017_027_WLC.txt", "004_NUM_018_014_WLC.txt", "APPARATUS"),
    ("004_NUM_017_028_WLC.txt", "004_NUM_018_015_WLC.txt", "APPARATUS"),
    ("004_NUM_025_019_WLC.txt", "004_NUM_026_001_WLC.txt", "APPARATUS"),
    ("004_NUM_030_017_WLC.txt", "004_NUM_031_001_WLC.txt", "APPARATUS"),
    ("005_DEU_013_019_WLC.txt", "005_DEU_014_001_WLC.txt", "APPARATUS"),
    ("005_DEU_023_026_WLC.txt", "005_DEU_024_001_WLC.txt", "APPARATUS"),
    ("005_DEU_028_069_WLC.txt", "005_DEU_029_001_WLC.txt", "APPARATUS"),
    ("009_1SA_021_016_WLC.txt", "009_1SA_022_001_WLC.txt", "APPARATUS"),
    ("009_1SA_024_023_WLC.txt", "009_1SA_025_001_WLC.txt", "APPARATUS"),
    ("010_2SA_019_044_WLC.txt", "010_2SA_020_001_WLC.txt", "APPARATUS"),
    ("011_1KI_005_019_WLC.txt", "011_1KI_005_001_WLC.txt", "APPARATUS"),
    ("011_1KI_005_020_WLC.txt", "011_1KI_005_002_WLC.txt", "APPARATUS"),
    ("011_1KI_005_021_WLC.txt", "011_1KI_005_003_WLC.txt", "APPARATUS"),
    ("011_1KI_005_022_WLC.txt", "011_1KI_005_004_WLC.txt", "APPARATUS"),
    ("011_1KI_005_023_WLC.txt", "011_1KI_005_005_WLC.txt", "APPARATUS"),
    ("011_1KI_005_024_WLC.txt", "011_1KI_005_006_WLC.txt", "APPARATUS"),
    ("011_1KI_005_025_WLC.txt", "011_1KI_005_007_WLC.txt", "APPARATUS"),
    ("011_1KI_005_026_WLC.txt", "011_1KI_005_008_WLC.txt", "APPARATUS"),
    ("011_1KI_005_027_WLC.txt", "011_1KI_005_009_WLC.txt", "APPARATUS"),
    ("011_1KI_005_028_WLC.txt", "011_1KI_005_010_WLC.txt", "APPARATUS"),
    ("011_1KI_005_029_WLC.txt", "011_1KI_005_011_WLC.txt", "APPARATUS"),
    ("011_1KI_005_030_WLC.txt", "011_1KI_005_012_WLC.txt", "APPARATUS"),
    ("011_1KI_005_031_WLC.txt", "011_1KI_005_013_WLC.txt", "APPARATUS"),
    ("011_1KI_005_032_WLC.txt", "011_1KI_005_014_WLC.txt", "APPARATUS"),
    ("012_2KI_012_022_WLC.txt", "012_2KI_013_001_WLC.txt", "APPARATUS"),
    ("013_1CH_005_027_WLC.txt", "013_1CH_006_001_WLC.txt", "APPARATUS"),
    ("013_1CH_005_028_WLC.txt", "013_1CH_006_002_WLC.txt", "APPARATUS"),
    ("013_1CH_005_029_WLC.txt", "013_1CH_006_003_WLC.txt", "APPARATUS"),
    ("013_1CH_005_030_WLC.txt", "013_1CH_006_004_WLC.txt", "APPARATUS"),
    ("013_1CH_005_031_WLC.txt", "013_1CH_006_005_WLC.txt", "APPARATUS"),
    ("013_1CH_005_032_WLC.txt", "013_1CH_006_006_WLC.txt", "APPARATUS"),
    ("013_1CH_005_033_WLC.txt", "013_1CH_006_007_WLC.txt", "APPARATUS"),
    ("013_1CH_005_034_WLC.txt", "013_1CH_006_008_WLC.txt", "APPARATUS"),
    ("013_1CH_005_035_WLC.txt", "013_1CH_006_009_WLC.txt", "APPARATUS"),
    ("013_1CH_005_036_WLC.txt", "013_1CH_006_010_WLC.txt", "APPARATUS"),
    ("013_1CH_005_037_WLC.txt", "013_1CH_006_011_WLC.txt", "APPARATUS"),
    ("013_1CH_005_038_WLC.txt", "013_1CH_006_012_WLC.txt", "APPARATUS"),
    ("013_1CH_005_039_WLC.txt", "013_1CH_006_013_WLC.txt", "APPARATUS"),
    ("013_1CH_005_040_WLC.txt", "013_1CH_006_014_WLC.txt", "APPARATUS"),
    ("013_1CH_005_041_WLC.txt", "013_1CH_006_015_WLC.txt", "APPARATUS"),
    ("013_1CH_012_041_WLC.txt", "013_1CH_013_001_WLC.txt", "APPARATUS"),
    ("014_2CH_001_018_WLC.txt", "014_2CH_002_001_WLC.txt", "APPARATUS"),
    ("014_2CH_013_023_WLC.txt", "014_2CH_014_001_WLC.txt", "APPARATUS"),
    ("016_NEH_003_033_WLC.txt", "016_NEH_004_001_WLC.txt", "APPARATUS"),
    ("016_NEH_003_034_WLC.txt", "016_NEH_004_002_WLC.txt", "APPARATUS"),
    ("016_NEH_003_035_WLC.txt", "016_NEH_004_003_WLC.txt", "APPARATUS"),
    ("016_NEH_003_036_WLC.txt", "016_NEH_004_004_WLC.txt", "APPARATUS"),
    ("016_NEH_003_037_WLC.txt", "016_NEH_004_005_WLC.txt", "APPARATUS"),
    ("016_NEH_003_038_WLC.txt", "016_NEH_004_006_WLC.txt", "APPARATUS"),
    ("016_NEH_010_040_WLC.txt", "016_NEH_011_001_WLC.txt", "APPARATUS"),
    ("018_JOB_040_025_WLC.txt", "018_JOB_041_001_WLC.txt", "APPARATUS"),
    ("018_JOB_040_026_WLC.txt", "018_JOB_041_002_WLC.txt", "APPARATUS"),
    ("018_JOB_040_027_WLC.txt", "018_JOB_041_003_WLC.txt", "APPARATUS"),
    ("018_JOB_040_028_WLC.txt", "018_JOB_041_004_WLC.txt", "APPARATUS"),
    ("018_JOB_040_029_WLC.txt", "018_JOB_041_005_WLC.txt", "APPARATUS"),
    ("018_JOB_040_030_WLC.txt", "018_JOB_041_006_WLC.txt", "APPARATUS"),
    ("018_JOB_040_031_WLC.txt", "018_JOB_041_007_WLC.txt", "APPARATUS"),
    ("018_JOB_040_032_WLC.txt", "018_JOB_041_008_WLC.txt", "APPARATUS"),
    ("021_ECC_004_017_WLC.txt", "021_ECC_005_001_WLC.txt", "APPARATUS"),
    ("022_SNG_007_014_WLC.txt", "022_SNG_008_001_WLC.txt", "APPARATUS"),
    ("023_ISA_008_023_WLC.txt", "023_ISA_009_001_WLC.txt", "APPARATUS"),
    ("024_JER_008_023_WLC.txt", "024_JER_009_001_WLC.txt", "APPARATUS"),
    ("026_EZK_021_033_WLC.txt", "026_EZK_022_001_WLC.txt", "APPARATUS"),
    ("026_EZK_021_034_WLC.txt", "026_EZK_022_002_WLC.txt", "APPARATUS"),
    ("026_EZK_021_035_WLC.txt", "026_EZK_022_003_WLC.txt", "APPARATUS"),
    ("026_EZK_021_036_WLC.txt", "026_EZK_022_004_WLC.txt", "APPARATUS"),
    ("026_EZK_021_037_WLC.txt", "026_EZK_022_005_WLC.txt", "APPARATUS"),
    ("027_DAN_003_031_WLC.txt", "027_DAN_004_001_WLC.txt", "APPARATUS"),
    ("027_DAN_003_032_WLC.txt", "027_DAN_004_002_WLC.txt", "APPARATUS"),
    ("027_DAN_003_033_WLC.txt", "027_DAN_004_003_WLC.txt", "APPARATUS"),
    ("027_DAN_006_029_WLC.txt", "027_DAN_007_001_WLC.txt", "APPARATUS"),
    ("028_HOS_002_024_WLC.txt", "028_HOS_003_001_WLC.txt", "APPARATUS"),
    ("028_HOS_002_025_WLC.txt", "028_HOS_003_002_WLC.txt", "APPARATUS"),
    ("028_HOS_012_015_WLC.txt", "028_HOS_013_001_WLC.txt", "APPARATUS"),
    ("028_HOS_014_010_WLC.txt", "028_HOS_014_009_WLC.txt", "APPARATUS"),
    ("029_JOL_004_001_WLC.txt", "029_JOL_003_001_WLC.txt", "APPARATUS"),
    ("029_JOL_004_002_WLC.txt", "029_JOL_003_002_WLC.txt", "APPARATUS"),
    ("029_JOL_004_003_WLC.txt", "029_JOL_003_003_WLC.txt", "APPARATUS"),
    ("029_JOL_004_004_WLC.txt", "029_JOL_003_004_WLC.txt", "APPARATUS"),
    ("029_JOL_004_005_WLC.txt", "029_JOL_003_005_WLC.txt", "APPARATUS"),
    ("032_JON_002_011_WLC.txt", "032_JON_002_010_WLC.txt", "APPARATUS"),
    ("033_MIC_004_014_WLC.txt", "033_MIC_005_001_WLC.txt", "APPARATUS"),
    ("034_NAM_002_014_WLC.txt", "034_NAM_002_013_WLC.txt", "APPARATUS"),
    ("038_ZEC_002_014_WLC.txt", "038_ZEC_003_001_WLC.txt", "APPARATUS"),
    ("038_ZEC_002_015_WLC.txt", "038_ZEC_003_002_WLC.txt", "APPARATUS"),
    ("038_ZEC_002_016_WLC.txt", "038_ZEC_003_003_WLC.txt", "APPARATUS"),
    ("038_ZEC_002_017_WLC.txt", "038_ZEC_003_004_WLC.txt", "APPARATUS"),
]

# CLEAN RENAMES — no conflict, target does not exist
# These 23 verses have no KJV-addressed counterpart — pure rename
CLEAN_RENAMES = [
    # (source_file, kjv_ch, kjv_v)
    # MAL 3:19-24 → MAL 4:1-6
    ("039_MAL_003_019_WLC.txt", 4, 1),
    ("039_MAL_003_020_WLC.txt", 4, 2),
    ("039_MAL_003_021_WLC.txt", 4, 3),
    ("039_MAL_003_022_WLC.txt", 4, 4),
    ("039_MAL_003_023_WLC.txt", 4, 5),
    ("039_MAL_003_024_WLC.txt", 4, 6),
    # JOL 4:6-21 → JOL 3:6-21 (first 5 already handled as conflicts above)
    ("029_JOL_004_006_WLC.txt", 3, 6),
    ("029_JOL_004_007_WLC.txt", 3, 7),
    ("029_JOL_004_008_WLC.txt", 3, 8),
    ("029_JOL_004_009_WLC.txt", 3, 9),
    ("029_JOL_004_010_WLC.txt", 3, 10),
    ("029_JOL_004_011_WLC.txt", 3, 11),
    ("029_JOL_004_012_WLC.txt", 3, 12),
    ("029_JOL_004_013_WLC.txt", 3, 13),
    ("029_JOL_004_014_WLC.txt", 3, 14),
    ("029_JOL_004_015_WLC.txt", 3, 15),
    ("029_JOL_004_016_WLC.txt", 3, 16),
    ("029_JOL_004_017_WLC.txt", 3, 17),
    ("029_JOL_004_018_WLC.txt", 3, 18),
    ("029_JOL_004_019_WLC.txt", 3, 19),
    ("029_JOL_004_020_WLC.txt", 3, 20),
    ("029_JOL_004_021_WLC.txt", 3, 21),
    # 1KI 22:54 → 1KI 23:1
    ("011_1KI_022_054_WLC.txt", 23, 1),
]


# ── FILENAME HELPERS ──────────────────────────────────────────────────────────

def parse_wlc_filename(fname: str):
    """019_PSA_003_001_WLC.txt → (canonical, book, chapter, verse)"""
    stem = fname.replace(".txt", "")
    parts = stem.split("_")
    return int(parts[0]), parts[1], int(parts[2]), int(parts[3])


def make_wlc_filename(canonical: int, book: str, chapter: int, verse: int) -> str:
    return f"{canonical:03d}_{book}_{chapter:03d}_{verse:03d}_WLC.txt"


def make_filename_key(canonical: int, book: str, chapter: int, verse: int) -> str:
    return f"{canonical:03d}_{book}_{chapter:03d}_{verse:03d}_WLC"


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Resolve WLC alignment conflicts")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Show all actions, touch nothing")
    group.add_argument("--apply",   action="store_true",
                       help="Execute all operations")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "APPLY"

    print(f"\n{'='*60}")
    print(f"  WLC RESOLVE — {mode}")
    print(f"  WLC dir : {WLC_DIR}")
    print(f"  DB      : {DB_PATH}")
    print(f"{'='*60}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    forensics = []
    counts = {"APPARATUS": 0, "DUPLICATE": 0, "RENAME": 0, "ERROR": 0, "MISSING": 0}

    # ── PHASE 1: CONFLICTS (apparatus + duplicate) ────────────────────────────
    print(f"  PHASE 1 — Resolving {len(CONFLICT_PAIRS)} conflict pairs\n")

    for src_fname, tgt_fname, resolution in CONFLICT_PAIRS:
        src_path = WLC_DIR / src_fname
        tgt_path = WLC_DIR / tgt_fname

        try:
            canonical, book, wlc_ch, wlc_v = parse_wlc_filename(src_fname)
        except Exception as e:
            print(f"  [ERROR] Parse failed {src_fname}: {e}")
            counts["ERROR"] += 1
            continue

        if not src_path.exists():
            print(f"  [MISSING] {src_fname} — already resolved?")
            counts["MISSING"] += 1
            forensics.append({
                "phase": 1, "action": "MISSING", "resolution": resolution,
                "source": src_fname, "target": tgt_fname,
                "book": book, "wlc_ch": wlc_ch, "wlc_v": wlc_v,
                "note": "source file not found", "dry_run": args.dry_run
            })
            continue

        content = src_path.read_text(encoding="utf-8").strip()

        if resolution == "APPARATUS":
            print(f"  [APPARATUS] {src_fname}")
            if not args.dry_run:
                # Insert into apparatus
                conn.execute("""
                    INSERT OR IGNORE INTO apparatus
                    (version, book, chapter, verse, apparatus_type, content)
                    VALUES ('WLC', ?, ?, ?, 'CHAPTER_BOUNDARY', ?)
                """, (book, wlc_ch, wlc_v, content))
                # Delete DB row
                conn.execute("""
                    DELETE FROM verses
                    WHERE version='WLC' AND book=? AND chapter=? AND verse=?
                """, (book, wlc_ch, wlc_v))
                # Delete flatfile
                src_path.unlink()
            counts["APPARATUS"] += 1

        elif resolution == "DUPLICATE":
            print(f"  [DUPLICATE] {src_fname} — deleting")
            if not args.dry_run:
                # Delete DB row
                conn.execute("""
                    DELETE FROM verses
                    WHERE version='WLC' AND book=? AND chapter=? AND verse=?
                """, (book, wlc_ch, wlc_v))
                # Delete flatfile
                src_path.unlink()
            counts["DUPLICATE"] += 1

        forensics.append({
            "phase": 1, "action": resolution, "resolution": resolution,
            "source": src_fname, "target": tgt_fname,
            "book": book, "wlc_ch": wlc_ch, "wlc_v": wlc_v,
            "note": "", "dry_run": args.dry_run
        })

    if not args.dry_run:
        conn.commit()

    # ── PHASE 2: CLEAN RENAMES ────────────────────────────────────────────────
    print(f"\n  PHASE 2 — Processing {len(CLEAN_RENAMES)} clean renames\n")

    for src_fname, kjv_ch, kjv_v in CLEAN_RENAMES:
        src_path = WLC_DIR / src_fname

        try:
            canonical, book, wlc_ch, wlc_v = parse_wlc_filename(src_fname)
        except Exception as e:
            print(f"  [ERROR] Parse failed {src_fname}: {e}")
            counts["ERROR"] += 1
            continue

        if not src_path.exists():
            print(f"  [MISSING] {src_fname}")
            counts["MISSING"] += 1
            continue

        new_fname = make_wlc_filename(canonical, book, kjv_ch, kjv_v)
        new_path  = WLC_DIR / new_fname
        new_key   = make_filename_key(canonical, book, kjv_ch, kjv_v)

        # Safety check — target must not exist
        if new_path.exists():
            print(f"  [ERROR] Rename target exists: {new_fname} — skipping")
            counts["ERROR"] += 1
            forensics.append({
                "phase": 2, "action": "ERROR", "resolution": "RENAME",
                "source": src_fname, "target": new_fname,
                "book": book, "wlc_ch": wlc_ch, "wlc_v": wlc_v,
                "note": "target already exists", "dry_run": args.dry_run
            })
            continue

        print(f"  [RENAME] {src_fname} → {new_fname}")

        if not args.dry_run:
            src_path.rename(new_path)
            conn.execute("""
                UPDATE verses
                SET chapter      = ?,
                    verse        = ?,
                    filename_key = ?
                WHERE version='WLC' AND book=? AND chapter=? AND verse=?
            """, (kjv_ch, kjv_v, new_key, book, wlc_ch, wlc_v))

        counts["RENAME"] += 1
        forensics.append({
            "phase": 2, "action": "RENAME", "resolution": "RENAME",
            "source": src_fname, "target": new_fname,
            "book": book, "wlc_ch": wlc_ch, "wlc_v": wlc_v,
            "note": "", "dry_run": args.dry_run
        })

    if not args.dry_run:
        conn.commit()

    # ── PHASE 3: REASSIGN GOI ─────────────────────────────────────────────────
    print(f"\n  PHASE 3 — Reassigning GOI for all WLC verses\n")

    if not args.dry_run:
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
        """)
        conn.commit()

        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM verses
            WHERE version='WLC' AND goi IS NULL
        """)
        remaining = cur.fetchone()[0]
        print(f"  Remaining NULL GOI: {remaining} (expected ~66 superscriptions)")
    else:
        print(f"  [DRY RUN] GOI reassignment skipped")

    # ── PHASE 4: CONTRACT CHECK ───────────────────────────────────────────────
    print(f"\n  PHASE 4 — Contract check\n")

    cur = conn.cursor()
    cur.execute("""
        SELECT version, COUNT(*) as total,
               COUNT(goi) as goi_set,
               MIN(goi) as min_goi,
               MAX(goi) as max_goi
        FROM verses
        GROUP BY version
        ORDER BY version
    """)
    print(f"  {'VERSION':<8} {'TOTAL':>6}  {'GOI SET':>7}  {'RANGE'}")
    print(f"  {'-'*45}")
    for version, total, goi_set, min_goi, max_goi in cur.fetchall():
        null_count = total - goi_set
        status = "✓" if null_count == 0 else f"✗ ({null_count} NULL)"
        print(f"  {version:<8} {total:>6}  {status:>12}  {min_goi}-{max_goi}")

    conn.close()

    # ── FORENSICS LOG ─────────────────────────────────────────────────────────
    with open(FORENSICS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "phase", "action", "resolution", "source", "target",
            "book", "wlc_ch", "wlc_v", "note", "dry_run"
        ])
        writer.writeheader()
        writer.writerows(forensics)

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY ({mode})")
    print(f"    Apparatus   : {counts['APPARATUS']}")
    print(f"    Duplicates  : {counts['DUPLICATE']}")
    print(f"    Renames     : {counts['RENAME']}")
    print(f"    Missing     : {counts['MISSING']}")
    print(f"    Errors      : {counts['ERROR']}")
    print(f"    Forensics   : {FORENSICS}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("  Run with --apply to execute\n")


if __name__ == "__main__":
    main()
