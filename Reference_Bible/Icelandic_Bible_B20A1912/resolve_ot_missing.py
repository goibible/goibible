#!/usr/bin/env python3
"""Second pass: split merged verses at inline numerals for coordinates parse_ot_pages.py missed.
Reads parsed_ot/verses.tsv + report.json, writes parsed_ot/verses_resolved.tsv and resolve_report.json.
Machine candidates only. Never reads or writes One_Directory_B20A1912_GOI."""
import json, re
from pathlib import Path
H = Path(__file__).resolve().parent
P = H / "OCR_to_txt" / "parsed_ot"
SPINE = H.parent / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
spine = []
for p in sorted(SPINE.glob("*_WLC.txt")):
    n, b, c, v, _ = p.name.split("_")
    spine.append((f"{n}_{b}_{int(c):03d}_{int(v):03d}", b, int(c), int(v)))
text = {}
for l in (P / "verses.tsv").read_text(encoding="utf-8").split("\n")[1:]:
    if l:
        k, t = l.split("\t", 1); text[k] = t
CONF = {"3": "38", "8": "36", "1": "7l", "6": "5", "5": "6"}  # common OCR digit confusions
NUM = re.compile(r"(?<![\d,:.])(\d{1,3})(?= *[^\W\d_»„\"'(*]| *[»„\"'(*])")
resolved, unresolved = [], []
for idx, (k, b, c, v) in enumerate(spine):
    if k in text:
        continue
    prev = next((spine[j][0] for j in range(idx - 1, -1, -1) if spine[j][0] in text), None)
    if prev is None:
        unresolved.append(k); continue
    t = text[prev]
    want = str(v)
    hit = None
    if v == 1:  # chapter-first verse: chapter numeral followed by a superscript 1 marker
        hit = re.search(r"(?<![\d,:.])%d *\u00a71\u00a7" % c, t)
    if hit is None:
        for m in NUM.finditer(t):
            if m.group(1) == want:
                hit = m; break
    if hit is None:  # Hebrew-vs-KJV versification or confused digit: take the next numeral that is > previous verse's
        pv = int(prev.split("_")[3]); cands = [m for m in NUM.finditer(t) if int(m.group(1)) == pv + 1 or m.group(1) in CONF.get(want, "")]
        hit = cands[0] if cands and prev.split("_")[1] == b and int(prev.split("_")[2]) == c else None
    if hit is None:
        unresolved.append(k); continue
    text[prev] = t[:hit.start()].strip()
    text[k] = t[hit.end():].strip()
    resolved.append(k)
with open(P / "verses_resolved.tsv", "w", encoding="utf-8") as f:
    f.write("verse_key\ticelandic_text\n")
    for k, *_ in spine:
        if k in text:
            f.write(f"{k}\t{text[k]}\n")
(P / "resolve_report.json").write_text(json.dumps({"resolved": len(resolved), "unresolved": unresolved}, indent=1))
print(len(resolved), "resolved;", len(unresolved), "unresolved:", " ".join(u[4:] for u in unresolved))
