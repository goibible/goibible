#!/usr/bin/env python3
"""Reject unexpected Unicode scripts in a GOI language corpus.

Profiles live in Meta_Bible_Data/translation_qa/script_profiles.json. This
uses only Python's Unicode database, so it has no external package dependency.
Shared punctuation, digits, symbols, and whitespace are `common`; combining
marks are `inherited`. All other scripts must be explicitly allowed.
"""
from __future__ import annotations

import argparse
import json
import unicodedata as ud
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "Meta_Bible_Data/sqlite/editions.json"
PROFILES = ROOT / "Meta_Bible_Data/translation_qa/script_profiles.json"


def script_of(ch: str) -> str:
    code = ord(ch)
    category = ud.category(ch)
    if ch.isspace() or category[0] in {"P", "S", "N"}:
        return "common"
    if 0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F or 0xA960 <= code <= 0xA97F or 0xD7B0 <= code <= 0xD7FF:
        return "hangul"
    if 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF or 0x20000 <= code <= 0x2FA1F:
        return "han"
    if 0x0370 <= code <= 0x03FF or 0x1F00 <= code <= 0x1FFF:
        return "greek"
    if 0x0590 <= code <= 0x05FF or 0xFB1D <= code <= 0xFB4F:
        return "hebrew"
    if 0x0400 <= code <= 0x052F:
        return "cyrillic"
    if 0x0600 <= code <= 0x06FF:
        return "arabic"
    if 0x0980 <= code <= 0x09FF:
        return "bengali"
    if category.startswith("M"):
        return "inherited"
    if (0x0041 <= code <= 0x005A or 0x0061 <= code <= 0x007A or
            0x00C0 <= code <= 0x024F or 0x1E00 <= code <= 0x1EFF):
        return "latin"
    if category.startswith("C"):
        return "control"
    return "other"


def verify(config: dict[str, object], profile: dict[str, object]) -> int:
    edition_id = str(config["edition_id"])
    suffix = str(config.get("filename_suffix", edition_id))
    allowed = set(profile["allowed"])
    bad: Counter[str] = Counter()
    examples: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted((ROOT / str(config["flatfile_dir"])).glob(f"*_{suffix}.txt")):
        for ch in path.read_text(encoding="utf-8"):
            script = script_of(ch)
            if script not in allowed:
                bad[script] += 1
                if len(examples[script]) < 5:
                    examples[script].append((f"U+{ord(ch):04X} {ud.name(ch, 'UNNAMED')}", path.name))
    if bad:
        print(f"SCRIPT GATE FAILED {edition_id}")
        for script, count in sorted(bad.items()):
            sample = "; ".join(f"{char} in {path}" for char, path in examples[script])
            print(f"  {script}: {count} ({sample})")
        return 1
    print(f"SCRIPT GATE OK {edition_id}: allowed={','.join(sorted(allowed))}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("edition_id", nargs="?")
    group.add_argument("--all-active", action="store_true")
    args = parser.parse_args()
    catalog = {x["edition_id"]: x for x in json.loads(CATALOG.read_text(encoding="utf-8"))}
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    ids = [key for key, value in catalog.items() if key.startswith("GOI_") and value.get("status") == "active"] if args.all_active else [args.edition_id]
    failed = 0
    for edition_id in ids:
        if edition_id not in catalog:
            raise SystemExit(f"unknown edition {edition_id}")
        if edition_id not in profiles:
            raise SystemExit(f"no script profile for {edition_id}")
        failed |= verify(catalog[edition_id], profiles[edition_id])
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
