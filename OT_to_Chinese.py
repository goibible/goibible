#!/usr/bin/env python3
"""Translate KJV-addressed WLC Hebrew OT verses into Traditional Chinese.

Mirrors OT_to_English.py, but writes one Traditional Chinese verse per file to
GOI_Bible_Chinese_Hant/ and anchors Hebrew nouns via noun_translations(zho).

This is a REAL inference-driven translator — there is no deterministic mapping
from Hebrew morphology to fluent Traditional Chinese prose. An LLM call happens
per verse.

=====================  FILL THESE IN BEFORE RUNNING  =====================
LLM_BASE_URL    = ""   # e.g. "https://api.openai.com/v1"
LLM_MODEL       = ""   # e.g. "gpt-4.1-mini"
OPENAI_API_KEY  = ""   # or export OPENAI_API_KEY=... in your shell instead
===========================================================================

Usage:
  python3 OT_to_Chinese.py --missing-only
  python3 OT_to_Chinese.py --book GEN --chapter 1
  python3 OT_to_Chinese.py --book GEN --chapter 1 --verse 1 --dry-run
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sqlite3
import sys
import time
import unicodedata

import httpx


# ---------------------------------------------------------------------------
# Fill these in, or leave blank and export the equivalent environment variable
# (OPENAI_BASE_URL / OPENAI_MODEL / OPENAI_API_KEY) before running.
# ---------------------------------------------------------------------------
LLM_BASE_URL = "https://api.deepinfra.com/v1/openai"
LLM_MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507"
OPENAI_API_KEY = ""

ROOT = pathlib.Path(__file__).resolve().parent
NIM = ROOT / "Bible_Noun_Extraction"
if str(NIM) not in sys.path:
    sys.path.insert(0, str(NIM))

from build_wlc_kjv_source import build_grouped_segments

DB_PATH = NIM / "bible_noun.sqlite3"
SOURCE_DIR = ROOT / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
OUTPUT_DIR = ROOT / "GOI_Bible_Chinese_Hant"

BOOK_NUM = {
    "GEN": "001", "EXO": "002", "LEV": "003", "NUM": "004", "DEU": "005",
    "JOS": "006", "JDG": "007", "RUT": "008", "1SA": "009", "2SA": "010",
    "1KI": "011", "2KI": "012", "1CH": "013", "2CH": "014", "EZR": "015",
    "NEH": "016", "EST": "017", "JOB": "018", "PSA": "019", "PRO": "020",
    "ECC": "021", "SNG": "022", "ISA": "023", "JER": "024", "LAM": "025",
    "EZK": "026", "DAN": "027", "HOS": "028", "JOL": "029", "AMO": "030",
    "OBA": "031", "JON": "032", "MIC": "033", "NAM": "034", "HAB": "035",
    "ZEP": "036", "HAG": "037", "ZEC": "038", "MAL": "039",
}

BOOK_ID = {code: 28 + i for i, code in enumerate(BOOK_NUM)}
BOOK_CODE_BY_ID = {value: key for key, value in BOOK_ID.items()}
OSIS_TO_BOOK = {
    "Gen": "GEN", "Exod": "EXO", "Lev": "LEV", "Num": "NUM", "Deut": "DEU",
    "Josh": "JOS", "Judg": "JDG", "Ruth": "RUT", "1Sam": "1SA", "2Sam": "2SA",
    "1Kgs": "1KI", "2Kgs": "2KI", "1Chr": "1CH", "2Chr": "2CH", "Ezra": "EZR",
    "Neh": "NEH", "Esth": "EST", "Job": "JOB", "Ps": "PSA", "Prov": "PRO",
    "Eccl": "ECC", "Song": "SNG", "Isa": "ISA", "Jer": "JER", "Lam": "LAM",
    "Ezek": "EZK", "Dan": "DAN", "Hos": "HOS", "Joel": "JOL", "Amos": "AMO",
    "Obad": "OBA", "Jonah": "JON", "Mic": "MIC", "Nah": "NAM", "Hab": "HAB",
    "Zeph": "ZEP", "Hag": "HAG", "Zech": "ZEC", "Mal": "MAL",
}

SYSTEM_PROMPT = """You translate one verse of the Hebrew Westminster Leningrad Codex
(WLC) Old Testament into Traditional Chinese (繁體中文).

You will receive:
1. The pointed Hebrew verse text
2. Required noun anchors: each Hebrew lemma in this verse paired with its
   established Traditional Chinese rendering from the project's noun dictionary

Rules:
- Translate from the Hebrew. Do not invent content not present in the source.
- Preserve explicit negation, number, person, tense/aspect, and argument structure.
- Every noun anchor must appear in the output in an appropriate inflected form,
  rendered consistently with the supplied Chinese anchor when natural Chinese permits.
- Render the divine name (יהוה) consistently as 耶和華.
- Output exactly one verse, one line, in Traditional Chinese prose — no verse numbers,
  no commentary, no transliteration, no footnotes, no copying from other Bible versions.
- Use natural Traditional Chinese punctuation and wording, but do not drop clauses or ideas.
- When a Hebrew word or construction admits multiple plausible meanings that cannot all be expressed in Chinese, prefer the most lexically literal rendering and avoid resolving the ambiguity through interpretation or theology.
- Repeated Hebrew lexemes within the same verse should normally be translated by the same Chinese expression unless grammar makes this impossible.
"""

TARGET_SOURCE_KEYS = {
    target_ref: [
        key
        for index, key in enumerate(src.split("#", 1)[0] for src, _ in parts)
        if key not in [src.split("#", 1)[0] for src, _ in parts][:index]
    ]
    for target_ref, parts in build_grouped_segments().items()
}


def verse_output_path(book_code: str, chapter: int, verse: int) -> pathlib.Path:
    return OUTPUT_DIR / f"{BOOK_NUM[book_code]}_{book_code}_{chapter:03d}_{verse:03d}.txt"


def hebrew_source_text(book_code: str, chapter: int, verse: int) -> str:
    src = SOURCE_DIR / f"{BOOK_NUM[book_code]}_{book_code}_{chapter:03d}_{verse:03d}_WLC.txt"
    return src.read_text(encoding="utf-8").strip()


def target_source_refs(book_code: str, chapter: int, verse: int) -> list[tuple[int, int, int]]:
    source_keys = TARGET_SOURCE_KEYS.get((book_code, chapter, verse), [])
    if not source_keys and (book_code, chapter, verse) == ("NEH", 7, 68):
        source_keys = ["Ezra.2.66"]
    refs: list[tuple[int, int, int]] = []
    for key in source_keys:
        osis_book, src_chapter, src_verse = key.split(".")
        refs.append((BOOK_ID[OSIS_TO_BOOK[osis_book]], int(src_chapter), int(src_verse)))
    return refs


def noun_anchors(cur: sqlite3.Cursor, book_id: int, chapter: int, verse: int) -> list[tuple[str, str]]:
    """(surface_form, zh_rendering) for OT noun positions underlying this target verse."""
    anchors: list[tuple[str, str]] = []
    for src_book_id, src_chapter, src_verse in target_source_refs(
        BOOK_CODE_BY_ID[book_id],
        chapter,
        verse,
    ):
        rows = cur.execute(
            """
            SELECT
                so.word,
                COALESCE(nt.zh_translation, '')
            FROM verse_noun_occurrences o
            JOIN verses v
              ON v.verse_id = o.verse_id
            JOIN noun_translations nt
              ON nt.noun_id = o.noun_id
             AND nt.target_lang = 'zho'
            JOIN strongs_ot so
              ON so.book_id = v.book_id
             AND so.chapter = v.chapter_number
             AND so.verse = v.verse_number
             AND so.word_pos = o.token_index + 1
            WHERE v.book_id = ?
              AND v.chapter_number = ?
              AND v.verse_number = ?
              AND COALESCE(nt.zh_translation, '') <> ''
            ORDER BY o.token_index
            """,
            (src_book_id, src_chapter, src_verse),
        ).fetchall()
        anchors.extend((surface, zh) for surface, zh in rows if zh)
    return anchors


def build_user_prompt(hebrew: str, anchors: list[tuple[str, str]]) -> str:
    lines = [f"Hebrew verse:\n{hebrew}", "", "Noun anchors (Hebrew form -> Traditional Chinese rendering):"]
    if anchors:
        for surface, gloss in anchors:
            lines.append(f"  {surface} -> {gloss}")
    else:
        lines.append("  (none)")
    return "\n".join(lines)


def call_llm(system_prompt: str, user_prompt: str, base_url: str, model: str, api_key: str) -> str:
    resp = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "temperature": 0.2,
            "max_tokens": 512,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split())


def iter_targets(
    book_code: str | None,
    chapter: int | None,
    verse: int | None,
) -> list[tuple[str, int, int, int]]:
    if verse is not None and (book_code is None or chapter is None):
        sys.exit("--verse requires both --book and --chapter.")
    if chapter is not None and book_code is None:
        sys.exit("--chapter requires --book.")

    targets: list[tuple[str, int, int, int]] = []
    for src in sorted(SOURCE_DIR.glob("*_WLC.txt")):
        parts = src.stem.split("_")
        src_book = parts[1]
        src_chapter = int(parts[2])
        src_verse = int(parts[3])
        if book_code is not None and src_book != book_code:
            continue
        if chapter is not None and src_chapter != chapter:
            continue
        if verse is not None and src_verse != verse:
            continue
        targets.append((src_book, BOOK_ID[src_book], src_chapter, src_verse))
    if not targets:
        target = book_code or "OT"
        if chapter is not None:
            target += f" {chapter}"
        if verse is not None:
            target += f":{verse}"
        sys.exit(f"No source verses found for {target} in {SOURCE_DIR}.")
    return targets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=sorted(BOOK_NUM), help="3-letter OT book code, e.g. GEN")
    ap.add_argument("--chapter", type=int, help="Chapter within --book")
    ap.add_argument("--verse", type=int, help="Single verse only (requires --book and --chapter)")
    ap.add_argument(
        "--missing-only",
        action="store_true",
        help="Walk the whole OT and translate only missing verse files",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print prompts and result without writing files")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    args = ap.parse_args()

    if args.missing_only and args.overwrite:
        sys.exit("--missing-only and --overwrite cannot be used together.")
    if args.missing_only and (args.book or args.chapter or args.verse):
        sys.exit("--missing-only runs the whole OT; do not combine it with --book/--chapter/--verse.")
    if not args.missing_only and args.book is None:
        sys.exit("Specify --book (and usually --chapter), or use --missing-only for the whole OT.")

    base_url = LLM_BASE_URL or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = LLM_MODEL or os.environ.get("OPENAI_MODEL", "")
    api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
    if not args.dry_run and (not model or not api_key):
        sys.exit(
            "Set LLM_MODEL/OPENAI_API_KEY at the top of this file (or export "
            "OPENAI_MODEL / OPENAI_API_KEY) before running."
        )

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    targets = iter_targets(args.book, args.chapter, args.verse)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(targets)
    done = skipped = failed = 0
    run_started = time.monotonic()
    if args.missing_only:
        scope = "whole OT (missing-only)"
    elif args.verse is not None:
        scope = f"{args.book} {args.chapter}:{args.verse}"
    elif args.chapter is not None:
        scope = f"{args.book} {args.chapter}"
    else:
        scope = f"{args.book}"
    print(f"=== {scope}: {total} verse(s) | model={model or '(dry-run)'} | output -> {OUTPUT_DIR} ===")

    for i, (book_code, book_id, chapter, verse) in enumerate(targets, start=1):
        ref = f"{book_code} {chapter}:{verse}"
        out_path = verse_output_path(book_code, chapter, verse)
        progress = f"[{i}/{total}]"

        if out_path.exists() and not args.overwrite and not args.dry_run:
            skipped += 1
            print(f"  {progress} [skip] {ref} -> {out_path.name} already exists")
            continue

        hebrew = hebrew_source_text(book_code, chapter, verse)
        anchors = noun_anchors(cur, book_id, chapter, verse)
        user_prompt = build_user_prompt(hebrew, anchors)
        print(
            f"  {progress} [....] {ref}: {len(hebrew.split())} Hebrew word(s), "
            f"{len(anchors)} noun anchor(s) -> translating..."
        )

        if args.dry_run:
            print(f"=== {out_path.name} ===")
            print(f"--- system ---\n{SYSTEM_PROMPT}")
            print(f"--- user ---\n{user_prompt}")
            continue

        verse_started = time.monotonic()
        try:
            chinese = normalize(call_llm(SYSTEM_PROMPT, user_prompt, base_url, model, api_key))
        except Exception as exc:
            failed += 1
            print(f"  {progress} [FAIL] {ref}: {exc}")
            continue
        elapsed = time.monotonic() - verse_started

        out_path.write_text(chinese + "\n", encoding="utf-8")
        done += 1
        print(f"  {progress} [done] {ref} -> {out_path.name} ({elapsed:.1f}s): {chinese}")

    total_elapsed = time.monotonic() - run_started
    if not args.dry_run:
        print(
            f"=== {scope} complete in {total_elapsed:.1f}s: "
            f"{done} translated, {skipped} skipped, {failed} failed ==="
        )

    conn.close()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
