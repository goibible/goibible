#!/usr/bin/env python3
"""Run the full Proverbs video pipeline for one or all chapters.

Usage:
  /home/albert/miniconda3/envs/kokoro/bin/python run_all.py --chapter 1
  /home/albert/miniconda3/envs/kokoro/bin/python run_all.py            # all 31
  ... --resume                                                          # skip finished work
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_stage(stage: str, chapter: int, resume: bool, quiet: bool = False) -> None:
    cmd = [sys.executable, str(HERE / f"{stage}.py"), "--chapter", str(chapter)]
    if resume:
        cmd.append("--resume")
    if not quiet:
        print(f"\n=== {stage}.py chapter {chapter} ===", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GOI Proverbs videos.")
    parser.add_argument("--chapter", type=int, default=None, help="Single chapter 1-31 (default: all)")
    parser.add_argument("--resume", action="store_true", help="Reuse existing audio/frames")
    args = parser.parse_args()

    chapters = [args.chapter] if args.chapter is not None else range(1, 32)

    started = time.perf_counter()
    for chapter in chapters:
        t0 = time.perf_counter()
        run_stage("generate_audio", chapter, args.resume)
        run_stage("render_frames", chapter, args.resume)
        run_stage("render_video", chapter, args.resume, quiet=True)
        elapsed = time.perf_counter() - t0
        print(f"chapter {chapter} done in {elapsed / 60:.1f} min", flush=True)

    total = time.perf_counter() - started
    print(f"\nAll done in {total / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
