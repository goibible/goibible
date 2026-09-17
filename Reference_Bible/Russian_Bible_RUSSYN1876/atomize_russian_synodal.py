#!/usr/bin/env python3
"""Atomize the Russian Synodal (RUSSYN) verse-per-line export against the GOI/KJV spine.

Unlike the Korean atomizer, this is NOT a strict spine-or-fail build: the
Synodal tradition uses a different Psalm numbering/division (and smaller
divisions elsewhere), so a meaningful fraction of addresses will never
line up 1:1 with the KJV spine without a hand-built versification map.

This script writes only the verses whose (book, chapter, verse) address
matches the spine exactly, and records everything else -- GOI addresses
with no Russian match, and Russian addresses with no GOI match -- in a
gap report. That report is the input to the future Russian->GOI
versification map; this script does not attempt to guess that mapping.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
DEFAULT_OUT = Path(__file__).resolve().parent / "One_Directory_RUSSYN1876"
DEFAULT_REPORT = Path(__file__).resolve().parent / "alignment_report.json"
SOURCE_URL = "https://eBible.org/Scriptures/russyn_vpl.zip"
VPL_MEMBER = "russyn_vpl.txt"

# eBible/SIL book codes that differ from this project's KJV spine codes.
BOOK_CODE_MAP = {
    "1JO": "1JN",
    "2JO": "2JN",
    "3JO": "3JN",
    "EZE": "EZK",
    "JAM": "JAS",
    "JOE": "JOL",
    "JOH": "JHN",
    "MAR": "MRK",
    "NAH": "NAM",
    "PHI": "PHP",
    "SOL": "SNG",
}

LINE_RE = re.compile(r"^([1-3]?[A-Z]{2,3})\s+(\d+):(\d+)\s+(.*)$")


def spine() -> tuple[dict[tuple[str, int, int], str], dict[tuple[str, int], list[int]]]:
    """Map (book, chapter, verse) -> canonical file prefix, plus expected verses per chapter."""
    addr_to_conical: dict[tuple[str, int, int], str] = {}
    chapters: dict[tuple[str, int], list[int]] = defaultdict(list)
    for path in sorted(KJV_DIR.glob("*_KJV.txt")):
        conical, book, chapter, verse, _ = path.stem.split("_")
        key = (book, int(chapter), int(verse))
        addr_to_conical[key] = conical
        chapters[(book, int(chapter))].append(int(verse))
    if len(addr_to_conical) == 0 or len({b for b, _, _ in addr_to_conical}) != 66:
        raise SystemExit("KJV spine is incomplete")
    return addr_to_conical, chapters


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_vpl(zip_path: Path) -> dict[tuple[str, int, int], str]:
    verses: dict[tuple[str, int, int], str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read(VPL_MEMBER).decode("utf-8")
    for lineno, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        match = LINE_RE.match(line)
        if not match:
            raise ValueError(f"{VPL_MEMBER}:{lineno}: unparseable line: {line!r}")
        book, chapter, verse, text = match.groups()
        book = BOOK_CODE_MAP.get(book, book)
        key = (book, int(chapter), int(verse))
        if key in verses:
            raise ValueError(f"{VPL_MEMBER}:{lineno}: duplicate address {key}")
        verses[key] = normalize(text)
    return verses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vpl_zip", type=Path, nargs="?",
                         default=Path(__file__).resolve().parent / "source/russyn_vpl.zip")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write", action="store_true", help="write the matched verses to --out")
    args = parser.parse_args()

    addr_to_conical, expected_chapters = spine()
    russian = parse_vpl(args.vpl_zip)

    # Psalms is handled exclusively by build_psalm_versification_map.py +
    # apply_psalm_versification_map.py: the Synodal Psalter uses different
    # chapter numbering (see that script's docstring), so naive address
    # equality pairs the WRONG Russian verse with a GOI address almost
    # everywhere in Psalms -- verified against a real build, where only 47
    # of 1,705 naively-"matched" Psalm addresses were actually correct.
    # Excluding PSA here means --write can never silently reintroduce that.
    goi_addrs = {a for a in addr_to_conical if a[0] != "PSA"}
    rus_addrs = {a for a in russian if a[0] != "PSA"}
    matched = goi_addrs & rus_addrs
    absent = goi_addrs - rus_addrs
    russian_only = rus_addrs - goi_addrs

    def by_book(addrs: set[tuple[str, int, int]]) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for book, _, _ in addrs:
            counts[book] += 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    report = {
        "source": "eBible Russian Synodal Bible, verse-per-line export",
        "source_url": SOURCE_URL,
        "spine": "KJV/GOI",
        "note": "PSA is excluded from every count below; see psalm_versification_map.csv for Psalms coverage (2,461/2,461, verified).",
        "goi_addresses": len(goi_addrs),
        "russian_addresses": len(rus_addrs),
        "matched": len(matched),
        "goi_addresses_absent_from_russian": len(absent),
        "russian_only_addresses": len(russian_only),
        "absent_by_book": by_book(absent),
        "russian_only_by_book": by_book(russian_only),
        "absent_addresses": sorted(f"{b} {c}:{v}" for b, c, v in absent),
        "russian_only_addresses_list": sorted(f"{b} {c}:{v}" for b, c, v in russian_only),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.write:
        args.out.mkdir(parents=True, exist_ok=True)
        for book, chapter, verse in matched:
            conical = addr_to_conical[(book, chapter, verse)]
            path = args.out / f"{conical}_{book}_{chapter:03d}_{verse:03d}_RUSSYN1876.txt"
            path.write_text(russian[(book, chapter, verse)] + "\n", encoding="utf-8")

    print(f"GOI addresses:            {len(goi_addrs)}")
    print(f"Russian addresses:        {len(rus_addrs)}")
    print(f"Matched (written):        {len(matched)}")
    print(f"GOI addresses absent:     {len(absent)}")
    print(f"Russian-only addresses:   {len(russian_only)}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
