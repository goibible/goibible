import os
import re
import sys

# =========================
# CONFIGURATION
# =========================

INPUT_FILE = "kjv_cambridge_clean.txt"   # your cleaned Cambridge KJV file
OUTPUT_ROOT = "atoms/KJV"
VERSION = "KJV"

# =========================
# CANONICAL BOOK MAP (66)
# =========================

BOOK_MAP = {
    # Old Testament
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
    "Psalm": ("019", "PSA"),
    "Psalms": ("019", "PSA"),
    "Proverbs": ("020", "PRO"),
    "Ecclesiastes": ("021", "ECC"),
    "Song of Solomon": ("022", "SNG"),
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

    # New Testament
    "Matthew": ("040", "MAT"),
    "Mark": ("041", "MRK"),
    "Luke": ("042", "LUK"),
    "John": ("043", "JHN"),
    "Acts": ("044", "ACT"),
    "Romans": ("045", "ROM"),
    "1 Corinthians": ("046", "1CO"),
    "2 Corinthians": ("047", "2CO"),
    "Galatians": ("048", "GAL"),
    "Ephesians": ("049", "EPH"),
    "Philippians": ("050", "PHP"),
    "Colossians": ("051", "COL"),
    "1 Thessalonians": ("052", "1TH"),
    "2 Thessalonians": ("053", "2TH"),
    "1 Timothy": ("054", "1TI"),
    "2 Timothy": ("055", "2TI"),
    "Titus": ("056", "TIT"),
    "Philemon": ("057", "PLM"),
    "Hebrews": ("058", "HEB"),
    "James": ("059", "JAS"),
    "1 Peter": ("060", "1PE"),
    "2 Peter": ("061", "2PE"),
    "1 John": ("062", "1JN"),
    "2 John": ("063", "2JN"),
    "3 John": ("064", "3JN"),
    "Jude": ("065", "JUD"),
    "Revelation": ("066", "REV"),
}

# =========================
# REGEX (STRICT)
# =========================

LINE_RE = re.compile(
    r'^([1-3]?\s?[A-Za-z ]+)\s+(\d+):(\d+)\s+(.*)$'
)

# =========================
# MAIN
# =========================

def die(msg):
    print("ERROR:", msg)
    sys.exit(1)

def main():
    if not os.path.isfile(INPUT_FILE):
        die(f"Input file not found: {INPUT_FILE}")

    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    total_written = 0

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue

            m = LINE_RE.match(line)
            if not m:
                die(f"Unparseable line at {lineno}: {line}")

            book_name, chapter, verse, text = m.groups()
            book_name = book_name.strip()

            if book_name not in BOOK_MAP:
                die(f"Unknown book '{book_name}' at line {lineno}")

            book_order, book_id = BOOK_MAP[book_name]

            out_dir = os.path.join(OUTPUT_ROOT, book_id)
            os.makedirs(out_dir, exist_ok=True)

            filename = (
                f"{book_order}_{book_id}_"
                f"{chapter.zfill(3)}_{verse.zfill(3)}_{VERSION}.txt"
            )

            out_path = os.path.join(out_dir, filename)

            if os.path.exists(out_path):
                die(f"Duplicate verse detected: {out_path}")

            with open(out_path, "w", encoding="utf-8") as out:
                out.write(text.strip())

            total_written += 1

    print(f"KJV atomization complete.")
    print(f"Total verses written: {total_written}")

if __name__ == "__main__":
    main()