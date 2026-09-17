#!/usr/bin/env python3
"""Build a proposed KJV/GOI Psalms <-> Russian Synodal versification map.

The Synodal Psalter follows the traditional Church-Slavonic/LXX Psalm
numbering (per the well-documented Hebrew/LXX correspondence table), not
the KJV/Masoretic numbering -- not a random one-off drift. This script:

  1. Applies that documented chapter-level correspondence (9-10 merge,
     114-115 merge, 116 split, 147 split, otherwise -1 shift for 11-113
     and 117-146).
  2. Within each mapped chapter, many Russian Psalms carry one extra
     verse (occasionally two) at the front relative to KJV -- the
     superscription/title, which Hebrew/Slavonic tradition numbers as
     verse 1 and KJV does not count separately. Detected per chapter as
     len(russian) - len(kjv) and applied as a uniform trailing shift.
  3. For the two merge groups (9+10, and the two splits), the split
     point is derived from exact verse-count arithmetic, which matches
     the observed Russian counts exactly (verified below) -- there's
     only one way to split 39 = 1(title) + 20 + 18, 19 = 9 + 10, etc.

This is a PROPOSED map (status=proposed in the output), not yet verified
against actual verse content. It must be spot-checked -- ideally against
a sibling GOI edition already aligned to this same Psalm content (see
memory: use sibling GOI editions as references) -- before being treated
as authoritative for translation QA.
"""
from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

KJV_DIR = Path(__file__).resolve().parents[2] / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
VPL_ZIP = Path(__file__).resolve().parent / "source/russyn_vpl.zip"
OUT_CSV = Path(__file__).resolve().parent / "psalm_versification_map.csv"

MERGE_910_SPLIT = None  # computed below from counts, not hardcoded


def load_kjv_psalms() -> dict[int, set[int]]:
    kjv: dict[int, set[int]] = {}
    for p in KJV_DIR.glob("*_PSA_*_KJV.txt"):
        _, _, chapter, verse, _ = p.stem.split("_")
        kjv.setdefault(int(chapter), set()).add(int(verse))
    return kjv


def load_rus_psalms() -> dict[int, set[int]]:
    rus: dict[int, set[int]] = {}
    with zipfile.ZipFile(VPL_ZIP) as z:
        raw = z.read("russyn_vpl.txt").decode("utf-8")
    for line in raw.splitlines():
        m = re.match(r"^PSA\s+(\d+):(\d+)\s+", line)
        if m:
            ch, vs = int(m.group(1)), int(m.group(2))
            rus.setdefault(ch, set()).add(vs)
    return rus


def main() -> None:
    kjv = load_kjv_psalms()
    rus = load_rus_psalms()
    for n in range(1, 151):
        assert len(kjv.get(n, ())) > 0, f"KJV Psalm {n} missing from spine"
        assert len(rus.get(n, ())) > 0, f"Russian Psalm {n} missing from source"

    rows: list[dict] = []

    def emit(kjv_ch, kjv_vs, rus_ch, rus_vs, relation, notes):
        rows.append({
            "goi_book": "PSA", "goi_chapter": kjv_ch, "goi_verse": kjv_vs,
            "rus_chapter": rus_ch, "rus_verse": rus_vs,
            "relation": relation, "status": "proposed", "notes": notes,
        })

    def emit_direct_with_title_offset(n, rus_chapter):
        kn, rn = len(kjv[n]), len(rus[rus_chapter])
        offset = rn - kn
        assert offset >= 0, f"Psalm {n}: Russian has FEWER verses ({rn}) than KJV ({kn}) -- needs manual review"
        for title_v in range(1, offset + 1):
            emit(n, None, rus_chapter, title_v, "title", "Russian superscription verse(s) with no KJV counterpart")
        for v in range(1, kn + 1):
            emit(n, v, rus_chapter, v + offset, "direct" if offset == 0 else "title-shifted", "")

    # 1-8: same chapter number, check for title offsets same as any other direct chapter
    for n in range(1, 9):
        emit_direct_with_title_offset(n, n)

    # 9-10 merge into Russian 9
    total = len(kjv[9]) + len(kjv[10])
    offset = len(rus[9]) - total
    assert offset in (0, 1), f"Psalm 9/10 merge: unexpected verse-count delta {offset}"
    cursor = 1
    for title_v in range(1, offset + 1):
        emit(9, None, 9, title_v, "title", "combined Psalm 9/10 superscription, no KJV counterpart")
        cursor += 1
    for v in range(1, len(kjv[9]) + 1):
        emit(9, v, 9, cursor, "merged", "KJV Psalm 9 half of combined Russian Psalm 9")
        cursor += 1
    for v in range(1, len(kjv[10]) + 1):
        emit(10, v, 9, cursor, "merged", "KJV Psalm 10 half of combined Russian Psalm 9")
        cursor += 1
    assert cursor - 1 == len(rus[9])

    # 11-113: direct with title offset, Russian chapter = n-1
    for n in range(11, 114):
        emit_direct_with_title_offset(n, n - 1)

    # 114-115 merge into Russian 113
    total = len(kjv[114]) + len(kjv[115])
    assert len(rus[113]) == total, f"Psalm 114/115 merge count mismatch: {len(rus[113])} != {total}"
    cursor = 1
    for v in range(1, len(kjv[114]) + 1):
        emit(114, v, 113, cursor, "merged", "KJV Psalm 114 half of combined Russian Psalm 113")
        cursor += 1
    for v in range(1, len(kjv[115]) + 1):
        emit(115, v, 113, cursor, "merged", "KJV Psalm 115 half of combined Russian Psalm 113")
        cursor += 1

    # 116 split into Russian 114 + 115
    total = len(rus[114]) + len(rus[115])
    assert len(kjv[116]) == total, f"Psalm 116 split count mismatch: {len(kjv[116])} != {total}"
    for v in range(1, len(rus[114]) + 1):
        emit(116, v, 114, v, "split", "first half of KJV Psalm 116 -> Russian Psalm 114")
    for i, v in enumerate(range(1, len(rus[115]) + 1), start=len(rus[114]) + 1):
        emit(116, i, 115, v, "split", "second half of KJV Psalm 116 -> Russian Psalm 115")

    # 117-146: direct with title offset, Russian chapter = n-1
    for n in range(117, 147):
        emit_direct_with_title_offset(n, n - 1)

    # 147 split into Russian 146 + 147
    total = len(rus[146]) + len(rus[147])
    assert len(kjv[147]) == total, f"Psalm 147 split count mismatch: {len(kjv[147])} != {total}"
    for v in range(1, len(rus[146]) + 1):
        emit(147, v, 146, v, "split", "first half of KJV Psalm 147 -> Russian Psalm 146")
    for i, v in enumerate(range(1, len(rus[147]) + 1), start=len(rus[146]) + 1):
        emit(147, i, 147, v, "split", "second half of KJV Psalm 147 -> Russian Psalm 147")

    # 148-150: same chapter number
    for n in range(148, 151):
        emit_direct_with_title_offset(n, n)

    mapped_kjv = {(r["goi_chapter"], r["goi_verse"]) for r in rows if r["goi_verse"] is not None}
    expected_kjv = {(n, v) for n in range(1, 151) for v in kjv[n]}
    missing = expected_kjv - mapped_kjv
    extra = mapped_kjv - expected_kjv
    assert not missing, f"{len(missing)} KJV Psalm addresses not covered by the map: {sorted(missing)[:10]}"
    assert not extra, f"{len(extra)} mapped addresses aren't real KJV Psalm addresses: {sorted(extra)[:10]}"

    title_rows = [r for r in rows if r["relation"] == "title"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["goi_book", "goi_chapter", "goi_verse", "rus_chapter", "rus_verse", "relation", "status", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"KJV Psalm addresses covered: {len(mapped_kjv)}/{len(expected_kjv)}")
    print(f"Rows written: {len(rows)} ({len(rows) - len(title_rows)} address mappings + {len(title_rows)} unmapped Russian title verses)")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
