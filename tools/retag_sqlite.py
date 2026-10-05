#!/usr/bin/env python3
"""Re-tag source-edition language values in SQLite databases (2026-10-05 BCP 47 rename): WLC he->hbo, TR1550 el->grc, and the
Hebrew source label 'he'->'hbo' in cube tables (lexemes/chunks .language). Matches by table+column, never by blind text replace:
  editions(edition_id,bcp47_tag,language_subtag)  rows for WLC/TR1550 only
  verses(edition_id,language_subtag)              rows for WLC/TR1550 only
  any table with a `language` column               'he' -> 'hbo'   (no other meaning of 'he' exists in those columns)
One transaction per database, busy_timeout 120 s (embedding workers may be reading). Idempotent.
  python3 tools/retag_sqlite.py DB [DB ...]      (prints what changed per database)"""
import sqlite3, sys
MAP = {"WLC": ("he", "hbo"), "TR1550": ("el", "grc")}

def retag(path):
    con = sqlite3.connect(path, timeout=120); con.execute("PRAGMA busy_timeout=120000")
    changed = {}
    try:
        con.execute("BEGIN IMMEDIATE")
        tabs = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for t in tabs:
            cols = {r[1] for r in con.execute(f'PRAGMA table_info("{t}")')}
            if t == "editions" and {"edition_id", "bcp47_tag", "language_subtag"} <= cols:
                for ed, (old, new) in MAP.items():
                    n = con.execute("UPDATE editions SET bcp47_tag=?, language_subtag=? WHERE edition_id=? AND (bcp47_tag=? OR language_subtag=?)", (new, new, ed, old, old)).rowcount
                    if n: changed[f"editions:{ed}"] = n
            if t == "verses" and {"edition_id", "language_subtag"} <= cols:
                for ed, (old, new) in MAP.items():
                    n = con.execute("UPDATE verses SET language_subtag=? WHERE edition_id=? AND language_subtag=?", (new, ed, old)).rowcount
                    if n: changed[f"verses:{ed}"] = n
            if "language" in cols and t not in ("editions", "verses"):
                n = con.execute(f'UPDATE "{t}" SET language=? WHERE language=?', ("hbo", "he")).rowcount
                if n: changed[f"{t}.language"] = n
        con.commit()
    except Exception:
        con.rollback(); raise
    finally:
        con.close()
    return changed

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p.split("/")[-1] if len(p) > 70 else p, retag(p), flush=True)
