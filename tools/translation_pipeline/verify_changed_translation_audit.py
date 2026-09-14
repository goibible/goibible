#!/usr/bin/env python3
"""Require ledger entries for changed coordinates in active GOI corpora.

Use `--base <git-revision>` in CI. A changed active GOI verse must have its
`NNN_BOOK_CCC_VVV` coordinate in the cross-language regression ledger, which
then requires receipts for every active GOI edition.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "Meta_Bible_Data/sqlite/editions.json"
LEDGER = ROOT / "Meta_Bible_Data/staging/cross_language_regressions.csv"
COORD = re.compile(r"^(\d{3}_[123]?[A-Z]{2,3}_\d{3}_\d{3})_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git revision before the change")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    active_dirs = {
        str(item["flatfile_dir"])
        for item in catalog
        if str(item["edition_id"]).startswith("GOI_") and item.get("status") == "active"
    }
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", args.base, "HEAD", "--", "GOI_Bible"], cwd=ROOT, text=True
    ).splitlines()
    coordinates: set[str] = set()
    for changed_path in changed:
        path = Path(changed_path)
        if str(path.parent) not in active_dirs:
            continue
        match = COORD.match(path.name)
        if match:
            coordinates.add(match.group(1))
    ledger_coordinates = {row["coordinate"] for row in csv.DictReader(LEDGER.open(encoding="utf-8", newline="")) if row.get("coordinate")}
    missing = sorted(coordinates - ledger_coordinates)
    if missing:
        print("CHANGED TRANSLATION AUDIT FAILED", file=sys.stderr)
        print("Add a row for each changed coordinate to Meta_Bible_Data/staging/cross_language_regressions.csv", file=sys.stderr)
        print("\n".join(missing[:30]), file=sys.stderr)
        return 1
    print(f"CHANGED TRANSLATION AUDIT OK: {len(coordinates)} active GOI coordinates have ledger entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
