#!/usr/bin/env python3
"""Project integrity gate. Asserts every invariant the pipeline relies on and
exits non-zero on any violation. Run after ANY edit to the corpus or DB —
by a human or by an LLM translating the next language.

  python3 validate.py            # validate the English corpus + DB
  python3 validate.py --lang en  # same, explicit

Checks (each prints PASS/FAIL):
  CORPUS   file count, naming, single-line, non-empty, NFC, canonical punctuation
  GREEK    every (book,ch,verse) has a raw TR1550 source file
  DB       FK integrity; override positions valid; sense_key catalog; sense en
  NOUNS    verse_noun_occurrences == strongs_nt(in_tr1550) per verse;
           every occurrence surface physically present in its raw verse
  COVERAGE English noun coverage == 0 missing (delegates to verify_noun_coverage)
"""
import argparse, pathlib, re, sqlite3, subprocess, sys, unicodedata
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent
GOI  = ROOT / "GOI_Bible_English"
NIM  = ROOT / "Bible_Noun_Extraction_NIM"
DB   = NIM / "bible_noun.sqlite3"
RAW  = NIM / "One_Directory_TR1550"
BOOK = {1:('MAT','040'),2:('MRK','041'),3:('LUK','042'),4:('JHN','043'),5:('ACT','044'),
6:('ROM','045'),7:('1CO','046'),8:('2CO','047'),9:('GAL','048'),10:('EPH','049'),11:('PHP','050'),
12:('COL','051'),13:('1TH','052'),14:('2TH','053'),15:('1TI','054'),16:('2TI','055'),17:('TIT','056'),
18:('PHM','057'),19:('HEB','058'),20:('JAS','059'),21:('1PE','060'),22:('2PE','061'),23:('1JN','062'),
24:('2JN','063'),25:('3JN','064'),26:('JUD','065'),27:('REV','066')}

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))

def norm_tokens(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('ς','σ')
    s = re.sub(r"^\[\d+:\d+\]\s*", "", s).replace('[',' ').replace(']',' ')
    s = re.sub(r"[·.,;:!?\"'«»()]", ' ', s)
    return Counter(t for t in s.split() if t)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()

    print("=== CORPUS ===")
    files = sorted(GOI.glob("*.txt"))
    check("file count == 7957", len(files) == 7957, f"got {len(files)}")
    bad = [f.name for f in files if not re.fullmatch(r"\d{3}_[A-Z0-9]{3}_\d{3}_\d{3}\.txt", f.name)]
    check("filenames valid", not bad, f"{len(bad)} bad")
    issues = Counter()
    from normalize_corpus import normalize
    for f in files:
        raw = f.read_text(encoding="utf-8"); body = raw.rstrip("\n")
        if not body.strip(): issues['empty'] += 1
        if "\n" in body: issues['multiline'] += 1
        if normalize(raw) != raw: issues['noncanonical'] += 1
    check("no empty verses", issues['empty'] == 0, f"{issues['empty']}")
    check("single line per verse", issues['multiline'] == 0, f"{issues['multiline']}")
    check("canonical punctuation/NFC", issues['noncanonical'] == 0, f"{issues['noncanonical']} need normalize")

    print("=== GREEK SOURCE ===")
    conn = sqlite3.connect(DB); cur = conn.cursor()
    verses = cur.execute(
        "SELECT DISTINCT book_id,chapter,verse FROM strongs_nt WHERE book_id <= 27 ORDER BY 1,2,3"
    ).fetchall()
    missing_raw = sum(1 for b,c,v in verses if not (RAW/f"{BOOK[b][1]}_{BOOK[b][0]}_{c:03d}_{v:03d}_TR1550.txt").exists())
    check("every verse has TR1550 source", missing_raw == 0, f"{missing_raw} missing")

    print("=== DB INTEGRITY ===")
    check("foreign keys", not cur.execute("PRAGMA foreign_key_check").fetchall())
    check("override positions valid", cur.execute("""SELECT COUNT(*) FROM verse_rendering_overrides v
        LEFT JOIN strongs_nt s ON s.book_id=v.book_id AND s.chapter=v.chapter AND s.verse=v.verse
        AND s.word_pos=v.word_pos AND s.strongs_num=v.strongs_num WHERE s.id IS NULL""").fetchone()[0] == 0)
    check("override sense_keys in catalog", cur.execute("""SELECT COUNT(*) FROM verse_rendering_overrides
        WHERE sense_key IS NOT NULL AND sense_key NOT IN (SELECT sense_key FROM senses)""").fetchone()[0] == 0)
    check("every sense has 'en' rendering", cur.execute("""SELECT COUNT(*) FROM senses s WHERE NOT EXISTS
        (SELECT 1 FROM sense_renderings r WHERE r.sense_key=s.sense_key AND r.lang='en')""").fetchone()[0] == 0)

    print("=== NOUN COUNT (canonical to raw TR1550) ===")
    a = dict(cur.execute(
        "SELECT book_id||'-'||chapter||'-'||verse,COUNT(*) FROM strongs_nt "
        "WHERE book_id <= 27 AND morph LIKE 'N-%' AND in_tr1550=1 GROUP BY 1"
    ))
    b = dict(cur.execute("""SELECT v.book_id||'-'||v.chapter_number||'-'||v.verse_number,COUNT(*)
        FROM verse_noun_occurrences o JOIN verses v ON v.verse_id=o.verse_id
        WHERE v.book_id <= 27 GROUP BY 1"""))
    check("occurrences == strongs_nt(in_tr1550) per verse",
          sum(1 for k in set(a)|set(b) if a.get(k,0)!=b.get(k,0)) == 0)
    vmap = dict(cur.execute("SELECT verse_id, book_id||','||chapter_number||','||verse_number FROM verses WHERE book_id <= 27"))
    rawc = {}
    bad_surf = 0
    # multiplicity-aware: each occurrence surface present in its raw verse
    surf_by_v = Counter()
    rows = cur.execute("""SELECT o.verse_id,o.surface_form FROM verse_noun_occurrences o
        JOIN verses v ON v.verse_id=o.verse_id WHERE v.book_id <= 27""").fetchall()
    def rawtok(b,c,v):
        k=(b,c,v)
        if k in rawc: return rawc[k]
        p = RAW/f"{BOOK[b][1]}_{BOOK[b][0]}_{c:03d}_{v:03d}_TR1550.txt"
        if not p.exists(): rawc[k]=Counter(); return rawc[k]
        rawc[k]=norm_tokens(p.read_text(encoding='utf-8')); return rawc[k]
    def nrm(s):
        s=unicodedata.normalize('NFD',s.lower()); return ''.join(c for c in s if unicodedata.category(c)!='Mn').replace('ς','σ')
    for vid,surf in rows: surf_by_v[(vid,nrm(surf))]+=1
    for (vid,s),n in surf_by_v.items():
        b,c,v=(int(x) for x in vmap[vid].split(','));
        if rawtok(b,c,v)[s] < n: bad_surf+=1
    check("every noun surface present in its raw verse", bad_surf == 0, f"{bad_surf} not found")
    conn.close()

    print("=== ENGLISH COVERAGE ===")
    if args.lang == "en":
        out = subprocess.run([sys.executable, str(NIM/"verify_noun_coverage.py")],
                             capture_output=True, text=True, cwd=NIM).stdout
        m = re.search(r"missing:\s+(\d+)", out)
        check("noun coverage 0 missing", bool(m) and int(m.group(1)) == 0,
              f"{m.group(1) if m else '?'} missing")
    else:
        print(f"  [SKIP] coverage check defined only for 'en' (see matchers.py for other langs)")

    print()
    if all(results):
        print(f"ALL {len(results)} CHECKS PASSED ✓"); sys.exit(0)
    print(f"{results.count(False)} of {len(results)} CHECKS FAILED ✗"); sys.exit(1)

if __name__ == "__main__":
    main()
