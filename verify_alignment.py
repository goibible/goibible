#!/usr/bin/env python3
"""
verify_alignment.py — Triple alignment verification + apparatus extraction.

TRIPLE VERIFY:
  1. Flatfiles vs KJV expected counts     (structural)
  2. DB rows vs KJV expected counts       (ingestion integrity)
  3. Flatfiles vs DB                      (sync integrity)

RESULT:
  ALIGNED   → stays in atomic_bible.sqlite3, GOI assigned
  UNALIGNED → moved to apparatus table, typed, forensics logged

Usage:
  python3 verify_alignment.py --ot              # WLC only
  python3 verify_alignment.py --nt              # TR1550 only
  python3 verify_alignment.py --both            # all versions
  python3 verify_alignment.py --both --fix      # verify + populate apparatus
  python3 verify_alignment.py --both --fix --dry-run
"""

import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR = Path("/home/albert/projects/bible")
DB_PATH  = BASE_DIR / "atomic_bible.sqlite3"

VERSIONS = {
    "KJV":   ("English_Bible_KJV/One_Directory_KJV",         "both"),
    "WEBUS": ("English_Bible_WEBUS/One_Directory_WEBUS",      "both"),
    "CUV":   ("Chinese_Bible_CUV/One_Directory_CUV",          "both"),
    "TR1550":("Greek_Bible_TR1550/One_Directory_TR1550",      "nt"),
    "WLC":   ("Hebrew_Bible_WLC/One_Directory_WLC",           "ot"),
}

FORENSICS_LOG = BASE_DIR / f"apparatus_forensics_{datetime.now():%Y%m%d_%H%M%S}.csv"

# Apparatus type classification rules
def classify_apparatus(book: str, chapter: int, verse: int, filename: str) -> str:
    """Classify why a verse is unaligned."""
    if verse == 0:
        return "SUPERSCRIPTION"
    if book == "PSA":
        return "SUPERSCRIPTION"
    if book == "MAL":
        return "CHAPTER_BOUNDARY"
    if book == "JOL":
        return "CHAPTER_BOUNDARY"
    # Generic chapter boundary for everything else
    return "CHAPTER_BOUNDARY"


# ── FILENAME PARSER ───────────────────────────────────────────────────────────

def parse_filename(fname: str):
    """
    Parse: 019_PSA_003_001_WLC.txt
    Returns: (canonical, book, chapter, verse, version)
    """
    stem = fname.replace(".txt", "")
    parts = stem.split("_")
    # parts: ['019', 'PSA', '003', '001', 'WLC']
    # Handle books with underscores like 1SA, 2KI etc. — they don't have underscores
    # Handle compound version codes: TR1550
    canonical = int(parts[0])
    book      = parts[1]
    chapter   = int(parts[2])
    verse     = int(parts[3])
    version   = "_".join(parts[4:])  # handles TR1550
    return canonical, book, chapter, verse, version


# ── KJV REFERENCE ────────────────────────────────────────────────────────────

def load_kjv_reference(conn) -> dict:
    """
    Build KJV reference: {(book, chapter): verse_count}
    Also: {book: total_verses}
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT book, chapter, COUNT(*) as cnt
        FROM verses
        WHERE version = 'KJV'
        GROUP BY book, chapter
        ORDER BY canonical, chapter
    """)
    ref = {}
    for book, chapter, cnt in cur.fetchall():
        ref[(book, chapter)] = cnt
    return ref


def load_kjv_books(conn) -> dict:
    """Returns {book: (canonical, testament)}"""
    cur = conn.cursor()
    cur.execute("SELECT osis, canonical, testament FROM books ORDER BY canonical")
    return {osis: (canonical, testament) for osis, canonical, testament in cur.fetchall()}


# ── FLATFILE SCANNER ──────────────────────────────────────────────────────────

def scan_flatfiles(version: str) -> dict:
    """
    Scan flatfiles for a version.
    Returns: {(book, chapter, verse): Path}
    """
    rel_path, _ = VERSIONS[version]
    directory = BASE_DIR / rel_path

    if not directory.exists():
        print(f"  [WARN] Directory not found: {directory}")
        return {}

    files = {}
    for f in sorted(directory.glob("*.txt")):
        try:
            canonical, book, chapter, verse, ver = parse_filename(f.name)
            files[(book, chapter, verse)] = f
        except Exception as e:
            print(f"  [WARN] Cannot parse filename {f.name}: {e}")
    return files


# ── DB SCANNER ────────────────────────────────────────────────────────────────

def scan_db(conn, version: str) -> dict:
    """
    Load DB verses for a version.
    Returns: {(book, chapter, verse): goi}
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT book, chapter, verse, goi
        FROM verses
        WHERE version = ?
    """, (version,))
    return {(book, chapter, verse): goi for book, chapter, verse, goi in cur.fetchall()}


# ── TRIPLE VERIFY ─────────────────────────────────────────────────────────────

def verify_version(conn, version: str, kjv_ref: dict, kjv_books: dict,
                   scope: str, forensics: list, dry_run: bool, fix: bool):

    print(f"\n{'='*60}")
    print(f"  VERSION: {version}")
    print(f"{'='*60}")

    flatfiles = scan_flatfiles(version)
    db_verses  = scan_db(conn, version)

    if not flatfiles:
        print(f"  [SKIP] No flatfiles found.")
        return

    # ── TIER 1: Flatfiles vs KJV expected ────────────────────────────────────
    print(f"\n  TIER 1 — Flatfiles vs KJV expected counts")

    tier1_issues = []
    chapters_seen = {}
    for (book, chapter, verse), path in flatfiles.items():
        chapters_seen.setdefault((book, chapter), set()).add(verse)

    for (book, chapter), verses in sorted(chapters_seen.items()):
        kjv_count = kjv_ref.get((book, chapter))
        actual    = len(verses)
        if kjv_count is None:
            # Chapter doesn't exist in KJV at all
            tier1_issues.append({
                "version": version, "book": book, "chapter": chapter,
                "issue": "NO_KJV_CHAPTER",
                "kjv_expected": 0, "actual": actual, "delta": actual
            })
        elif actual != kjv_count:
            tier1_issues.append({
                "version": version, "book": book, "chapter": chapter,
                "issue": "COUNT_MISMATCH",
                "kjv_expected": kjv_count, "actual": actual,
                "delta": actual - kjv_count
            })

    if tier1_issues:
        print(f"  [FAIL] {len(tier1_issues)} chapter mismatches:")
        for i in tier1_issues:
            print(f"    {i['book']:>4} ch{i['chapter']:>3}  "
                  f"KJV={i['kjv_expected']:>3}  actual={i['actual']:>3}  "
                  f"delta={i['delta']:>+3}  ({i['issue']})")
    else:
        print(f"  [OK] All chapters match KJV expected counts")

    # ── TIER 2: DB vs KJV expected ───────────────────────────────────────────
    print(f"\n  TIER 2 — DB rows vs KJV expected counts")

    db_chapters = {}
    for (book, chapter, verse), goi in db_verses.items():
        db_chapters.setdefault((book, chapter), set()).add(verse)

    tier2_issues = []
    for (book, chapter), verses in sorted(db_chapters.items()):
        kjv_count = kjv_ref.get((book, chapter))
        actual    = len(verses)
        if kjv_count is None:
            tier2_issues.append({
                "book": book, "chapter": chapter,
                "issue": "NO_KJV_CHAPTER", "kjv_expected": 0, "actual": actual
            })
        elif actual != kjv_count:
            tier2_issues.append({
                "book": book, "chapter": chapter,
                "issue": "COUNT_MISMATCH",
                "kjv_expected": kjv_count, "actual": actual
            })

    if tier2_issues:
        print(f"  [FAIL] {len(tier2_issues)} DB chapter mismatches:")
        for i in tier2_issues:
            print(f"    {i['book']:>4} ch{i['chapter']:>3}  "
                  f"KJV={i['kjv_expected']:>3}  actual={i['actual']:>3}  "
                  f"({i['issue']})")
    else:
        print(f"  [OK] All DB chapters match KJV expected counts")

    # ── TIER 3: Flatfiles vs DB sync ─────────────────────────────────────────
    print(f"\n  TIER 3 — Flatfile vs DB sync")

    flatfile_keys = set(flatfiles.keys())
    db_keys       = set(db_verses.keys())

    only_in_files = flatfile_keys - db_keys
    only_in_db    = db_keys - flatfile_keys
    in_both       = flatfile_keys & db_keys

    null_goi = [(k, db_verses[k]) for k in in_both if db_verses[k] is None]

    if only_in_files:
        print(f"  [FAIL] {len(only_in_files)} verses in flatfiles but NOT in DB:")
        for k in sorted(only_in_files)[:20]:
            print(f"    {k[0]} {k[1]}:{k[2]}")
        if len(only_in_files) > 20:
            print(f"    ... and {len(only_in_files)-20} more")
    else:
        print(f"  [OK] All flatfile verses present in DB")

    if only_in_db:
        print(f"  [FAIL] {len(only_in_db)} verses in DB but NOT in flatfiles:")
        for k in sorted(only_in_db)[:20]:
            print(f"    {k[0]} {k[1]}:{k[2]}")
        if len(only_in_db) > 20:
            print(f"    ... and {len(only_in_db)-20} more")
    else:
        print(f"  [OK] All DB verses have flatfile counterparts")

    if null_goi:
        print(f"  [FAIL] {len(null_goi)} verses in both but GOI is NULL (unaligned):")
        for k, _ in sorted(null_goi)[:20]:
            print(f"    {k[0]} {k[1]}:{k[2]}")
        if len(null_goi) > 20:
            print(f"    ... and {len(null_goi)-20} more")
    else:
        print(f"  [OK] All shared verses have GOI assigned")

    # ── APPARATUS EXTRACTION ──────────────────────────────────────────────────
    # Unaligned = in flatfiles but no KJV match (no GOI possible)
    unaligned = only_in_files | {k for k, _ in null_goi}

    if unaligned:
        print(f"\n  APPARATUS — {len(unaligned)} verses to apparatus:")
        for key in sorted(unaligned):
            book, chapter, verse = key
            path = flatfiles.get(key)
            content = ""
            if path and path.exists():
                content = path.read_text(encoding="utf-8").strip()

            app_type = classify_apparatus(book, chapter, verse, 
                                          path.name if path else "")

            print(f"    [{app_type}] {book} {chapter}:{verse}")

            forensics.append({
                "timestamp":      datetime.now().isoformat(),
                "version":        version,
                "book":           book,
                "chapter":        chapter,
                "verse":          verse,
                "apparatus_type": app_type,
                "content":        content[:80],
                "dry_run":        dry_run,
            })

            if fix and not dry_run:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO apparatus
                        (version, book, chapter, verse, apparatus_type, content)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (version, book, chapter, verse, app_type, content))
                except Exception as e:
                    print(f"    [ERROR] apparatus insert failed: {e}")

        if fix and not dry_run:
            conn.commit()
            print(f"  [DONE] Apparatus records written to DB")
        elif fix and dry_run:
            print(f"  [DRY RUN] Would write {len(unaligned)} apparatus records")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    aligned_count   = len(in_both) - len(null_goi)
    apparatus_count = len(unaligned)
    print(f"\n  SUMMARY: {version}")
    print(f"    Flatfiles total   : {len(flatfile_keys):>6}")
    print(f"    DB total          : {len(db_keys):>6}")
    print(f"    Aligned (GOI set) : {aligned_count:>6}")
    print(f"    → Apparatus       : {apparatus_count:>6}")
    print(f"    Only in flatfiles : {len(only_in_files):>6}")
    print(f"    Only in DB        : {len(only_in_db):>6}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Triple alignment verify + apparatus extraction")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--ot",   action="store_true", help="OT versions only (WLC)")
    scope.add_argument("--nt",   action="store_true", help="NT versions only (TR1550)")
    scope.add_argument("--both", action="store_true", help="All versions")

    parser.add_argument("--fix",     action="store_true", help="Write unaligned to apparatus table")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no DB writes")

    args = parser.parse_args()

    if args.dry_run and not args.fix:
        print("[INFO] --dry-run has no effect without --fix")

    # Determine which versions to process
    if args.ot:
        target_scope = {"ot"}
        skip_kjv_check = True
    elif args.nt:
        target_scope = {"nt"}
        skip_kjv_check = True
    else:
        target_scope = {"ot", "nt", "both"}
        skip_kjv_check = False

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    print(f"\n{'='*60}")
    print(f"  BIBLE ALIGNMENT VERIFIER")
    print(f"  DB     : {DB_PATH}")
    print(f"  Scope  : {'OT' if args.ot else 'NT' if args.nt else 'BOTH'}")
    print(f"  Fix    : {args.fix}")
    print(f"  Dry run: {args.dry_run}")
    print(f"{'='*60}")

    kjv_ref   = load_kjv_reference(conn)
    kjv_books = load_kjv_books(conn)

    forensics = []

    for version, (rel_path, ver_scope) in VERSIONS.items():
        if version == "KJV":
            continue  # KJV is the anchor, not verified against itself

        # Scope filter
        if ver_scope not in target_scope and "both" not in target_scope:
            if not (ver_scope in target_scope):
                continue

        # --ot flag: only process OT versions
        if args.ot and ver_scope == "nt":
            continue
        if args.nt and ver_scope == "ot":
            continue

        verify_version(
            conn, version, kjv_ref, kjv_books,
            ver_scope, forensics, args.dry_run, args.fix
        )

    # ── FINAL REPORT ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  FINAL: {len(forensics)} apparatus candidates found")

    if forensics:
        with open(FORENSICS_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "version", "book", "chapter", "verse",
                "apparatus_type", "content", "dry_run"
            ])
            writer.writeheader()
            writer.writerows(forensics)
        print(f"  Forensics log : {FORENSICS_LOG}")

    # ── CONTRACT CHECK ────────────────────────────────────────────────────────
    print(f"\n  CONTRACT CHECK — every version must align to 31102:")
    cur = conn.cursor()
    cur.execute("""
        SELECT version, COUNT(*) as total,
               COUNT(goi) as goi_populated,
               MIN(goi) as min_goi,
               MAX(goi) as max_goi
        FROM verses
        GROUP BY version
        ORDER BY version
    """)
    rows = cur.fetchall()
    for row in rows:
        status = "✓" if row[1] == 31102 else "✗"
        goi_status = "✓" if row[2] == row[1] else f"✗ ({row[1]-row[2]} NULL)"
        print(f"  {status} {row[0]:<8} total={row[1]:>6}  "
              f"goi={goi_status}  "
              f"range={row[3]}-{row[4]}")

    print(f"{'='*60}\n")
    conn.close()


if __name__ == "__main__":
    main()
