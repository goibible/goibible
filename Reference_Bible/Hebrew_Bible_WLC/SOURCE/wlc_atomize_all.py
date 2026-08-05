#!/usr/bin/env python3
# wlc_atomize_all.py
#
# Usage:
#   python wlc_atomize_all.py "C:\Users\twobl\Downloads\Tanach.xml\Books"
#
# Output:
#   atom/<BOOK_ID>/<001_BOOK_002_003_WLC.txt>
#
# Behavior:
# - Iterates all *.xml in the folder
# - Skips TanachHeader.xml, TanachIndex.xml, *.DH.xml
# - Atomizes verses (<c n>, <v n>, <w>)
# - One file per verse
# - Sanity prints per-book counts + OT total

from __future__ import annotations

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple, Optional

SOURCE_ID = "WLC"
OUT_ROOT = Path("atom")

# 39-book OT map (Protestant order, OSIS IDs)
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

FILENAME_ALIASES = {
    "Samuel_1": "1 Samuel",
    "Samuel_2": "2 Samuel",
    "Kings_1": "1 Kings",
    "Kings_2": "2 Kings",
    "Chronicles_1": "1 Chronicles",
    "Chronicles_2": "2 Chronicles",
    "Song_of_Songs": "Song of Songs",
}

SKIP_FILES = {
    "TanachHeader.xml",
    "TanachIndex.xml",
}

def die(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

def zero3(n: str) -> str:
    return str(int(n)).zfill(3)

def resolve_book(root: ET.Element, path: Path):
    # Try XML name
    for el in root.iter():
        if strip_ns(el.tag) == "name" and el.text:
            name = el.text.strip()
            if name in BOOK_MAP:
                return BOOK_MAP[name], name

    # Fallback filename
    stem = path.stem.replace(".DH", "")
    canonical = FILENAME_ALIASES.get(stem, stem.replace("_", " "))
    if canonical in BOOK_MAP:
        return BOOK_MAP[canonical], canonical

    die(f"Unknown book: {path.name}")

def iter_verses(root: ET.Element):
    chapter = None
    for el in root.iter():
        tag = strip_ns(el.tag)

        if tag == "c":
            chapter = el.attrib.get("n")

        elif tag == "v" and chapter:
            verse = el.attrib.get("n")
            words = []
            for w in el.iter():
                if strip_ns(w.tag) == "w" and w.text:
                    words.append(w.text.strip())
            yield chapter, verse, " ".join(words)

def main():
    if len(sys.argv) != 2:
        die("Usage: python wlc_atomize_all.py <BooksFolder>")

    books_dir = Path(sys.argv[1])
    if not books_dir.is_dir():
        die("Input must be a directory")

    totals = {}
    grand_total = 0

    for xml_file in sorted(books_dir.glob("*.xml")):
        if xml_file.name in SKIP_FILES:
            continue
        if xml_file.name.endswith(".DH.xml"):
            continue

        tree = ET.parse(xml_file)
        root = tree.getroot()

        (book_order, book_id), book_name = resolve_book(root, xml_file)
        out_dir = OUT_ROOT / book_id
        out_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        seen = set()

        for chap, verse, text in iter_verses(root):
            c3, v3 = zero3(chap), zero3(verse)
            key = (book_id, c3, v3)
            if key in seen:
                die(f"Duplicate verse {book_id} {c3}:{v3}")
            seen.add(key)

            fname = f"{book_order}_{book_id}_{c3}_{v3}_{SOURCE_ID}.txt"
            (out_dir / fname).write_text(text, encoding="utf-8")
            count += 1

        totals[book_id] = count
        grand_total += count
        print(f"{book_id}: {count}")

    print("-" * 30)
    print(f"TOTAL OT VERSES: {grand_total}")

if __name__ == "__main__":
    main()
