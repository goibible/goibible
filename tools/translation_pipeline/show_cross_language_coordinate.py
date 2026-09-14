#!/usr/bin/env python3
"""Print one GOI coordinate from every active translation for retro-checking.

Use this whenever a translation defect is fixed. It makes the same coordinate
visible in each active GOI language; record the human review results in
`cross_language_regressions.csv` before closing the issue.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "Meta_Bible_Data/sqlite/editions.json"
COORDINATE = re.compile(r"^(\d{3})_([123]?[A-Z]{2,3})_(\d{3})_(\d{3})$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coordinate", help="for example 001_GEN_001_001")
    args = parser.parse_args()
    match = COORDINATE.fullmatch(args.coordinate)
    if not match:
        raise SystemExit("coordinate must be NNN_BOOK_CCC_VVV, for example 001_GEN_001_001")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    missing: list[str] = []
    for edition in catalog:
        if not edition["edition_id"].startswith("GOI_") or edition["status"] != "active":
            continue
        suffix = edition.get("filename_suffix", edition["edition_id"])
        path = ROOT / edition["flatfile_dir"] / f"{args.coordinate}_{suffix}.txt"
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            missing.append(str(edition["edition_id"]))
            print(f"## {edition['edition_id']} — MISSING")
            continue
        print(f"## {edition['edition_id']}\n{path.read_text(encoding='utf-8').strip()}\n")
    if missing:
        raise SystemExit(f"missing substantive text for: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
