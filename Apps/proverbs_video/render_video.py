#!/usr/bin/env python3
"""Stage 3: assemble a synced 1080p mp4 for a Proverbs chapter.

Sync model
----------
Each verse has an absolute audio onset (start_sec) recorded in timeline.json.
We anchor every verse's on-screen window to the *absolute* audio timecode:

    start_frame(verse_i) = round(start_sec_i * FPS)
    end_frame(verse_i)   = round(start_frame of next verse)   (last: round(total*FPS))

so each verse is on screen from the frame nearest its speech onset to the frame
nearest the next verse's onset (speech + trailing pause), and the last verse holds
to the end of the audio. Because boundaries are anchored to absolute audio time
(rather than accumulated), per-frame rounding can never stack into drift.

Why not the concat demuxer's image `duration` directives?
---------------------------------------------------------
That path is unreliable for exact timing: it ignores the last file's duration
(emits it for ~1 frame) and turns non-integer durations into slightly-off frame
counts, which accumulate across 30+ verses (~1.4s of drift by the end of a
chapter). Instead we encode each verse as its own tiny video segment using
`-loop 1 -framerate FPS -frames:v N` (which provably emits exactly N frames — no
rounding ambiguity), stitch the segments with `-c copy` (preserving their exact
timing), then mux the audio with `-c:v copy` so the video timing is untouched.

Output: output/020_PRO_<cc>.mp4  (1080p, H.264 + AAC, 30 fps)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

WORK_DIR = Path("work")
OUTPUT_DIR = Path("output")
SEG_DIR = Path("work") / "_segments"

FPS = 30
VIDEO_ENCODE = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"]
AUDIO_ENCODE = ["-c:a", "aac", "-b:a", "96k"]


def work_dir(chapter: int) -> Path:
    return WORK_DIR / f"proverbs_{chapter:02d}"


def anchor(sec: float) -> int:
    return int(round(sec * FPS))


def verse_frame_counts(timeline: dict) -> list[int]:
    """Absolute-anchored output frame count for each verse."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a synced Proverbs mp4.")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--resume", action="store_true",
                        help="Accepted for orchestrator uniformity; the mp4 is always regenerated.")
    args = parser.parse_args()

    if not 1 <= args.chapter <= 31:
        raise SystemExit("Chapter must be between 1 and 31.")

    wd = work_dir(args.chapter)
    timeline = json.loads((wd / "timeline.json").read_text(encoding="utf-8"))
    verses = timeline["verses"]
    audio = wd / "chapter.wav"
    if not audio.exists():
        raise SystemExit(f"No chapter audio at {audio}; run generate_audio.py first.")

    counts = verse_frame_counts(timeline)
    if sum(counts) <= 0:
        raise SystemExit("No frames to render.")

    build_dir = SEG_DIR / f"proverbs_{args.chapter:02d}"
    seg_paths: list[Path] = []
    for i, v in enumerate(verses):
        frame = wd / "frames" / f"{v['chapter']:02d}_{v['verse']:03d}.png"
        if not frame.exists():
            raise FileNotFoundError(f"Missing frame {frame}")
        seg = build_dir / f"{i:03d}.mp4"
        encode_segment(frame, counts[i], seg, build_dir)
        seg_paths.append(seg)

    stitched = build_dir / "stitched.mp4"
    stitch_segments(seg_paths, stitched)

    OUTDIR = OUTPUT_DIR
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out_mp4 = OUTDIR / f"020_PRO_{args.chapter:02d}.mp4"
    if out_mp4.exists():
        out_mp4.unlink()

    # Mux stitched video (copy -> timing preserved) with the chapter audio.
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(stitched.resolve()),
            "-i", str(audio.resolve()),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", *AUDIO_ENCODE,
            "-movflags", "+faststart",
            str(out_mp4.resolve()),
        ],
        check=True,
    )

    # Clean intermediate segments for this chapter.
    for p in seg_paths:
        p.unlink(missing_ok=True)
    stitched.unlink(missing_ok=True)

    print(f"Wrote {out_mp4}", flush=True)

    # ---- Length verification (the check the user asked for) ----
    def probe_len(args_for_stream: list[str]) -> float:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", *args_for_stream, str(out_mp4)],
            capture_output=True, text=True,
        )
        try:
            return float(r.stdout.strip()) if r.stdout.strip() else float("nan")
        except ValueError:
            return float("nan")

    total = verses[-1]["end_sec"] + timeline["inter_verse_gap"]
    expected = anchor(total) / FPS
    fmt_dur = probe_len([])
    vid_dur = probe_len(["-select_streams", "v:0"])
    aud_dur = probe_len(["-select_streams", "a:0"])
    ok = abs(vid_dur - expected) < 0.05 and abs(aud_dur - expected) < 0.05
    print(f"  format={fmt_dur:.3f}s video={vid_dur:.3f}s audio={aud_dur:.3f}s "
          f"expected={expected:.3f}s -> {'OK' if ok else 'MISMATCH'}", flush=True)
    if not ok:
        raise SystemExit(f"DURATION MISMATCH for chapter {args.chapter}: video {vid_dur:.3f}s "
                         f"/ audio {aud_dur:.3f}s vs expected {expected:.3f}s")


if __name__ == "__main__":
    main()
