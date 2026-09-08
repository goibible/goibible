#!/usr/bin/env python3
"""Build a Kindle-ready EPUB3 for a completed GOI Bible edition.

Reads the flat verse files under GOI_Bible/GOI_Bible_<lang>/ (one .txt per
verse, named <NNN>_<BOOK>_<CCC>_<VVV>_<suffix>.txt), groups them into
book/chapter XHTML, and zips a standard EPUB3 package. Amazon's own
tooling (Kindle Previewer / Send-to-Kindle / KDP) accepts EPUB directly
and converts it to KFX for the device -- no separate MOBI step needed.

Usage:
  python3 tools/build_epub.py                 # build every completed edition
  python3 tools/build_epub.py GOI_En GOI_Es    # build just these
"""
from __future__ import annotations

import argparse
import html
import re
import sqlite3
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_DB = ROOT / "Meta_Bible_Data" / "sqlite" / "goi_bible_shell.db"
OUT_DIR = ROOT / "epub"

# edition_id -> (flatfile dir name under GOI_Bible/, filename suffix, display title)
EDITIONS = {
    "GOI_En":      ("GOI_Bible_English",        "GOI_En",      "GOI Bible - English"),
    "GOI_Es":      ("GOI_Bible_es",              "GOI_Es",      "GOI Bible - Español"),
    "GOI_Zh_Hant": ("GOI_Bible_Chinese_Hant",     "GOI_Zh_Hant", "GOI Bible - 繁體中文"),
    "GOI_Zh_Hans": ("GOI_Bible_Chinese_Hans",     "GOI_Zh_Hans", "GOI Bible - 简体中文"),
    "GOI_vi":      ("GOI_Bible_vi",               "GOI_vi",      "GOI Bible - Tiếng Việt"),
    "GOI_Pt":      ("GOI_Bible_pt",               "GOI_Pt",      "GOI Bible - Português"),
}

LANG_TAG = {
    "GOI_En": "en", "GOI_Es": "es", "GOI_Zh_Hant": "zh-Hant",
    "GOI_Zh_Hans": "zh-Hans", "GOI_vi": "vi", "GOI_Pt": "pt",
}

FNAME_RE = re.compile(r"^(\d{3})_([0-9A-Z]+)_(\d{3})_(\d{3})_.+\.txt$")


def load_books() -> list[tuple[int, str, str, str]]:
    conn = sqlite3.connect(SHELL_DB)
    rows = conn.execute(
        "SELECT conical, osis, long_name, testament FROM books ORDER BY conical"
    ).fetchall()
    conn.close()
    return rows


def load_verses(flat_dir: Path) -> dict[str, dict[int, dict[int, str]]]:
    """book_osis -> chapter -> verse -> text"""
    data: dict[str, dict[int, dict[int, str]]] = {}
    for f in flat_dir.iterdir():
        m = FNAME_RE.match(f.name)
        if not m:
            continue
        _, book, ch, vs = m.groups()
        text = f.read_text(encoding="utf-8").strip()
        data.setdefault(book, {}).setdefault(int(ch), {})[int(vs)] = text
    return data


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def build_book_xhtml(osis: str, long_name: str, chapters: dict[int, dict[int, str]]) -> str:
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml">',
        "<head>",
        f"<title>{esc(long_name)}</title>",
        '<link rel="stylesheet" type="text/css" href="../styles.css"/>',
        "</head>",
        "<body>",
        f'<h1 id="{osis}">{esc(long_name)}</h1>',
    ]
    for ch_num in sorted(chapters):
        parts.append(f'<h2 id="{osis}_{ch_num}">{esc(long_name)} {ch_num}</h2>')
        verses = chapters[ch_num]
        for vs_num in sorted(verses):
            text = esc(verses[vs_num])
            parts.append(
                f'<p><sup class="vnum">{vs_num}</sup> {text}</p>'
            )
    parts += ["</body>", "</html>"]
    return "\n".join(parts)


def build_nav_xhtml(books: list[tuple[int, str, str, str]]) -> str:
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">',
        "<head><title>Table of Contents</title></head>",
        "<body>",
        '<nav epub:type="toc" id="toc">',
        "<h1>Table of Contents</h1>",
        "<ol>",
    ]
    for conical, osis, long_name, _testament in books:
        parts.append(
            f'<li><a href="text/{conical:03d}_{osis}.xhtml">{esc(long_name)}</a></li>'
        )
    parts += ["</ol>", "</nav>", "</body>", "</html>"]
    return "\n".join(parts)


def build_ncx(books: list[tuple[int, str, str, str]], uid: str) -> str:
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
        "<head>",
        f'<meta name="dtb:uid" content="{uid}"/>',
        "</head>",
        f"<docTitle><text>{esc(uid)}</text></docTitle>",
        "<navMap>",
    ]
    for i, (conical, osis, long_name, _t) in enumerate(books, start=1):
        parts.append(
            f'<navPoint id="np{i}" playOrder="{i}">'
            f"<navLabel><text>{esc(long_name)}</text></navLabel>"
            f'<content src="text/{conical:03d}_{osis}.xhtml"/></navPoint>'
        )
    parts += ["</navMap>", "</ncx>"]
    return "\n".join(parts)


def build_opf(edition_id: str, title: str, lang_tag: str,
              books: list[tuple[int, str, str, str]]) -> str:
    manifest_items = []
    spine_items = []
    for conical, osis, _long_name, _t in books:
        item_id = f"book{conical:03d}"
        manifest_items.append(
            f'<item id="{item_id}" href="text/{conical:03d}_{osis}.xhtml" '
            f'media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{item_id}"/>')

    return "\n".join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        f'unique-identifier="bookid" xml:lang="{lang_tag}">',
        "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\">",
        f'<dc:identifier id="bookid">urn:goi-bible:{edition_id}</dc:identifier>',
        f"<dc:title>{esc(title)}</dc:title>",
        f"<dc:language>{lang_tag}</dc:language>",
        "<dc:creator>GOI Bible Project</dc:creator>",
        '<meta property="dcterms:modified">2026-09-08T00:00:00Z</meta>',
        "</metadata>",
        "<manifest>",
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="styles.css" media-type="text/css"/>',
        "\n".join(manifest_items),
        "</manifest>",
        '<spine toc="ncx">',
        "\n".join(spine_items),
        "</spine>",
        "</package>",
    ])


STYLES_CSS = """
body { font-family: serif; margin: 1em; }
h1 { font-size: 1.6em; page-break-before: always; }
h2 { font-size: 1.2em; margin-top: 1.2em; }
p { margin: 0 0 0.3em 0; text-indent: 0; line-height: 1.4; }
sup.vnum { font-size: 0.7em; color: #666; margin-right: 0.3em; }
"""


def build_epub(edition_id: str) -> Path:
    flat_dirname, suffix, title = EDITIONS[edition_id]
    lang_tag = LANG_TAG[edition_id]
    flat_dir = ROOT / "GOI_Bible" / flat_dirname
    if not flat_dir.is_dir():
        raise SystemExit(f"{edition_id}: flatfile dir not found: {flat_dir}")

    books = load_books()
    verses = load_verses(flat_dir)

    missing = [osis for _c, osis, _n, _t in books if osis not in verses]
    if missing:
        raise SystemExit(f"{edition_id}: missing books in flatfiles: {missing}")

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / f"{edition_id}.epub"
    if out_path.exists():
        out_path.unlink()

    with zipfile.ZipFile(out_path, "w") as z:
        # mimetype must be first entry, stored (uncompressed)
        z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            "<rootfiles>\n"
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            "</rootfiles>\n"
            "</container>\n",
            zipfile.ZIP_DEFLATED,
        )
        z.writestr("OEBPS/styles.css", STYLES_CSS, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", build_nav_xhtml(books), zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", build_ncx(books, edition_id), zipfile.ZIP_DEFLATED)
        z.writestr(
            "OEBPS/content.opf",
            build_opf(edition_id, title, lang_tag, books),
            zipfile.ZIP_DEFLATED,
        )
        for conical, osis, long_name, _t in books:
            xhtml = build_book_xhtml(osis, long_name, verses[osis])
            z.writestr(f"OEBPS/text/{conical:03d}_{osis}.xhtml", xhtml, zipfile.ZIP_DEFLATED)

    verse_count = sum(len(vv) for cc in verses.values() for vv in cc.values())
    print(f"{edition_id}: wrote {out_path.relative_to(ROOT)} "
          f"({len(books)} books, {verse_count} verses)")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("editions", nargs="*", help="edition ids to build (default: all)")
    args = ap.parse_args()
    targets = args.editions or list(EDITIONS)
    for edition_id in targets:
        if edition_id not in EDITIONS:
            raise SystemExit(f"unknown edition: {edition_id} (known: {list(EDITIONS)})")
        build_epub(edition_id)


if __name__ == "__main__":
    main()
