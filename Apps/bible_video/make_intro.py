#!/usr/bin/env python3
"""Render the "Intro to GOI Bible" video in the same format as the chapter videos.

intro.txt holds the script, one paragraph per line; each paragraph is voiced and
highlighted the way a verse is. SPOKEN rewrites words only in the audio, so the
screen shows "GOI" while the voice says the letters.

  /home/albert/miniconda3/envs/kokoro/bin/python make_intro.py                 # video + sidecar
  /home/albert/miniconda3/envs/kokoro/bin/python make_intro.py --sidecar-only  # rewrite the JSON only

Output: <OUTPUT_DIR>/000_Intro_to_GOI_Bible.mp4 (top level, outside the 66 book
folders, so validate_metadata.py's chapter checks are unaffected), plus a .json
sidecar shaped as a YouTube Data API videos.insert body (snippet + status), with
"playlist" as the one extra key (null: the intro belongs to no playlist).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np

import books
import generate_audio as ga
import render_frames as rf
import render_video as rv

TITLE = "Intro to GOI Bible"
NAME = "000_Intro_to_GOI_Bible"
SCRIPT = books.APP_DIR / "intro.txt"
WD = books.WORK_DIR / NAME
OUT_MP4 = books.OUTPUT_DIR / f"{NAME}.mp4"
OUT_JSON = OUT_MP4.with_suffix(".json")

# YouTube rejects "<" and ">" in titles/descriptions; title <= 100 chars, description <= 5000.
DESCRIPTION = """What is the GOI Bible, and why does every verse have a number?

GOI stands for Global Ordinal Index: every verse from Genesis to Revelation gets one whole number in reading order. Genesis 1:1 is 1, John 3:16 is 26,137, Revelation 22:21 is 31,102. One shared key means the same verse in every edition and every language, so the Bible becomes data: one row per verse in a SQLite database, parallel reading in any two languages, the Hebrew and Greek sources side by side, and every correction visible as a plain-text change.

Sources: Old Testament from the Hebrew Westminster Leningrad Codex; New Testament from the Greek Textus Receptus (Stephanus 1550). Both public domain.
Current translations: English, Spanish, French, Portuguese, Russian, Japanese, Korean, Vietnamese, Simplified Chinese, Traditional Chinese, and more to come.

This channel will carry the whole Bible in every GOI translation, one video per chapter (1,189 chapters), each verse highlighted as it is read. English comes first; the other languages follow as their own series.

Text, database, apps and downloads: https://goibible.org
License: MIT, free to read, copy and share.
The translation is AI-assisted and checked against the Hebrew and Greek. Narration is a synthetic voice (Kokoro TTS).

#Bible #GOIBible #AudioBible"""

SIDECAR = {
    "snippet": {
        "title": "Intro to GOI Bible: one number for every verse",
        "description": DESCRIPTION,
        "tags": ["Bible", "GOI Bible", "Audio Bible", "Global Ordinal Index", "Bible database", "SQLite",
                 "parallel Bible", "open source Bible", "Hebrew Bible", "Greek New Testament", "Yahweh"],
        "categoryId": "27",  # Education
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en",
    },
    "status": {
        "privacyStatus": "private",  # flip to public after review
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": True,
    },
    "playlist": None,  # owner 2026-10-20: the intro is uploaded once, standalone, not in any book playlist
}

SPOKEN = [
    (r"goibible\.org", "G O I Bible dot org"),
    (r"\bGOI\b", "G O I"),
    (r"\bMIT\b", "M I T"),
    (r"\b1550\b", "fifteen fifty"),
    (r"\bSQLite\b", "S Q Lite"),
    (r"\b(\d+):(\d+)\b", r"\1 \2"),  # "John 3:16" -> "John 3 16", read as "John three sixteen"
]


def spoken(text: str) -> str:
    for pattern, repl in SPOKEN:
        text = re.sub(pattern, repl, text)
    return text


def build_timeline() -> dict:
    paragraphs = [line.strip() for line in SCRIPT.read_text(encoding="utf-8").splitlines() if line.strip()]
    voice = ga.load_voice()
    engine = ga.KokoroEngine()
    audio_dir = WD / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    gap = np.zeros(int(ga.SAMPLE_RATE * ga.INTER_VERSE_GAP), dtype=np.float32)
    verses, tracks, cursor = [], [], 0.0
    for n, text in enumerate(paragraphs, 1):
        say = spoken(text)
        print(f"[{n:02d}] {say}", flush=True)
        track = ga._synthesize_one(say, voice, engine, audio_dir / f"{n:03d}.wav", ga.verse_content_hash(say))
        start, end = cursor, cursor + track.size / ga.SAMPLE_RATE
        cursor = end + ga.INTER_VERSE_GAP
        tracks.append(np.concatenate([track, gap]))
        verses.append({"chapter": 0, "verse": n, "text": text, "spoken": say,
                       "start_sec": round(start, 6), "end_sec": round(end, 6)})
    ga.save_audio(np.concatenate(tracks).astype(np.float32), WD / "chapter.wav", ga.SAMPLE_RATE)
    return {"book_display": TITLE, "voice": voice, "inter_verse_gap": ga.INTER_VERSE_GAP, "verses": verses}


def write_sidecar() -> None:
    snippet = SIDECAR["snippet"]
    assert len(snippet["title"]) <= 100 and len(snippet["description"]) <= 5000
    assert not any(c in snippet["title"] + snippet["description"] for c in "<>")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(SIDECAR, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the Intro to GOI Bible video and its YouTube sidecar.")
    parser.add_argument("--sidecar-only", action="store_true", help="Rewrite the .json sidecar without re-rendering")
    args = parser.parse_args()
    write_sidecar()
    if args.sidecar_only:
        return

    timeline = build_timeline()
    verses = timeline["verses"]

    rows, _ypos, total_h = rf.build_rows(verses, TITLE, attribution="GOI Bible · English · goibible.org",
                                         chapter_headings=False, numbered=False)
    frames = [WD / "frames" / f"{v['verse']:03d}.png" for v in verses]
    for v, frame in zip(verses, frames):
        rf.render_frame(rows, total_h, v["verse"], frame)

    seg_dir = rv.SEG_DIR / NAME
    segs = []
    for i, (frame, count) in enumerate(zip(frames, rv.verse_frame_counts(timeline))):
        seg = seg_dir / f"{i:03d}.mp4"
        rv.encode_segment(frame, count, seg, seg_dir)
        segs.append(seg)
    stitched = seg_dir / "stitched.mp4"
    rv.stitch_segments(segs, stitched)

    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_MP4.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(stitched), "-i", str(WD / "chapter.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", *rv.AUDIO_ENCODE,
                    "-movflags", "+faststart", str(tmp)], check=True)
    for p in [*segs, stitched]:
        p.unlink(missing_ok=True)

    expected = rv.anchor(verses[-1]["end_sec"] + timeline["inter_verse_gap"]) / rv.FPS
    ok, *_ = rv.length_report(tmp, expected)
    if not ok:
        tmp.unlink(missing_ok=True)
        raise SystemExit("DURATION MISMATCH for intro")
    os.replace(tmp, OUT_MP4)
    print(f"Finalized {OUT_MP4}", flush=True)


if __name__ == "__main__":
    main()
