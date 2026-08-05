#!/usr/bin/env python3
"""Three-pass Greek->Vietnamese NT audit via local Gemma4.

For every NT verse, runs three independent, narrowly-scoped model calls
against the Vietnamese GOI translation:

  1. translation_fidelity_check  - meaning, grammar, omissions/additions,
                                    negation, tense/number/person
  2. strongs_coverage_check      - every Strong's-tagged lemma in the verse
                                    is represented, using the project's
                                    Strong's lexicon + established Vietnamese
                                    renderings (greek_noun.sqlite3) as ground
                                    truth fed to the model
  3. noun_consistency_check      - proper nouns / titles / theological terms
                                    extracted for the verse, checked against
                                    established renderings where known

Each pass returns strict JSON, validated against a pydantic schema, and is
saved atomically and independently per verse so the sweep is resumable at
the individual-check level (not just the verse level) -- a crash or restart
never redoes work that already produced a valid result.

Usage:
  python3 gemma4_vi_nt_audit.py               # full NT, resumable
  python3 gemma4_vi_nt_audit.py --book MAT     # one book
  python3 gemma4_vi_nt_audit.py --report       # build priority queue CSV only

Output:
  audits/<stem>.json         one record per verse, all three passes
  audit_priority.csv         union of flags per verse with priority tier
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────
# INFERENCE CONFIG
# ─────────────────────────────────────────────────────────────
MODEL = "gemma4-12b"
HOST  = "http://192.168.1.88:11434"
# ─────────────────────────────────────────────────────────────

import argparse
import csv
import json
import os
import pathlib
import re
import sqlite3
import sys
import time
from typing import Literal, Optional

import ollama
from pydantic import BaseModel, ValidationError

ROOT   = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[4]
GREEK  = REPO_ROOT / "Reference_Bible" / "Greek_Bible_TR1550" / "One_Directory_TR1550"
DB     = REPO_ROOT / "Meta_Bible_Data" / "Bible_Noun_Extraction" / "greek_noun.sqlite3"
VI_DIR = REPO_ROOT / "GOI_Bible" / "GOI_Bible_vi"
AUDITS = ROOT / "audits"
PRIORITY_CSV = ROOT / "audit_priority.csv"

CHECK_KEYS = ("translation_fidelity", "strongs_coverage", "noun_consistency")


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class FidelityIssue(BaseModel):
    kind: Literal["omission", "addition", "mistranslation", "negation",
                  "number_person_tense", "other"]
    detail: str

class FidelityResult(BaseModel):
    verdict: Literal["OK", "FLAG"]
    issues: list[FidelityIssue] = []
    confidence: float

class StrongsIssue(BaseModel):
    strongs_num: int
    lemma: str
    problem: Literal["missing", "distorted", "unjustified_addition"]
    detail: str

class StrongsResult(BaseModel):
    verdict: Literal["OK", "FLAG"]
    issues: list[StrongsIssue] = []
    confidence: float

class NounIssue(BaseModel):
    surface_form: str
    category: str
    problem: Literal["missing", "wrong_name", "inconsistent_rendering", "other"]
    detail: str

class NounResult(BaseModel):
    verdict: Literal["OK", "FLAG"]
    issues: list[NounIssue] = []
    confidence: float

SCHEMAS: dict[str, type[BaseModel]] = {
    "translation_fidelity": FidelityResult,
    "strongs_coverage":     StrongsResult,
    "noun_consistency":     NounResult,
}


# ─────────────────────────────────────────────────────────────
# Ground-truth lookups (greek_noun.sqlite3)
# ─────────────────────────────────────────────────────────────

def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_strongs_rows(conn: sqlite3.Connection, book: str, ch: int, vs: int) -> list[dict]:
    rows = conn.execute("""
        SELECT snt.word_pos, snt.word, snt.strongs_num, snt.morph,
               sr.translit, sr.english,
               slv.rendering AS vi_rendering,
               lex.definition AS lex_definition
        FROM strongs_nt snt
        JOIN books b ON b.book_id = snt.book_id
        LEFT JOIN strongs_renderings sr ON sr.strongs_num = snt.strongs_num
        LEFT JOIN strongs_lang_renderings slv
               ON slv.strongs_num = snt.strongs_num AND slv.lang = 'vi'
        LEFT JOIN strongs_lexicon lex
               ON lex.strongs_num = snt.strongs_num AND lex.language = 'G'
        WHERE b.book_code = ? AND snt.chapter = ? AND snt.verse = ?
              AND snt.in_tr1550 = 1
        ORDER BY snt.word_pos
    """, (book, ch, vs)).fetchall()
    return [dict(r) for r in rows]


def get_noun_rows(conn: sqlite3.Connection, book: str, ch: int, vs: int) -> list[dict]:
    rows = conn.execute("""
        SELECT o.surface_form, n.lemma, c.category_code AS category,
               slv.rendering AS established_vi_rendering
        FROM verse_noun_occurrences o
        JOIN verses v ON v.verse_id = o.verse_id
        JOIN books b ON b.book_id = v.book_id
        JOIN nouns n ON n.noun_id = o.noun_id
        JOIN noun_categories c ON c.category_id = o.category_id
        LEFT JOIN strongs_lexicon lex ON lex.lemma = n.lemma AND lex.language = 'G'
        LEFT JOIN strongs_lang_renderings slv
               ON slv.strongs_num = lex.strongs_num AND slv.lang = 'vi'
        WHERE b.book_code = ? AND v.chapter_number = ? AND v.verse_number = ?
              AND o.version_id = 1
        ORDER BY o.token_index
    """, (book, ch, vs)).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────

def clean_greek(greek: str) -> str:
    greek = re.sub(r"^\[\d+:\d+\]\s*", "", greek)
    return greek.replace("[", "").replace("]", "").strip()


def fidelity_prompt(greek: str, vietnamese: str) -> tuple[str, str]:
    system = (
        "You are a Greek New Testament scholar checking ONLY translation fidelity: "
        "meaning, grammar, omissions, additions, negation, tense, number, and person. "
        "Do not comment on proper names or lexical/Strong's-level word choice -- those "
        "are handled by separate checks.\n\n"
        "FLAG ONLY if a Vietnamese reader would come away believing something factually "
        "different from, or missing something substantive that is present in, the Greek. "
        "If you are not sure, or the difference is purely stylistic, mark OK. When in "
        "doubt, OK.\n\n"
        "Do NOT flag any of the following -- they are correct, idiomatic translation, "
        "not errors:\n"
        "- Natural Vietnamese connectors/appositive markers with no Greek equivalent "
        "word (e.g. 'tức là', 'là', 'rằng') inserted to make the sentence read naturally.\n"
        "- Prepositions or particles rendered by Vietnamese word order or a synonym "
        "instead of a literal one-to-one gloss (e.g. Greek 'kata' -> Vietnamese "
        "possessive/locative construction with no separate preposition word).\n"
        "- A relative clause, verb tense choice, or clause structure that conveys the "
        "same meaning as the Greek even if the surface grammar differs.\n"
        "- Any translation choice you would still consider 'a close/acceptable "
        "rendering' after your own explanation -- if your explanation ends up agreeing "
        "the Vietnamese is basically right, the verdict must be OK, not FLAG.\n"
        "- Word order, paraphrase that preserves meaning, or pronouns/subjects added "
        "for natural Vietnamese.\n\n"
        "Only use FLAG for: a name/number/negation reversed or dropped, a clause or "
        "concept entirely missing, a concept added that has no basis in the Greek and "
        "changes the verse's claim, or a wrong tense/person that changes who is doing "
        "what to whom.\n\n"
        "Respond with JSON only, matching this schema:\n"
        f"{json.dumps(FidelityResult.model_json_schema())}"
    )
    user = f"GREEK: {clean_greek(greek)}\nVIETNAMESE: {vietnamese.strip()}"
    return system, user


def strongs_prompt(greek: str, vietnamese: str, rows: list[dict]) -> tuple[str, str]:
    lines = []
    for r in rows:
        gloss = r["vi_rendering"] or r["english"] or r["lex_definition"] or "?"
        lines.append(f"  #{r['strongs_num']} {r['word']} ({r['translit'] or ''}) "
                     f"[{r['morph'] or ''}] -> expected sense: {gloss}")
    lexicon_block = "\n".join(lines) if lines else "  (no Strong's data for this verse)"
    system = (
        "You are a Greek New Testament lexicographer checking ONLY Strong's-lemma "
        "coverage. You are given the ordered Strong's-tagged words of the Greek verse, "
        "each with its expected sense, and the Vietnamese translation. Confirm every "
        "meaningful lemma (skip pure grammar words: articles, particles like δε/και/γαρ "
        "unless they carry real semantic weight) is represented correctly in the "
        "Vietnamese. Flag a lemma only if it is missing, its sense is distorted, or the "
        "Vietnamese adds a concept with no corresponding lemma.\n\n"
        "Prepositions and conjunctions are very often correctly rendered by Vietnamese "
        "word order, a possessive construction, or a natural connector instead of a "
        "separate preposition word -- that is NOT missing or distorted, do not flag it. "
        "If your own explanation says the rendering is 'acceptable' or 'close', the "
        "verdict must be OK, not FLAG. When in doubt, OK.\n\n"
        "Respond with JSON only, matching this schema:\n"
        f"{json.dumps(StrongsResult.model_json_schema())}"
    )
    user = (f"GREEK: {clean_greek(greek)}\nVIETNAMESE: {vietnamese.strip()}\n\n"
             f"STRONG'S WORDS IN ORDER:\n{lexicon_block}")
    return system, user


def noun_prompt(vietnamese: str, rows: list[dict]) -> tuple[str, str]:
    lines = []
    for r in rows:
        established = f" -> established Vietnamese rendering: {r['established_vi_rendering']}" \
            if r["established_vi_rendering"] else ""
        lines.append(f"  {r['surface_form']} ({r['lemma']}) [{r['category']}]{established}")
    noun_block = "\n".join(lines) if lines else "  (no nouns extracted for this verse)"
    system = (
        "You are checking ONLY proper-noun and theological-term consistency in a "
        "Vietnamese New Testament translation. You are given the Greek nouns extracted "
        "for this verse (person/place/God names, titles, and other nouns), some with an "
        "established project rendering. For each PERSON, PLACE, or GOD category noun, "
        "confirm the Vietnamese uses the correct name/title and does not drop, swap, or "
        "misidentify it. Where an established rendering is given, the Vietnamese should "
        "match it (minor grammatical inflection is fine). Do not flag common nouns "
        "(category OTHER) unless they are a project theological term rendered "
        "inconsistently.\n\n"
        "Respond with JSON only, matching this schema:\n"
        f"{json.dumps(NounResult.model_json_schema())}"
    )
    user = f"VIETNAMESE: {vietnamese.strip()}\n\nGREEK NOUNS EXTRACTED:\n{noun_block}"
    return system, user


# ─────────────────────────────────────────────────────────────
# Model call + validation
# ─────────────────────────────────────────────────────────────

def call_check(client: ollama.Client, schema: type[BaseModel],
               system: str, user: str, attempts: int = 3) -> dict:
    last_err = None
    for attempt in range(attempts):
        try:
            resp = client.chat(
                model=MODEL,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                format="json",
                options={"temperature": 0},
            )
            content = resp["message"]["content"]
            parsed = schema.model_validate_json(content)
            return {"ok": True, "result": parsed.model_dump()}
        except (ValidationError, json.JSONDecodeError, KeyError, Exception) as e:
            last_err = str(e)
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
    return {"ok": False, "error": last_err}


# ─────────────────────────────────────────────────────────────
# Per-verse audit record: load / save atomically / is-valid
# ─────────────────────────────────────────────────────────────

def audit_path(stem: str) -> pathlib.Path:
    return AUDITS / f"{stem}.json"


def load_record(stem: str) -> dict:
    p = audit_path(stem)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def check_is_valid(record: dict, key: str) -> bool:
    entry = record.get(key)
    if not isinstance(entry, dict) or not entry.get("ok"):
        return False
    try:
        SCHEMAS[key].model_validate(entry["result"])
        return True
    except (ValidationError, KeyError):
        return False


def save_record_atomic(stem: str, record: dict) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    target = audit_path(stem)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)


# ─────────────────────────────────────────────────────────────
# Verse iteration
# ─────────────────────────────────────────────────────────────

def iter_verses(book_filter: Optional[str]):
    for gf in sorted(GREEK.glob("*.txt")):
        stem = gf.stem.replace("_TR1550", "")
        code = stem[4:7]
        if book_filter and code != book_filter.upper():
            continue
        ch = int(stem[8:11])
        vs = int(stem[12:15])
        vf = VI_DIR / f"{stem}_GOI_vi.txt"
        if not vf.exists():
            continue
        yield stem, code, ch, vs, gf, vf


# ─────────────────────────────────────────────────────────────
# Report / priority queue
# ─────────────────────────────────────────────────────────────

FLAG_LABELS = {"translation_fidelity": "TRANSLATION",
               "strongs_coverage": "STRONGS",
               "noun_consistency": "NOUN"}


def build_report() -> None:
    rows_out = []
    for p in sorted(AUDITS.glob("*.json")):
        record = json.loads(p.read_text(encoding="utf-8"))
        flags = []
        for key, label in FLAG_LABELS.items():
            entry = record.get(key)
            if isinstance(entry, dict) and entry.get("ok") and entry["result"]["verdict"] == "FLAG":
                flags.append(label)
        if not flags:
            continue
        priority = {1: "normal", 2: "priority", 3: "mandatory"}[len(flags)]
        rows_out.append({
            "book": record.get("book", ""), "chapter": record.get("chapter", ""),
            "verse": record.get("verse", ""), "flags": ",".join(flags),
            "priority": priority,
        })
    with PRIORITY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["book", "chapter", "verse", "flags", "priority"])
        w.writeheader()
        w.writerows(rows_out)
    counts = {"mandatory": 0, "priority": 0, "normal": 0}
    for r in rows_out:
        counts[r["priority"]] += 1
    print(f"Priority queue: {PRIORITY_CSV}")
    print(f"  mandatory={counts['mandatory']}  priority={counts['priority']}  normal={counts['normal']}")
    print(f"  total flagged verses: {len(rows_out)}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", help="limit to one book e.g. MAT")
    ap.add_argument("--report", action="store_true",
                     help="build audit_priority.csv from existing audits/*.json and exit")
    ap.add_argument("--checks", default=",".join(CHECK_KEYS),
                     help="comma-separated subset of checks to run "
                          "(default: all three). E.g. --checks translation_fidelity")
    args = ap.parse_args()

    if args.report:
        build_report()
        return

    active_checks = tuple(args.checks.split(","))
    for k in active_checks:
        if k not in CHECK_KEYS:
            sys.exit(f"Unknown check {k!r}; choose from {CHECK_KEYS}")

    client = ollama.Client(host=HOST)
    conn = db_connect()

    verses = list(iter_verses(args.book))
    total = len(verses)
    if total == 0:
        sys.exit("No matching verses found (check --book and that GOI_vi files exist).")

    done_verses = errors = 0
    for i, (stem, code, ch, vs, gf, vf) in enumerate(verses, 1):
        record = load_record(stem)
        record["book"], record["chapter"], record["verse"] = code, ch, vs

        if all(check_is_valid(record, k) for k in active_checks):
            done_verses += 1
            continue

        greek = gf.read_text(encoding="utf-8")
        vietnamese = vf.read_text(encoding="utf-8")
        status_parts = []

        if "translation_fidelity" in active_checks and not check_is_valid(record, "translation_fidelity"):
            system, user = fidelity_prompt(greek, vietnamese)
            record["translation_fidelity"] = call_check(client, FidelityResult, system, user)
            save_record_atomic(stem, record)
            status_parts.append(_status("TR", record["translation_fidelity"]))

        if "strongs_coverage" in active_checks and not check_is_valid(record, "strongs_coverage"):
            rows = get_strongs_rows(conn, code, ch, vs)
            system, user = strongs_prompt(greek, vietnamese, rows)
            record["strongs_coverage"] = call_check(client, StrongsResult, system, user)
            save_record_atomic(stem, record)
            status_parts.append(_status("STR", record["strongs_coverage"]))

        if "noun_consistency" in active_checks and not check_is_valid(record, "noun_consistency"):
            rows = get_noun_rows(conn, code, ch, vs)
            system, user = noun_prompt(vietnamese, rows)
            record["noun_consistency"] = call_check(client, NounResult, system, user)
            save_record_atomic(stem, record)
            status_parts.append(_status("NOUN", record["noun_consistency"]))

        if any(not r["ok"] for r in
               (record.get(k, {"ok": True}) for k in active_checks) if isinstance(r, dict)):
            errors += 1

        pct = 100 * i / total
        print(f"[{i}/{total} {pct:.1f}%] {code} {ch}:{vs} -> {'  '.join(status_parts) or 'cached'}")

    conn.close()
    print(f"\nDone. already_complete={done_verses}  processed={total - done_verses}  errors_seen={errors}")
    print(f"Audits: {AUDITS}")
    print("Run with --report to build the priority queue CSV.")


def _status(label: str, entry: dict) -> str:
    if not entry.get("ok"):
        return f"{label}=ERROR"
    return f"{label}={entry['result']['verdict']}"


if __name__ == "__main__":
    main()
