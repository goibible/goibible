#!/usr/bin/env python3
"""Replace the naively address-matched Psalms in One_Directory_RUSSYN1876
with correctly versification-mapped ones.

atomize_russian_synodal.py matches purely on (book, chapter, verse)
address equality, which is wrong for Psalms: the Synodal Psalter uses a
different chapter numbering (see build_psalm_versification_map.py), so a
coincidental address match there almost always paired the wrong Russian
verse with a GOI Psalm address. Verified against the already-committed
output: of 1,705 existing PSA flatfiles, only 47 were actually correct
(chapters 1-8 and 148-150, where the Russian and KJV numbering happens to
coincide) -- 1,658 had the wrong Russian text attached to a GOI address.

This script deletes every existing PSA flatfile and regenerates all 2,461
from psalm_versification_map.csv, which has been spot-verified against
actual verse content at every merge/split boundary (see its docstring and
Reference_Bible/Russian_Bible_RUSSYN1876/README.md).
"""
from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
OUT_DIR = Path(__file__).resolve().parent / "One_Directory_RUSSYN1876"
MAP_CSV = Path(__file__).resolve().parent / "psalm_versification_map.csv"
VPL_ZIP = Path(__file__).resolve().parent / "source/russyn_vpl.zip"


def normalize(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    conical = next(p.stem.split("_")[0] for p in KJV_DIR.glob("*_PSA_001_001_KJV.txt"))

    with zipfile.ZipFile(VPL_ZIP) as z:
        raw = z.read("russyn_vpl.txt").decode("utf-8")
    rus_text: dict[tuple[int, int], str] = {}
    for line in raw.splitlines():
        m = re.match(r"^PSA\s+(\d+):(\d+)\s+(.*)$", line)
        if m:
            rus_text[(int(m.group(1)), int(m.group(2)))] = normalize(m.group(3))

    removed = 0
    for f in OUT_DIR.glob(f"{conical}_PSA_*_RUSSYN1876.txt"):
        f.unlink()
        removed += 1

    written = 0
    with MAP_CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row["goi_verse"]:
                continue  # unmapped Russian title verse, no GOI address
            chapter, verse = int(row["goi_chapter"]), int(row["goi_verse"])
            rus_chapter, rus_verse = int(row["rus_chapter"]), int(row["rus_verse"])
            text = rus_text[(rus_chapter, rus_verse)]
            path = OUT_DIR / f"{conical}_PSA_{chapter:03d}_{verse:03d}_RUSSYN1876.txt"
            path.write_text(text + "\n", encoding="utf-8")
            written += 1

    print(f"Removed {removed} naively-matched PSA flatfiles")
    print(f"Wrote {written} versification-mapped PSA flatfiles")


if __name__ == "__main__":
    main()
