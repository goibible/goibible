#!/usr/bin/env python3
"""Atomize the Wikisource Meiji Genyaku (明治元訳) OT into per-verse files and
align them to the GOI/KJV verse spine.

Source: ja.wikisource.org 明治元訳旧約聖書 (文語訳), {{PD-old}}, transcribed from
the 1937/1953 Japan Bible Society printing. Hand-typed, unlike the scanned
archive.org OCR in source/ (which is unusable). Raw wikitext for all 39 books
is kept in source_wikisource/.

Two markup styles occur across the books, both handled here:
  {{verse|C|V}} text...        (e.g. Genesis, Exodus)
  ==== C:V ====\\n text...      (e.g. Leviticus, Numbers)
Ruby annotations {{ruby|base|reading}} are reduced to the base text so the
ruby-annotated Wikisource edition can be used as a drop-in fallback.

Outputs:
  One_Directory_Meiji1887/      native numbering, one file per verse
  One_Directory_Meiji1887_GOI/  KJV-keyed (via BOOK_OVERRIDES)
  alignment_report.txt          per-book missing/extra keys vs KJV
Unlike the NT script this reports mismatches instead of exiting, so the
overrides can be filled in book by book.
"""
from __future__ import annotations

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SRC = ROOT / "source_wikisource"
NATIVE = ROOT / "One_Directory_Meiji1887"
GOI = ROOT / "One_Directory_Meiji1887_GOI"
KJV_DIR = REPO / "Reference_Bible" / "English_Bible_KJV" / "One_Directory_KJV"
REPORT = ROOT / "alignment_report.txt"
SUFFIX = "Meiji1887"

VERSE_TPL = re.compile(r"\{\{verse\|(\d+)\|(\d+)\}\}")
VERSE_HDR = re.compile(r"^=+\s*(\d+)\s*[:：]\s*(\d+)\s*=+\s*$", re.M)
RUBY = re.compile(r"\{\{ruby\|([^|}]*)\|[^}]*\}\}")
LINK = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]")
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
COMMENT = re.compile(r"<!--.*?-->", re.S)
TAG = re.compile(r"<[^>]+>")

# (book, native_ch, native_vs) -> list of KJV (ch, vs) targets. Several
# native verses landing on one target are concatenated in native order.
BOOK_OVERRIDES: dict[str, dict[tuple[int, int], list[tuple[int, int]]]] = {
    # Each entry: the Meiji verse whose text also carries the listed KJV
    # verse(s). Checked by reading the Meiji text against the KJV: the
    # "missing" KJV verse's content is present inside the neighbouring verse.
    "EXO": {(7, 24): [(7, 24), (7, 25)]},
    "2SA": {(6, 18): [(6, 17), (6, 18)], (10, 17): [(10, 17), (10, 18)],
            (19, 26): [(19, 25), (19, 26)]},
    "1CH": {(2, 47): [(2, 46), (2, 47)], (16, 11): [(16, 11), (16, 12), (16, 13)]},
    "2CH": {(2, 12): [(2, 12), (2, 13)]},
    "PSA": {(49, 2): [(49, 1), (49, 2)], (49, 9): [(49, 8), (49, 9)],
            (50, 17): [(50, 16), (50, 17)], (58, 5): [(58, 4), (58, 5)],
            (63, 6): [(63, 5), (63, 6)], (66, 14): [(66, 13), (66, 14)],
            (76, 9): [(76, 8), (76, 9)], (89, 51): [(89, 50), (89, 51)],
            (105, 6): [(105, 5), (105, 6)], (113, 6): [(113, 5), (113, 6)],
            (132, 5): [(132, 3), (132, 4), (132, 5)]},
    "PRO": {(26, 17): [(26, 17), (26, 18), (26, 19)]},
    "JER": {(9, 24): [(9, 24), (9, 25), (9, 26)]},
}
# Not transcribed on Wikisource at all (no Meiji text exists to align);
# translation falls back to KJV-only references for these verses.
# Numbers 2-36, and 1 Samuel 2:1-13:21 (the Wikisource page resumes at 13:22).
def untranscribed(book: str, ch: int, vs: int) -> bool:
    if book == "NUM":
        return ch >= 2
    if book == "1SA":
        return 2 <= ch <= 12 or (ch == 13 and vs <= 21)
    return False


def clean(raw: str) -> str:
    t = COMMENT.sub("", raw)
    t = RUBY.sub(r"\1", t)
    t = LINK.sub(r"\1", t)
    for _ in range(3):
        t = TEMPLATE.sub("", t)
    t = TAG.sub("", t)
    t = html.unescape(t)
    lines = [l.strip() for l in t.splitlines()]
    lines = [l for l in lines if l and not l.startswith(("==", "-*-", "<[[", "[[", "Category", "カテゴリ"))]
    return re.sub(r"\s+", "", "".join(lines))


def parse(text: str) -> dict[tuple[int, int], str]:
    marks = [(m.start(), m.end(), int(m.group(1)), int(m.group(2))) for m in VERSE_TPL.finditer(text)]
    marks += [(m.start(), m.end(), int(m.group(1)), int(m.group(2))) for m in VERSE_HDR.finditer(text)]
    marks.sort()
    verses: dict[tuple[int, int], str] = {}
    for i, (s, e, ch, vs) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        body = text[e:end]
        # a chapter heading between the last verse and the next chapter belongs to neither
        body = re.split(r"^==+\s*第", body, maxsplit=1, flags=re.M)[0]
        cleaned = clean(body)
        if cleaned:
            verses[(ch, vs)] = verses.get((ch, vs), "") + cleaned
    return verses


def main() -> int:
    for d in (NATIVE, GOI):
        d.mkdir(exist_ok=True)
        for old in d.glob(f"*_{SUFFIX}.txt"):
            old.unlink()
    kjv: dict[str, set[tuple[int, int]]] = {}
    for p in KJV_DIR.glob("*_KJV.txt"):
        n, b, c, v, _ = p.name.split("_")
        if int(n) <= 39:
            kjv.setdefault(b, set()).add((int(c), int(v)))
    report, total_missing, total_extra, native_total = [], 0, 0, 0
    for f in sorted(SRC.glob("*.wikitext")):
        num, book = f.stem.split("_")
        verses = parse(f.read_text(encoding="utf-8"))
        native_total += len(verses)
        targets: dict[tuple[int, int], list[str]] = {}
        for (ch, vs), t in sorted(verses.items()):
            (NATIVE / f"{num}_{book}_{ch:03d}_{vs:03d}_{SUFFIX}.txt").write_text(t + "\n", encoding="utf-8")
            for key in BOOK_OVERRIDES.get(book, {}).get((ch, vs), [(ch, vs)]):
                targets.setdefault(key, []).append(t)
        want = kjv.get(book, set())
        for (ch, vs), texts in targets.items():
            if (ch, vs) in want:
                (GOI / f"{num}_{book}_{ch:03d}_{vs:03d}_{SUFFIX}.txt").write_text(" ".join(texts) + "\n", encoding="utf-8")
        missing_all = sorted(want - set(targets))
        gaps = [k for k in missing_all if untranscribed(book, *k)]
        missing = [k for k in missing_all if not untranscribed(book, *k)]
        extra = sorted(set(targets) - want)
        total_missing += len(missing); total_extra += len(extra)
        line = f"{num} {book}: native {len(verses)}, KJV {len(want)}, missing {len(missing)}, extra {len(extra)}"
        if gaps: line += f", untranscribed on Wikisource {len(gaps)} (KJV-only reference fallback)"
        if missing: line += f"\n    missing: {missing[:25]}{' ...' if len(missing) > 25 else ''}"
        if extra: line += f"\n    extra:   {extra[:25]}{' ...' if len(extra) > 25 else ''}"
        report.append(line)
    summary = f"TOTAL native {native_total}; GOI files {len(list(GOI.glob('*.txt')))} of 23145 KJV OT keys; missing {total_missing}; extra {total_extra}"
    REPORT.write_text("\n".join(report + ["", summary]) + "\n", encoding="utf-8")
    print("\n".join(report)); print(summary)
    return 0 if total_missing == 0 and total_extra == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
