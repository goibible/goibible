#!/usr/bin/env python3
"""Read-only checks for Bible video paths, generated media, and SQLite metadata."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
from collections import defaultdict
from pathlib import Path

import books


HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "bible_video.sqlite3"
VERSE_DIR = Path("/home/albert/projects/bible") / "GOI_Bible" / "GOI_Bible_English"
OUTPUT_DIR = Path("output")
PATH_RE = re.compile(r"^output/(\d{3})_([A-Za-z0-9_]+)/(\d{3})_([A-Za-z0-9_]+)\.mp4$")


def issue(message: str, issues: list[str]) -> None:
    issues.append(message)


def duration_display(seconds: float) -> str:
    rounded = int(round(seconds))
    return f"{rounded // 60}:{rounded % 60:02d}"


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def parse_rate(value: str) -> float:
    if "/" in value:
        num, den = value.split("/", 1)
        return float(num) / float(den)
    return float(value)


def book_chapters(osis: str) -> list[int]:
    nnn = books.number_of(osis)
    seen: set[int] = set()
    for path in VERSE_DIR.glob(f"{nnn:03d}_{osis}_*_GOI_En.txt"):
        match = re.search(r"_(\d{3})_(\d{3})_GOI_En\.txt$", path.name)
        if match:
            seen.add(int(match.group(1)))
    return sorted(seen)


def verse_files_for(osis: str, chapter: int) -> list[Path]:
    nnn = books.number_of(osis)
    return sorted(VERSE_DIR.glob(f"{nnn:03d}_{osis}_{chapter:03d}_*_GOI_En.txt"))


def expected_chapter_count() -> int:
    return sum(len(book_chapters(osis)) for _, osis in books.BOOK_ORDER)


def check_schema(db_path: Path, issues: list[str]) -> None:
    if not db_path.exists():
        issue(f"missing database: {db_path}", issues)
        return
    expected_tables = {"schema_migrations", "corpus_chapters", "media_assets", "youtube_distribution"}
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        missing = expected_tables - tables
        if missing:
            issue(f"database missing table(s): {sorted(missing)}", issues)
        fk_bad = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_bad:
            issue(f"database foreign-key failures: {fk_bad}", issues)
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        if quick != "ok":
            issue(f"database quick_check failed: {quick}", issues)


def check_paths_and_samples(sample_probe_limit: int, issues: list[str]) -> None:
    outputs = sorted(OUTPUT_DIR.glob("*/*.mp4"))
    for path in outputs:
        rel = path.as_posix()
        match = PATH_RE.match(rel)
        if not match:
            issue(f"unexpected mp4 path convention: {rel}", issues)
            continue
        book_num, book_name, chapter_num, file_book_name = match.groups()
        if book_name != file_book_name:
            issue(f"book folder/file name mismatch: {rel}", issues)
        osis = next((code for number, code in books.BOOK_ORDER if number == int(book_num)), None)
        if osis is None:
            issue(f"unknown book number in path: {rel}", issues)
            continue
        expected_rel = (OUTPUT_DIR / books.book_dir_name(osis) / books.chapter_file_name(osis, int(chapter_num))).as_posix()
        if rel != expected_rel:
            issue(f"path should be {expected_rel}, found {rel}", issues)

    for path in outputs[:sample_probe_limit]:
        try:
            data = ffprobe(path)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            issue(f"ffprobe failed for {path}: {exc}", issues)
            continue
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        duration = float(data.get("format", {}).get("duration", 0))
        if video is None:
            issue(f"missing video stream: {path}", issues)
        if audio is None:
            issue(f"missing audio stream: {path}", issues)
        if duration <= 0:
            issue(f"non-positive duration: {path}", issues)
        if video and (video.get("width"), video.get("height")) != (1920, 1080):
            issue(f"unexpected dimensions for {path}: {video.get('width')}x{video.get('height')}", issues)
        if video and abs(parse_rate(video.get("r_frame_rate", "0/1")) - 30.0) > 0.01:
            issue(f"unexpected fps for {path}: {video.get('r_frame_rate')}", issues)


def check_source_invariants(issues: list[str]) -> None:
    books.cross_check(VERSE_DIR)
    chapters_by_book: dict[str, set[int]] = defaultdict(set)
    verses_by_chapter: dict[tuple[str, int], set[int]] = defaultdict(set)

    for path in VERSE_DIR.glob("*_GOI_En.txt"):
        parts = path.stem.split("_")
        if len(parts) < 5:
            issue(f"unexpected source filename: {path.name}", issues)
            continue
        _book_num, osis, chapter, verse = parts[:4]
        chapters_by_book[osis].add(int(chapter))
        verses_by_chapter[(osis, int(chapter))].add(int(verse))

    total_chapters = sum(len(chapters) for chapters in chapters_by_book.values())
    if total_chapters != 1189:
        issue(f"source chapter count is {total_chapters}, expected 1189", issues)

    for osis, chapter in [(osis, chapter) for _, osis in books.BOOK_ORDER for chapter in book_chapters(osis)]:
        files = verse_files_for(osis, chapter)
        expected = set(range(1, len(files) + 1))
        found = verses_by_chapter[(osis, chapter)]
        if found != expected:
            issue(f"non-contiguous verses for {osis} {chapter}: found {sorted(found)[:5]}...{sorted(found)[-5:]}", issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only validation; does not render, delete, upload, or bulk-write.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--sample-probe-limit", type=int, default=2)
    args = parser.parse_args()

    issues: list[str] = []
    check_schema(args.db, issues)
    check_source_invariants(issues)
    check_paths_and_samples(args.sample_probe_limit, issues)

    if issues:
        print("VALIDATION FAILED")
        for item in issues:
            print(f"- {item}")
        raise SystemExit(1)

    print("VALIDATION OK")
    print(f"- expected chapters from source: {expected_chapter_count()}")
    print(f"- mp4 files currently present: {len(sorted(OUTPUT_DIR.glob('*/*.mp4')))}")
    print(f"- sampled media probes: {args.sample_probe_limit}")


if __name__ == "__main__":
    main()
