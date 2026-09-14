#!/usr/bin/env python3
"""Require a review receipt for every active GOI edition after a shared issue.

Add one CSV row per reviewed edition to
Meta_Bible_Data/staging/cross_language_regressions.csv. A resolved issue is
not complete until every active GOI edition has `fixed`, `reviewed`, or a
documented `not_applicable` receipt.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "Meta_Bible_Data/sqlite/editions.json"
LEDGER = ROOT / "Meta_Bible_Data/staging/cross_language_regressions.csv"
ACCEPTED = {"fixed", "reviewed", "not_applicable"}


def main() -> int:
    editions = json.loads(CATALOG.read_text(encoding="utf-8"))
    required = {x["edition_id"] for x in editions if x["edition_id"].startswith("GOI_") and x["status"] == "active"}
    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8", newline="")))
    by_issue: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not row.get("issue_id"):
            continue
        by_issue[row["issue_id"]].append(row)
    errors: list[str] = []
    for issue_id, receipts in by_issue.items():
        reviewed = {r["reviewed_edition"] for r in receipts if r.get("status") in ACCEPTED and r.get("evidence") and r.get("reviewed_on")}
        missing = required - reviewed
        if missing:
            errors.append(f"{issue_id}: missing retro-check receipts for {', '.join(sorted(missing))}")
    if errors:
        print("CROSS-LANGUAGE AUDIT FAILED", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"CROSS-LANGUAGE AUDIT OK: {len(by_issue)} logged issue(s), {len(required)} active GOI editions required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
