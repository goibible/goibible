#!/usr/bin/env python3
"""Apply narrow divine/common-noun sense fixes from the remaining scrub queue."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EN_DIR = ROOT / "GOI_Bible" / "GOI_Bible_English"


BOOK_NUM = {
    "GEN": "001", "EXO": "002", "LEV": "003", "NUM": "004", "DEU": "005",
    "JOS": "006", "JDG": "007", "RUT": "008", "1SA": "009", "2SA": "010",
    "1KI": "011", "2KI": "012", "1CH": "013", "2CH": "014", "EZR": "015",
    "NEH": "016", "EST": "017", "JOB": "018", "PSA": "019", "PRO": "020",
    "ECC": "021", "SNG": "022", "ISA": "023", "JER": "024", "LAM": "025",
    "EZK": "026", "DAN": "027", "HOS": "028", "JOL": "029", "AMO": "030",
    "OBA": "031", "JON": "032", "MIC": "033", "NAM": "034", "HAB": "035",
    "ZEP": "036", "HAG": "037", "ZEC": "038", "MAL": "039",
}


FIXES = {
    ("GEN", 31, 30): ("why have you stolen my god?", "why have you stolen my gods?"),
    ("EXO", 22, 20): ("Whoever sacrifices to the gods", "Whoever sacrifices to a god"),
    ("NUM", 23, 27): ("pleasing in the sight of the gods", "pleasing in the sight of God"),
    ("DEU", 4, 33): ("voice of gods speaking", "voice of God speaking"),
    ("JDG", 5, 8): ("God chose new rulers", "They chose new gods"),
    ("JDG", 9, 27): ("the temple of their gods", "the temple of their god"),
    ("JDG", 16, 24): ("praised their God", "praised their god"),
    ("JDG", 16, 24, "second"): ("Our God has delivered", "Our god has delivered"),
    ("2KI", 1, 2): ("the gods of Ekron", "the god of Ekron"),
    ("2KI", 17, 29): ("made its own god", "made its own gods"),
    ("2KI", 19, 37): ("Nisroch his gods", "Nisroch his god"),
    ("1CH", 5, 22): ("the battle is from the angels", "the battle is from God"),
    ("1CH", 10, 10): ("the temple of their god", "the temple of their gods"),
    ("2CH", 13, 12): ("the chief of the gods", "the chief God"),
    ("NEH", 13, 26): ("he was loved by his gods", "he was loved by his God"),
    ("JOB", 1, 6): ("sons of the gods", "sons of God"),
    ("JOB", 1, 16): ("A fiery divine fire fell", "The fire of God fell"),
    ("JOB", 2, 1): ("sons of the gods", "sons of God"),
    ("ISA", 8, 21): ("curse his king and his gods", "curse his king and his God"),
    ("HOS", 4, 12): ("beneath their gods", "beneath their God"),
    ("JON", 1, 5): ("each cried out to his gods", "each cried out to his god"),
    ("1SA", 28, 13): ("I have seen God coming up", "I have seen gods coming up"),
    ("AMO", 2, 8): ("in the temple of their gods", "in the temple of their god"),
}


def path_for(book: str, chapter: int, verse: int) -> Path:
    return EN_DIR / f"{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}_GOI_En.txt"


def main() -> None:
    changed = []
    for key, (old, new) in FIXES.items():
        book, chapter, verse = key[:3]
        path = path_for(book, chapter, verse)
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise RuntimeError(f"{path}: missing expected text {old!r}")
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
        changed.append(path.name)
    print(f"changed {len(changed)} divine-sense verse files")
    for name in changed:
        print(name)


if __name__ == "__main__":
    main()
