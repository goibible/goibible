import re
import json
import sqlite3
import requests
import unicodedata
import logging
import argparse
from pathlib import Path
from datetime import datetime


# ------------------------------------------------------------
# CONFIG — PATHS (ANCHOR TO SCRIPT LOCATION)
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "greek_noun.sqlite3"
VERSE_DIR = BASE_DIR / "One_Directory_TR1550"

PROGRESS_LOG = BASE_DIR / "progress.log"
ERROR_LOG = BASE_DIR / "error.log"


# ------------------------------------------------------------
# CONFIG — LLM / PIPELINE PARAMETERS
# ------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = (BASE_DIR / "ai_llm.txt").read_text().strip()

CONFIDENCE_THRESHOLD = 0.85


# ------------------------------------------------------------
# CONFIG — PERFORMANCE / SAFETY (OPTIONAL BUT RECOMMENDED)
# ------------------------------------------------------------

REQUEST_TIMEOUT = 300          # Gemma 26B can be slow
MAX_RETRIES = 3               # LLM retry attempts
BATCH_SIZE = 100              # DB commit frequency

# ------------------------------------------------------------
# LOGGING SETUP
# ------------------------------------------------------------

logging.basicConfig(level=logging.INFO)

progress_logger = logging.getLogger("progress")
progress_logger.setLevel(logging.INFO)
progress_logger.handlers.clear()
progress_handler = logging.FileHandler(PROGRESS_LOG, mode="a", encoding="utf-8")
progress_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
progress_logger.addHandler(progress_handler)
progress_logger.propagate = False

error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)
error_logger.handlers.clear()
error_handler = logging.FileHandler(ERROR_LOG, mode="a", encoding="utf-8")
error_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
error_logger.addHandler(error_handler)
error_logger.propagate = False


# ------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------

def normalize_text(text):
    return unicodedata.normalize("NFC", text.strip())


def is_pure_greek(text):
    for ch in text:
        if ch == ' ':
            continue
        block = unicodedata.name(ch, '').split()[0]
        if block not in ('GREEK', 'COMBINING'):
            return False
    return True


def strip_diacritics(text):
    """Remove combining diacritics and normalize sigma variants for token matching.

    Source text uses final sigma (ς U+03C2); models often emit medial sigma (σ U+03C3).
    Normalizing both sides to medial sigma makes lookup sigma-agnostic.
    """
    nfd = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return stripped.replace('ς', 'σ')  # ς → σ


def tokenize(text):
    text = re.sub(r"[·.,;:!?\"'«»()\[\]]", "", text)
    return text.split()


def parse_filename(filename):
    parts = filename.replace(".txt", "").split("_")
    canon_order = int(parts[0])
    book_code = parts[1]
    chapter = int(parts[2])
    verse = int(parts[3])
    return canon_order, book_code, chapter, verse


def clean_llm_response(raw):
    """Strip HTML comments and extract valid noun objects from malformed LLM output."""
    cleaned = re.sub(r'<!--.*?-->', '', raw, flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    noun_pattern = re.compile(
        r'\{\s*"surface_form"\s*:\s*"([^"]+)"\s*,'
        r'\s*"lemma"\s*:\s*"([^"]+)"\s*,'
        r'\s*"category"\s*:\s*"([^"]+)"\s*,'
        r'\s*"confidence"\s*:\s*([\d.]+)\s*\}',
        re.DOTALL
    )
    nouns = [
        {"surface_form": m.group(1), "lemma": m.group(2),
         "category": m.group(3), "confidence": float(m.group(4))}
        for m in noun_pattern.finditer(cleaned)
    ]
    return {"nouns": nouns} if nouns else None


def call_llm(verse_text, model=MODEL_NAME):
    prompt = f"""You are analyzing Koine Greek.

CRITICAL: Return ONLY valid JSON. No comments. No explanation. No HTML. No markdown. Only the JSON object.
If a word is NOT a noun, do not include it — exclude it entirely with no comment or annotation.

Rules:
- Return ONLY single-token nouns.
- The surface_form must be the EXACT token as it appears in the verse text — copy it character by character.
- The verse text is unaccented. Do NOT add accent marks to surface_form.
- Do NOT return inflected stems or lemma forms — return the exact inflected token (e.g. "γην" not "γη", "καιρον" not "καιρος").
- Do NOT split compound words — if the token is "ψευδοπροφηται", return that full token, not "προφηται".
- Do NOT include articles (τον, τους, τη, etc.).
- Do NOT combine multiple tokens.
- If a noun appears with an article, return only the noun token.
- If uncertain, exclude the token — do not include it with any comment or explanation.
- Use only Unicode Greek characters. Never use Latin characters a-z in surface_form or lemma.

ABSOLUTE REQUIREMENT: surface_form and lemma must contain ONLY Ancient Greek Unicode characters.
Proper names (Jesus, Abraham, David, etc.) must be written in Greek script exactly as they appear in the TR1550 source text.
NEVER use Hebrew, Latin, or any other script. If you cannot write a token in Greek characters, omit it entirely.

Examples of correct surface→lemma mapping (surface_form copied verbatim from verse, lemma is dictionary form):
- Token "γη" in verse  → {{"surface_form": "γη",       "lemma": "γῆ",        "category": "PLACE",  "confidence": 0.95}}
- Token "θεον" in verse → {{"surface_form": "θεον",     "lemma": "θεός",      "category": "GOD",    "confidence": 0.95}}
- Token "ιωαννην" in verse → {{"surface_form": "ιωαννην", "lemma": "Ἰωάννης", "category": "PERSON", "confidence": 0.95}}

Return JSON only:
{{
  "nouns": [
    {{
      "surface_form": "...",
      "lemma": "...",
      "category": "GOD | PERSON | PLACE | OTHER",
      "confidence": 0.0
    }}
  ]
}}

Verse:
{verse_text}
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0,
                        "top_p": 0.1,
                        "repeat_penalty": 1.0
                    }
                },
                timeout=120
            )

            response.raise_for_status()

            try:
                data = response.json()
            except Exception:
                raise ValueError(f"Non-JSON HTTP response: {response.text[:300]}")

            raw = data.get("response", "").strip()

            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens

            print(
                f"TOKENS | prompt={prompt_tokens} "
                f"completion={completion_tokens} total={total_tokens}"
            )

            if not raw:
                raise ValueError("Empty response from LLM")

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = clean_llm_response(raw)
                if parsed is None:
                    print("\n--- BAD RAW OUTPUT ---")
                    print(raw[:1000])
                    raise ValueError("LLM returned invalid JSON")
                print(f"WARNING: Used fallback JSON cleaner on response")

            if not isinstance(parsed, dict):
                raise ValueError(f"LLM JSON root is not an object: {type(parsed).__name__}")

            nouns = parsed.get("nouns")
            if nouns is None:
                raise ValueError("LLM JSON missing 'nouns' key")

            if not isinstance(nouns, list):
                raise ValueError("'nouns' is not a list")

            return parsed, prompt_tokens, completion_tokens, total_tokens

        except Exception as e:
            last_error = e
            if attempt < 3:
                print(f"Retry {attempt}/3 due to error: {e}")
            else:
                raise last_error


# ------------------------------------------------------------
# DB HELPERS
# ------------------------------------------------------------

def init_db(conn):
    schema_path = BASE_DIR / "greek_noun_schema.sql"
    raw_sql = schema_path.read_text(encoding="utf-8")
    safe_sql = re.sub(r'\bCREATE TABLE\b', 'CREATE TABLE IF NOT EXISTS', raw_sql)
    safe_sql = re.sub(r'\bCREATE INDEX\b', 'CREATE INDEX IF NOT EXISTS', safe_sql)
    conn.executescript(safe_sql)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS noun_translations (
            translation_id   INTEGER PRIMARY KEY,
            noun_id          INTEGER NOT NULL,
            target_lang      TEXT NOT NULL DEFAULT 'zho',
            zh_translation   TEXT,
            cuv_translation  TEXT,
            notes            TEXT,
            UNIQUE (noun_id, target_lang),
            FOREIGN KEY (noun_id) REFERENCES nouns(noun_id) ON DELETE CASCADE
        );
    """)

    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO versions (version_code, language_code)
        VALUES ('TR1550', 'grc')
    """)
    for code in ("GOD", "PERSON", "PLACE", "OTHER"):
        cur.execute("""
            INSERT OR IGNORE INTO noun_categories (category_code)
            VALUES (?)
        """, (code,))

    cur.execute("""
        INSERT OR IGNORE INTO noun_translations (noun_id, target_lang)
        SELECT noun_id, 'zho' FROM nouns
    """)

    conn.commit()

    cur.execute("SELECT version_id FROM versions WHERE version_code = 'TR1550'")
    return cur.fetchone()[0]


def get_or_create_book(conn, canon_order, book_code):
    cur = conn.cursor()
    cur.execute("SELECT book_id FROM books WHERE book_code = ?", (book_code,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO books (canon_order, book_code, book_name) VALUES (?, ?, ?)",
        (canon_order, book_code, book_code)
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_verse(conn, book_id, chapter, verse):
    cur = conn.cursor()
    cur.execute("""
        SELECT verse_id FROM verses
        WHERE book_id = ? AND chapter_number = ? AND verse_number = ?
    """, (book_id, chapter, verse))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO verses (book_id, chapter_number, verse_number)
        VALUES (?, ?, ?)
    """, (book_id, chapter, verse))
    conn.commit()
    return cur.lastrowid


def get_or_create_noun(conn, lemma):
    cur = conn.cursor()
    cur.execute("""
        SELECT noun_id FROM nouns
        WHERE lemma = ? AND language_code = 'grc'
    """, (lemma,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO nouns (lemma, language_code)
        VALUES (?, 'grc')
    """, (lemma,))
    noun_id = cur.lastrowid
    cur.execute("""
        INSERT OR IGNORE INTO noun_translations (noun_id, target_lang)
        VALUES (?, 'zho')
    """, (noun_id,))
    conn.commit()
    return noun_id


def get_category_id(conn, category_code):
    cur = conn.cursor()
    cur.execute("""
        SELECT category_id FROM noun_categories
        WHERE category_code = ?
    """, (category_code,))
    row = cur.fetchone()
    if row:
        return row[0]
    error_logger.error(f"Unknown category '{category_code}' — falling back to OTHER")
    cur.execute("SELECT category_id FROM noun_categories WHERE category_code = 'OTHER'")
    return cur.fetchone()[0]


def verse_is_processed(conn, verse_id, version_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM verse_noun_occurrences
        WHERE verse_id = ? AND version_id = ? LIMIT 1
    """, (verse_id, version_id))
    return cur.fetchone() is not None


# ------------------------------------------------------------
# EXPORT UTILITIES
# ------------------------------------------------------------

def export_nouns(path):
    import sys
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)

    rows = conn.execute("""
        SELECT
            n.lemma,
            n.language_code,
            (SELECT nc2.category_code
             FROM verse_noun_occurrences vno2
             JOIN noun_categories nc2 ON nc2.category_id = vno2.category_id
             WHERE vno2.noun_id = n.noun_id
             GROUP BY nc2.category_code
             ORDER BY COUNT(*) DESC, nc2.category_code ASC
             LIMIT 1) AS category,
            COUNT(vno.occurrence_id) AS occurrence_count,
            COALESCE(nt.zh_translation, '') AS zh_translation
        FROM nouns n
        LEFT JOIN verse_noun_occurrences vno ON vno.noun_id = n.noun_id
        LEFT JOIN noun_translations nt
            ON nt.noun_id = n.noun_id AND nt.target_lang = 'zho'
        GROUP BY n.noun_id
        ORDER BY occurrence_count DESC, n.lemma ASC
    """).fetchall()
    conn.close()

    header = "lemma\tlanguage_code\tcategory\toccurrence_count\tzh_translation\n"
    if path == "-":
        sys.stdout.write(header)
        for row in rows:
            sys.stdout.write("\t".join(str(c) for c in row) + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            for row in rows:
                f.write("\t".join(str(c) for c in row) + "\n")
        print(f"Exported {len(rows)} nouns to {path}")


def export_verse_counts(path):
    import sys
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)

    rows = conn.execute("""
        SELECT
            b.book_code,
            v.chapter_number,
            v.verse_number,
            COUNT(vno.occurrence_id) AS noun_count
        FROM verses v
        JOIN books b ON b.book_id = v.book_id
        LEFT JOIN verse_noun_occurrences vno ON vno.verse_id = v.verse_id
        GROUP BY v.verse_id
        ORDER BY b.canon_order ASC, v.chapter_number ASC, v.verse_number ASC
    """).fetchall()
    conn.close()

    header = "book_code\tchapter\tverse\tnoun_count\n"
    if path == "-":
        sys.stdout.write(header)
        for row in rows:
            sys.stdout.write("\t".join(str(c) for c in row) + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            for row in rows:
                f.write("\t".join(str(c) for c in row) + "\n")
        print(f"Exported {len(rows)} verse counts to {path}")


# ------------------------------------------------------------
# MAIN PROCESS
# ------------------------------------------------------------

def process_all(dry_run=False, start_from=None, skip_processed=False, files_filter=None, rerun_errors=False, model=MODEL_NAME):
    start_time = datetime.now()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    version_id = init_db(conn)

    files = sorted(Path(VERSE_DIR).glob("*.txt"))

    if start_from:
        files = [f for f in files if f.name >= start_from]
        print(f"Resuming from {start_from} ({len(files)} files remaining)")

    if rerun_errors:
        error_files = set()
        with open(ERROR_LOG, 'r') as f:
            for line in f:
                match = re.search(r'Error processing (\S+):', line)
                if match:
                    error_files.add(match.group(1))
        files = [f for f in files if f.name in error_files]
        print(f"Rerunning {len(files)} files from error.log")

    if files_filter:
        files = [f for f in files if f.name in files_filter]

    insert_mode = "INSERT OR REPLACE"

    total_files = len(files)

    processed = 0
    total_nouns = 0
    total_errors = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    mode_label = " [DRY RUN]" if dry_run else ""
    print(f"\nStarting processing of {total_files} verses...{mode_label}\n")

    for file_path in files:
        processed += 1
        print(f"[{processed}/{total_files}] {file_path.name}")

        try:
            canon_order, book_code, chapter, verse = parse_filename(file_path.name)

            with open(file_path, "r", encoding="utf-8") as f:
                verse_text = normalize_text(f.read())

            if not dry_run:
                book_id = get_or_create_book(conn, canon_order, book_code)
                verse_id = get_or_create_verse(conn, book_id, chapter, verse)

                conn.execute("""
                    INSERT OR IGNORE INTO verse_texts (verse_id, version_id, verse_text)
                    VALUES (?, ?, ?)
                """, (verse_id, version_id, verse_text))

                if skip_processed and verse_is_processed(conn, verse_id, version_id):
                    print(f"  [SKIP] already processed")
                    continue

            tokens = tokenize(verse_text)
            token_positions = {}
            for i, token in enumerate(tokens):
                key = strip_diacritics(token)
                token_positions.setdefault(key, []).append(i)

            llm_data, prompt_tokens, completion_tokens, verse_total_tokens = call_llm(verse_text, model=model)

            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            total_tokens += verse_total_tokens

            verse_noun_count = 0

            for noun in llm_data.get("nouns", []):
                surface = normalize_text(str(noun["surface_form"]))
                lemma = normalize_text(str(noun.get("lemma", surface)))
                category = str(noun["category"]).strip().upper()
                confidence = float(noun["confidence"])

                if not is_pure_greek(surface):
                    error_logger.error(f"Mixed-script surface in {file_path.name}: {surface!r}")
                    total_errors += 1
                    continue

                # Source text is unaccented; strip any accents the model added
                surface = strip_diacritics(surface)

                if surface not in token_positions or not token_positions[surface]:
                    error_logger.error(f"Hallucinated token in {file_path.name}: {surface}")
                    total_errors += 1
                    continue

                if dry_run:
                    token_index = token_positions[surface][0]
                    print(f"  DRY-RUN noun: surface={surface!r} lemma={lemma!r} "
                          f"category={category} confidence={confidence} token_index={token_index}")
                    verse_noun_count += 1
                    continue

                noun_id = get_or_create_noun(conn, lemma)
                category_id = get_category_id(conn, category)
                token_index = token_positions[surface].pop(0)

                conn.execute(f"""
                    {insert_mode} INTO verse_noun_occurrences
                    (verse_id, version_id, noun_id,
                     surface_form, category_id,
                     token_index, confidence, needs_review)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    verse_id,
                    version_id,
                    noun_id,
                    surface,
                    category_id,
                    token_index,
                    confidence,
                    1 if confidence < CONFIDENCE_THRESHOLD else 0
                ))

                verse_noun_count += 1

            if not dry_run:
                conn.commit()

            total_nouns += verse_noun_count
            progress_logger.info(
                f"{file_path.name} | nouns={verse_noun_count} | "
                f"prompt_tokens={prompt_tokens} | completion_tokens={completion_tokens} | "
                f"total_tokens={verse_total_tokens}"
            )

        except Exception as e:
            error_logger.error(f"Error processing {file_path.name}: {str(e)}")
            total_errors += 1
            continue

    conn.close()

    duration = datetime.now() - start_time

    print("\nProcessing complete.")
    print(f"Total verses: {total_files}")
    print(f"Total nouns extracted: {total_nouns}")
    print(f"Total errors: {total_errors}")
    print(f"Total prompt tokens: {total_prompt_tokens}")
    print(f"Total completion tokens: {total_completion_tokens}")
    print(f"Total tokens: {total_tokens}")
    print(f"Duration: {duration}")
    if dry_run:
        print("(DRY RUN — no DB writes performed)")

    progress_logger.info(
        f"RUN COMPLETE | dry_run={dry_run} verses={total_files} nouns={total_nouns} "
        f"errors={total_errors} prompt_tokens={total_prompt_tokens} "
        f"completion_tokens={total_completion_tokens} total_tokens={total_tokens} "
        f"duration={duration}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Greek nouns from TR1550 verse files into SQLite"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run LLM and log output without writing to DB"
    )
    parser.add_argument(
        "--start-from",
        metavar="FILENAME",
        help="Resume from this filename (e.g. 040_MAT_001_001_TR1550.txt)"
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Skip verses that already have rows in verse_noun_occurrences"
    )
    parser.add_argument(
        "--export-nouns",
        metavar="FILE",
        nargs="?",
        const="nouns_export.tsv",
        help="Export lemma dictionary TSV (default: nouns_export.tsv; use - for stdout)"
    )
    parser.add_argument(
        "--export-verse-counts",
        metavar="FILE",
        nargs="?",
        const="verse_counts_export.tsv",
        help="Export per-verse noun count TSV (default: verse_counts_export.tsv; use - for stdout)"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        metavar="FILENAME",
        help="Process only these specific verse files"
    )
    parser.add_argument(
        "--rerun-errors",
        action="store_true",
        help="Reprocess all files that appear in error.log"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL_NAME,
        help="Ollama model to use for noun extraction"
    )
    args = parser.parse_args()

    if args.export_nouns:
        export_nouns(args.export_nouns)
    elif args.export_verse_counts:
        export_verse_counts(args.export_verse_counts)
    else:
        process_all(
            dry_run=args.dry_run,
            start_from=args.start_from,
            skip_processed=args.skip_processed,
            files_filter=args.files,
            rerun_errors=args.rerun_errors,
            model=args.model,
        )
