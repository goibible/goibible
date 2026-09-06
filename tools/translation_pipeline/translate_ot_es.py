#!/usr/bin/env python3
"""Generate the full Spanish OT from WLC plus RV1909 reference (name-grounded)."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
sys.path.insert(0, str(META / "Bible_Noun_Extraction"))

from llm_client import add_llm_arguments, complete_text, config_from_args  # noqa: E402

WLC_DIR = ROOT / "Reference_Bible" / "Hebrew_Bible_WLC" / "One_Directory_WLC_KJV"
RV1909_DIR = ROOT / "Reference_Bible" / "Spanish_Bible_RV1909" / "One_Directory_RV1909_GOI"
DEFAULT_REFS = META / "staging" / "ot_torah" / "full_ot_refs.json"
DEFAULT_OUT_DIR = ROOT / "GOI_Bible" / "GOI_Bible_es"
DEFAULT_REVIEW = META / "staging" / "ot_torah" / "GOI_es_full_ot_review.md"
DEFAULT_NAMES_DB = META / "staging" / "ot_names" / "ot_names.sqlite3"
NAMES_DB_LANGUAGE = "es"
NAMES_DB_EDITION = "RV1909"

BOOK_NUMBERS = {
    "GEN": "001", "EXO": "002", "LEV": "003", "NUM": "004", "DEU": "005",
    "JOS": "006", "JDG": "007", "RUT": "008", "1SA": "009", "2SA": "010",
    "1KI": "011", "2KI": "012", "1CH": "013", "2CH": "014", "EZR": "015",
    "NEH": "016", "EST": "017", "JOB": "018", "PSA": "019", "PRO": "020",
    "ECC": "021", "SNG": "022", "ISA": "023", "JER": "024", "LAM": "025",
    "EZK": "026", "DAN": "027", "HOS": "028", "JOL": "029", "AMO": "030",
    "OBA": "031", "JON": "032", "MIC": "033", "NAM": "034", "HAB": "035",
    "ZEP": "036", "HAG": "037", "ZEC": "038", "MAL": "039",
}

REF_RE = re.compile(r"^([1-3]?[A-Z]{2,3})\s+(\d+)(?::(\d+)(?:-(\d+))?)?$")


@dataclass(frozen=True)
class VerseRef:
    book: str
    chapter: int
    verse: int
    group_name: str
    group_reason: str

    @property
    def conical(self) -> str:
        return BOOK_NUMBERS[self.book]

    @property
    def stem(self) -> str:
        return f"{self.conical}_{self.book}_{self.chapter:03d}_{self.verse:03d}"

    @property
    def label(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", type=pathlib.Path, default=DEFAULT_REFS)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--review", type=pathlib.Path, default=DEFAULT_REVIEW)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=4.0)
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Number of verses to translate concurrently (threaded, IO-bound on the "
             "LLM HTTP call). Single-verse measured throughput (~42 tok/s) is well "
             "under DeepInfra's ~200 tok/s account cap, so a handful of workers "
             "should scale near-linearly until that cap is hit.",
    )
    parser.add_argument(
        "--names-db", type=pathlib.Path, default=DEFAULT_NAMES_DB,
        help="Reusable OT name-QA sqlite DB (staging/ot_names/ot_names.sqlite3). "
             "Ground each verse's proper names before generation instead of catching drift after.",
    )
    parser.add_argument(
        "--no-names-db", action="store_true",
        help="Disable name grounding even if --names-db exists.",
    )
    # 700 was sized for zero-reasoning output; with reasoning_effort now defaulting
    # to "low" project-wide, a verse's reasoning_content length is NOT tightly
    # bounded by "low" (observed anywhere from ~200 to 1600+ tokens depending on
    # verse complexity) and can by itself consume the whole budget, leaving an
    # empty content string (finish_reason="length"). 1600 still wasn't enough
    # headroom for a meaningful fraction of verses; 3000 leaves real margin for
    # both reasoning and a one-verse translation.
    add_llm_arguments(parser, default_temperature=0.15, default_max_tokens=3000)
    return parser.parse_args()


def open_names_db(path: pathlib.Path) -> sqlite3.Connection | None:
    if not path.exists():
        print(f"Note: names DB not found at {path}; generating without name grounding.", flush=True)
        return None
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)


NAMES_DB_LOCK = threading.Lock()


def approved_names_for_verse(conn: sqlite3.Connection | None, ref: "VerseRef") -> list[str]:
    if conn is None:
        return []
    with NAMES_DB_LOCK:
        rows = conn.execute(
            """
            SELECT DISTINCT approved_text FROM name_occurrences
            WHERE language = ? AND edition = ? AND book = ? AND chapter = ? AND verse = ?
                  AND approved_text IS NOT NULL
            ORDER BY approved_text
            """,
            (NAMES_DB_LANGUAGE, NAMES_DB_EDITION, ref.book, ref.chapter, ref.verse),
        ).fetchall()
    return [row[0] for row in rows]


def chapter_verses(book: str, chapter: int) -> list[int]:
    conical = BOOK_NUMBERS[book]
    verses = []
    for path in sorted(WLC_DIR.glob(f"{conical}_{book}_{chapter:03d}_*_WLC.txt")):
        verses.append(int(path.stem.split("_")[3]))
    if not verses:
        raise RuntimeError(f"No WLC verses found for {book} {chapter}")
    return verses


def expand_ref(ref: str, group_name: str, group_reason: str) -> list[VerseRef]:
    match = REF_RE.match(ref.strip().upper())
    if not match:
        raise ValueError(f"Unsupported reference syntax: {ref!r}")
    book, chapter_text, verse_text, end_text = match.groups()
    if book not in BOOK_NUMBERS:
        raise ValueError(f"Unsupported OT book: {book}")
    chapter = int(chapter_text)
    if verse_text is None:
        verses = chapter_verses(book, chapter)
    else:
        start = int(verse_text)
        end = int(end_text or verse_text)
        verses = list(range(start, end + 1))
    return [VerseRef(book, chapter, verse, group_name, group_reason) for verse in verses]


def load_refs(path: pathlib.Path) -> list[VerseRef]:
    data = json.loads(path.read_text(encoding="utf-8"))
    refs: list[VerseRef] = []
    for group in data["groups"]:
        for ref in group["refs"]:
            refs.extend(expand_ref(ref, group["name"], group["reason"]))
    return refs


def read_required(path: pathlib.Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()


def read_optional(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def get_reference(ref: VerseRef) -> tuple[str, str]:
    """Return (edition_label, text). RV1909 has full OT coverage (GOI-versification
    aligned), so no KJV fallback is needed the way VIE1934 needed one."""
    rv1909 = read_optional(RV1909_DIR / f"{ref.stem}_RV1909.txt")
    if rv1909:
        return "RV1909", rv1909
    return "none", ""


def strip_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:text|spanish|es)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    # Strip a leaked Spanish book-name citation header the model occasionally
    # emits before the verse itself (e.g. "Genesis 33:18" or "Números 33:44"),
    # same failure class documented in translate_ot_smoke_vi.py.
    text = re.sub(
        r"^(?:[1-3] )?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]*(?:[ -][A-Za-záéíóúñ]+)* *\d+:\d+ *(?:\n+|$)",
        "", text,
    )
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) == 1:
        text = lines[0]
    return re.sub(r"^\s*(?:[A-Z0-9]{2,3}\s+)?\d+:\d+\s*", "", text).strip()


def build_prompt(
    ref: VerseRef, wlc: str, reference_edition: str, reference_text: str, approved_names: list[str],
) -> tuple[str, str]:
    system_prompt = (
        "You are translating the Hebrew Old Testament into clear, reverent Spanish for "
        "GOI Bible. Translate from the supplied WLC Hebrew source. "
        "Treat RV1909 only as a post-draft QA reference for names, numbers, divine "
        "titles, omissions, and Spanish religious terminology. Do not copy, "
        "paraphrase, or modernize RV1909's archaic wording. "
        "Before final output, verify that your Spanish subject, names, numbers, kinship "
        "relations, and divine title choices match the Hebrew source; use the RV1909 "
        "reference only to catch obvious draft mistakes in those items. "
        "Genealogies repeat the same short list of names across two different lineages "
        "(e.g. Cain's line and Seth's line both contain an Enoch and end at a Lamech, with "
        "similarly-spelled intermediate names like Methushael vs Methuselah). Before naming "
        "anyone in a genealogy verse, confirm which lineage this verse belongs to and use "
        "that lineage's own name — never borrow a name from the parallel genealogy."
    )
    if approved_names:
        names_line = (
            "Approved Spanish name spellings already established for this verse "
            "(use these exact spellings for these names; do not invent an alternate "
            "transliteration for any of them): " + ", ".join(approved_names)
        )
    else:
        names_line = "No proper names have an established Spanish spelling on file for this verse."

    user_prompt = f"""Translate {ref.label} into Spanish.

{names_line}

Rules:
- Draft from WLC first; consult the RV1909 reference only afterward as a QA check.
- Output exactly one Spanish verse, with no verse number, no markdown, and no commentary.
- Preserve names, numbers, family relationships, commands, negatives, and sequence.
- Use the approved Spanish name spellings given above exactly as listed, every time one of those names occurs.
- Do not replace a human subject with a divine subject. In genealogies, the named person lives, begets, and dies; God does not.
- If your draft's subject, name, number, family relationship, or divine title conflicts with both WLC and the reference, fix the draft before output.
- If WLC and the reference genuinely disagree with each other (not just a draft mistake), WLC wins; translate the Hebrew, not the reference's reading.
- Preserve Hebrew poetic parallelism and image order when the verse is poetry.
- For יהוה, use "Jehová"; for אלהים, use "Dios" unless context demands otherwise.
- Second person: use "tú" (singular) and "vosotros" (plural, with -áis/-éis/-ís verb conjugations), matching Reina-Valera register. Never use "vos" (voseo) or "usted"/"ustedes" (ustedeo) anywhere, as subject, object, or verb conjugation.
- For messianic prophecy, do not smooth away servant, suffering, exaltation, substitution, or rejection language.
- Keep Spanish natural and readable, but stay close enough to the Hebrew source for alignment review. Use modern Spanish orthography (accents, punctuation), not RV1909's archaic spelling conventions.

WLC Hebrew source:
{wlc}

RV1909 QA reference, not source text:
{reference_text or "[missing]"}
"""
    return system_prompt, user_prompt


def translate_one(
    ref: VerseRef, config, attempts: int, retry_delay: float, names_conn: sqlite3.Connection | None,
) -> str:
    wlc = read_required(WLC_DIR / f"{ref.stem}_WLC.txt")
    reference_edition, reference_text = get_reference(ref)
    approved_names = approved_names_for_verse(names_conn, ref)
    system_prompt, user_prompt = build_prompt(ref, wlc, reference_edition, reference_text, approved_names)
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            result = strip_response(complete_text(system_prompt, user_prompt, config))
            if not result:
                raise RuntimeError("empty response (likely reasoning consumed the whole token budget)")
            return result
        except (httpx.HTTPError, KeyError, IndexError, RuntimeError) as exc:
            last_error = exc
            print(f"RETRY {ref.label} attempt {attempt}/{attempts}: {exc}", flush=True)
            if attempt < attempts:
                time.sleep(retry_delay * attempt)
    raise RuntimeError(f"{ref.label} failed after {attempts} attempts: {last_error}")


def write_review(refs: list[VerseRef], out_dir: pathlib.Path, review_path: pathlib.Path) -> None:
    review_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GOI Spanish OT Full Review",
        "",
        f"Total selected verses: {len(refs)}",
        "",
    ]
    current_group = None
    for ref in refs:
        if ref.group_name != current_group:
            current_group = ref.group_name
            lines.extend([f"## {current_group}", "", ref.group_reason, ""])
        wlc = read_optional(WLC_DIR / f"{ref.stem}_WLC.txt")
        reference_edition, reference_text = get_reference(ref)
        goi = read_optional(out_dir / f"{ref.stem}_GOI_Es.txt")
        lines.extend(
            [
                f"### {ref.label}",
                "",
                f"- WLC: {wlc}",
                f"- {reference_edition}: {reference_text}",
                f"- GOI_Es: {goi}",
                "",
            ]
        )
    review_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    refs = load_refs(args.refs)
    config = config_from_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names_conn = None if args.no_names_db else open_names_db(args.names_db)
    print(f"Model: {config.model}", flush=True)
    print(f"Output: {args.output_dir}", flush=True)
    print(f"Selected verses: {len(refs)}", flush=True)
    print(f"Name grounding: {'on (' + str(args.names_db) + ')' if names_conn else 'off'}", flush=True)

    written = 0
    skipped = 0
    print_lock = threading.Lock()

    def work_one(index: int, ref: "VerseRef") -> None:
        nonlocal written
        out = args.output_dir / f"{ref.stem}_GOI_Es.txt"
        verse = None
        for file_attempt in range(5):
            try:
                verse = translate_one(ref, config, args.max_attempts, args.retry_delay, names_conn)
                break
            except FileNotFoundError as exc:
                if file_attempt < 4:
                    with print_lock:
                        print(f"RETRY (missing source file, attempt {file_attempt + 1}/5) "
                              f"{ref.label}: {exc}", flush=True)
                    time.sleep(5 * (file_attempt + 1))
                else:
                    with print_lock:
                        print(f"SKIP (source file still missing after retries) {ref.label}: {exc}", flush=True)
            except RuntimeError as exc:
                # translate_one already exhausted its own internal --max-attempts
                # retries (e.g. every attempt hit "empty response" or a repeated
                # HTTP failure). Don't let one stubborn verse crash an unattended
                # multi-hour run — back off, retry the outer loop a few more
                # times, then skip this single verse and keep going; a later
                # --missing-only-style resume (verse file absent) will retry it.
                if file_attempt < 4:
                    with print_lock:
                        print(f"RETRY (translate_one exhausted, outer attempt {file_attempt + 1}/5) "
                              f"{ref.label}: {exc}", flush=True)
                    time.sleep(10 * (file_attempt + 1))
                else:
                    with print_lock:
                        print(f"SKIP (translate_one failed after all retries) {ref.label}: {exc}", flush=True)
        if verse is None:
            return
        out.write_text(verse + "\n", encoding="utf-8")
        with print_lock:
            written += 1
            print(f"[{index:05d}/{len(refs):05d}] WROTE {ref.label}: {verse[:96]}", flush=True)

    try:
        pending: list[tuple[int, "VerseRef"]] = []
        for index, ref in enumerate(refs, start=1):
            out = args.output_dir / f"{ref.stem}_GOI_Es.txt"
            if out.exists() and out.stat().st_size > 0 and not args.overwrite:
                skipped += 1
                print(f"[{index:05d}/{len(refs):05d}] SKIP {ref.label}", flush=True)
                continue
            if args.dry_run:
                print(f"[{index:05d}/{len(refs):05d}] DRY {ref.label} -> {out.name}", flush=True)
                continue
            pending.append((index, ref))

        if pending and not args.dry_run:
            if args.workers <= 1:
                for index, ref in pending:
                    work_one(index, ref)
            else:
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    futures = [pool.submit(work_one, index, ref) for index, ref in pending]
                    for future in as_completed(futures):
                        future.result()  # surface any unexpected exception
    finally:
        if names_conn is not None:
            names_conn.close()

    if not args.dry_run:
        write_review(refs, args.output_dir, args.review)
        print(f"Review: {args.review}", flush=True)
    print(f"Done. written={written} skipped={skipped}", flush=True)


if __name__ == "__main__":
    main()
