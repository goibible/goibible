#!/usr/bin/env python3
"""Write hand-checked retro-check receipts for one edition into cross_language_regressions.csv.
  add_ledger_receipts.py GOI_Fr --fixed 222,223,... [--na 224] [--first 217 --last 247] --note "how it was checked"
Every issue in the range not listed as fixed/na gets 'reviewed'. Existing receipts for that edition+issue are replaced."""
import argparse, csv
from pathlib import Path
L = Path(__file__).resolve().parents[2] / "Meta_Bible_Data/staging/cross_language_regressions.csv"
ap = argparse.ArgumentParser(); ap.add_argument("edition"); ap.add_argument("--fixed", default=""); ap.add_argument("--na", default="")
ap.add_argument("--first", type=int, default=217); ap.add_argument("--last", type=int, default=247); ap.add_argument("--note", required=True); ap.add_argument("--detail", default="")
a = ap.parse_args()
fixed = {int(x) for x in a.fixed.split(",") if x}; na = {int(x) for x in a.na.split(",") if x}
rows = list(csv.DictReader(L.open(encoding="utf-8", newline=""))); cols = list(rows[0])
first = {}
for r in rows: first.setdefault(int(r["issue_id"]), r)
rows = [r for r in rows if not (r["reviewed_edition"] == a.edition and a.first <= int(r["issue_id"]) <= a.last)]
for i in range(a.first, a.last + 1):
    if i not in first: continue
    st = "fixed" if i in fixed else "not_applicable" if i in na else "reviewed"
    ev = {"fixed": f"fixed in {a.edition} text; {a.note}", "not_applicable": "script/spelling defect specific to the source edition's script; this edition is covered by the script gate", "reviewed": f"checked verse(s) against the source senses, already correct; {a.note}"}[st]
    b = dict(first[i]); b.update(reviewed_edition=a.edition, reviewer="Claude (AI); no native-speaker review", status=st, evidence=ev, reviewed_on="2026-10-07"); rows.append(b)
w = csv.DictWriter(L.open("w", encoding="utf-8", newline=""), fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(a.edition, "fixed", len(fixed), "na", len(na), "reviewed", sum(1 for i in range(a.first, a.last + 1) if i in first and i not in fixed and i not in na))
