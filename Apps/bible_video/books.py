"""Canonical GOI English Bible book metadata and unix-friendly naming.

Book numbers and canonical order come from the GOI English data itself
(GOI_Bible/GOI_Bible_English/001_GEN_* ... 066_REV_*). Full English names are the
standard Protestant-canon names, capitalized. Whole-Bible naming conventions:

  book folder : <nnn>_<Name>        e.g. 020_Proverbs, 022_Song_of_Solomon
  chapter file: <ccc>_<Name>.mp4    e.g. 001_Proverbs.mp4, 031_Proverbs.mp4

Name capitalization (title-case words joined by underscores) is applied here so
every output path is unix-friendly (no spaces).
"""

from __future__ import annotations

from pathlib import Path

# OSIS code -> canonical, capitalized long name (Protestant 66-book order).
BOOK_NAMES: dict[str, str] = {
    "GEN": "Genesis",
    "EXO": "Exodus",
    "LEV": "Leviticus",
    "NUM": "Numbers",
    "DEU": "Deuteronomy",
    "JOS": "Joshua",
    "JDG": "Judges",
    "RUT": "Ruth",
    "1SA": "1_Samuel",
    "2SA": "2_Samuel",
    "1KI": "1_Kings",
    "2KI": "2_Kings",
    "1CH": "1_Chronicles",
    "2CH": "2_Chronicles",
    "EZR": "Ezra",
    "NEH": "Nehemiah",
    "EST": "Esther",
    "JOB": "Job",
    "PSA": "Psalms",
    "PRO": "Proverbs",
    "ECC": "Ecclesiastes",
    "SNG": "Song_of_Solomon",
    "ISA": "Isaiah",
    "JER": "Jeremiah",
    "LAM": "Lamentations",
    "EZK": "Ezekiel",
    "DAN": "Daniel",
    "HOS": "Hosea",
    "JOL": "Joel",
    "AMO": "Amos",
    "OBA": "Obadiah",
    "JON": "Jonah",
    "MIC": "Micah",
    "NAM": "Nahum",
    "HAB": "Habakkuk",
    "ZEP": "Zephaniah",
    "HAG": "Haggai",
    "ZEC": "Zechariah",
    "MAL": "Malachi",
    "MAT": "Matthew",
    "MRK": "Mark",
    "LUK": "Luke",
    "JHN": "John",
    "ACT": "Acts",
    "ROM": "Romans",
    "1CO": "1_Corinthians",
    "2CO": "2_Corinthians",
    "GAL": "Galatians",
    "EPH": "Ephesians",
    "PHP": "Philippians",
    "COL": "Colossians",
    "1TH": "1_Thessalonians",
    "2TH": "2_Thessalonians",
    "1TI": "1_Timothy",
    "2TI": "2_Timothy",
    "TIT": "Titus",
    "PHM": "Philemon",
    "HEB": "Hebrews",
    "JAS": "James",
    "1PE": "1_Peter",
    "2PE": "2_Peter",
    "1JN": "1_John",
    "2JN": "2_John",
    "3JN": "3_John",
    "JUD": "Jude",
    "REV": "Revelation",
}

# Ordered list of (number, osis) in canonical order — authoritative order.
BOOK_ORDER: list[tuple[int, str]] = [
    (1, "GEN"), (2, "EXO"), (3, "LEV"), (4, "NUM"), (5, "DEU"),
    (6, "JOS"), (7, "JDG"), (8, "RUT"), (9, "1SA"), (10, "2SA"),
    (11, "1KI"), (12, "2KI"), (13, "1CH"), (14, "2CH"), (15, "EZR"),
    (16, "NEH"), (17, "EST"), (18, "JOB"), (19, "PSA"), (20, "PRO"),
    (21, "ECC"), (22, "SNG"), (23, "ISA"), (24, "JER"), (25, "LAM"),
    (26, "EZK"), (27, "DAN"), (28, "HOS"), (29, "JOL"), (30, "AMO"),
    (31, "OBA"), (32, "JON"), (33, "MIC"), (34, "NAM"), (35, "HAB"),
    (36, "ZEP"), (37, "HAG"), (38, "ZEC"), (39, "MAL"),
    (40, "MAT"), (41, "MRK"), (42, "LUK"), (43, "JHN"), (44, "ACT"),
    (45, "ROM"), (46, "1CO"), (47, "2CO"), (48, "GAL"), (49, "EPH"),
    (50, "PHP"), (51, "COL"), (52, "1TH"), (53, "2TH"), (54, "1TI"),
    (55, "2TI"), (56, "TIT"), (57, "PHM"), (58, "HEB"), (59, "JAS"),
    (60, "1PE"), (61, "2PE"), (62, "1JN"), (63, "2JN"), (64, "3JN"),
    (65, "JUD"), (66, "REV"),
]

_NUM_BY_OSIS = {osis: n for n, osis in BOOK_ORDER}
_OSIS_BY_NUM = {n: osis for n, osis in BOOK_ORDER}


def _alias_key(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _build_book_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    ordinal_words = {"1": "first", "2": "second", "3": "third"}
    for number, osis in BOOK_ORDER:
        name = BOOK_NAMES[osis]
        display = name.replace("_", " ")
        raw_aliases = {
            osis,
            osis.lower(),
            str(number),
            f"{number:02d}",
            f"{number:03d}",
            name,
            display,
            name.replace("_", ""),
            display.replace(" ", ""),
        }
        if name[0].isdigit() and "_" in name:
            digit, rest = name.split("_", 1)
            word = ordinal_words.get(digit)
            if word:
                rest_display = rest.replace("_", " ")
                raw_aliases.update({
                    f"{digit} {rest_display}",
                    f"{digit}{rest_display}",
                    f"{word} {rest_display}",
                    f"{word}{rest_display}",
                })
        for alias in raw_aliases:
            aliases[_alias_key(alias)] = osis
    return aliases


_BOOK_ALIASES = _build_book_aliases()


def resolve_book(value: str) -> str:
    """Resolve OSIS, book name, or book number to a canonical OSIS code."""
    key = _alias_key(value.strip())
    if key in _BOOK_ALIASES:
        return _BOOK_ALIASES[key]
    raise SystemExit(f"Unknown book '{value}'. Use a book name, number, or OSIS code, e.g. Genesis, 01, GEN, Jude, JUD.")


def number_of(osis: str) -> int:
    return _NUM_BY_OSIS[osis]


def name_of(osis: str) -> str:
    return BOOK_NAMES[osis]


def display_name_of(osis: str) -> str:
    """Human heading for a book (name with spaces, e.g. 'Song of Solomon')."""
    return BOOK_NAMES[osis].replace("_", " ")


def book_dir_name(osis: str) -> str:
    """<nnn>_<Name>, e.g. 020_Proverbs."""
    return f"{number_of(osis):03d}_{name_of(osis)}"


def chapter_file_name(osis: str, chapter: int) -> str:
    """<ccc>_<Name>.mp4, e.g. 031_Proverbs.mp4."""
    return f"{chapter:03d}_{name_of(osis)}.mp4"


def chapters_for(osis: str, verse_dir: Path) -> list[int]:
    """Sorted chapter numbers present for a book, derived from GOI verse files."""
    nnn = number_of(osis)
    seen: set[int] = set()
    for path in verse_dir.glob(f"{nnn:03d}_{osis}_*_GOI_En.txt"):
        parts = path.name.split("_")
        if len(parts) >= 4 and parts[2].isdigit():
            seen.add(int(parts[2]))
    if not seen:
        raise FileNotFoundError(f"No GOI English verses found for {osis}")
    return sorted(seen)


def cross_check(verse_dir: Path) -> None:
    """Fail fast if the GOI verse prefixes disagree with our ordered map."""
    codes_found = set()
    for p in verse_dir.glob("*_GOI_En.txt"):
        part = p.name.split("_")
        if len(part) >= 3:
            codes_found.add(part[1])
    expected = {osis for _, osis in BOOK_ORDER}
    missing = expected - codes_found
    extra = codes_found - expected
    if missing:
        raise SystemExit(f"books.py: missing GOI book code(s) not in map: {sorted(missing)}")
    if extra:
        raise SystemExit(f"books.py: GOI code(s) not in ordered map: {sorted(extra)}")
