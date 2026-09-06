#!/usr/bin/env python3
"""Stage 3: assemble a synced 1080p mp4 for one book chapter.

Whole-Bible generalization of the Proverbs video stage. Each verse is on screen
from the frame nearest its speech onset to the frame nearest the next verse's
onset (last verse holds to the end of the audio); boundaries are anchored to
absolute audio timecode so per-frame rounding never accumulates into drift.

Method: encode each verse's frame as its own tiny segment with
`-loop 1 -framerate FPS -frames:v N` (provably exact N frames), stitch with
`-c copy`, then mux the chapter audio with `-c:v copy` so video timing is
untouched. This replaces the unreliable concat-demuxer image-duration path.

The script verifies its own length/sync and fails fast on any mismatch.

Output: output/<nnn>_<Book>/<ccc>_<Book>.mp4
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import books

WORK_DIR = Path("work")
OUTPUT_DIR = Path("output")
SEG_DIR = Path("work") / "_segments"

FPS = 30
VIDEO_ENCODE = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"]
AUDIO_ENCODE = ["-c:a", "aac", "-b:a", "96k"]


def chapter_work_dir(osis: str, chapter: int) -> Path:
    return WORK_DIR / books.book_dir_name(osis) / f"{chapter:03d}"


def anchor(sec: float) -> int:
    return int(round(sec * FPS))


def verse_frame_counts(timeline: dict) -> list[int]:
    verses = timeline["verses"]
    total = verses[-1]["end_sec"] + timeline["inter_verse_gap"]
    starts = [anchor(v["start_sec"]) for v in verses] + [anchor(total)]
    return [max(starts[i + 1] - starts[i], 1) for i in range(len(verses))]


def encode_segment(frame_path: Path, frame_count: int, seg_path: Path, build_dir: Path) -> None:
    build_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", str(frame_path.resolve()),
            "-frames:v", str(frame_count),
            *VIDEO_ENCODE, "-an",
            str(seg_path.resolve()),
        ],
        check=True,
    )


def stitch_segments(seg_paths: list[Path], stitched_path: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as h:
        concat = Path(h.name)
        for p in seg_paths:
            esc = str(p.resolve()).replace("\\", "/").replace("'", "'\\''")
            h.write(f"file '{esc}'\n")
    try:
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat),
                "-c", "copy", str(stitched_path.resolve()),
            ],
            check=True,
        )
    finally:
        concat.unlink(missing_ok=True)


def probe_len(mp4_path: Path, stream: list[str]) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", *stream, str(mp4_path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip()) if r.stdout.strip() else float("nan")
    except ValueError:
        return float("nan")


def length_report(mp4_path: Path, expected: float) -> tuple[bool, float, float, float]:
    fmt_dur = probe_len(mp4_path, [])
    vid_dur = probe_len(mp4_path, ["-select_streams", "v:0"])
    aud_dur = probe_len(mp4_path, ["-select_streams", "a:0"])
    ok = abs(vid_dur - expected) < 0.05 and abs(aud_dur - expected) < 0.05
    print(f"  format={fmt_dur:.3f}s video={vid_dur:.3f}s audio={aud_dur:.3f}s "
          f"expected={expected:.3f}s -> {'OK' if ok else 'MISMATCH'}", flush=True)
    return ok, fmt_dur, vid_dur, aud_dur


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a synced book-chapter mp4.")
    parser.add_argument("--book", required=True, help="Book name, number, or OSIS code, e.g. Genesis, 01, GEN, Jude")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--resume", action="store_true",
                        help="Skip an existing mp4 when its length/sync check already passes.")
    args = parser.parse_args()

    osis = books.resolve_book(args.book)
    if osis not in books.BOOK_NAMES:
        raise SystemExit(f"Unknown book code '{osis}'")

    wd = chapter_work_dir(osis, args.chapter)
    timeline = json.loads((wd / "timeline.json").read_text(encoding="utf-8"))
    verses = timeline["verses"]
    audio = wd / "chapter.wav"
    if not audio.exists():
        raise SystemExit(f"No chapter audio at {audio}; run generate_audio.py first.")

    counts = verse_frame_counts(timeline)
    if sum(counts) <= 0:
        raise SystemExit("No frames to render.")
    total = verses[-1]["end_sec"] + timeline["inter_verse_gap"]
    expected = anchor(total) / FPS

    out_dir = OUTPUT_DIR / books.book_dir_name(osis)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / books.chapter_file_name(osis, args.chapter)

    if args.resume and out_mp4.exists() and out_mp4.stat().st_size > 0:
        print(f"Checking existing {out_mp4}", flush=True)
        ok, _fmt_dur, _vid_dur, _aud_dur = length_report(out_mp4, expected)
        if ok:
            print(f"Reusing {out_mp4}", flush=True)
            return
        print(f"Existing {out_mp4} failed verification; regenerating.", flush=True)

    build_dir = SEG_DIR / books.book_dir_name(osis) / f"{args.chapter:03d}"
    seg_paths: list[Path] = []
    for i, v in enumerate(verses):
        frame = wd / "frames" / f"{args.chapter:02d}_{v['verse']:03d}.png"
        if not frame.exists():
            raise FileNotFoundError(f"Missing frame {frame}")
        seg = build_dir / f"{i:03d}.mp4"
        encode_segment(frame, counts[i], seg, build_dir)
        seg_paths.append(seg)

    stitched = build_dir / "stitched.mp4"
    stitch_segments(seg_paths, stitched)

    tmp_mp4 = out_mp4.with_suffix(".tmp.mp4")
    tmp_mp4.unlink(missing_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(stitched.resolve()),
            "-i", str(audio.resolve()),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", *AUDIO_ENCODE,
            "-movflags", "+faststart",
            str(tmp_mp4.resolve()),
        ],
        check=True,
    )

    for p in seg_paths:
        p.unlink(missing_ok=True)
    stitched.unlink(missing_ok=True)

    print(f"Wrote {tmp_mp4}", flush=True)

    # ---- Length verification (fail-fast on mismatch) ----
    ok, _fmt_dur, vid_dur, aud_dur = length_report(tmp_mp4, expected)
    if not ok:
        tmp_mp4.unlink(missing_ok=True)
        raise SystemExit(f"DURATION MISMATCH for {osis} ch {args.chapter}: video {vid_dur:.3f}s "
                         f"/ audio {aud_dur:.3f}s vs expected {expected:.3f}s")
    os.replace(tmp_mp4, out_mp4)
    print(f"Finalized {out_mp4}", flush=True)


if __name__ == "__main__":
    main()
