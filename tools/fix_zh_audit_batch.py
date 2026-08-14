#!/usr/bin/env python3
"""Fix Chinese audit-priority verses in bounded batches.

Uses the repo .env OpenAI-compatible endpoint. The script rewrites Traditional
Chinese verse files only for flagged rows whose Hant file has no git diff yet,
then mirrors each changed Hant verse to Simplified Chinese with OpenCC.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import re
import subprocess
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI
from opencc import OpenCC


ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "Meta_Bible_Data" / "staging" / "reports" / "zh" / "audits"
HANT_DIR = ROOT / "GOI_Bible" / "GOI_Bible_Chinese_Hant"
HANS_DIR = ROOT / "GOI_Bible" / "GOI_Bible_Chinese_Hans"
STATE_DIR = ROOT / "state"
HEBREW_DIR = ROOT / "Reference_Bible" / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
GREEK_DIR = ROOT / "Reference_Bible" / "Greek_Bible_TR1550" / "One_Directory_TR1550"
KJV_DIR = ROOT / "Reference_Bible" / "English_Bible_KJV" / "One_Directory_KJV"
CUV_DIR = ROOT / "Reference_Bible" / "Chinese_Bible_CUV" / "One_Directory_CUV"

OT_BOOKS = "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL".split()
NT_BOOKS = "MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV".split()
BOOK_NUM = {book: f"{i:03d}" for i, book in enumerate(OT_BOOKS + NT_BOOKS, start=1)}

SYSTEM = """You are correcting one verse in the GOI Traditional Chinese Bible.

You receive the source-language verse, KJV reference, CUV reference, current GOI
Traditional Chinese verse, and a machine-audit issue.

Task:
- Return a corrected Traditional Chinese verse that fixes the substantive audit issue.
- Preserve the GOI style where possible.
- Do not add commentary, verse numbers, footnotes, or alternatives.
- Keep exactly one verse on one line.
- If the audit issue itself says the flag was mistaken or only stylistic, make the
  smallest safe correction, or keep the verse unchanged if there is genuinely no
  substantive source-fidelity problem.

Respond as JSON only: {"revision": "..."}.
"""


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def changed_hant_paths() -> set[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "--", str(HANT_DIR.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
    )
    return set(out.splitlines())


def audit_detail(kind: str, book: str, chapter: int, verse: int, row: dict[str, str]) -> str:
    if kind == "ot":
        return row["issues"]
    audit_json = AUDIT_DIR / "audits" / f"{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}.json"
    if not audit_json.exists():
        return row.get("flags", "")
    data = json.loads(audit_json.read_text(encoding="utf-8"))
    issues = []
    for check in ("translation_fidelity", "strongs_coverage", "noun_consistency"):
        result = data.get(check, {}).get("result", {})
        if result.get("verdict") == "FLAG":
            for issue in result.get("issues", []):
                detail = issue.get("detail") or json.dumps(issue, ensure_ascii=False)
                issues.append(f"{check}: {detail}")
    return "\n".join(issues) or row.get("flags", "")


def source_text(kind: str, book: str, chapter: int, verse: int) -> str:
    num = BOOK_NUM[book]
    if kind == "ot":
        return read(HEBREW_DIR / f"{num}_{book}_{chapter:03d}_{verse:03d}_WLC.txt")
    return read(GREEK_DIR / f"{num}_{book}_{chapter:03d}_{verse:03d}_TR1550.txt")


def kjv_text(book: str, chapter: int, verse: int) -> str:
    return read(KJV_DIR / f"{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}_KJV.txt")


def cuv_text(book: str, chapter: int, verse: int) -> str:
    return read(CUV_DIR / f"{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}_CUV.txt")


def hant_path(book: str, chapter: int, verse: int) -> pathlib.Path:
    return HANT_DIR / f"{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}_GOI_Zh_Hant.txt"


def hans_path_for(hant: pathlib.Path) -> pathlib.Path:
    return HANS_DIR / hant.name.replace("_GOI_Zh_Hant.txt", "_GOI_Zh_Hans.txt")


def normalize_revision(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text).strip()
    try:
        data = json.loads(text)
        text = str(data["revision"])
    except Exception:
        pass
    text = " ".join(text.split())
    if not text:
        raise ValueError("empty model revision")
    if "\n" in text:
        raise ValueError("revision contains newline")
    return text


def iter_rows(kind: str) -> list[tuple[str, int, int, dict[str, str]]]:
    csv_path = AUDIT_DIR / ("audit_priority_ot.csv" if kind == "ot" else "audit_priority.csv")
    rows = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append((row["book"], int(row["chapter"]), int(row["verse"]), row))
    return rows


def processed_state_path(kind: str) -> pathlib.Path:
    return STATE_DIR / f"fix_zh_audit_batch_{kind}_processed.txt"


def load_processed(kind: str) -> set[str]:
    path = processed_state_path(kind)
    if not path.exists():
        return set()
    return set(path.read_text(encoding="utf-8").splitlines())


def append_processed(kind: str, paths: list[pathlib.Path]) -> None:
    if not paths:
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with processed_state_path(kind).open("a", encoding="utf-8") as handle:
        for path in paths:
            handle.write(str(path.relative_to(ROOT)) + "\n")


def build_prompt(kind: str, book: str, chapter: int, verse: int, issue: str, current: str) -> str:
    label = "Hebrew WLC" if kind == "ot" else "Greek TR1550"
    return "\n\n".join(
        [
            f"Reference: {book} {chapter}:{verse}",
            f"{label}:\n{source_text(kind, book, chapter, verse)}",
            f"KJV:\n{kjv_text(book, chapter, verse)}",
            f"CUV Chinese reference:\n{cuv_text(book, chapter, verse)}",
            f"Current GOI Traditional Chinese:\n{current}",
            f"Audit issue to fix:\n{issue}",
        ]
    )


def call_model(client: OpenAI, model: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return normalize_revision(response.choices[0].message.content or "")


def sync_hans(paths: list[pathlib.Path]) -> int:
    cc = OpenCC("t2s")
    count = 0
    for path in paths:
        target = hans_path_for(path)
        expected = cc.convert(path.read_text(encoding="utf-8"))
        if target.read_text(encoding="utf-8") != expected:
            target.write_text(expected, encoding="utf-8")
            count += 1
    return count


def sync_all_mismatched_hans() -> int:
    return sync_hans(sorted(HANT_DIR.glob("*.txt")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("ot", "nt"), default="ot")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--include-touched", action="store_true")
    parser.add_argument("--sync-only", action="store_true")
    args = parser.parse_args()

    if args.sync_only:
        print(f"synced {sync_all_mismatched_hans()} Hans file(s)")
        return 0

    load_dotenv(ROOT / ".env")
    base_url = os.environ["OPENAI_BASE_URL"]
    model = os.environ["OPENAI_MODEL"]
    api_key = os.environ["OPENAI_API_KEY"]
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=180.0, max_retries=1)

    changed = changed_hant_paths()
    processed = load_processed(args.kind)
    selected = []
    for book, chapter, verse, row in iter_rows(args.kind):
        path = hant_path(book, chapter, verse)
        rel = str(path.relative_to(ROOT))
        if path.exists() and rel not in processed and (args.include_touched or rel not in changed):
            selected.append((book, chapter, verse, row, path))
        if len(selected) >= args.limit:
            break

    if not selected:
        print(f"no {args.kind.upper()} rows selected")
        print(f"synced {sync_all_mismatched_hans()} Hans file(s)")
        return 0

    written: list[pathlib.Path] = []
    for index, (book, chapter, verse, row, path) in enumerate(selected, start=1):
        issue = audit_detail(args.kind, book, chapter, verse, row)
        current = read(path)
        prompt = build_prompt(args.kind, book, chapter, verse, issue, current)
        started = time.monotonic()
        revision = call_model(client, model, prompt)
        path.write_text(revision + "\n", encoding="utf-8")
        written.append(path)
        elapsed = time.monotonic() - started
        changed_marker = "changed" if revision != current else "kept"
        print(f"[{index:03d}/{len(selected):03d}] {changed_marker} {book} {chapter}:{verse} ({elapsed:.1f}s)")

    synced = sync_hans(written)
    append_processed(args.kind, written)
    print(f"fixed {len(written)} {args.kind.upper()} row(s); synced {synced} paired Hans file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
