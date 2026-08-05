#!/usr/bin/env python3
"""Verse-by-verse Greek→Vietnamese NT translation check via local Gemma4.

Compares the raw Greek (TR1550) with the GOI_Bible_vi Vietnamese translation
and asks a local Ollama model to flag anything it questions: dropped clauses,
mistranslated words, flipped negatives, wrong names/numbers, or meaning that
doesn't match the Greek. This is a broad "does this look right" pass, not a
narrow clause-completeness check.

Usage:
  python3 gemma4_vi_nt_verify.py [--book MAT] [--resume]
  python3 gemma4_vi_nt_verify.py --missing-only

Output (written next to this script):
  gemma4_vi_nt_verify_results.csv   — all reviewed verses (verdict + note)
  gemma4_vi_nt_verify_flagged.csv   — FLAGGED only (the shortlist to fix)
"""

# ─────────────────────────────────────────────────────────────
# INFERENCE CONFIG
# ─────────────────────────────────────────────────────────────
MODEL = "gemma4-12b"
HOST  = "http://192.168.1.88:11434"
# ─────────────────────────────────────────────────────────────

import argparse, csv, pathlib, re, sys, time
import ollama

ROOT  = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[4]
RAW   = REPO_ROOT / "Reference_Bible" / "Greek_Bible_TR1550" / "One_Directory_TR1550"
VI_DIR = REPO_ROOT / "GOI_Bible" / "GOI_Bible_vi"

RESULTS_CSV = ROOT / "gemma4_vi_nt_verify_results.csv"
FLAGGED_CSV = ROOT / "gemma4_vi_nt_verify_flagged.csv"

SYSTEM = """You are a Greek New Testament scholar who also reads Vietnamese fluently.
You will be given:
  GREEK: a raw Greek verse (Textus Receptus, unaccented)
  VIETNAMESE: its translation

Your task: decide whether the Vietnamese accurately conveys the Greek. Flag any of:
  - a dropped clause, predicate, or whole idea present in the Greek but absent from the Vietnamese
  - a mistranslated word or phrase that changes the meaning
  - a flipped or missing negation
  - a wrong name, number, or person/tense (singular vs plural, wrong verb tense)
  - Vietnamese that states something the Greek does not say

Do NOT flag:
  - style or word-order differences
  - paraphrases that convey the same meaning differently
  - implied subjects/pronouns added for natural Vietnamese
  - traditional Vietnamese renderings of divine names/titles

Respond with exactly one of:
  OK
  FLAG: <one-sentence description in English of what is wrong>

Nothing else. No explanation beyond the flag line."""


def make_prompt(greek: str, vietnamese: str) -> str:
    greek = re.sub(r"^\[\d+:\d+\]\s*", "", greek).replace("[", "").replace("]", "").strip()
    return f"GREEK: {greek}\nVIETNAMESE: {vietnamese.strip()}"


def call_llm(client: ollama.Client, greek: str, vietnamese: str) -> str:
    for attempt in range(3):
        try:
            resp = client.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": make_prompt(greek, vietnamese)},
                ],
                options={"temperature": 0},
            )
            return resp["message"]["content"].strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                return f"ERROR: {e}"


def load_done(book_filter: str | None) -> set:
    done = set()
    if not RESULTS_CSV.exists():
        return done
    with RESULTS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if book_filter and row["book"] != book_filter:
                continue
            done.add((row["book"], row["chapter"], row["verse"]))
    return done


def iter_verses(book_filter: str | None):
    for gf in sorted(RAW.glob("*.txt")):
        stem = gf.stem.replace("_TR1550", "")
        code = stem[4:7]
        if book_filter and code != book_filter.upper():
            continue
        ch = stem[8:11].lstrip("0")
        vs = stem[12:15].lstrip("0")
        vf = VI_DIR / f"{stem}_GOI_vi.txt"
        if not vf.exists():
            continue
        yield code, ch, vs, gf, vf


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", help="limit to one book e.g. MAT")
    ap.add_argument("--resume", action="store_true",
                     help="skip already-reviewed verses in results CSV")
    ap.add_argument("--missing-only", action="store_true",
                     help="print FLAGGED rows from existing results and exit (no model calls)")
    args = ap.parse_args()

    if args.missing_only:
        if not FLAGGED_CSV.exists():
            sys.exit("No flagged CSV found. Run without --missing-only first.")
        with FLAGGED_CSV.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        print(f"{len(rows)} flagged verses:\n")
        for r in rows:
            print(f"  {r['book']} {r['chapter']}:{r['verse']}: {r['note']}")
            print(f"    {r['vietnamese'][:90]}")
        return

    client = ollama.Client(host=HOST)

    done = load_done(args.book) if args.resume else set()
    verses = list(iter_verses(args.book))
    total = len(verses)
    if total == 0:
        sys.exit("No matching verses found (check --book and that GOI_vi files exist).")

    mode = "a" if args.resume and RESULTS_CSV.exists() else "w"
    rf = RESULTS_CSV.open(mode, newline="", encoding="utf-8")
    ff = FLAGGED_CSV.open(mode, newline="", encoding="utf-8")
    fields = ["book", "chapter", "verse", "verdict", "note", "vietnamese"]
    rw = csv.DictWriter(rf, fieldnames=fields)
    fw = csv.DictWriter(ff, fieldnames=fields)
    if mode == "w":
        rw.writeheader(); fw.writeheader()

    flagged = ok = errors = 0
    for i, (code, ch, vs, gf, vf) in enumerate(verses, 1):
        key_tuple = (code, ch, vs)
        if key_tuple in done:
            continue
        greek = gf.read_text(encoding="utf-8")
        vietnamese = vf.read_text(encoding="utf-8")
        answer = call_llm(client, greek, vietnamese)
        is_flag = answer.upper().startswith("FLAG")
        is_error = answer.upper().startswith("ERROR")
        note = answer[5:].strip().lstrip(":").strip() if is_flag else answer if is_error else ""
        row = {"book": code, "chapter": ch, "verse": vs,
               "verdict": "FLAG" if is_flag else ("ERROR" if is_error else "OK"),
               "note": note, "vietnamese": vietnamese.strip()}
        rw.writerow(row); rf.flush()
        if is_flag:
            fw.writerow(row); ff.flush()
            flagged += 1
        elif is_error:
            errors += 1
        else:
            ok += 1
        pct = 100 * i / total
        print(f"[{i}/{total} {pct:.1f}%] {code} {ch}:{vs} -> {row['verdict']}"
              + (f"  <- {note[:60]}" if is_flag else ""))

    rf.close(); ff.close()
    print(f"\nDone. ok={ok}  flagged={flagged}  errors={errors}")
    print(f"Results : {RESULTS_CSV}")
    print(f"Flagged : {FLAGGED_CSV}")


if __name__ == "__main__":
    main()
