#!/usr/bin/env python3
"""Atomize the structured Korean 1910/1911 HTML export on the KJV spine.

The KJV directory is the coordinate authority. The Korean source is parsed
one chapter at a time, so a missing, duplicate, or unexpected verse marker
stops the build instead of producing silently shifted reference files.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
DEFAULT_OUT = Path(__file__).resolve().parent / "One_Directory_KORSYS1911"
DEFAULT_REPORT = Path(__file__).resolve().parent / "alignment_report.json"
SOURCE_URL = "https://ebible.org/kor/kor_html.zip"


class VerseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current: int | None = None
        self.parts: list[str] = []
        self.verses: dict[int, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "span":
            return
        values = dict(attrs)
        if values.get("class") == "verse" and values.get("id", "").startswith("V"):
            self.current = int(values["id"][1:])
            self.parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.current is not None:
            self.verses[self.current] = normalize(" ".join(self.parts))
            self.current = None
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.parts.append(data)

    def close(self) -> None:
        super().close()
        if self.current is not None:
            self.verses[self.current] = normalize(" ".join(self.parts))
            self.current = None


def spine() -> dict[tuple[str, int], list[int]]:
    result: dict[tuple[str, int], list[int]] = {}
    for path in sorted(KJV_DIR.glob("*_KJV.txt")):
        conical, book, chapter, verse, _ = path.stem.split("_")
        result.setdefault((book, int(chapter)), []).append(int(verse))
    if len(result) == 0 or len({book for book, _ in result}) != 66:
        raise SystemExit("KJV spine is incomplete")
    return result


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", html.unescape(text))
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chapter_verses(archive: zipfile.ZipFile, book: str, chapter: int) -> dict[int, str]:
    width = 3 if book == "PSA" else 2
    name = f"{book}{chapter:0{width}d}.htm"
    try:
        raw = archive.read(name).decode("utf-8")
    except KeyError as exc:
        raise ValueError(f"missing chapter member {name}") from exc
    parser = VerseParser()
    parser.feed(raw)
    parser.close()
    return parser.verses


def parse_chapter(found: dict[int, str], verses: list[int]) -> tuple[dict[int, str], list[str]]:
    expected = set(verses)
    problems: list[str] = []
    for number in verses:
        if number not in found:
            problems.append(f"verse {number}: marker missing")
        elif not found[number]:
            problems.append(f"verse {number}: empty text")
    unexpected = sorted(set(found) - expected)
    if unexpected:
        problems.append(f"unexpected verse markers: {unexpected}")
    return {number: found[number] for number in verses if number in found}, problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_zip", type=Path, help="eBible kor_html.zip")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write", action="store_true", help="write files only when every chapter passes")
    parser.add_argument("--write-partial", action="store_true", help="write only chapters that pass; retain the gap report")
    args = parser.parse_args()

    expected = spine()
    report: dict[str, object] = {
        "source": "eBible Korean Bible 1910 structured HTML export",
        "source_url": SOURCE_URL,
        "spine": "KJV",
        "chapters": {},
        "errors": [],
    }
    parsed_all: dict[tuple[str, int], dict[int, str]] = {}
    with zipfile.ZipFile(args.html_zip) as archive:
        for (book, chapter), verses in expected.items():
            conical = next(path.stem.split("_")[0] for path in KJV_DIR.glob(f"*_{book}_{chapter:03d}_001_KJV.txt"))
            key = f"{book} {chapter}"
            try:
                parsed, problems = parse_chapter(chapter_verses(archive, book, chapter), verses)
            except ValueError as exc:
                parsed, problems = {}, [str(exc)]
            report["chapters"][key] = {"expected_verses": len(verses), "parsed_verses": len(parsed), "errors": problems}
            if problems:
                report["errors"].extend([f"{key}: {problem}" for problem in problems])
            parsed_all[(book, chapter)] = parsed

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = report["errors"]
    if errors and not args.write_partial:
        raise SystemExit(f"Korean/KJV alignment failed: {len(errors)} issue(s); see {args.report}")
    if args.write or args.write_partial:
        args.out.mkdir(parents=True, exist_ok=True)
        for (book, chapter), verses in parsed_all.items():
            conical = next(path.stem.split("_")[0] for path in KJV_DIR.glob(f"*_{book}_{chapter:03d}_001_KJV.txt"))
            for verse in sorted(verses):
                path = args.out / f"{conical}_{book}_{chapter:03d}_{verse:03d}_KORSYS1911.txt"
                path.write_text(verses[verse] + "\n", encoding="utf-8")
    print(f"Korean/KJV aligned chapters: {len(expected)}")
    print(f"Korean/KJV aligned verses: {sum(len(v) for v in expected.values())}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
