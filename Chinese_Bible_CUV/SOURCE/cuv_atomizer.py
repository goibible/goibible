import os
import re
import html

INPUT_DIR = r"T:\CUV Chinese Bible\cuv_html"
OUTPUT_ROOT = r"T:\CUV Chinese Bible\atoms"
VERSION = "CUV"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

for fname in sorted(os.listdir(INPUT_DIR)):
    if not fname.lower().endswith(".htm"):
        continue

    m = re.match(r"(\d{3})_([A-Z0-9]{3})\.htm$", fname)
    if not m:
        continue

    book_order, book_id = m.groups()

    input_path = os.path.join(INPUT_DIR, fname)
    book_out_dir = os.path.join(OUTPUT_ROOT, VERSION, book_id)
    os.makedirs(book_out_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # 🔑 Anchor-first extraction
    matches = re.findall(
        r'<A NAME="an_(\d+):(\d+)">\d+:\d+</A>(.*?)</p>',
        raw,
        flags=re.S | re.I
    )

    print(fname, "verses found:", len(matches))  # DEBUG LINE

    for chapter, verse, tail in matches:
        # remove &nbsp;
        tail = tail.replace('&nbsp;', '').strip()

        # decode HTML entities
        text = html.unescape(tail).strip()

        if not text:
            continue

        out_name = (
            f"{book_order}_{book_id}_"
            f"{chapter.zfill(3)}_{verse.zfill(3)}_{VERSION}.txt"
        )

        out_path = os.path.join(book_out_dir, out_name)

        with open(out_path, "w", encoding="utf-8") as out:
            out.write(text)