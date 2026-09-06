#!/usr/bin/env python3
"""Stage 1: synthesize one Kokoro WAV per verse + build a chapter timeline.

Whole-Bible generalization of the Proverbs audio stage. For a given book (OSIS
code) it discovers that book's chapters from the GOI English verse files and, for
each chapter (or --chapter N), synthesizes each verse separately with Kokoro,
normalizes loudness, appends a fixed inter-verse gap, and writes:

  work/<book>/<ccc>/audio/<cc>_<vv>.wav   (one normalized mono 24kHz WAV / verse)
  work/<book>/<ccc>/chapter.wav           (concatenated chapter audio track)
  work/<book>/<ccc>/timeline.json         (per-verse start/end seconds + hash)

timeline.json is the single source of truth that both the video frame timing and
the muxed audio derive from, so highlight<->voice sync cannot drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

import books

# Prefer the project-local Kokoro wrapper so this app can move to another server consistently.
LOCAL_KOKORO_REPO = Path(__file__).resolve().parent / "vendor" / "kokoro"
FALLBACK_KOKORO_REPO = Path("/home/albert/projects/kokoro")
KOKORO_REPO = Path(os.environ.get("BIBLE_VIDEO_KOKORO_REPO", LOCAL_KOKORO_REPO))
if not (KOKORO_REPO / "benchmark_kokoro_voices.py").exists():
    KOKORO_REPO = FALLBACK_KOKORO_REPO
sys.path.insert(0, str(KOKORO_REPO))
from benchmark_kokoro_voices import (  # noqa: E402
    KokoroEngine,
    LUFS_TARGET,
    SAMPLE_RATE,
    normalize_lufs,
    save_audio,
)

# GOI English source in the bible repo.
VERSE_DIR = Path("/home/albert/projects/bible") / "GOI_Bible" / "GOI_Bible_English"
VOICE_FILE = KOKORO_REPO / "reading_voice_choice.txt"

WORK_DIR = Path("work")
INTER_VERSE_GAP = 0.35  # seconds of silence between verses


def load_voice(path: Path = VOICE_FILE) -> str:
    voice = path.read_text(encoding="utf-8").strip()
    if not voice:
        raise ValueError(f"Voice file {path} is empty; set a GOI voice there.")
    return voice


def verse_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def book_chapters(osis: str) -> list[int]:
    """Sorted chapter numbers present for a book, derived from the GOI files."""
    nnn = books.number_of(osis)
    seen: set[int] = set()
    for p in VERSE_DIR.glob(f"{nnn:03d}_{osis}_*_GOI_En.txt"):
        m = re.search(r"_(\d{3})_(\d{3})_GOI_En\.txt$", p.name)
        if m:
            seen.add(int(m.group(1)))
    if not seen:
        raise FileNotFoundError(f"No GOI English verses found for {osis}")
    return sorted(seen)


def verse_files_for(osis: str, chapter: int) -> list[Path]:
    nnn = books.number_of(osis)
    files = sorted(VERSE_DIR.glob(f"{nnn:03d}_{osis}_{chapter:03d}_*_GOI_En.txt"))
    if not files:
        raise FileNotFoundError(f"No GOI English verses for {osis} {chapter}")
    return files


def chapter_work_dir(osis: str, chapter: int) -> Path:
    return WORK_DIR / books.book_dir_name(osis) / f"{chapter:03d}"


def build_timeline(osis: str, chapter: int, engine: KokoroEngine, voice: str, resume: bool) -> dict:
    wd = chapter_work_dir(osis, chapter)
    audio_dir = wd / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    verses: list[dict] = []
    tracks: list[np.ndarray] = []
    cursor = 0.0

    for path in verse_files_for(osis, chapter):
        m = re.search(r"_(\d{3})_(\d{3})_GOI_En\.txt$", path.name)
        chap, vv = int(m.group(1)), int(m.group(2))
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"  !! empty verse file {path.name}; skipping", flush=True)
            continue

        h = verse_content_hash(text)
        wav_path = audio_dir / f"{chap:02d}_{vv:03d}.wav"
        info_path = wav_path.with_suffix(".wav.json")

        if resume and wav_path.exists() and wav_path.stat().st_size > 0:
            if info_path.exists() and json.loads(info_path.read_text())["hash"] == h:
                print(f"[{path.name}] reusing {wav_path.name}", flush=True)
                track = np.asarray(sf.read(wav_path, dtype="float32")[0], dtype=np.float32)
            else:
                print(f"[{path.name}] hash changed -> re-synthesizing", flush=True)
                track = _synthesize_one(text, voice, engine, wav_path, h)
        else:
            print(f"[{path.name}] synthesizing ({len(text)} chars, voice={voice})", flush=True)
            track = _synthesize_one(text, voice, engine, wav_path, h)

        if track.size == 0:
            raise RuntimeError(f"Kokoro returned empty audio for {path.name}")

        gap = np.zeros(int(SAMPLE_RATE * INTER_VERSE_GAP), dtype=np.float32)
        start = cursor
        end = cursor + float(track.size) / SAMPLE_RATE
        cursor = end + INTER_VERSE_GAP

        tracks.append(np.concatenate([track, gap]))
        verses.append(
            {
                "book": osis,
                "chapter": chap,
                "verse": vv,
                "text": text,
                "wav": str(wav_path.relative_to(wd)),
                "start_sec": round(start, 6),
                "end_sec": round(end, 6),
                "hash": h,
            }
        )

    chapter_audio = np.concatenate(tracks).astype(np.float32, copy=False)
    save_audio(chapter_audio, wd / "chapter.wav", SAMPLE_RATE)

    timeline = {
        "book": osis,
        "book_dir": books.book_dir_name(osis),
        "book_display": books.display_name_of(osis),
        "chapter": chapter,
        "voice": voice,
        "sample_rate": SAMPLE_RATE,
        "inter_verse_gap": INTER_VERSE_GAP,
        "verses": verses,
    }
    (wd / "timeline.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    return timeline


def _synthesize_one(text: str, voice: str, engine: KokoroEngine, wav_path: Path, h: str) -> np.ndarray:
    audio = engine.synthesize(text, voice)
    audio = normalize_lufs(audio, engine.sample_rate, LUFS_TARGET)
    save_audio(audio, wav_path, engine.sample_rate)
    wav_path.with_suffix(".wav.json").write_text(json.dumps({"hash": h}), encoding="utf-8")
    return audio


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize GOI book chapter audio with Kokoro.")
    parser.add_argument("--book", required=True, help="Book name, number, or OSIS code, e.g. Genesis, 01, GEN, Jude")
    parser.add_argument("--chapter", type=int, default=None, help="Single chapter (default: all chapters)")
    parser.add_argument("--resume", action="store_true", help="Reuse unchanged verses")
    args = parser.parse_args()

    osis = books.resolve_book(args.book)
    if osis not in books.BOOK_NAMES:
        raise SystemExit(f"Unknown book code '{osis}'. Expected one of: {sorted(books.BOOK_NAMES)}")

    voice = load_voice()
    engine = KokoroEngine()
    chapters = [args.chapter] if args.chapter is not None else book_chapters(osis)
    for chapter in chapters:
        timeline = build_timeline(osis, chapter, engine, voice, args.resume)
        n = len(timeline["verses"])
        total = timeline["verses"][-1]["end_sec"] + INTER_VERSE_GAP if n else 0.0
        print(f"{books.book_dir_name(osis)} ch {chapter}: {n} verses, ~{total:.1f}s audio "
              f"-> {chapter_work_dir(osis, chapter)}", flush=True)


if __name__ == "__main__":
    main()
