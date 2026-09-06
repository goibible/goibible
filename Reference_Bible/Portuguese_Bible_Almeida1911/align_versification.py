#!/usr/bin/env python3
"""Align Almeida 1911 native verse files to the GOI/KJV verse spine.

Where Almeida 1911 merges two or more KJV verses into one native verse, the
same Portuguese reference text is copied into every covered GOI key. This keeps
the reference usable for QA without pretending that a source verse split exists.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SRC_DIR = ROOT / "One_Directory_Almeida1911"
OUT_DIR = ROOT / "One_Directory_Almeida1911_GOI"
KJV_DIR = REPO / "Reference_Bible" / "English_Bible_KJV" / "One_Directory_KJV"


def jon() -> dict[tuple[int, int], list[tuple[int, int]]]:
    m: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for v in range(1, 17):
        m[(1, v)] = [(1, v)]
    m[(2, 1)] = [(1, 17)]
    for v in range(2, 10):
        m[(2, v)] = [(2, v - 1)]
    m[(2, 10)] = [(2, 9), (2, 10)]
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


BOOK_OVERRIDES = {
    "JON": jon(),
    "NUM": num(),
    "1SA": sa1(),
    "2SA": sa2(),
    "2CH": ch2(),
    "ACT": act(),
    "2CO": co2(),
}


def target_keys(book: str, chapter: int, verse: int) -> list[tuple[int, int]]:
    overrides = BOOK_OVERRIDES.get(book)
    if not overrides:
        return [(chapter, verse)]
    return overrides.get((chapter, verse), [(chapter, verse)])


def normalized_names(directory: pathlib.Path, suffix: str) -> set[str]:
    return {path.name.replace(f"_{suffix}.txt", ".txt") for path in directory.glob(f"*_{suffix}.txt")}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*_Almeida1911.txt"):
        old.unlink()

    written = 0
    merges = 0
    for path in sorted(SRC_DIR.glob("*_Almeida1911.txt")):
        canon, book, chap_s, verse_s, _suffix = path.stem.split("_")
        keys = target_keys(book, int(chap_s), int(verse_s))
        if len(keys) > 1:
            merges += 1
        text = path.read_text(encoding="utf-8")
        for chapter, verse in keys:
            target = OUT_DIR / f"{canon}_{book}_{chapter:03d}_{verse:03d}_Almeida1911.txt"
            target.write_text(text, encoding="utf-8")
            written += 1

    out_names = normalized_names(OUT_DIR, "Almeida1911")
    kjv_names = normalized_names(KJV_DIR, "KJV")
    missing = sorted(kjv_names - out_names)
    extra = sorted(out_names - kjv_names)
    if missing or extra:
        print(f"missing GOI/KJV keys: {len(missing)}", file=sys.stderr)
        print(f"extra aligned keys: {len(extra)}", file=sys.stderr)
        if missing:
            print("first missing: " + ", ".join(missing[:10]), file=sys.stderr)
        if extra:
            print("first extra: " + ", ".join(extra[:10]), file=sys.stderr)
        raise SystemExit(1)

    print(f"source files read: {sum(1 for _ in SRC_DIR.glob('*_Almeida1911.txt'))}")
    print(f"source verses that map to >1 target key (merges): {merges}")
    print(f"target files written: {written}")


if __name__ == "__main__":
    main()
