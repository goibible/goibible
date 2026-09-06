#!/usr/bin/env python3
"""Convert queued text files in input/ to Kokoro-read M4A audiobooks.

Each source text file is split into conservative narration chunks, rendered to
numbered WAV files under output/<book-stem>/, combined into one M4A file, and
then moved to finished/ only after the final audio is written successfully.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

from benchmark_kokoro_voices import (
    LUFS_TARGET,
    KokoroEngine,
    normalize_lufs,
    save_audio,
)


INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
FINISHED_DIR = Path("finished")
VOICE_FILE = Path("reading_voice_choice.txt")

MAX_CHARS = 900
MIN_CHARS = 240
M4A_BITRATE = "96k"


def load_voice(path: Path = VOICE_FILE) -> str:
    voice = path.read_text(encoding="utf-8").strip()
    if not voice:
        raise ValueError(f"{path} is empty")
    return voice


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_piece(piece: str, max_chars: int) -> list[str]:
    """Split a paragraph-like piece on sentence and clause boundaries."""

    piece = piece.strip()
    if len(piece) <= max_chars:
        return [piece] if piece else []

    sentence_parts = re.split(r"(?<=[.!?;:])\s+", piece)
    chunks: list[str] = []
    current = ""

    for sentence in sentence_parts:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(split_oversized_sentence(sentence, max_chars))
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks


def split_oversized_sentence(sentence: str, max_chars: int) -> list[str]:
    parts = re.split(r"(?<=[,])\s+", sentence)
    chunks: list[str] = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = f"{current} {part}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(part) > max_chars:
            split_at = part.rfind(" ", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = max_chars
            chunks.append(part[:split_at].strip())
            part = part[split_at:].strip()
        current = part

    if current:
        chunks.append(current)
    return chunks


def chunk_text(text: str, max_chars: int = MAX_CHARS, min_chars: int = MIN_CHARS) -> list[str]:
    """Build chunks from paragraphs while preserving natural pauses."""

    normalized = normalize_text(text)
    if not normalized:
        return []

    pieces: list[str] = []
    for paragraph in re.split(r"\n\s*\n", normalized):
        pieces.extend(split_long_piece(paragraph, max_chars))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        separator = "\n\n" if current else ""
        candidate = f"{current}{separator}{piece}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = piece
        else:
            current = candidate

        if len(current) >= min_chars and re.search(r"[.!?](['\"])?$", current):
            chunks.append(current)
            current = ""

    if current:
        if chunks and len(current) < min_chars and len(chunks[-1]) + len(current) + 2 <= max_chars:
            chunks[-1] = f"{chunks[-1]}\n\n{current}"
        else:
            chunks.append(current)

    return chunks


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 10_000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find an unused path based on {path}")


def synthesize_chunks(
    engine: KokoroEngine,
    chunks: list[str],
    voice: str,
    output_dir: Path,
    resume: bool,
) -> list[Path]:
    wav_paths: list[Path] = []
    width = max(4, len(str(len(chunks))))

    for index, chunk in enumerate(chunks, start=1):
        wav_path = output_dir / f"{index:0{width}d}.wav"
        wav_paths.append(wav_path)
        if resume and wav_path.exists() and wav_path.stat().st_size > 0:
            print(f"[{index}/{len(chunks)}] Reusing {wav_path}", flush=True)
            continue

        print(f"[{index}/{len(chunks)}] Synthesizing {len(chunk)} chars", flush=True)
        audio = engine.synthesize(chunk, voice)
        audio = normalize_lufs(audio, engine.sample_rate, LUFS_TARGET)

        silence = np.zeros(int(engine.sample_rate * 0.35), dtype=np.float32)
        save_audio(np.concatenate([audio, silence]), wav_path, engine.sample_rate)

    return wav_paths


def write_m4a(wav_paths: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output_path.with_suffix(".tmp.m4a")
    if temp_output.exists():
        temp_output.unlink()

    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as handle:
        concat_file = Path(handle.name)
        for wav_path in wav_paths:
            escaped = wav_path.resolve().as_posix().replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")

    try:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            M4A_BITRATE,
            str(temp_output),
        ]
        subprocess.run(command, check=True)
        temp_output.replace(output_path)
    finally:
        concat_file.unlink(missing_ok=True)
        temp_output.unlink(missing_ok=True)


def move_to_finished(source_path: Path) -> Path:
    FINISHED_DIR.mkdir(parents=True, exist_ok=True)
    destination = unique_path(FINISHED_DIR / source_path.name)
    shutil.move(str(source_path), str(destination))
    return destination


def process_file(engine: KokoroEngine, source_path: Path, voice: str, resume: bool) -> None:
    started = time.perf_counter()
    print(f"Reading {source_path}", flush=True)
    text = source_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(f"{source_path} contains no readable text")

    book_dir = OUTPUT_DIR / source_path.stem
    book_dir.mkdir(parents=True, exist_ok=True)
    final_path = unique_path(OUTPUT_DIR / f"{source_path.stem}.m4a")

    print(f"Voice: {voice}", flush=True)
    print(f"Chunks: {len(chunks)}", flush=True)
    wav_paths = synthesize_chunks(engine, chunks, voice, book_dir, resume)
    write_m4a(wav_paths, final_path)
    finished_path = move_to_finished(source_path)

    elapsed = time.perf_counter() - started
    print(f"Wrote {final_path}", flush=True)
    print(f"Moved source to {finished_path}", flush=True)
    print(f"Elapsed: {elapsed / 60:.1f} minutes", flush=True)


def iter_input_files(limit: int | None) -> list[Path]:
    files = sorted(path for path in INPUT_DIR.iterdir() if path.is_file() and path.suffix == ".txt")
    if limit is None:
        return files
    return files[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process only the first queued text file.")
    parser.add_argument("--resume", action="store_true", help="Reuse existing non-empty WAV chunks.")
    args = parser.parse_args()

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINISHED_DIR.mkdir(parents=True, exist_ok=True)

    voice = load_voice()
    engine = KokoroEngine()
    processed = 0

    while True:
        files = iter_input_files(limit=1 if args.once else None)
        if not files:
            print("input/ is empty.", flush=True)
            break
        for source_path in files:
            process_file(engine, source_path, voice, args.resume)
            processed += 1
        if args.once:
            break

    print(f"Processed files: {processed}", flush=True)


if __name__ == "__main__":
    main()
