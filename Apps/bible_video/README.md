# GOI Bible — Whole-Bible Read-Along Videos

Generates a synced, verse-highlighted, 1080p read-along mp4 for **every chapter
of the entire GOI English Bible** (66 books, 31,102 verses), using the same
proven pipeline as the Proverbs videos.

- **Voice**: Kokoro via your conda env (`/home/albert/miniconda3/envs/kokoro/bin/python`),
  using the localized wrapper and voice choice in `vendor/kokoro/` (default `am_onyx`).
  Set `BIBLE_VIDEO_KOKORO_REPO` only when intentionally pointing at a different Kokoro wrapper.
- **Text**: `GOI_Bible/GOI_Bible_en/` (GOI English edition).
- **Sync**: every verse is read as a scrolling text column; the verse being spoken
  is highlighted and kept centered. Audio timeline and video timing both derive
  from the same per-verse onsets, so highlight↔voice cannot drift (verified by the
  built-in length check on every chapter).

## Output layout (unix-friendly, capitalized names)
Videos go to `~/projects/bible/youtube/` (`books.OUTPUT_DIR`; override with `BIBLE_VIDEO_OUTPUT_DIR`).
Intermediate audio/frames go to `Apps/bible_video/work/` (`books.WORK_DIR`). Both are gitignored.
```
youtube/
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
rebuilds what changed: verse audio is keyed by the verse text hash, and frames and the mp4
are keyed by the chapter timeline signature (`frames/signature.txt`, `video_signature.txt`),
so a text edit anywhere in a chapter re-renders that chapter.

## Intro video and YouTube sidecars
- `make_intro.py` renders `youtube/000_Intro_to_GOI_Bible.mp4` from `intro.txt` (one paragraph per line, highlighted like verses; `SPOKEN` rewrites words for the voice only, e.g. GOI -> "G O I"). It sits at the top level, outside the book folders, and belongs to no playlist.
- Every mp4 gets a `.json` sidecar next to it, shaped as a YouTube Data API `videos.insert` body (`snippet` + `status`, private, synthetic media declared) plus `playlist` (one per book; null for the intro).
  - `make_intro.py --sidecar-only` rewrites the intro's.
  - `python3 make_sidecars.py [--book Psalms]` rewrites the chapters'. It skips (and reports) any chapter whose mp4 was not built from its current timeline.
- Previous/next links need YouTube video IDs, so they come in a pass after upload.
