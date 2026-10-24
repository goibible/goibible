#!/usr/bin/env python3
"""Split the DeepSeek page OCR (printed pages 1-1003 = OT) into verses on the WLC/KJV spine.

Machine candidates only: output goes to OCR_to_txt/parsed_ot/, never to One_Directory_B20A1912_GOI.
Walk the spine in order; for each coordinate find the next numeral token equal to the expected
verse number (chapter number stands in for verse 1). Coordinates not found are logged as missing.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGES = HERE / "OCR_to_txt" / "deepseek_2section"
SPINE = HERE.parent / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
OUT = HERE / "OCR_to_txt" / "parsed_ot"
LAST_OT_PAGE = 1003

spine = []
for p in sorted(SPINE.glob("*_WLC.txt")):
    n, book, c, v, _ = p.name.split("_")
    spine.append((n, book, int(c), int(v)))

RUNHEAD = re.compile(r"^[\dIVX. ]*[A-ZÁÐÉÍÓÚÝÞÆÖ][A-ZÁÐÉÍÓÚÝÞÆÖ .,\d:]{3,}$")
parts = []
for pg in range(1, LAST_OT_PAGE + 1):
    t = (PAGES / f"page_{pg:04d}.txt").read_text(encoding="utf-8")
    first, _, rest = t.strip("\n").partition("\n")
    if RUNHEAD.match(first.strip()):
        t = rest
    parts.append(t.strip("\n").replace("**", ""))
text = "\n".join(parts)
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: " \u00a7" + m.group(0).translate(SUP) + "\u00a7 ", text)
text = re.sub(r"(?<=[a-záðéíóúýþæö])-\n(?=[a-záðéíóúýþæö])", "", text)  # hyphenated line breaks
text = re.sub(r"[ \t]*\n(?!\n)", " ", text)  # soft line joins; keep blank lines for headings
# section headings: blank line, one short line without numerals, then verse text
text = re.sub(r"\n\n([^\n\d]{3,110})\n(?=\d)", r"\n\n", text)
text = re.sub(r"\n\n(?=\d)", " ", text)

TOKEN = re.compile(r"\u00a7(\d{1,3})\u00a7 *|(?<![\d,:.;])(\d{1,3})(?= +[^\W\d_]| +[»„\"'(*])")
cands = [(m.start(), m.end(), int(m.group(1) or m.group(2))) for m in TOKEN.finditer(text)]

import numpy as np

E = np.array([(c if v == 1 and c > 1 else v) for _, _, c, v in spine], dtype=np.int32)
C = np.array([x[2] for x in cands], dtype=np.int32)
nE, nC = len(E), len(C)
B = 3000
W = 2 * B + 1
ratio = nC / nE
lo = [max(0, min(int(i * ratio) - B, max(0, nC - W))) for i in range(nE + 1)]
NEG = -10**6
dp = np.full((nE + 1, W), NEG, dtype=np.int32)
for k in range(W):
    j = lo[0] + k
    dp[0, k] = 0 if j <= nC else NEG
for i in range(1, nE + 1):
    s_ = lo[i] - lo[i - 1]
    prev = dp[i - 1]
    idx = np.arange(W)
    same = np.where(idx + s_ < W, prev[np.minimum(idx + s_, W - 1)], prev[W - 1])
    dj = idx + s_ - 1
    diag = np.where((dj >= 0) & (dj < W), prev[np.clip(dj, 0, W - 1)], NEG)
    jj = lo[i] + idx
    cj = np.where((jj >= 1) & (jj <= nC), C[np.clip(jj - 1, 0, nC - 1)], -1)
    match = np.where(cj == E[i - 1], diag + 1, diag)
    row = np.maximum(same, match)
    row = np.maximum.accumulate(row)
    row[jj > nC] = NEG
    dp[i] = row

# traceback
found = {}
i, j = nE, nC
best_k = int(np.argmax(dp[nE]))
j = lo[nE] + best_k
while i > 0 and j > 0:
    k = j - lo[i]
    cur = dp[i, k]
    kd = j - 1 - lo[i - 1]
    if C[j - 1] == E[i - 1] and 0 <= kd < W and dp[i - 1, kd] + 1 == cur:
        found[i - 1] = cands[j - 1]
        i -= 1
        j -= 1
        continue
    ku = j - lo[i - 1]
    if 0 <= ku < W and dp[i - 1, ku] == cur:
        i -= 1
    else:
        j -= 1
missing = [spine[i] for i in range(nE) if i not in found]

# slice text between consecutive found starts
order = sorted(found)
OUT.mkdir(parents=True, exist_ok=True)
verses = {}
for k, i in enumerate(order):
    start = found[i][1]
    end = found[order[k + 1]][0] if k + 1 < len(order) else len(text)
    verses[i] = re.sub(r"\s+", " ", text[start:end]).strip()

report = {"spine_ot": len(spine), "found": len(found), "missing": len(missing)}
by_book = {}
for n, book, c, v in spine:
    by_book.setdefault(book, [0, 0])[0] += 1
for i in found:
    by_book[spine[i][1]][1] += 1
report["by_book"] = {b: {"spine": s, "found": f} for b, (s, f) in by_book.items()}
report["missing_list"] = [f"{b} {c}:{v}" for n, b, c, v in missing]
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
with open(OUT / "verses.tsv", "w", encoding="utf-8") as f:
    f.write("verse_key\ticelandic_text\n")
    for i in order:
        n, book, c, v = spine[i]
        f.write(f"{n}_{book}_{c:03d}_{v:03d}\t{verses[i]}\n")
print(json.dumps({k: report[k] for k in ("spine_ot", "found", "missing")}))
for b, d in report["by_book"].items():
    if d["spine"] != d["found"]:
        print(b, d["found"], "/", d["spine"])
