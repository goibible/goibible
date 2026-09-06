#!/usr/bin/env python3
"""Generate Portuguese OT verses from WLC with Almeida 1911 as QA reference."""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
sys.path.insert(0, str(META / "Bible_Noun_Extraction"))

from llm_client import add_llm_arguments, complete_text, config_from_args  # noqa: E402
from translate_ot_es import BOOK_NUMBERS, VerseRef, load_refs, read_optional, read_required  # noqa: E402

WLC_DIR = ROOT / "Reference_Bible" / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
ALMEIDA_DIR = ROOT / "Reference_Bible" / "Portuguese_Bible_Almeida1911" / "One_Directory_Almeida1911_GOI"
DEFAULT_REFS = META / "staging" / "ot_torah" / "full_ot_refs.json"
DEFAULT_OUT_DIR = ROOT / "GOI_Bible" / "GOI_Bible_pt"
DEFAULT_REVIEW = META / "staging" / "ot_torah" / "GOI_pt_full_ot_review.md"
DEFAULT_NAMES_DB = META / "staging" / "ot_names" / "pt_ot_names.sqlite3"
NAMES_DB_LANGUAGE = "pt"
NAMES_DB_EDITION = "Almeida1911"

NAMES_DB_LOCK = threading.Lock()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", type=pathlib.Path, default=DEFAULT_REFS)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--review", type=pathlib.Path, default=DEFAULT_REVIEW)
    parser.add_argument("--names-db", type=pathlib.Path, default=DEFAULT_NAMES_DB)
    parser.add_argument("--no-names-db", action="store_true")
    parser.add_argument("--book", action="append", choices=sorted(BOOK_NUMBERS))
    parser.add_argument("--chapter-start", type=int)
    parser.add_argument("--chapter-end", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--overwrite-pending", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=4.0)
    add_llm_arguments(parser, default_temperature=0.15, default_max_tokens=3000)
    return parser.parse_args()


def open_names_db(path: pathlib.Path) -> sqlite3.Connection | None:
    if not path.exists():
        print(f"Note: names DB not found at {path}; generating without name grounding.", flush=True)
        return None
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)


def approved_names_for_verse(conn: sqlite3.Connection | None, ref: VerseRef) -> list[str]:
    if conn is None:
        return []
    with NAMES_DB_LOCK:
        rows = conn.execute(
            """
            SELECT DISTINCT approved_text FROM name_occurrences
            WHERE language=? AND edition=? AND book=? AND chapter=? AND verse=?
              AND approved_text IS NOT NULL
            ORDER BY approved_text
            """,
            (NAMES_DB_LANGUAGE, NAMES_DB_EDITION, ref.book, ref.chapter, ref.verse),
        ).fetchall()
    return [row[0] for row in rows]


def get_reference(ref: VerseRef) -> str:
    return read_optional(ALMEIDA_DIR / f"{ref.stem}_Almeida1911.txt")


def strip_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:text|portuguese|pt)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"^(?:[1-3] )?[A-ZÁÉÍÓÚÃÕÂÊÔÇ][^\n]*\d+:\d+\s*(?:\n+|$)", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return (lines[0] if len(lines) == 1 else " ".join(lines)).strip()


def build_prompt(ref: VerseRef, wlc: str, reference: str, names: list[str]) -> tuple[str, str]:
    system = (
        "Você traduz um versículo do Antigo Testamento hebraico para português claro, "
        "reverente e natural para a Bíblia GOI. Traduza do texto hebraico WLC fornecido. "
        "A Almeida 1911 é somente uma referência pública para QA posterior: nomes, números, "
        "títulos divinos, omissões e termos religiosos; não copie sua redação arcaica. "
        "Preserve o sentido, a ordem das imagens poéticas, sujeitos, negações, relações "
        "familiares e sequência do hebraico."
    )
    names_line = (
        "Use exatamente estas grafias portuguesas aprovadas para os nomes: " + ", ".join(names)
        if names else "Não há grafias de nomes aprovadas previamente para este versículo."
    )
    user = f"""Traduza {ref.label} para português.

{names_line}

Regras:
- Produza exatamente um versículo, sem número, markdown ou comentários.
- WLC é a fonte; Almeida 1911 é apenas uma testemunha de QA.
- Preserve nomes, números, gênero, relações de parentesco, comandos, negações e sujeitos.
- Para יהוה use "SENHOR"; para אלהים use "Deus", salvo quando o contexto exigir outra forma.
- Use ortografia portuguesa moderna, não a grafia arcaica de Almeida 1911.
- Em genealogias, confirme a linhagem no hebraico antes de escolher nomes semelhantes.
- Mantenha paralelismos e imagens da poesia hebraica.

Texto hebraico WLC:
{wlc}

Referência Almeida 1911 para QA, não para cópia:
{reference or "[ausente]"}
"""
    return system, user


def translate_one(
    ref: VerseRef,
    config,
    names_conn: sqlite3.Connection | None,
    max_attempts: int,
    retry_delay: float,
) -> str:
    wlc = read_required(WLC_DIR / f"{ref.stem}_WLC.txt")
    reference = get_reference(ref)
    system, user = build_prompt(ref, wlc, reference, approved_names_for_verse(names_conn, ref))
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = strip_response(complete_text(system, user, config))
            if result:
                return result
            raise RuntimeError("empty response")
        except (httpx.HTTPError, KeyError, IndexError, RuntimeError) as exc:
            last_error = exc
            print(f"RETRY {ref.label} attempt {attempt}/{max_attempts}: {exc}", flush=True)
            if attempt < max_attempts:
                time.sleep(retry_delay * attempt)
    raise RuntimeError(f"{ref.label} failed: {last_error}")


def main() -> None:
    args = parse_args()
    refs = load_refs(args.refs)
    selected_books = set(args.book or BOOK_NUMBERS)
    refs = [
        ref for ref in refs
        if ref.book in selected_books
        and (args.chapter_start is None or ref.chapter >= args.chapter_start)
        and (args.chapter_end is None or ref.chapter <= args.chapter_end)
    ]
    if not refs:
        raise SystemExit("No verses selected")
    config = config_from_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names_conn = None if args.no_names_db else open_names_db(args.names_db)
    print(f"Model: {config.model}", flush=True)
    print(f"Output: {args.output_dir}", flush=True)
    print(f"Selected verses: {len(refs)}", flush=True)
    print(f"Name grounding: {'on (' + str(args.names_db) + ')' if names_conn else 'off'}", flush=True)
    lock = threading.Lock()
    written = 0
    skipped = 0

    def work(index: int, ref: VerseRef) -> None:
        nonlocal written
        out = args.output_dir / f"{ref.stem}_GOI_Pt.txt"
        for outer in range(5):
            try:
                verse = translate_one(ref, config, names_conn, args.max_attempts, args.retry_delay)
                out.write_text(verse + "\n", encoding="utf-8")
                with lock:
                    written += 1
                    print(f"[{index:05d}/{len(refs):05d}] WROTE {ref.label}: {verse[:96]}", flush=True)
                return
            except FileNotFoundError as exc:
                if outer == 4:
                    print(f"SKIP {ref.label}: {exc}", flush=True)
                else:
                    time.sleep(5 * (outer + 1))
            except RuntimeError as exc:
                if outer == 4:
                    print(f"SKIP {ref.label}: {exc}", flush=True)
                else:
                    print(f"RETRY outer {ref.label}: {exc}", flush=True)
                    time.sleep(10 * (outer + 1))

    pending: list[tuple[int, VerseRef]] = []
    for index, ref in enumerate(refs, 1):
        out = args.output_dir / f"{ref.stem}_GOI_Pt.txt"
        existing = read_optional(out)
        is_pending = existing == "__PT_TRANSLATION_PENDING__"
        if out.exists() and out.stat().st_size > 0 and not args.overwrite and not (args.overwrite_pending and is_pending):
            skipped += 1
            continue
        if args.dry_run:
            print(f"DRY {ref.label} -> {out.name}", flush=True)
        else:
            pending.append((index, ref))
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(work, index, ref) for index, ref in pending]
            for future in as_completed(futures):
                future.result()
    finally:
        if names_conn is not None:
            names_conn.close()
    if not args.dry_run:
        args.review.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# GOI Portuguese OT Review", "", f"Selected verses: {len(refs)}", ""]
        for ref in refs:
            out = args.output_dir / f"{ref.stem}_GOI_Pt.txt"
            lines.extend([f"## {ref.label}", "", f"- WLC: {read_optional(WLC_DIR / (ref.stem + '_WLC.txt'))}", f"- Almeida1911: {get_reference(ref)}", f"- GOI_Pt: {read_optional(out)}", ""])
        args.review.write_text("\n".join(lines), encoding="utf-8")
        print(f"Review: {args.review}", flush=True)
    print(f"Done. written={written} skipped={skipped}", flush=True)


if __name__ == "__main__":
    main()
