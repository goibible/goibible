#!/usr/bin/env python3
"""Atomize Project Gutenberg #62383 Almeida 1911 into one verse per file.

The Gutenberg text prints verse 1 of each chapter with the chapter number
instead of the verse number, e.g. Genesis 2:1 starts with "2 Assim...".
Expected chapter/verse counts are derived from the KJV directory so the output
can be checked directly against the GOI spine.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE = ROOT / "SOURCE" / "gutenberg_62383_almeida1911.txt"
OUT_DIR = ROOT / "One_Directory_Almeida1911"
KJV_DIR = REPO / "Reference_Bible" / "English_Bible_KJV" / "One_Directory_KJV"

BOOKS = [
    ("001", "GEN", "O PRIMEIRO LIVRO DE MOYSÉS CHAMADO GENESIS."),
    ("002", "EXO", "O SEGUNDO LIVRO DE MOYSÉS CHAMADO EXODO."),
    ("003", "LEV", "O TERCEIRO LIVRO DE MOYSÉS CHAMADO LEVITICO."),
    ("004", "NUM", "O QUARTO LIVRO DE MOYSÉS CHAMADO NUMEROS."),
    ("005", "DEU", "O QUINTO LIVRO DE MOYSÉS CHAMADO DEUTERONOMIO."),
    ("006", "JOS", "O LIVRO DE JOSUÉ."),
    ("007", "JDG", "O LIVRO DOS JUIZES."),
    ("008", "RUT", "O LIVRO DE RUTH."),
    ("009", "1SA", "O PRIMEIRO LIVRO DE SAMUEL."),
    ("010", "2SA", "O SEGUNDO LIVRO DE SAMUEL."),
    ("011", "1KI", "O PRIMEIRO LIVRO DOS REIS."),
    ("012", "2KI", "O SEGUNDO LIVRO DOS REIS."),
    ("013", "1CH", "O PRIMEIRO LIVRO DAS CHRONICAS."),
    ("014", "2CH", "O SEGUNDO LIVRO DAS CHRONICAS."),
    ("015", "EZR", "O LIVRO DE ESDRAS."),
    ("016", "NEH", "O LIVRO DE NEHEMIAS."),
    ("017", "EST", "O LIVRO DE ESTHER."),
    ("018", "JOB", "[MT] O LIVRO DE JOB."),
    ("019", "PSA", "O LIVRO DOS PSALMOS."),
    ("020", "PRO", "PROVERBIOS DE SALOMÃO."),
    ("021", "ECC", "LIVRO DO ECCLESIASTES, OU PRÉGADOR."),
    ("022", "SNG", "CANTARES DE SALOMÃO."),
    ("023", "ISA", "ISAIAS."),
    ("024", "JER", "JEREMIAS."),
    ("025", "LAM", "LAMENTAÇÕES DE JEREMIAS."),
    ("026", "EZK", "EZEQUIEL."),
    ("027", "DAN", "DANIEL."),
    ("028", "HOS", "OSEAS."),
    ("029", "JOL", "JOEL."),
    ("030", "AMO", "AMÓS."),
    ("031", "OBA", "OBADIAS."),
    ("032", "JON", "JONAS."),
    ("033", "MIC", "MIQUEAS."),
    ("034", "NAM", "NAHUM."),
    ("035", "HAB", "HABACUC."),
    ("036", "ZEP", "SOFONIAS."),
    ("037", "HAG", "AGGEO."),
    ("038", "ZEC", "ZACHARIAS."),
    ("039", "MAL", "MALACHIAS."),
    ("040", "MAT", "O SANCTO EVANGELHO SEGUNDO S. MATTHEUS."),
    ("041", "MRK", "O SANCTO EVANGELHO SEGUNDO S. MARCOS."),
    ("042", "LUK", "O SANCTO EVANGELHO SEGUNDO S. LUCAS."),
    ("043", "JHN", "O SANCTO EVANGELHO SEGUNDO S. JOÃO."),
    ("044", "ACT", "ACTOS DOS APOSTOLOS."),
    ("045", "ROM", "EPISTOLA DE S. PAULO AOS ROMANOS."),
    ("046", "1CO", "PRIMEIRA EPISTOLA DE S. PAULO APOSTOLO AOS CORINTHIOS."),
    ("047", "2CO", "SEGUNDA EPISTOLA DE S. PAULO APOSTOLO AOS CORINTHIOS."),
    ("048", "GAL", "EPISTOLA DE S. PAULO APOSTOLO AOS GALATAS."),
    ("049", "EPH", "EPISTOLA DE S. PAULO APOSTOLO AOS EPHESIOS."),
    ("050", "PHP", "EPISTOLA DE S. PAULO APOSTOLO AOS PHILIPPENSES."),
    ("051", "COL", "EPISTOLA DE S. PAULO APOSTOLO AOS COLOSSENSES."),
    ("052", "1TH", "PRIMEIRA EPISTOLA DE S. PAULO APOSTOLO AOS THESSALONICENSES."),
    ("053", "2TH", "SEGUNDA EPISTOLA DE S. PAULO APOSTOLO AOS THESSALONICENSES."),
    ("054", "1TI", "PRIMEIRA EPISTOLA DE S. PAULO APOSTOLO A TIMOTHEO."),
    ("055", "2TI", "SEGUNDA EPISTOLA DE S. PAULO APOSTOLO A TIMOTHEO."),
    ("056", "TIT", "EPISTOLA DE S. PAULO APOSTOLO A TITO."),
    ("057", "PHM", "EPISTOLA DE S. PAULO APOSTOLO A PHILEMON."),
    ("058", "HEB", "EPISTOLA DE S. PAULO APOSTOLO AOS HEBREOS."),
    ("059", "JAS", "EPISTOLA UNIVERSAL DO APOSTOLO S. THIAGO."),
    ("060", "1PE", "PRIMEIRA EPISTOLA UNIVERSAL DO APOSTOLO S. PEDRO."),
    ("061", "2PE", "SEGUNDA EPISTOLA UNIVERSAL DO APOSTOLO S. PEDRO."),
    ("062", "1JN", "PRIMEIRA EPISTOLA UNIVERSAL DO APOSTOLO S. JOÃO."),
    ("063", "2JN", "SEGUNDA EPISTOLA DO APOSTOLO S. JOÃO."),
    ("064", "3JN", "TERCEIRA EPISTOLA DO APOSTOLO S. JOÃO."),
    ("065", "JUD", "EPISTOLA UNIVERSAL DO APOSTOLO S. JUDAS."),
    ("066", "REV", "APOCALYPSE DO APOSTOLO S. JOÃO."),
]

INLINE_REF = re.compile(r"\[[A-Z0-9]+\]")
SPACES = re.compile(r"\s+")
INLINE_VERSE_START = re.compile(r"(?<=[.!?:;])\s+(\d{1,3})\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ_])")
CROSS_REF_HEADING = re.compile(r"^(?:[1I]{0,3}\s*)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç. ]+\.\s+\d")
MARKER_OVERRIDES = {
    ("MRK", 4, 34): "31",
}
ACROSTIC_WORDS = (
    "ALEPH",
    "BETH",
    "GIMEL",
    "DALETH",
    "HE",
    "VAU",
    "ZAIN",
    "HETH",
    "TETH",
    "JOD",
    "CAPH",
    "LAMED",
    "MEM",
    "NUN",
    "SAMECH",
    "AIN",
    "PE",
    "TSADE",
    "COPH",
    "KOPH",
    "RESCH",
    "SCHIN",
    "TAU",
)
ACROSTIC_PREFIX = r"(?:(?:" + "|".join(ACROSTIC_WORDS) + r")\.?\s+)?"
MARKER_PREFIX = ACROSTIC_PREFIX + r"(?:\[[A-Z0-9]+\]\s+)*"


def kjv_counts() -> dict[tuple[str, int], int]:
    counts: dict[tuple[str, int], int] = {}
    for path in KJV_DIR.glob("*_KJV.txt"):
        canon, book, chap_s, verse_s, _suffix = path.stem.split("_")
        key = (book, int(chap_s))
        counts[key] = max(counts.get(key, 0), int(verse_s))
    return counts


def native_counts() -> dict[tuple[str, int], int]:
    counts = kjv_counts()
    adjustments = {
        ("JON", 1): 16,
        ("NUM", 12): 15,
        ("NUM", 29): 39,
        ("1SA", 23): 28,
        ("2SA", 20): 25,
        ("2CH", 33): 24,
        ("ACT", 19): 40,
        ("2CO", 13): 13,
    }
    counts.update(adjustments)
    return counts


def prepare_lines(text: str) -> list[str]:
    prepared: list[str] = []
    for line in text.splitlines():
        prepared.extend(INLINE_VERSE_START.sub(r"\n\1 ", line).splitlines())
    return prepared


def clean_text(lines: list[str]) -> str:
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("_") and stripped.endswith("_"):
            continue
        if stripped.startswith("[Antes de Christo"):
            continue
        if len(stripped) < 90 and CROSS_REF_HEADING.match(stripped):
            continue
        stripped = INLINE_REF.sub("", stripped)
        stripped = stripped.replace("_", "")
        kept.append(stripped)
    return SPACES.sub(" ", " ".join(kept)).strip()


def marker_for(book: str, chapter: int, verse: int) -> str:
    return MARKER_OVERRIDES.get((book, chapter, verse), str(chapter if verse == 1 else verse))


def is_marker(line: str, marker: str) -> bool:
    return bool(re.match(rf"^{MARKER_PREFIX}{re.escape(marker)}\s+\S", line))


def is_note_start(line: str) -> bool:
    return bool(re.match(r"^\[[A-Z0-9]+\]\s+", line.strip()))


def find_marker(lines: list[str], start: int, marker: str, end: int) -> int:
    for idx in range(start, end):
        if is_marker(lines[idx].strip(), marker):
            return idx
    raise ValueError(f"could not find marker {marker!r} after line {start}")


def collect_verse(lines: list[str], start: int, next_marker: str | None) -> tuple[str, int]:
    first = lines[start].strip()
    text_lines = [re.sub(rf"^{MARKER_PREFIX}\d+\s+", "", first, count=1)]
    idx = start + 1
    while idx < len(lines):
        stripped = lines[idx].strip()
        if next_marker and is_marker(stripped, next_marker):
            break
        if is_note_start(stripped):
            break
        text_lines.append(stripped)
        idx += 1
    return clean_text(text_lines), idx


def atomize(clean: bool = False) -> int:
    lines = prepare_lines(SOURCE.read_text(encoding="utf-8-sig"))
    book_starts: dict[str, int] = {}
    for _canon, book, heading in BOOKS:
        try:
            book_starts[book] = next(i for i, line in enumerate(lines) if line.strip() == heading)
        except StopIteration as exc:
            raise RuntimeError(f"{book}: heading not found: {heading}") from exc

    counts = native_counts()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if clean:
        for old in OUT_DIR.glob("*_Almeida1911.txt"):
            old.unlink()

    written = 0
    for book_index, (canon, book, _heading) in enumerate(BOOKS):
        cursor = book_starts[book]
        if book_index + 1 < len(BOOKS):
            end = book_starts[BOOKS[book_index + 1][1]]
        else:
            end = len(lines)
        chapters = sorted(chapter for b, chapter in counts if b == book)
        if not chapters:
            raise RuntimeError(f"no KJV counts found for {book}")
        for chapter in chapters:
            max_verse = counts[(book, chapter)]
            for verse in range(1, max_verse + 1):
                marker = marker_for(book, chapter, verse)
                if verse < max_verse:
                    next_marker = marker_for(book, chapter, verse + 1)
                elif chapter < chapters[-1]:
                    next_marker = marker_for(book, chapter + 1, 1)
                else:
                    next_marker = None
                try:
                    verse_start = find_marker(lines, cursor, marker, end)
                    text, cursor = collect_verse(lines, verse_start, next_marker)
                except ValueError as exc:
                    raise RuntimeError(f"{book} {chapter}:{verse}: {exc}") from exc
                if not text:
                    raise RuntimeError(f"{book} {chapter}:{verse}: empty parsed verse")
                out = OUT_DIR / f"{canon}_{book}_{chapter:03d}_{verse:03d}_Almeida1911.txt"
                out.write_text(text + "\n", encoding="utf-8")
                written += 1
        print(f"{book}: {sum(counts[(book, chapter)] for chapter in chapters)}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    total = atomize(clean=args.clean)
    expected = sum(native_counts().values())
    print(f"TOTAL: {total}")
    if total != expected:
        print(f"expected {expected}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
