#!/usr/bin/env python3
"""Run the whole-Bible GOI read-along video pipeline.

Usage:
  /home/albert/miniconda3/envs/kokoro/bin/python run_all.py                 # all 66 books
  /home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book Proverbs # one book
  /home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book Genesis --chapter 1
  ... --resume                                                               # skip finished work

Each chapter produces output/<nnn>_<Name>/<ccc>_<Name>.mp4. Every chapter passes
the built-in length/sync check before the run proceeds; a failing chapter aborts.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import books


HERE = Path(__file__).resolve().parent
VERSE_DIR = Path("/home/albert/projects/bible") / "GOI_Bible" / "GOI_Bible_English"


def run_stage(stage: str, osis: str, chapter: int, resume: bool, quiet: bool = False) -> None:
    cmd = [sys.executable, str(HERE / f"{stage}.py"), "--book", osis, "--chapter", str(chapter)]
    if resume:
        cmd.append("--resume")
    if not quiet:
        print(f"\n=== {stage}.py {osis} ch {chapter} ===", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build all GOI Bible read-along videos.")
    parser.add_argument("--book", default=None, help="Book name, number, or OSIS code for one book only (default: all 66)")
    parser.add_argument("--chapter", type=int, default=None, help="Single chapter (default: all chapters)")
    parser.add_argument("--resume", action="store_true", help="Reuse existing audio/frames/mp4")
    parser.add_argument("--dry-run", action="store_true", help="Print the chapters that would run without generating files")
    args = parser.parse_args()

    books.cross_check(VERSE_DIR)

    if args.book:
        books_to_run = [books.resolve_book(args.book)]
    else:
        books_to_run = [osis for _, osis in books.BOOK_ORDER]

    if args.dry_run:
        total = 0
        for osis in books_to_run:
            if osis not in books.BOOK_NAMES:
                raise SystemExit(f"Unknown book code '{osis}'")
            chapters = [args.chapter] if args.chapter is not None else books.chapters_for(osis, VERSE_DIR)
            total += len(chapters)
            chapter_list = ", ".join(str(chapter) for chapter in chapters)
            print(f"DRY RUN: {books.book_dir_name(osis)} chapter(s): {chapter_list}", flush=True)
        print(f"DRY RUN: {total} chapter video(s) would be processed; no files changed.", flush=True)
        return

    started = time.perf_counter()
    for osis in books_to_run:
        if osis not in books.BOOK_NAMES:
            raise SystemExit(f"Unknown book code '{osis}'")
        t_book = time.perf_counter()
        chapters = [args.chapter] if args.chapter is not None else books.chapters_for(osis, VERSE_DIR)
        for chapter in chapters:
            t0 = time.perf_counter()
            run_stage("generate_audio", osis, chapter, args.resume)
            run_stage("render_frames", osis, chapter, args.resume)
            run_stage("render_video", osis, chapter, args.resume, quiet=True)
            print(f"{books.book_dir_name(osis)} ch {chapter} done in "
                  f"{(time.perf_counter() - t0) / 60:.1f} min", flush=True)
        print(f"{books.book_dir_name(osis)} done in {(time.perf_counter() - t_book) / 60:.1f} min", flush=True)

    print(f"\nAll done in {(time.perf_counter() - started) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
