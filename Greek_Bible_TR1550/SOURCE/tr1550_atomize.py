import sys
import re
from pathlib import Path

VERSE_RE = re.compile(r'^(\d+):(\d+)\s+(.+)$')

def atomize_book(path: Path, output_dir: Path):
    verse_count = 0

    # Expected filename format: NNN_BOOK_TR1550.txt
    parts = path.stem.split('_')
    if len(parts) != 3:
        print(f"Skipping malformed filename: {path.name}")
        return 0

    conical = parts[0]     # e.g. 041
    book_code = parts[1]   # e.g. MRK
    version = "TR1550"     # hard-set per your instruction

    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Skip title lines like: [το κατα μαρκον αγιον ευαγγελιον]
            if line.startswith('[') and line.endswith(']'):
                continue

            m = VERSE_RE.match(line)
            if not m:
                continue

            chapter, verse, text = m.groups()

            ccc = f"{int(chapter):03d}"
            vvv = f"{int(verse):03d}"

            output_name = f"{conical}_{book_code}_{ccc}_{vvv}_{version}.txt"
            output_path = output_dir / output_name

            output_path.write_text(text, encoding='utf-8')
            verse_count += 1

    return verse_count


def main(root_dir):
    root = Path(root_dir)

    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        sys.exit(1)

    output_dir = root / "atomized"
    output_dir.mkdir(exist_ok=True)

    total_verses = 0

    print("Book-level atomization counts:")
    print("--------------------------------")

    for txt_file in sorted(root.glob("*.txt")):
        count = atomize_book(txt_file, output_dir)
        total_verses += count
        print(f"{txt_file.name} : {count}")

    print("--------------------------------")
    print(f"TOTAL : {total_verses}")
    print(f"\nAtomized files written to: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: tr1550_atomize.py <Greek_Bible_TR1550_dir>")
        sys.exit(1)

    main(sys.argv[1])