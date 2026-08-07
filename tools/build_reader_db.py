#!/usr/bin/env python3
"""Rebuild /var/www/goibible.org/read/data/bible.sqlite3 (the read.goibible.org
public reader) from the current Meta_Bible_Data/goi_db_download/*.db editions.

This database is a THIRD, independent copy of the Bible data (separate from
the git-tracked goi_db_download/*.db files and from the Android/desktop app
bundles) and has no prior build script -- it was assembled by hand at some
point and then never re-synced, so it silently drifted out of date (missing
GOI_vi entirely, and stale text for every other edition) until this script
existed. Run this any time goi_db_download/*.db changes and the change needs
to reach the live reader.

Usage:
  python3 tools/build_reader_db.py [--target /path/to/bible.sqlite3]

Then rsync the resulting file to the dsvx server (see docs/inventory.md).
"""

from __future__ import annotations

import argparse
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = ROOT / "Meta_Bible_Data" / "goi_db_download"
DEFAULT_TARGET = pathlib.Path("/var/www/goibible.org/read/data/bible.sqlite3")

# Vietnamese book long names, standard VIE1934/common Vietnamese Protestant
# convention -- matches this project's secondary Vietnamese reference. There
# is no existing source for this in the repo (book_names is reader-only,
# hand-populated for Chinese when Chinese was added), so it is defined here.
VI_BOOK_NAMES = {
    1: "Sáng Thế Ký", 2: "Xuất Ê-díp-tô Ký", 3: "Lê-vi Ký", 4: "Dân Số Ký",
    5: "Phục Truyền Luật Lệ Ký", 6: "Giô-suê", 7: "Các Quan Xét", 8: "Ru-tơ",
    9: "1 Sa-mu-ên", 10: "2 Sa-mu-ên", 11: "1 Các Vua", 12: "2 Các Vua",
    13: "1 Sử Ký", 14: "2 Sử Ký", 15: "E-xơ-ra", 16: "Nê-hê-mi", 17: "Ê-xơ-tê",
    18: "Gióp", 19: "Thi Thiên", 20: "Châm Ngôn", 21: "Truyền Đạo",
    22: "Nhã Ca", 23: "Ê-sai", 24: "Giê-rê-mi", 25: "Ca Thương",
    26: "Ê-xê-chi-ên", 27: "Đa-ni-ên", 28: "Ô-sê", 29: "Giô-ên", 30: "A-mốt",
    31: "Áp-đia", 32: "Giô-na", 33: "Mi-chê", 34: "Na-hum", 35: "Ha-ba-cúc",
    36: "Sô-phô-ni", 37: "A-ghê", 38: "Xa-cha-ri", 39: "Ma-la-chi",
    40: "Ma-thi-ơ", 41: "Mác", 42: "Lu-ca", 43: "Giăng",
    44: "Công Vụ Các Sứ Đồ", 45: "Rô-ma", 46: "1 Cô-rinh-tô",
    47: "2 Cô-rinh-tô", 48: "Ga-la-ti", 49: "Ê-phê-sô", 50: "Phi-líp",
    51: "Cô-lô-se", 52: "1 Tê-sa-lô-ni-ca", 53: "2 Tê-sa-lô-ni-ca",
    54: "1 Ti-mô-thê", 55: "2 Ti-mô-thê", 56: "Tít", 57: "Phi-lê-môn",
    58: "Hê-bơ-rơ", 59: "Gia-cơ", 60: "1 Phi-e-rơ", 61: "2 Phi-e-rơ",
    62: "1 Giăng", 63: "2 Giăng", 64: "3 Giăng", 65: "Giu-đe",
    66: "Khải Huyền",
}

EDITIONS = {
    "KJV":         ("en", "en", "King James Version", None),
    "WEBUS":       ("en-US", "en", "World English Bible (US)", None),
    "TR1550":      ("el", "el", "Textus Receptus 1550", "Partial corpus in current source"),
    "WLC":         ("he", "he", "Westminster Leningrad Codex", "WLC OT corpus imported from Hebrew_Bible_WLC/One_Directory_WLC_KJV; filename_key uses _WLC suffix."),
    "GOI_En":      ("en", "en", "GOI Bible English", "GOI English corpus imported from GOI_Bible_English; filename_key uses _GOI_En suffix."),
    "GOI_Zh_Hant": ("zh-Hant", "zh", "GOI Bible Traditional Chinese", "GOI Traditional Chinese corpus imported from GOI_Bible_Chinese_Hant; filename_key uses _GOI_Zh_Hant suffix."),
    "GOI_Zh_Hans": ("zh-Hans", "zh", "GOI Bible Simplified Chinese", "GOI Simplified Chinese corpus converted from GOI_Bible_Chinese_Hant using OpenCC t2s; filename_key uses _GOI_Zh_Hans suffix."),
    "GOI_vi":      ("vi", "vi", "Tiếng Việt - Kinh Thánh GOI", "Vietnamese full Bible (OT+NT) generated from Hebrew/Greek noun-anchored pipeline; filename_key uses _GOI_vi suffix."),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=str(DEFAULT_TARGET))
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    conn = sqlite3.connect(target)
    cur = conn.cursor()

    for edition_id, (bcp47, subtag, display, notes) in EDITIONS.items():
        cur.execute(
            "INSERT INTO editions (edition_id, bcp47_tag, language_subtag, status, display_name, notes) "
            "VALUES (?, ?, ?, 'active', ?, ?) "
            "ON CONFLICT(edition_id) DO UPDATE SET bcp47_tag=excluded.bcp47_tag, "
            "language_subtag=excluded.language_subtag, display_name=excluded.display_name, notes=excluded.notes",
            (edition_id, bcp47, subtag, display, notes),
        )

    for conical, name in VI_BOOK_NAMES.items():
        cur.execute(
            "INSERT INTO book_names (edition_id, conical, name) VALUES ('GOI_vi', ?, ?) "
            "ON CONFLICT(edition_id, conical) DO UPDATE SET name=excluded.name",
            (conical, name),
        )

    for edition_id in EDITIONS:
        src_path = DOWNLOAD_DIR / f"{edition_id}.db"
        if not src_path.exists():
            print(f"SKIP {edition_id}: {src_path} not found")
            continue
        cur.execute("ATTACH DATABASE ? AS src", (str(src_path),))
        cur.execute("DELETE FROM verses WHERE edition_id = ?", (edition_id,))
        cur.execute(
            "INSERT INTO verses (goi, conical, edition_id, version, language_subtag, book, chapter, verse, testament, verse_text) "
            "SELECT goi, conical, edition_id, version, language_subtag, book, chapter, verse, testament, verse_text FROM src.verses"
        )
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM verses WHERE edition_id = ?", (edition_id,))
        n = cur.fetchone()[0]
        print(f"{edition_id}: {n} verses")
        cur.close()
        cur = conn.cursor()
        conn.execute("DETACH DATABASE src")

    print("Rebuilding verse_fts index...")
    cur.execute("DELETE FROM verse_fts")
    cur.execute(
        "INSERT INTO verse_fts (edition_id, conical, chapter, verse, goi, testament, book_name, verse_text) "
        "SELECT v.edition_id, v.conical, v.chapter, v.verse, v.goi, v.testament, "
        "       COALESCE(bn.name, b.long_name), v.verse_text "
        "FROM verses v "
        "JOIN books b ON b.conical = v.conical "
        "LEFT JOIN book_names bn ON bn.edition_id = v.edition_id AND bn.conical = v.conical"
    )

    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    print(f"Done. Total verses in reader db: {total}")
    conn.close()


if __name__ == "__main__":
    main()
