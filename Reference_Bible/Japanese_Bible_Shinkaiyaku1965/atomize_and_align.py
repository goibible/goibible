#!/usr/bin/env python3
"""Atomize the jpn1965 USFM NT into per-verse files, then align to the
GOI/KJV verse spine.

Shinkaiyaku 1965 (New Japanese Bible NT, (c) expired 2015-12-31, public
domain) is distributed by ebible.org as clean per-verse USFM -- no OCR
involved, unlike the Meiji 1887 scan. This script:

  1. Parses \\c / \\v markers out of each source/*.usfm file, stripping
     footnotes (\\f ... \\f*), cross-refs (\\x ... \\x*), and section
     headings (\\s1 etc.), and writes one native-numbered verse file per
     verse into One_Directory_Shinkaiyaku1965/.
  2. Compares the resulting (book, chapter, verse) key set against the
     KJV NT key set. jpn1965 is a modern translation and is expected to
     already match standard versification almost everywhere; any real
     mismatches get recorded in BOOK_OVERRIDES below (same pattern as
     Reference_Bible/Portuguese_Bible_Almeida1911/align_versification.py)
     before this script is considered done.
  3. Writes the GOI/KJV-keyed copy into One_Directory_Shinkaiyaku1965_GOI/.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SRC_DIR = ROOT / "source"
NATIVE_DIR = ROOT / "One_Directory_Shinkaiyaku1965"
GOI_DIR = ROOT / "One_Directory_Shinkaiyaku1965_GOI"
KJV_DIR = REPO / "Reference_Bible" / "English_Bible_KJV" / "One_Directory_KJV"

# canon numbers for the 27 NT books, matching Meta_Bible_Data/sqlite books table
CANON = {
    "MAT": 40, "MRK": 41, "LUK": 42, "JHN": 43, "ACT": 44, "ROM": 45,
    "1CO": 46, "2CO": 47, "GAL": 48, "EPH": 49, "PHP": 50, "COL": 51,
    "1TH": 52, "2TH": 53, "1TI": 54, "2TI": 55, "TIT": 56, "PHM": 57,
    "HEB": 58, "JAS": 59, "1PE": 60, "2PE": 61, "1JN": 62, "2JN": 63,
    "3JN": 64, "JUD": 65, "REV": 66,
}

FOOTNOTE_RE = re.compile(r"\\f\s.*?\\f\*", re.DOTALL)
XREF_RE = re.compile(r"\\x\s.*?\\x\*", re.DOTALL)
INLINE_MARKUP_RE = re.compile(r"\\[a-z0-9]+\*?")  # \wj, \nd, \add, etc. -- drop the tag, keep text
WHITESPACE_RE = re.compile(r"[ \t]+")

# Real native-vs-KJV verse-numbering deltas, found by running this script
# once and inspecting every reported missing/extra key against the source
# (see git history for the diagnostic session). Two kinds show up in a
# modern, well-versified translation like this one:
#   - verse bridges ("\v 44-45"): one native verse covers two KJV verses
#     with identical text (textual-criticism verses some traditions omit).
#   - genuine splits/merges at a verse or chapter boundary: multiple
#     native verses' text concatenates into a single KJV verse, or vice
#     versa. Where several native keys map to the same target key, their
#     texts are concatenated in native (file) order.


def _bridge(book: str, chapter: int, first: int, last: int) -> None:
    # The parser stores a "\v N-M" range under its single starting verse
    # number N (see parse_usfm); populate every KJV verse in the range
    # with that same text.
    BOOK_OVERRIDES.setdefault(book, {})
    BOOK_OVERRIDES[book][(chapter, first)] = [(chapter, v) for v in range(first, last + 1)]


BOOK_OVERRIDES: dict[str, dict[tuple[int, int], list[tuple[int, int]]]] = {
    # jpn 13:12 covers both the "holy kiss" and "all the saints salute
    # you" clauses that KJV splits into 13:12/13:13, which pushes jpn's
    # closing benediction (13:13) to KJV's 13:14.
    "2CO": {(13, 12): [(13, 12), (13, 13)], (13, 13): [(13, 14)]},
    # KJV 3 John 1:14 = jpn 1:14 + 1:15 concatenated (jpn splits the
    # farewell into two sentences; KJV keeps them as one verse).
    "3JN": {(1, 14): [(1, 14)], (1, 15): [(1, 14)]},
    # KJV Rev 13:1 = jpn 12:18 + 13:1 concatenated (jpn ends chapter 12
    # with "and I stood upon the sand of the sea", which KJV/TR treats
    # as the opening clause of 13:1 instead).
    "REV": {(12, 18): [(13, 1)]},
}
for _book, _chapter, _first, _last in [
    ("MRK", 7, 16, 17), ("MRK", 9, 44, 45), ("MRK", 9, 46, 47),
    ("MRK", 11, 26, 27), ("MRK", 15, 28, 29),
    ("LUK", 1, 1, 2), ("LUK", 1, 74, 75), ("LUK", 11, 51, 52),
    ("LUK", 17, 36, 37), ("LUK", 23, 17, 18), ("LUK", 24, 40, 41),
    ("JHN", 5, 4, 5),
    ("ACT", 8, 37, 38), ("ACT", 15, 34, 35), ("ACT", 24, 7, 8), ("ACT", 28, 29, 30),
    ("ROM", 2, 19, 20), ("ROM", 16, 24, 26),
]:
    _bridge(_book, _chapter, _first, _last)


def clean_text(raw: str) -> str:
    text = FOOTNOTE_RE.sub("", raw)
    text = XREF_RE.sub("", text)
    text = INLINE_MARKUP_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def parse_usfm(path: pathlib.Path) -> dict[tuple[int, int], str]:
    verses: dict[tuple[int, int], str] = {}
    book = None
    chapter = None
    verse = None
    buf: list[str] = []

    def flush():
        if book and chapter is not None and verse is not None:
            text = clean_text(" ".join(buf))
            if text:
                verses[(chapter, verse)] = text

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("\\id "):
            book = line.split()[1][:3]
            continue
        m = re.match(r"\\c\s+(\d+)", line)
        if m:
            flush()
            chapter = int(m.group(1))
            verse = None
            buf = []
            continue
        m = re.match(r"\\v\s+(\d+)(?:-(\d+))?\s*(.*)", line)
        if m:
            flush()
            verse = int(m.group(1))
            buf = [m.group(3)]
            continue
        if line.startswith("\\s") or line.startswith("\\mt") or line.startswith("\\toc") or \
           line.startswith("\\h ") or line.startswith("\\id") or line.startswith("\\ide"):
            continue
        # paragraph markers (\p, \m, \q1, \nb, ...) and continuation lines: keep as verse text
        buf.append(line)
    flush()
    return verses


def target_keys(book: str, chapter: int, verse: int) -> list[tuple[int, int]]:
    overrides = BOOK_OVERRIDES.get(book)
    if not overrides:
        return [(chapter, verse)]
    return overrides.get((chapter, verse), [(chapter, verse)])


def main() -> None:
    NATIVE_DIR.mkdir(parents=True, exist_ok=True)
    GOI_DIR.mkdir(parents=True, exist_ok=True)
    for old in NATIVE_DIR.glob("*_Shinkaiyaku1965.txt"):
        old.unlink()
    for old in GOI_DIR.glob("*_Shinkaiyaku1965.txt"):
        old.unlink()

    native_written = 0
    splits = 0
    # (canon, book, chapter, verse) -> list of native texts, in native
    # verse order, that land on this one GOI/KJV target key.
    goi_texts: dict[tuple[int, str, int, int], list[str]] = {}

    for usfm_path in sorted(SRC_DIR.glob("*.usfm")):
        book = usfm_path.stem.split("-")[1][:3]
        if book not in CANON:
            continue  # front matter (01-INT), etc.
        canon = CANON[book]
        verses = parse_usfm(usfm_path)
        for (chapter, verse), text in sorted(verses.items()):
            native_path = NATIVE_DIR / f"{canon:03d}_{book}_{chapter:03d}_{verse:03d}_Shinkaiyaku1965.txt"
            native_path.write_text(text + "\n", encoding="utf-8")
            native_written += 1

            keys = target_keys(book, chapter, verse)
            if len(keys) > 1:
                splits += 1
            for gchapter, gverse in keys:
                goi_texts.setdefault((canon, book, gchapter, gverse), []).append(text)

    goi_written = 0
    merges = 0
    for (canon, book, gchapter, gverse), texts in goi_texts.items():
        if len(texts) > 1:
            merges += 1
        goi_path = GOI_DIR / f"{canon:03d}_{book}_{gchapter:03d}_{gverse:03d}_Shinkaiyaku1965.txt"
        goi_path.write_text(" ".join(texts) + "\n", encoding="utf-8")
        goi_written += 1

    def normalized_names(directory: pathlib.Path, suffix: str) -> set[str]:
        return {p.name.replace(f"_{suffix}.txt", ".txt") for p in directory.glob(f"*_{suffix}.txt")}

    goi_names = normalized_names(GOI_DIR, "Shinkaiyaku1965")
    kjv_names = {p.name.replace("_KJV.txt", ".txt") for p in KJV_DIR.glob("*_KJV.txt") if int(p.name[:3]) >= 40}
    missing = sorted(kjv_names - goi_names)
    extra = sorted(goi_names - kjv_names)

    print(f"native verse files written: {native_written}")
    print(f"GOI/KJV-keyed files written: {goi_written} (1-to-many splits: {splits}, many-to-1 merges: {merges})")
    print(f"KJV NT keys expected: {len(kjv_names)}")
    print(f"missing GOI/KJV keys: {len(missing)}")
    print(f"extra (unmapped) keys: {len(extra)}")
    if missing:
        print("first missing: " + ", ".join(missing[:20]))
    if extra:
        print("first extra: " + ", ".join(extra[:20]))
    if missing or extra:
        sys.exit(1)


if __name__ == "__main__":
    main()
