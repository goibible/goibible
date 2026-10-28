#!/usr/bin/env python3
"""Write a YouTube metadata sidecar next to every chapter mp4.

  <OUTPUT_DIR>/<nnn>_<Book>/<ccc>_<Book>.json

Same shape as make_intro.py's sidecar: a YouTube Data API videos.insert body
(snippet + status) plus "playlist" (one per book). Built from each chapter's
work/<book>/<ccc>/timeline.json, and only when video_signature.txt shows the mp4
was rendered from that timeline, so the text quoted is the text spoken.

  python3 make_sidecars.py            # all 1,189 chapters
  python3 make_sidecars.py --book Psalms
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import books

VERSE_DIR = Path("/home/albert/projects/bible") / "GOI_Bible" / "GOI_Bible_en"
FPS = 30  # = render_video.FPS (kept local so this script runs with plain python3)
QUOTE_MAX = 300


def chapter_label(osis: str, chapter: int) -> str:
    name = books.display_name_of(osis)
    return f"Psalm {chapter}" if osis == "PSA" else f"{name} {chapter}"


def duration(timeline: dict) -> str:
    v = timeline["verses"]
    secs = round((v[-1]["end_sec"] + timeline["inter_verse_gap"]) * FPS) // FPS
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def quote(text: str) -> str:
    if len(text) <= QUOTE_MAX:
        return text
    return text[:QUOTE_MAX].rsplit(" ", 1)[0].rstrip(",;:") + " …"


def sidecar(osis: str, chapter: int, n_chapters: int, timeline: dict) -> dict:
    name = books.display_name_of(osis)
    label = chapter_label(osis, chapter)
    number = books.number_of(osis)
    testament = "Old Testament" if number <= 39 else "New Testament"
    verses = timeline["verses"]
    hashtag = "#" + name.replace(" ", "")
    description = f"""{label}, read aloud from the GOI Bible (English), with each verse highlighted as it is read.

"{quote(verses[0]['text'])}" ({label}:{verses[0]['verse']})

{name} · chapter {chapter} of {n_chapters} · book {number} of 66 · {testament} · {len(verses)} verses · {duration(timeline)}
Playlist: {name}, GOI Bible (English). New here? Start with the video "Intro to GOI Bible".

GOI stands for Global Ordinal Index: every verse of the Bible has one number, so every GOI edition lines up verse for verse in every language. Old Testament from the Hebrew Westminster Leningrad Codex; New Testament from the Greek Textus Receptus (Stephanus 1550).

Text, database, apps and downloads: https://goibible.org
License: MIT, free to read, copy and share.
The translation is AI-assisted and checked against the Hebrew and Greek. Narration is a synthetic voice (Kokoro TTS).

#Bible {hashtag} #AudioBible"""
    title = f"{label} | GOI Bible (English) Audio Bible"
    assert len(title) <= 100 and len(description) <= 5000, (osis, chapter)
    assert not any(c in title + description for c in "<>"), (osis, chapter)
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["Bible", "GOI Bible", "Audio Bible", name, label, testament, "Bible reading", "KJV numbering"],
            "categoryId": "27",  # Education
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",  # flip to public after review
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
        "playlist": f"{name}, GOI Bible (English)",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write YouTube JSON sidecars for chapter videos.")
    parser.add_argument("--book", default=None, help="One book (name, number, or OSIS); default all 66")
    args = parser.parse_args()
    targets = [books.resolve_book(args.book)] if args.book else [osis for _, osis in books.BOOK_ORDER]

    written, problems = 0, []
    for osis in targets:
        chapters = books.chapters_for(osis, VERSE_DIR)
        for chapter in chapters:
            wd = books.WORK_DIR / books.book_dir_name(osis) / f"{chapter:03d}"
            mp4 = books.OUTPUT_DIR / books.book_dir_name(osis) / books.chapter_file_name(osis, chapter)
            timeline = json.loads((wd / "timeline.json").read_text(encoding="utf-8"))
            sig = wd / "video_signature.txt"
            if not mp4.exists():
                problems.append(f"missing mp4 {mp4}"); continue
            if not sig.exists() or sig.read_text().strip() != books.timeline_signature(timeline):
                problems.append(f"mp4 not built from current timeline: {mp4}"); continue
            data = sidecar(osis, chapter, len(chapters), timeline)
            mp4.with_suffix(".json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            written += 1
    print(f"wrote {written} sidecar(s) under {books.OUTPUT_DIR}")
    if problems:
        print("\n".join(problems))
        raise SystemExit(f"{len(problems)} chapter(s) skipped")


if __name__ == "__main__":
    main()
