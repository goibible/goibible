#!/usr/bin/env python3
"""Realign RV1909's native (Hebrew/Byzantine-tradition) verse numbering onto
the GOI project's own canonical spine, which follows the English/KJV
versification (see Reference_Bible/Hebrew_Bible_WLC/One_Directory_WLC_KJV and
Reference_Bible/Greek_Bible_TR1550 -- both already KJV-numbered).

Reads:  One_Directory_RV1909/          (raw atomization, native numbering)
Writes: One_Directory_RV1909_GOI/      (GOI/KJV-numbered, for --reference-dir use)

Every one of the 9 affected books below was individually content-verified
against KJV before this table was written (see PLANS_ES.md history / session
log for the verification transcript). Where RV1909 merges two or more KJV
verses into a single native verse, the merged text is copied into *every*
target verse-key it covers -- this is reference-only material, so preserving
full information at each key beats silently dropping half of a merged verse.

The remaining 57 books are a straight copy: RV1909's native numbering already
matches KJV/GOI verse-for-verse there.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC_DIR = ROOT / "One_Directory_RV1909"
OUT_DIR = ROOT / "One_Directory_RV1909_GOI"
SUFFIX = "RV1909"


def identity(book: str) -> dict[tuple[int, int], list[tuple[int, int]]]:
    return {}


def jon() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 17):
        m[(1, v)] = [(1, v)]
    m[(2, 1)] = [(1, 17)]
    for v in range(2, 10):
        m[(2, v)] = [(2, v - 1)]
    m[(2, 10)] = [(2, 9), (2, 10)]
    for c in (3, 4):
        for v in range(1, 30):
            m[(c, v)] = [(c, v)]
    return m


def hos() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 12):
        m[(11, v)] = [(11, v)]
    m[(12, 1)] = [(11, 12)]
    for v in range(2, 14):
        m[(12, v)] = [(12, v - 1)]
    m[(12, 14)] = [(12, 13), (12, 14)]
    return m


def num() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 16):
        m[(12, v)] = [(12, v)]
    m[(13, 1)] = [(12, 16)]
    for v in range(2, 33):
        m[(13, v)] = [(13, v - 1)]
    m[(13, 33)] = [(13, 32), (13, 33)]
    for v in range(1, 40):
        m[(29, v)] = [(29, v)]
    m[(30, 1)] = [(29, 40)]
    for v in range(2, 16):
        m[(30, v)] = [(30, v - 1)]
    m[(30, 16)] = [(30, 15), (30, 16)]
    return m


def sa1() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 29):
        m[(23, v)] = [(23, v)]
    m[(24, 1)] = [(23, 29)]
    for v in range(2, 22):
        m[(24, v)] = [(24, v - 1)]
    m[(24, 22)] = [(24, 21), (24, 22)]
    return m


def sa2() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 25):
        m[(20, v)] = [(20, v)]
    m[(20, 25)] = [(20, 25), (20, 26)]
    return m


def ch2() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 10):
        m[(33, v)] = [(33, v)]
    m[(33, 10)] = [(33, 10), (33, 11)]
    for v in range(11, 25):
        m[(33, v)] = [(33, v + 1)]
    return m


def act() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 40):
        m[(19, v)] = [(19, v)]
    m[(19, 40)] = [(19, 40), (19, 41)]
    return m


def co2() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 12):
        m[(13, v)] = [(13, v)]
    m[(13, 12)] = [(13, 12), (13, 13)]
    m[(13, 13)] = [(13, 14)]
    return m


def job() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 15):
        m[(35, v)] = [(35, v)]
    m[(35, 15)] = [(35, 15), (35, 16)]
    for v in range(1, 39):
        m[(38, v)] = [(38, v)]
    m[(39, 1)] = [(38, 39)]
    m[(39, 2)] = [(38, 40)]
    m[(39, 3)] = [(38, 41)]
    for v in range(4, 30):
        m[(39, v)] = [(39, v - 3)]
    m[(39, 30)] = [
        (39, 27), (39, 28), (39, 29), (39, 30),
        (40, 1), (40, 2), (40, 3), (40, 4), (40, 5),
    ]
    for v in range(1, 20):
        m[(40, v)] = [(40, v + 5)]
    for v in range(1, 35):
        m[(41, v)] = [(41, v)]
    return m


# book -> chapter-scoped correction map; chapters/books not listed are a
# straight identity copy (native numbering already matches KJV/GOI).
BOOK_OVERRIDES = {
    "JON": jon(),
    "HOS": hos(),
    "NUM": num(),
    "1SA": sa1(),
    "2SA": sa2(),
    "2CH": ch2(),
    "ACT": act(),
    "2CO": co2(),
    "JOB": job(),
}


def target_keys(book: str, chapter: int, verse: int) -> list[tuple[int, int]]:
    overrides = BOOK_OVERRIDES.get(book)
    if not overrides:
        return [(chapter, verse)]
    return overrides.get((chapter, verse), [(chapter, verse)])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.txt"):
        old.unlink()

    written = 0
    merges = 0
    for path in sorted(SRC_DIR.glob("*.txt")):
        canon, book, chap_s, verse_s, _suffix = path.stem.split("_")
        chapter, verse = int(chap_s), int(verse_s)
        text = path.read_text(encoding="utf-8")
        keys = target_keys(book, chapter, verse)
        if len(keys) > 1:
            merges += 1
        for out_chapter, out_verse in keys:
            out = OUT_DIR / f"{canon}_{book}_{out_chapter:03d}_{out_verse:03d}_{SUFFIX}.txt"
            out.write_text(text, encoding="utf-8")
            written += 1

    print(f"source verses read: {sum(1 for _ in SRC_DIR.glob('*.txt'))}")
    print(f"source verses that map to >1 target key (merges): {merges}")
    print(f"target files written: {written}")


if __name__ == "__main__":
    main()
