#!/usr/bin/env python3
"""Write OCR_to_txt/parsed_ot/verses_resolved.tsv as one file per verse in One_Directory_B20A1912_OT_OCR_candidates/
(generated, gitignored). Machine OCR, unreviewed: used ONLY as the corroboration reference of
triage_ot_existing.py --lang is (checks_is.reference_ot). It never feeds GOI_Bible_is.
python3 -I write_ot_candidate_dir.py"""
import csv, pathlib
HERE = pathlib.Path(__file__).resolve().parent
out = HERE / "One_Directory_B20A1912_OT_OCR_candidates"
out.mkdir(exist_ok=True)
csv.field_size_limit(10**7)
n = 0
for r in csv.DictReader(open(HERE / "OCR_to_txt/parsed_ot/verses_resolved.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
    t = (r.get("icelandic_text") or "").strip()
    if t:
        (out / f"{r['verse_key']}_B20A1912.txt").write_text(t + "\n", encoding="utf-8")
        n += 1
print(f"wrote {n} files to {out.name}")
