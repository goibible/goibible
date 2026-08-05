#!/usr/bin/env python3
# wlc_atomize.py
#
# Usage:
#   python wlc_atomize.py "C:\path\to\Genesis.xml"
#
# Output (example):
#   atom/GEN/001_GEN_002_003_WLC.txt
#
# Notes:
# - Parses Tanach.us UXLC/WLC-style book XML files (one book per XML).
# - Atomizes at <v n="..."> level; verse text = all <w> tokens joined with spaces.
# - Ignores non-<w> elements inside verses (e.g., <pe/>).
# - Preserves Hebrew Unicode (niqqud/cantillation) as-is.

from __future__ import annotations

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple, Optional

SOURCE_ID = "WLC"
OUT_ROOT = Path("atom")

# 39-book OT map (Protestant ordering; OSIS 3-letter codes)
BOOK_MAP: Dict[str, Tuple[str, str]] = {
    "Genesis": ("001", "GEN"),
    "Exodus": ("002", "EXO"),
    "Leviticus": ("003", "LEV"),
    "Numbers": ("004", "NUM"),
    "Deuteronomy": ("005", "DEU"),
    "Joshua": ("006", "JOS"),
    "Judges": ("007", "JDG"),
    "Ruth": ("008", "RUT"),
    "1 Samuel": ("009", "1SA"),
    "2 Samuel": ("010", "2SA"),
    "1 Kings": ("011", "1KI"),
    "2 Kings": ("012", "2KI"),
    "1 Chronicles": ("013", "1CH"),
    "2 Chronicles": ("014", "2CH"),
    "Ezra": ("015", "EZR"),
    "Nehemiah": ("016", "NEH"),
    "Esther": ("017", "EST"),
    "Job": ("018", "JOB"),
    "Psalms": ("019", "PSA"),
    "Proverbs": ("020", "PRO"),
    "Ecclesiastes": ("021", "ECC"),
    "Song of Songs": ("022", "SNG"),
    "Song of Solomon": ("022", "SNG"),  # alias, just in case
    "Isaiah": ("023", "ISA"),
    "Jeremiah": ("024", "JER"),
    "Lamentations": ("025", "LAM"),
    "Ezekiel": ("026", "EZE"),
    "Daniel": ("027", "DAN"),
    "Hosea": ("028", "HOS"),
    "Joel": ("029", "JOL"),
    "Amos": ("030", "AMO"),
    "Obadiah": ("031", "OBA"),
    "Jonah": ("032", "JON"),
    "Micah": ("033", "MIC"),
    "Nahum": ("034", "NAH"),
    "Habakkuk": ("035", "HAB"),
    "Zephaniah": ("036", "ZEP"),
    "Haggai": ("037", "HAG"),
    "Zechariah": ("038", "ZEC"),
    "Malachi": ("039", "MAL"),
}

# Filename-to-book-name fallback (Tanach.us filenames)
FILENAME_ALIASES: Dict[str, str] = {
    "Samuel_1": "1 Samuel",
    "Samuel_2": "2 Samuel",
    "Kings_1": "1 Kings",
    "Kings_2": "2 Kings",
    "Chronicles_1": "1 Chronicles",
    "Chronicles_2": "2 Chronicles",
    "Song_of_Songs": "Song of Songs",
}

def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def strip_ns(tag: str) -> str:
    # Handles "{namespace}tag" → "tag"
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag

def zero3(n: str) -> str:
    return str(int(n)).zfill(3)

def resolve_book_from_xml(root: ET.Element, input_path: Path) -> Tuple[str, str, str]:
    """
    Returns (book_order, book_id, canonical_book_name).
    Prefers <tanach><book><names><name>English</name>.
    Falls back to filename conventions (e.g., Song_of_Songs.xml, Samuel_1.xml).
    """
    # Find first <book> then <names><name>
    book_name: Optional[str] = None
    for child in root.iter():
        if strip_ns(child.tag) == "book":
            # inside book, look for names/name
            for names in child:
                if strip_ns(names.tag) == "names":
                    for n in names:
                        if strip_ns(n.tag) == "name" and (n.text and n.text.strip()):
                            book_name = n.text.strip()
                            break
                if book_name:
                    break
            break

    if book_name:
        if book_name in BOOK_MAP:
            order, bid = BOOK_MAP[book_name]
            return order, bid, book_name
        # Some XML might use "Song of Songs" vs "Song_of_Songs" etc.
        # Try a normalized compare
        normalized = re.sub(r"\s+", " ", book_name).strip()
        if normalized in BOOK_MAP:
            order, bid = BOOK_MAP[normalized]
            return order, bid, normalized
        die(f"Book name in XML not recognized: '{book_name}'")

    # Fallback: use filename stem
    stem = input_path.stem
    stem = stem.replace(".DH", "")  # if someone passed a *.DH.xml
    if stem in FILENAME_ALIASES:
        canonical = FILENAME_ALIASES[stem]
    else:
        # Convert underscores to spaces: e.g., "Song_of_Songs" (handled above), otherwise "Genesis"
        canonical = stem.replace("_", " ")

    if canonical in BOOK_MAP:
        order, bid = BOOK_MAP[canonical]
        return order, bid, canonical

    die(f"Could not resolve book from XML or filename: '{input_path.name}'")
    raise RuntimeError  # unreachable

def iter_verses(root: ET.Element):
    """
    Yields tuples (chapter_n, verse_n, verse_text).
    Expects chapters as <c n="...">, verses as <v n="...">, tokens as <w>...</w>.
    """
    # Find <tanach> then inside <book>, then chapters/verses.
    in_book = False
    current_chapter: Optional[str] = None

    for elem in root.iter():
        t = strip_ns(elem.tag)

        if t == "book":
            in_book = True
            continue

        if not in_book:
            continue

        if t == "c":
            n = elem.attrib.get("n")
            if n is None:
                continue
            current_chapter = n

        if t == "v":
            if current_chapter is None:
                die("Encountered <v> before any <c n='...'> chapter.")
            verse_n = elem.attrib.get("n")
            if verse_n is None:
                continue

            # Collect all <w> descendants in document order
            tokens = []
            for w in elem.iter():
                if strip_ns(w.tag) == "w":
                    if w.text:
                        tok = w.text.strip()
                        if tok:
                            tokens.append(tok)

            verse_text = " ".join(tokens).strip()
            yield current_chapter, verse_n, verse_text

def main() -> None:
    if len(sys.argv) != 2:
        die('Usage: python wlc_atomize.py "path\\to\\Book.xml"')

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        die(f"Input file not found: {input_path}")

    try:
        tree = ET.parse(str(input_path))
    except ET.ParseError as e:
        die(f"XML parse error: {e}")

    root = tree.getroot()

    book_order, book_id, canonical_book_name = resolve_book_from_xml(root, input_path)

    out_dir = OUT_ROOT / book_id
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    seen = set()

    for chap, verse, text in iter_verses(root):
        c3 = zero3(chap)
        v3 = zero3(verse)

        filename = f"{book_order}_{book_id}_{c3}_{v3}_{SOURCE_ID}.txt"
        out_path = out_dir / filename

        key = (book_id, c3, v3)
        if key in seen:
            die(f"Duplicate verse encountered: {book_id} {c3}:{v3}")
        seen.add(key)

        # Write even if empty, but flag it (rare)
        if text == "":
            # keep deterministic artifact; empty verses should be investigated later
            pass

        # Avoid overwriting existing output
        if out_path.exists():
            die(f"Output file already exists (refusing to overwrite): {out_path}")

        out_path.write_text(text, encoding="utf-8")
        written += 1

    print(f"WLC atomization complete for {canonical_book_name} ({book_id}).")
    print(f"Verses written: {written}")
    print(f"Output dir: {out_dir}")

if __name__ == "__main__":
    main()
