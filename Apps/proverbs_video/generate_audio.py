#!/usr/bin/env python3
"""Stage 1: synthesize one Kokoro WAV per verse + build the chapter timeline.

Reads GOI English Proverbs verse files, synthesizes each verse separately with
the installed Kokoro engine (reusing KokoroEngine from the user's kokoro repo),
normalizes loudness, appends a fixed inter-verse silence gap, and writes:

  work/<proverbs>/audio/<cc>_<vv>.wav   (one normalized mono 24kHz WAV per verse)
  work/<proverbs>/chapter.wav           (concatenated chapter audio track)
  work/<proverbs>/timeline.json         (per-verse start/end seconds + content hash)

The per-verse windows in timeline.json are the single source of truth that both
the video frame timing and the muxed audio derive from, so highlight<->voice sync
cannot drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

# Reuse the user's established Kokoro engine wrapper (installed in their conda env).
KOKORO_REPO = Path("/home/albert/projects/kokoro")
sys.path.insert(0, str(KOKORO_REPO))
from benchmark_kokoro_voices import (  # noqa: E402
    KokoroEngine,
    LUFS_TARGET,
    SAMPLE_RATE,
    normalize_lufs,
    save_audio,
)

# GOI English Proverbs source in the bible repo.
BIBLE_REPO = Path("/home/albert/projects/bible")
VERSE_GLOB = "GOI_Bible/GOI_Bible_English/020_PRO_{cc:03d}_{vv:03d}_GOI_En.txt"
VOICE_FILE = KOKORO_REPO / "reading_voice_choice.txt"

WORK_DIR = Path("work")
OUTPUT_DIR = Path("output")

INTER_VERSE_GAP = 0.35  # seconds of silence between verses (matching existing pipeline)


def load_voice(path: Path = VOICE_FILE) -> str:
    voice = path.read_text(encoding="utf-8").strip()
    if not voice:
        raise ValueError(f"Voice file {path} is empty; set a GOI voice there.")
    return voice


def verse_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_verse_path(path: Path):
    """Return (chapter:int, verse:int) from a 020_PRO_cc_vvv_GOI_En.txt filename."""
    match = re.search(r"020_PRO_(\d{3})_(\d{3})_GOI_En\.txt$", path.name)
    if not match:
        raise ValueError(f"Unexpected verse filename: {path.name}")
    return int(match.group(1)), int(match.group(2))


def verse_files_for(chapter: int) -> list[Path]:
    files = sorted(BIBLE_REPO.glob(f"GOI_Bible/GOI_Bible_English/020_PRO_{chapter:03d}_*_GOI_En.txt"))
    if not files:
        raise FileNotFoundError(f"No GOI English Proverbs verses found for chapter {chapter}")
    return files


def chapter_work_dir(chapter: int) -> Path:
    return WORK_DIR / f"proverbs_{chapter:02d}"


def build_timeline(chapter: int, engine: KokoroEngine, voice: str, resume: bool) -> dict:
    audio_dir = chapter_work_dir(chapter) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    verses = []  # {chapter, verse, text, wav, start_sec, end_sec, hash}
    tracks: list[np.ndarray] = []
    cursor = 0.0

    files = verse_files_for(chapter)
    for path in files:
        chap, vv = parse_verse_path(path)
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"  !! empty verse file {path.name}; skipping", flush=True)
            continue

        h = verse_content_hash(text)
        wav_path = audio_dir / f"{chap:02d}_{vv:03d}.wav"

        if resume and wav_path.exists() and wav_path.stat().st_size > 0:
            info_path = wav_path.with_suffix(".wav.json")
            if info_path.exists() and json.loads(info_path.read_text())["hash"] == h:
                print(f"[{path.name}] reusing {wav_path.name}", flush=True)
                samples = np.asarray(sf.read(wav_path, dtype="float32")[0], dtype=np.float32)
                track = samples
            else:
                print(f"[{path.name}] hash changed -> re-synthesizing", flush=True)
                track = _synthesize_one(text, voice, engine, wav_path, h)
        else:
            print(f"[{path.name}] synthesizing ({len(text)} chars, voice={voice})", flush=True)
            track = _synthesize_one(text, voice, engine, wav_path, h)

        if track.size == 0:
            raise RuntimeError(f"Kokoro returned empty audio for {path.name}")

        gap = np.zeros(int(SAMPLE_RATE * INTER_VERSE_GAP), dtype=np.float32)
        full = np.concatenate([track, gap])
        start = cursor
        end = cursor + float(track.size) / SAMPLE_RATE
        cursor = end + INTER_VERSE_GAP

        tracks.append(full)
        verses.append(
            {
                "chapter": chap,
                "verse": vv,
                "text": text,
                "wav": str(wav_path.relative_to(chapter_work_dir(chapter))),
                "start_sec": round(start, 6),
                "end_sec": round(end, 6),
                "hash": h,
            }
        )

    chapter_audio = np.concatenate(tracks).astype(np.float32, copy=False)
    chapter_wav = chapter_work_dir(chapter) / "chapter.wav"
    save_audio(chapter_audio, chapter_wav, SAMPLE_RATE)

    timeline = {
        "chapter": chapter,
        "voice": voice,
        "sample_rate": SAMPLE_RATE,
        "inter_verse_gap": INTER_VERSE_GAP,
        "verses": verses,
    }
    timeline_path = chapter_work_dir(chapter) / "timeline.json"
    timeline_path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    return timeline


def _synthesize_one(text: str, voice: str, engine: KokoroEngine, wav_path: Path, h: str) -> np.ndarray:
    audio = engine.synthesize(text, voice)
    audio = normalize_lufs(audio, engine.sample_rate, LUFS_TARGET)
    save_audio(audio, wav_path, engine.sample_rate)
    wav_path.with_suffix(".wav.json").write_text(json.dumps({"hash": h}), encoding="utf-8")
    return audio


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize GOI Proverbs chapter audio with Kokoro.")
    parser.add_argument("--chapter", type=int, required=True, help="Proverbs chapter 1-31")
    parser.add_argument("--resume", action="store_true", help="Reuse already-rendered verses when content unchanged")
    args = parser.parse_args()

    if not 1 <= args.chapter <= 31:
        raise SystemExit("Chapter must be between 1 and 31.")

    voice = load_voice()
    engine = KokoroEngine()
    timeline = build_timeline(args.chapter, engine, voice, args.resume)
    n = len(timeline["verses"])
    total = timeline["verses"][-1]["end_sec"] + INTER_VERSE_GAP if n else 0.0
    print(f"chapter {args.chapter}: {n} verses, ~{total:.1f}s audio -> {chapter_work_dir(args.chapter)}", flush=True)


if __name__ == "__main__":
    main()
