#!/usr/bin/env python3
"""Benchmark every English Kokoro voice and write WAV samples.

This script intentionally uses the installed Kokoro Python package directly.
It does not call web APIs and writes 24 kHz WAV files suitable for production
review. The benchmark logic is separated from the Kokoro engine wrapper so
other TTS engines can be added later without rewriting reports or outputs.
"""

from __future__ import annotations

import csv
import html
import os
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np
import soundfile as sf
from kokoro import KPipeline

try:
    import pyloudnorm as pyln
except ImportError:  # Loudness normalization is a bonus feature, not required.
    pyln = None


SAMPLE_RATE = 24_000
LUFS_TARGET = -16.0
TEXT_FILE = Path("text_sample.txt")
OUTPUT_DIR = Path("voice_samples")
COMBINED_FILE = "all_voices.wav"
KOKORO_REPO_ID = "hexgrad/Kokoro-82M"


VOICE_GROUPS: dict[tuple[str, str], list[str]] = {
    ("American", "Female"): [
        "af_alloy",
        "af_aoede",
        "af_bella",
        "af_heart",
        "af_jessica",
        "af_kore",
        "af_nicole",
        "af_nova",
        "af_river",
        "af_sarah",
        "af_sky",
    ],
    ("American", "Male"): [
        "am_adam",
        "am_echo",
        "am_eric",
        "am_fenrir",
        "am_liam",
        "am_michael",
        "am_onyx",
        "am_puck",
        "am_santa",
    ],
    ("British", "Female"): [
        "bf_alice",
        "bf_emma",
        "bf_isabella",
        "bf_lily",
    ],
    ("British", "Male"): [
        "bm_daniel",
        "bm_fable",
        "bm_george",
        "bm_lewis",
    ],
}


@dataclass(frozen=True)
class Voice:
    name: str
    accent: str
    gender: str

    @property
    def output_subdir(self) -> str:
        return self.gender.lower()

    @property
    def relative_audio_path(self) -> Path:
        return Path(self.output_subdir) / f"{self.name}.wav"


@dataclass
class BenchmarkResult:
    voice: Voice
    audio: np.ndarray
    duration: float
    generation_seconds: float

    @property
    def realtime_factor(self) -> float:
        if self.duration <= 0:
            return float("inf")
        return self.generation_seconds / self.duration


class TTSEngine(Protocol):
    """Common shape expected from any future local TTS engine."""

    sample_rate: int

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        """Return mono float audio for the requested voice."""


class KokoroEngine:
    """Small adapter around the installed Kokoro package."""

    sample_rate = SAMPLE_RATE

    def __init__(self) -> None:
        self._pipelines: dict[str, KPipeline] = {}

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        lang_code = self._lang_code_for_voice(voice)
        pipeline = self._pipeline(lang_code)

        chunks: list[np.ndarray] = []
        for result in pipeline(text, voice=voice):
            chunks.append(self._extract_audio(result))

        if not chunks:
            raise RuntimeError(f"Kokoro returned no audio for {voice}")

        return np.concatenate(chunks).astype(np.float32, copy=False)

    def _pipeline(self, lang_code: str) -> KPipeline:
        if lang_code not in self._pipelines:
            device = os.environ.get("BIBLE_VIDEO_KOKORO_DEVICE")
            self._pipelines[lang_code] = KPipeline(
                lang_code=lang_code,
                repo_id=KOKORO_REPO_ID,
                device=device,
            )
        return self._pipelines[lang_code]

    @staticmethod
    def _lang_code_for_voice(voice: str) -> str:
        if voice.startswith(("af_", "am_")):
            return "a"
        if voice.startswith(("bf_", "bm_")):
            return "b"
        raise ValueError(f"Unsupported English Kokoro voice prefix: {voice}")

    @staticmethod
    def _extract_audio(result: object) -> np.ndarray:
        # Kokoro versions have yielded tuples and result objects. Support both.
        audio = getattr(result, "audio", None)
        if audio is None and isinstance(result, tuple) and len(result) >= 3:
            audio = result[2]
        if audio is None:
            raise RuntimeError("Could not extract audio from Kokoro result")
        return np.asarray(audio, dtype=np.float32)


def iter_voices() -> list[Voice]:
    voices: list[Voice] = []
    for (accent, gender), names in VOICE_GROUPS.items():
        voices.extend(Voice(name=name, accent=accent, gender=gender) for name in names)
    return voices


def load_text(path: Path = TEXT_FILE) -> str:
    """Read narration text from disk and validate that it is usable."""

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{path} is empty")
    return text


def normalize_lufs(audio: np.ndarray, sample_rate: int, target_lufs: float) -> np.ndarray:
    """Normalize audio to a shared LUFS target when pyloudnorm is available."""

    if pyln is None:
        return audio

    meter = pyln.Meter(sample_rate)
    loudness = meter.integrated_loudness(audio)
    if not np.isfinite(loudness):
        return audio

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Possible clipped samples in output.")
        normalized = pyln.normalize.loudness(audio, loudness, target_lufs)

    # Preserve the loudness target when possible, but never write clipped samples.
    peak = float(np.max(np.abs(normalized))) if normalized.size else 0.0
    if peak > 0.99:
        normalized = normalized * (0.99 / peak)

    return normalized.astype(np.float32, copy=False)


def generate_voice(engine: TTSEngine, voice: Voice, text: str) -> BenchmarkResult:
    """Generate and time one voice sample."""

    started = time.perf_counter()
    audio = engine.synthesize(text, voice.name)
    generation_seconds = time.perf_counter() - started
    audio = normalize_lufs(audio, engine.sample_rate, LUFS_TARGET)
    duration = len(audio) / engine.sample_rate

    return BenchmarkResult(
        voice=voice,
        audio=audio,
        duration=duration,
        generation_seconds=generation_seconds,
    )


def save_audio(audio: np.ndarray, output_path: Path, sample_rate: int = SAMPLE_RATE) -> None:
    """Write a 24 kHz WAV file, creating parent directories when needed."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, audio, sample_rate, format="WAV")


def write_report(results: Iterable[BenchmarkResult], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "Voice",
                "Gender",
                "Accent",
                "Duration",
                "Generation Seconds",
                "Realtime Factor",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.voice.name,
                    result.voice.gender,
                    result.voice.accent,
                    f"{result.duration:.3f}",
                    f"{result.generation_seconds:.3f}",
                    f"{result.realtime_factor:.4f}",
                ]
            )


def write_index(results: Iterable[BenchmarkResult], output_path: Path) -> None:
    rows = []
    for result in results:
        voice = html.escape(result.voice.name)
        accent = html.escape(result.voice.accent)
        gender = html.escape(result.voice.gender)
        filename = html.escape(result.voice.relative_audio_path.as_posix())
        rows.append(
            f"<tr><td>{voice}</td><td>{accent}</td><td>{gender}</td>"
            f'<td><audio controls preload="none" src="{filename}"></audio></td></tr>'
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kokoro Voice Benchmark</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.65rem 0.75rem; border-bottom: 1px solid #d9e2ec; text-align: left; }}
    th {{ background: #f0f4f8; font-weight: 700; }}
    audio {{ width: min(28rem, 100%); }}
  </style>
</head>
<body>
  <h1>Kokoro Voice Benchmark</h1>
  <table>
    <thead><tr><th>Voice</th><th>Accent</th><th>Gender</th><th>Audio Player</th></tr></thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    output_path.write_text(page, encoding="utf-8")


def synthesize_announcement(engine: TTSEngine, voice: Voice) -> np.ndarray:
    spoken_name = voice.name.replace("_", " ")
    audio = engine.synthesize(f"{spoken_name}.", voice.name)
    return normalize_lufs(audio, engine.sample_rate, LUFS_TARGET)


def write_all_voices(engine: TTSEngine, results: list[BenchmarkResult], output_path: Path) -> None:
    """Concatenate every successful voice with an announced label and silence."""

    if not results:
        return

    silence = np.zeros(engine.sample_rate, dtype=np.float32)
    segments: list[np.ndarray] = []
    for result in results:
        try:
            announcement = synthesize_announcement(engine, result.voice)
        except Exception as exc:
            print(f"Warning: announcement failed for {result.voice.name}: {exc}", flush=True)
            announcement = np.zeros(0, dtype=np.float32)
        segments.extend([announcement, result.audio, silence])

    save_audio(np.concatenate(segments), output_path, engine.sample_rate)


def benchmark() -> None:
    """Run the Kokoro voice benchmark and write all deliverables."""

    voices = iter_voices()
    text = load_text()
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if pyln is None:
        print("pyloudnorm is not installed; skipping LUFS normalization.")

    engine: TTSEngine = KokoroEngine()
    results: list[BenchmarkResult] = []
    failures: list[tuple[str, str]] = []
    started = time.perf_counter()

    for index, voice in enumerate(voices, start=1):
        print(f"[{index}/{len(voices)}] Generating {voice.name}...", flush=True)
        try:
            result = generate_voice(engine, voice, text)
            save_audio(result.audio, output_dir / voice.relative_audio_path, engine.sample_rate)
            results.append(result)
        except Exception as exc:
            failures.append((voice.name, str(exc)))
            print(f"  Failed {voice.name}: {exc}", flush=True)

    write_report(results, output_dir / "report.csv")
    write_index(results, output_dir / "index.html")
    write_all_voices(engine, results, output_dir / COMBINED_FILE)

    elapsed = time.perf_counter() - started
    total_audio_seconds = sum(result.duration for result in results)
    total_generation_seconds = sum(result.generation_seconds for result in results)
    average_speed = (
        total_audio_seconds / total_generation_seconds if total_generation_seconds > 0 else 0.0
    )
    average_rtf = (
        sum(result.realtime_factor for result in results) / len(results) if results else 0.0
    )

    print()
    print(f"Total elapsed time: {elapsed:.2f} seconds")
    print(f"Average generation speed: {average_speed:.2f}x realtime")

    if results:
        fastest = min(results, key=lambda item: item.realtime_factor)
        slowest = max(results, key=lambda item: item.realtime_factor)
        print(f"Fastest voice: {fastest.voice.name} ({fastest.realtime_factor:.4f} RTF)")
        print(f"Slowest voice: {slowest.voice.name} ({slowest.realtime_factor:.4f} RTF)")
        print(f"Average RTF: {average_rtf:.4f}")

    if failures:
        print()
        print("Failed voices:")
        for voice, error in failures:
            print(f"- {voice}: {error}")
    else:
        print("Failed voices: none")


if __name__ == "__main__":
    benchmark()
