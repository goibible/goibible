#!/usr/bin/env python3
"""Hebrew->Chinese (Traditional) OT translation-fidelity audit via
DeepSeek-V4-Flash-0731 (DeepInfra, OpenAI-compatible API, config from
repo-root .env).

Adapted from deepseek_vi_ot_audit.py (Meta_Bible_Data/staging/reports/vi/
audits_deepseek/) for Chinese Traditional -- Hant only, per explicit
instruction: Hans is not independently audited, it is checked against Hant
afterward via a separate diff/comparison pass instead.

Every flag still needs manual Hebrew/KJV/CUV verification before being
trusted -- this tool is a candidate generator, not a verdict (same lesson as
every other audit pass this project has run).

Usage:
  python3 deepseek_zh_ot_audit.py               # full OT, resumable
  python3 deepseek_zh_ot_audit.py --book RUT     # one book (smoketest)
  python3 deepseek_zh_ot_audit.py --report       # build priority queue CSV only

Output:
  audits_ot/<stem>.json      one record per verse
  audit_priority_ot.csv      flagged verses
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys
import time
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

ROOT = pathlib.Path(__file__).resolve().parent
META_ROOT = ROOT.parents[3]
REPO_ROOT = META_ROOT.parent
load_dotenv(REPO_ROOT / ".env")

MODEL = os.environ["OPENAI_MODEL"]
CLIENT_KWARGS = dict(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"],
                      timeout=180.0, max_retries=0)

HEBREW = REPO_ROOT / "Reference_Bible" / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
ZH_DIR = REPO_ROOT / "GOI_Bible" / "GOI_Bible_Chinese_Hant"
ZH_EDITION_SUFFIX = "_GOI_Zh_Hant.txt"
AUDITS = ROOT / "audits_ot"
PRIORITY_CSV = ROOT / "audit_priority_ot.csv"


class FidelityIssue(BaseModel):
    kind: Literal["omission", "addition", "mistranslation", "negation",
                  "number_person_tense", "name_swap", "other"]
    detail: str

class FidelityResult(BaseModel):
    verdict: Literal["OK", "FLAG"]
    issues: list[FidelityIssue] = []
    confidence: float


def fidelity_prompt(hebrew: str, chinese: str) -> tuple[str, str]:
    system = (
        "You are a Hebrew Old Testament scholar checking ONLY translation fidelity: "
        "meaning, grammar, omissions, additions, negation, tense, number, person, and "
        "proper names/numbers. Do not comment on lexical style choices.\n\n"
        "FLAG ONLY if a Chinese (Traditional) reader would come away believing something "
        "factually different from, or missing something substantive that is present in, "
        "the Hebrew. If you are not sure, or the difference is purely stylistic, mark OK. "
        "When in doubt, OK.\n\n"
        "Do NOT flag any of the following -- they are correct, idiomatic translation, "
        "not errors:\n"
        "- Hebrew infinitive-absolute + finite-verb emphatic doubling (e.g. מוֹת תָמוּת "
        "'surely die', שָׁמוֹעַ תִּשְׁמְעוּן 'diligently obey') rendered as a single "
        "Chinese verb with an intensifier (必, 定要, 切切) instead of a literal doubled "
        "word -- that is correct, not an omission.\n"
        "- Genuine doubled/distributive Hebrew constructions (e.g. אֶלֶף אֲלָפִים "
        "'thousand thousands' = a very large number, שְׁנַיִם שְׁנַיִם 'two by two') "
        "rendered with Chinese reduplication ('兩個兩個', '一批一批') -- this is a "
        "genuine, correct feature of Chinese, not a duplication bug.\n"
        "- Waw-consecutive/converted tense forms rendered with Chinese aspect markers "
        "(了, 要, 將) or narrative word order instead of a literal tense gloss -- "
        "Chinese verbs are not inflected the way Hebrew is, infer aspect from context.\n"
        "- Construct-chain (smikhut) possessives rendered as a natural Chinese "
        "possessive phrase (的) instead of a literal 'X of Y' gloss.\n"
        "- Hebrew parallelism (synonymous or antithetic parallel clauses, common in "
        "poetry/Psalms/Proverbs) where the Chinese preserves the same two-part "
        "structure and meaning even if word choice differs between the two halves.\n"
        "- Connective/appositive words with no separate Hebrew lexeme (e.g. 就是, "
        "是, 說) added for natural Chinese.\n"
        "- Any rendering you would still call 'a close/acceptable translation' after "
        "your own explanation -- if your explanation agrees the Chinese is basically "
        "right, the verdict must be OK, not FLAG.\n\n"
        "Only use FLAG for: a personal name, place name, or number reversed/dropped/"
        "swapped for a different one (e.g. the wrong king's name), a negation reversed "
        "or dropped, a clause or concept entirely missing, a concept added that has no "
        "basis in the Hebrew and changes the verse's claim, or a wrong tense/person that "
        "changes who is doing what to whom.\n\n"
        "Respond with JSON only, matching this schema:\n"
        f"{json.dumps(FidelityResult.model_json_schema())}"
    )
    user = f"HEBREW: {hebrew.strip()}\nCHINESE (Traditional): {chinese.strip()}"
    return system, user


def call_check(client: OpenAI, system: str, user: str, attempts: int = 3) -> dict:
    last_err = None
    for attempt in range(attempts):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0,
                extra_body={"service_tier": "flex"},
            )
            content = resp.choices[0].message.content
            parsed = FidelityResult.model_validate_json(content)
            return {"ok": True, "result": parsed.model_dump()}
        except (ValidationError, json.JSONDecodeError, KeyError, Exception) as e:
            last_err = str(e)
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
    return {"ok": False, "error": last_err}


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


def record_is_valid(record: dict) -> bool:
    entry = record.get("translation_fidelity")
    if not isinstance(entry, dict) or not entry.get("ok"):
        return False
    try:
        FidelityResult.model_validate(entry["result"])
        return True
    except (ValidationError, KeyError):
        return False


def save_record_atomic(stem: str, record: dict) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    target = audit_path(stem)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)


def iter_verses(book_filter: Optional[str]):
    for hf in sorted(HEBREW.glob("*.txt")):
        stem = hf.stem.replace("_WLC", "")
        code = stem[4:7]
        if book_filter and code != book_filter.upper():
            continue
        ch = int(stem[8:11])
        vs = int(stem[12:15])
        zf = ZH_DIR / f"{stem}{ZH_EDITION_SUFFIX}"
        if not zf.exists():
            continue
        yield stem, code, ch, vs, hf, zf


def build_report() -> None:
    rows_out = []
    for p in sorted(AUDITS.glob("*.json")):
        record = json.loads(p.read_text(encoding="utf-8"))
        entry = record.get("translation_fidelity")
        if isinstance(entry, dict) and entry.get("ok") and entry["result"]["verdict"] == "FLAG":
            rows_out.append({
                "book": record.get("book", ""), "chapter": record.get("chapter", ""),
                "verse": record.get("verse", ""),
                "issues": "; ".join(f"{i['kind']}: {i['detail']}" for i in entry["result"]["issues"]),
            })
    with PRIORITY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["book", "chapter", "verse", "issues"])
        w.writeheader()
        w.writerows(rows_out)
    print(f"Priority queue: {PRIORITY_CSV}")
    print(f"  total flagged verses: {len(rows_out)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", help="limit to one book e.g. RUT")
    ap.add_argument("--report", action="store_true",
                     help="build audit_priority_ot.csv from existing audits_ot/*.json and exit")
    args = ap.parse_args()

    if args.report:
        build_report()
        return

    client = OpenAI(**CLIENT_KWARGS)

    verses = list(iter_verses(args.book))
    total = len(verses)
    if total == 0:
        sys.exit("No matching verses found (check --book and that GOI_Zh_Hant/WLC files exist).")

    done_verses = errors = 0
    for i, (stem, code, ch, vs, hf, zf) in enumerate(verses, 1):
        record = load_record(stem)
        record["book"], record["chapter"], record["verse"] = code, ch, vs

        if record_is_valid(record):
            done_verses += 1
            continue

        hebrew = hf.read_text(encoding="utf-8")
        chinese = zf.read_text(encoding="utf-8")

        system, user = fidelity_prompt(hebrew, chinese)
        record["translation_fidelity"] = call_check(client, system, user)
        save_record_atomic(stem, record)

        entry = record["translation_fidelity"]
        if not entry.get("ok"):
            errors += 1
            status = "ERROR"
        else:
            status = entry["result"]["verdict"]

        pct = 100 * i / total
        print(f"[{i}/{total} {pct:.1f}%] {code} {ch}:{vs} -> {status}")

    print(f"\nDone. already_complete={done_verses}  processed={total - done_verses}  errors_seen={errors}")
    print(f"Audits: {AUDITS}")
    print("Run with --report to build the priority queue CSV.")


if __name__ == "__main__":
    main()
