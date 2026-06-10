#!/usr/bin/env python3
"""Integrity gate for the Traditional Chinese NT corpus (GOI_Bible_Chinese_Hant).

Mirrors validate.py (English gate) — run after any edit to the Chinese corpus or DB.

  python3 validate_zh.py

Checks (each prints PASS/FAIL):
  CORPUS    file count, naming, single-line, non-empty, NFC/canonical, has CJK chars
  GREEK     every (book,ch,verse) has a raw TR1550 source file
  DB        FK integrity; override positions valid; sense_key catalog
  NOUNS     verse_noun_occurrences == strongs_nt(in_tr1550) per verse
  COVERAGE  Chinese noun coverage >= 95% (delegates to verify_noun_coverage_zh.py)
"""
import pathlib, re, sqlite3, subprocess, sys, unicodedata
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent
GOI  = ROOT / "GOI_Bible_Chinese_Hant"
NIM  = ROOT / "Bible_Noun_Extraction"
DB   = NIM / "bible_noun.sqlite3"
RAW  = NIM / "One_Directory_TR1550"
BOOK = {1:('MAT','040'),2:('MRK','041'),3:('LUK','042'),4:('JHN','043'),5:('ACT','044'),
6:('ROM','045'),7:('1CO','046'),8:('2CO','047'),9:('GAL','048'),10:('EPH','049'),11:('PHP','050'),
12:('COL','051'),13:('1TH','052'),14:('2TH','053'),15:('1TI','054'),16:('2TI','055'),17:('TIT','056'),
18:('PHM','057'),19:('HEB','058'),20:('JAS','059'),21:('1PE','060'),22:('2PE','061'),23:('1JN','062'),
24:('2JN','063'),25:('3JN','064'),26:('JUD','065'),27:('REV','066')}

COVERAGE_THRESHOLD = 95.0  # percent

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))

def has_cjk(text):
    return any('一' <= c <= '鿿' or '㐀' <= c <= '䶿' for c in text)

def main():
    print("=== CORPUS ===")
    files = sorted(GOI.glob("*.txt"))
    check("file count == 7957", len(files) == 7957, f"got {len(files)}")
    bad = [f.name for f in files if not re.fullmatch(r"\d{3}_[A-Z0-9]{3}_\d{3}_\d{3}\.txt", f.name)]
    check("filenames valid", not bad, f"{len(bad)} bad")

    issues = Counter()
    from normalize_corpus import normalize
    for f in files:
        raw = f.read_text(encoding="utf-8")
        body = raw.rstrip("\n")
        if not body.strip():
            issues['empty'] += 1
        if "\n" in body:
            issues['multiline'] += 1
        if normalize(raw) != raw:
            issues['noncanonical'] += 1
        if not has_cjk(body):
            issues['no_cjk'] += 1

    check("no empty verses",              issues['empty'] == 0,       f"{issues['empty']}")
    check("single line per verse",        issues['multiline'] == 0,   f"{issues['multiline']}")
    check("canonical punctuation/NFC",    issues['noncanonical'] == 0, f"{issues['noncanonical']} need normalize")
    check("every verse has CJK chars",    issues['no_cjk'] == 0,      f"{issues['no_cjk']} verses missing CJK")

    print("=== GREEK SOURCE ===")
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    verses = cur.execute(
        "SELECT DISTINCT book_id,chapter,verse FROM strongs_nt WHERE book_id <= 27 ORDER BY 1,2,3"
    ).fetchall()
    missing_raw = sum(
        1 for b, c, v in verses
        if not (RAW / f"{BOOK[b][1]}_{BOOK[b][0]}_{c:03d}_{v:03d}_TR1550.txt").exists()
    )
    check("every verse has TR1550 source", missing_raw == 0, f"{missing_raw} missing")

    print("=== DB INTEGRITY ===")
    check("foreign keys",
          not cur.execute("PRAGMA foreign_key_check").fetchall())
    check("override positions valid",
          cur.execute("""
              SELECT COUNT(*) FROM verse_rendering_overrides v
              LEFT JOIN strongs_nt s
                ON s.book_id=v.book_id AND s.chapter=v.chapter AND s.verse=v.verse
               AND s.word_pos=v.word_pos AND s.strongs_num=v.strongs_num
              WHERE s.id IS NULL
          """).fetchone()[0] == 0)
    check("override sense_keys in catalog",
          cur.execute("""
              SELECT COUNT(*) FROM verse_rendering_overrides
              WHERE sense_key IS NOT NULL
                AND sense_key NOT IN (SELECT sense_key FROM senses)
          """).fetchone()[0] == 0)

    print("=== NOUN COUNT (canonical to raw TR1550) ===")
    a = dict(cur.execute(
        "SELECT book_id||'-'||chapter||'-'||verse, COUNT(*) "
        "FROM strongs_nt WHERE book_id <= 27 AND morph LIKE 'N-%' AND in_tr1550=1 GROUP BY 1"
    ))
    b = dict(cur.execute(
        "SELECT v.book_id||'-'||v.chapter_number||'-'||v.verse_number, COUNT(*) "
        "FROM verse_noun_occurrences o "
        "JOIN verses v ON v.verse_id=o.verse_id WHERE v.book_id <= 27 GROUP BY 1"
    ))
    check("occurrences == strongs_nt(in_tr1550) per verse",
          sum(1 for k in set(a) | set(b) if a.get(k, 0) != b.get(k, 0)) == 0)
    conn.close()

    print("=== CHINESE COVERAGE ===")
    result = subprocess.run(
        [sys.executable, str(NIM / "verify_noun_coverage_zh.py")],
        capture_output=True, text=True, cwd=NIM
    )
    m_rate    = re.search(r"coverage rate:\s+([\d.]+)%", result.stdout)
    m_missing = re.search(r"missing:\s+(\d+)", result.stdout)
    if m_rate:
        rate    = float(m_rate.group(1))
        missing = int(m_missing.group(1)) if m_missing else -1
        check(
            f"noun coverage >= {COVERAGE_THRESHOLD}%",
            rate >= COVERAGE_THRESHOLD,
            f"{rate:.1f}%  ({missing} missing)"
        )
    else:
        check("noun coverage ran successfully", False, "no output from coverage script")

    print()
    if all(results):
        print(f"ALL {len(results)} CHECKS PASSED ✓")
        sys.exit(0)
    print(f"{results.count(False)} of {len(results)} CHECKS FAILED ✗")
    sys.exit(1)

if __name__ == "__main__":
    main()
