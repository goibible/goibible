# GOI Bible — Whole-Bible Read-Along Videos

Generates a synced, verse-highlighted, 1080p read-along mp4 for **every chapter
of the entire GOI English Bible** (66 books, 31,102 verses), using the same
proven pipeline as the Proverbs videos.

- **Voice**: Kokoro via your conda env (`/home/albert/miniconda3/envs/kokoro/bin/python`),
  using the localized wrapper and voice choice in `vendor/kokoro/` (default `am_onyx`).
  Set `BIBLE_VIDEO_KOKORO_REPO` only when intentionally pointing at a different Kokoro wrapper.
- **Text**: `GOI_Bible/GOI_Bible_English/` (GOI English edition).
- **Sync**: every verse is read as a scrolling text column; the verse being spoken
  is highlighted and kept centered. Audio timeline and video timing both derive
  from the same per-verse onsets, so highlight↔voice cannot drift (verified by the
  built-in length check on every chapter).

## Output layout (unix-friendly, capitalized names)
```
output/
└── <nnn>_<Name>/            e.g. 020_Proverbs, 022_Song_of_Solomon, 001_Genesis
    └── <ccc>_<Name>.mp4     e.g. 001_Proverbs.mp4, 031_Proverbs.mp4
```

## Stages (modeled on `Apps/proverbs_video/`)
| File | Role |
| --- | --- |
| `books.py` | Canonical 66-book OSIS→name map + `nnn_Name` / `ccc_Name` helpers; cross-checks against the GOI data. |
| `generate_audio.py` | Stage 1 — Kokoro WAV per verse + `chapter.wav` + `timeline.json` (resumable). |
| `render_frames.py` | Stage 2 — one 1080p highlight frame per verse (resumable). |
| `render_video.py` | Stage 3 — synced mp4 via deterministic segment-stitch; **runs the length/sync check**. |
| `run_all.py` | Orchestrator over all 66 books × chapters. |

## Usage
```bash
cd Apps/bible_video
# dry-run a tiny book first; prints what would happen, changes nothing
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book Jude --dry-run
# one chapter, using a book name or number
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book Genesis --chapter 1
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book 01 --chapter 1
# one book (all its chapters)
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py --book Jude
# everything (66 books -> 1189 chapter videos)
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py
# --resume skips already-completed chapters after verifying the existing mp4
/home/albert/miniconda3/envs/kokoro/bin/python run_all.py --resume
```

## Verification
Each produced mp4 self-checks: `video ≈ audio ≈ expected` (≤0.05 s) or the run
fails fast with `DURATION MISMATCH`. `--resume` reuses finished work and only
rebuilds what changed.
