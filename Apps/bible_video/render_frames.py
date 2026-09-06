#!/usr/bin/env python3
"""Stage 2: render one 1080p PNG per verse for a book's chapter.

Whole-Bible generalization of the Proverbs frame stage. For each verse of a
chapter we draw the ENTIRE chapter as a scrolling text column with that verse
highlighted (bold + background band) and vertically centered. The chapter heading
uses the book's capitalized name (e.g. "Song of Solomon"). Consecutive frames
differ only by a small scroll offset, so playback reads as smooth scrolling.

Frame i is shown for exactly verse i's audio window (see render_video.py), so the
highlighted verse always matches the verse being spoken.

Output: work/<nnn>_<Book>/<ccc>/frames/<cc>_<vv>.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import books

FRAME_W = 1920
FRAME_H = 1080

PAPER = (250, 246, 238)
INK = (40, 42, 45)
VERSE_REF = (128, 108, 86)
HIGHLIGHT_BG = (232, 206, 144)  # warm band behind the active verse
HIGHLIGHT_INK = (24, 24, 28)
HEADING = (96, 66, 46)
ATTR = (150, 142, 132)

MARGIN_L = 190
MARGIN_R = 190
TEXT_W = FRAME_W - MARGIN_L - MARGIN_R
HEADING_SIZE = 58
VERSE_SIZE = 46
LINE_H = 64
VERSE_REF_W = 96  # reserved width for the verse number gutter
PARA_GAP = 26      # extra vertical gap before each verse block

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if font.getlength(candidate) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_rows(verses: list[dict], book_display: str) -> list[dict]:
    """Rows for the whole chapter column (heading + attribution + verse lines)."""
    verse_font = load_font(VERSE_SIZE)

    rows: list[dict] = [
        {"kind": "heading", "verse": None, "text": book_display},
        {"kind": "attribution", "verse": None, "text": f"GOI Bible · English · {book_display}"},
    ]

    for v in verses:
        if v.get("verse") == 1:
            rows.append({"kind": "heading", "verse": None, "text": f"Chapter {v['chapter']}"})
        wrapped = wrap(v["text"], verse_font, TEXT_W - VERSE_REF_W)
        for i, line in enumerate(wrapped):
            kind = "verse_start" if i == 0 else "verse_cont"
            rows.append({"kind": kind, "verse": v["verse"], "text": line})

    y_positions: list[int] = []
    y = 0
    for row in rows:
        if row["kind"] == "verse_start":
            y += PARA_GAP
        y_positions.append(y)
        y += LINE_H
    total_h = y
    for row, yy in zip(rows, y_positions):
        row["top"] = yy
    return rows, y_positions, total_h


def verse_row_range(rows: list[dict], verse: int):
    tops = [r["top"] for r in rows if r["verse"] == verse]
    first = min(tops)
    last = max(r["top"] + LINE_H for r in rows if r["verse"] == verse)
    return first, last


def render_frame(rows: list[dict], total_h: int, active_verse: int, out_path: Path) -> None:
    img = Image.new("RGB", (FRAME_W, FRAME_H), PAPER)
    draw = ImageDraw.Draw(img)

    head_font = load_font(HEADING_SIZE)
    verse_font = load_font(VERSE_SIZE)
    ref_font = load_font(int(VERSE_SIZE * 0.62))
    attr_font = load_font(int(VERSE_SIZE * 0.55))

    first, last = verse_row_range(rows, active_verse)
    center = (first + last) / 2.0
    top_margin = 80
    bottom_margin = 80
    min_offset = top_margin
    max_offset = max(top_margin, total_h + bottom_margin - FRAME_H)
    offset = int(min(max(center - FRAME_H / 2.0, min_offset), max_offset))

    for row in rows:
        y = row["top"] - offset
        if y + LINE_H < 0 or y > FRAME_H:
            continue
        is_active = row["verse"] == active_verse

        if row["kind"] == "heading":
            draw.text((MARGIN_L, y), row["text"], font=head_font, fill=HEADING)
        elif row["kind"] == "attribution":
            draw.text((MARGIN_L + VERSE_REF_W, y), row["text"], font=attr_font, fill=ATTR)
        elif row["kind"] == "verse_start":
            x = MARGIN_L
            if is_active:
                band_bottom = y + LINE_H
                draw.rectangle([MARGIN_L - 14, y - 4, FRAME_W - MARGIN_R + 14, band_bottom + 2],
                               fill=HIGHLIGHT_BG)
            draw.text((x, y), str(row["verse"]), font=ref_font, fill=HIGHLIGHT_INK if is_active else VERSE_REF)
            draw.text((x + VERSE_REF_W - 10, y), row["text"], font=verse_font,
                      fill=HIGHLIGHT_INK if is_active else INK)
        elif row["kind"] == "verse_cont":
            x = MARGIN_L
            if is_active:
                band_bottom = y + LINE_H
                draw.rectangle([MARGIN_L + VERSE_REF_W - 20, y - 4, FRAME_W - MARGIN_R + 14, band_bottom + 2],
                               fill=HIGHLIGHT_BG)
            draw.text((x + VERSE_REF_W - 10, y), row["text"], font=verse_font,
                      fill=HIGHLIGHT_INK if is_active else INK)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render highlight frames for a book chapter.")
    parser.add_argument("--book", required=True, help="Book name, number, or OSIS code, e.g. Genesis, 01, GEN, Jude")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--resume", action="store_true", help="Skip frames that already exist")
    args = parser.parse_args()

    osis = books.resolve_book(args.book)
    if osis not in books.BOOK_NAMES:
        raise SystemExit(f"Unknown book code '{osis}'")

    work = Path("work") / books.book_dir_name(osis) / f"{args.chapter:03d}"
    timeline = json.loads((work / "timeline.json").read_text(encoding="utf-8"))
    verses = timeline["verses"]
    if not verses:
        raise SystemExit(f"No verses in timeline for {osis} {args.chapter}")

    rows, _ypos, total_h = build_rows(verses, timeline["book_display"])
    frame_dir = work / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    for v in verses:
        vv = v["verse"]
        frame_path = frame_dir / f"{args.chapter:02d}_{vv:03d}.png"
        if args.resume and frame_path.exists():
            print(f"[{vv:03d}] reusing frame", flush=True)
        else:
            render_frame(rows, total_h, vv, frame_path)
            print(f"[{vv:03d}] frame written", flush=True)

    print(f"{timeline['book_display']} ch {args.chapter}: {len(verses)} frames -> {frame_dir}", flush=True)


if __name__ == "__main__":
    main()
