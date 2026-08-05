#!/usr/bin/env python3
"""Build and validate a reusable OT proper-name database for one target language."""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
DEFAULT_PROFILE_DIR = META / "translation_configs" / "name_qa"


@dataclass(frozen=True)
class NameProfile:
    language: str
    reference_dir: pathlib.Path
    reference_edition: str
    target_dir: pathlib.Path
    target_edition: str
    db: pathlib.Path
    flags: pathlib.Path
    confirm: pathlib.Path
    token_regex: re.Pattern[str]
    stopwords: set[str]
    always_names: set[str]
    known_corrections: dict[str, str]
    notes: str = ""


def path_from_profile(value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    return path if path.is_absolute() else ROOT / path


def load_profile(path: pathlib.Path) -> NameProfile:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "language",
        "reference_dir",
        "reference_edition",
        "target_dir",
        "target_edition",
        "db",
        "flags",
        "confirm",
        "token_regex",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"Profile {path} is missing required keys: {', '.join(missing)}")
    return NameProfile(
        language=data["language"],
        reference_dir=path_from_profile(data["reference_dir"]),
        reference_edition=data["reference_edition"],
        target_dir=path_from_profile(data["target_dir"]),
        target_edition=data["target_edition"],
        db=path_from_profile(data["db"]),
        flags=path_from_profile(data["flags"]),
        confirm=path_from_profile(data["confirm"]),
        token_regex=re.compile(data["token_regex"]),
        stopwords=set(data.get("stopwords", [])),
        always_names=set(data.get("always_names", [])),
        known_corrections=dict(data.get("known_corrections", {})),
        notes=data.get("notes", ""),
    )


def normalize_key(text: str) -> str:
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "", text)


def file_re(reference_edition: str, target_edition: str) -> re.Pattern[str]:
    editions = "|".join(re.escape(value) for value in (reference_edition, target_edition))
    return re.compile(rf"^(0[0-3][0-9])_([1-3]?[A-Z]{{2,3}})_(\d{{3}})_(\d{{3}})_({editions})\.txt$")


def parse_file(path: pathlib.Path, profile: NameProfile) -> tuple[str, str, int, int, str] | None:
    match = file_re(profile.reference_edition, profile.target_edition).match(path.name)
    if not match:
        return None
    conical, book, chapter, verse, edition = match.groups()
    if int(conical) > 39:
        return None
    return conical, book, int(chapter), int(verse), edition


def extract_names(text: str, profile: NameProfile) -> list[str]:
    names: list[str] = []
    known_names = set(profile.known_corrections) | set(profile.known_corrections.values()) | profile.always_names
    for match in profile.token_regex.finditer(text):
        token = match.group(0).strip()
        if token in profile.stopwords:
            continue
        if token in known_names:
            names.append(token)
            continue
        if "-" in token:
            names.append(token)
    return names


def connect(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS name_entities (
          entity_key TEXT PRIMARY KEY,
          entity_type TEXT NOT NULL DEFAULT 'unknown',
          canonical_label TEXT NOT NULL,
          notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS name_forms (
          language TEXT NOT NULL,
          form_key TEXT NOT NULL,
          entity_key TEXT NOT NULL,
          form_text TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'approved',
          source TEXT NOT NULL DEFAULT 'reference',
          notes TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (language, form_key),
          FOREIGN KEY (entity_key) REFERENCES name_entities(entity_key)
        );
        CREATE TABLE IF NOT EXISTS entity_occurrences (
          language TEXT NOT NULL,
          edition TEXT NOT NULL,
          book TEXT NOT NULL,
          chapter INTEGER NOT NULL,
          verse INTEGER NOT NULL,
          entity_key TEXT NOT NULL,
          form_text TEXT NOT NULL,
          form_key TEXT NOT NULL,
          occurrence_role TEXT NOT NULL DEFAULT 'observed',
          status TEXT NOT NULL DEFAULT 'observed',
          PRIMARY KEY (language, edition, book, chapter, verse, entity_key, form_text),
          FOREIGN KEY (entity_key) REFERENCES name_entities(entity_key)
        );
        CREATE INDEX IF NOT EXISTS idx_entity_occ_ref ON entity_occurrences(language, book, chapter, verse);
        CREATE INDEX IF NOT EXISTS idx_entity_occ_key ON entity_occurrences(entity_key);
        CREATE TABLE IF NOT EXISTS approved_names (
          language TEXT NOT NULL,
          name_key TEXT NOT NULL,
          approved_text TEXT NOT NULL,
          source TEXT NOT NULL DEFAULT 'reference',
          notes TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (language, name_key)
        );
        CREATE TABLE IF NOT EXISTS name_occurrences (
          language TEXT NOT NULL,
          edition TEXT NOT NULL,
          book TEXT NOT NULL,
          chapter INTEGER NOT NULL,
          verse INTEGER NOT NULL,
          name_text TEXT NOT NULL,
          name_key TEXT NOT NULL,
          approved_text TEXT,
          status TEXT NOT NULL DEFAULT 'observed',
          PRIMARY KEY (language, edition, book, chapter, verse, name_text)
        );
        CREATE INDEX IF NOT EXISTS idx_occ_ref ON name_occurrences(language, book, chapter, verse);
        CREATE INDEX IF NOT EXISTS idx_occ_name_key ON name_occurrences(language, name_key);
        CREATE TABLE IF NOT EXISTS validation_flags (
          language TEXT NOT NULL,
          batch TEXT NOT NULL,
          book TEXT NOT NULL,
          chapter INTEGER NOT NULL,
          verse INTEGER NOT NULL,
          severity TEXT NOT NULL,
          category TEXT NOT NULL,
          expected_name TEXT,
          observed_name TEXT,
          note TEXT NOT NULL,
          PRIMARY KEY (language, batch, book, chapter, verse, category, expected_name, observed_name)
        );
        """
    )
    return conn


def entity_key_for(approved_text: str) -> str:
    return normalize_key(approved_text)


def upsert_form(
    conn: sqlite3.Connection,
    profile: NameProfile,
    form_text: str,
    approved_text: str,
    status: str,
    source: str,
    notes: str = "",
) -> str:
    entity_key = entity_key_for(approved_text)
    form_key = normalize_key(form_text)
    conn.execute(
        """
        INSERT OR IGNORE INTO name_entities(entity_key, canonical_label)
        VALUES (?, ?)
        """,
        (entity_key, approved_text),
    )
    conn.execute(
        """
        INSERT INTO name_forms(language, form_key, entity_key, form_text, status, source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(language, form_key)
        DO UPDATE SET entity_key=excluded.entity_key,
                      form_text=excluded.form_text,
                      status=excluded.status,
                      source=excluded.source,
                      notes=excluded.notes
        """,
        (profile.language, form_key, entity_key, form_text, status, source, notes),
    )
    return entity_key


def rebuild(conn: sqlite3.Connection, profile: NameProfile) -> None:
    conn.execute("DELETE FROM name_occurrences WHERE language=?", (profile.language,))
    conn.execute("DELETE FROM entity_occurrences WHERE language=?", (profile.language,))
    conn.execute("DELETE FROM name_forms WHERE language=?", (profile.language,))
    conn.execute("DELETE FROM validation_flags WHERE language=?", (profile.language,))
    conn.execute("DELETE FROM approved_names WHERE language=?", (profile.language,))
    for path in sorted(profile.reference_dir.glob(f"*_{profile.reference_edition}.txt")):
        parsed = parse_file(path, profile)
        if not parsed:
            continue
        _conical, book, chapter, verse, edition = parsed
        text = path.read_text(encoding="utf-8").strip()
        for name in extract_names(text, profile):
            key = normalize_key(name)
            approved = profile.known_corrections.get(name, name)
            entity_key = upsert_form(conn, profile, approved, approved, "approved", "reference")
            conn.execute(
                """
                INSERT OR IGNORE INTO approved_names(language, name_key, approved_text, source)
                VALUES (?, ?, ?, 'reference')
                """,
                (profile.language, key, approved),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO name_occurrences
                (language, edition, book, chapter, verse, name_text, name_key, approved_text, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'expected')
                """,
                (profile.language, edition, book, chapter, verse, name, key, approved),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO entity_occurrences
                (language, edition, book, chapter, verse, entity_key, form_text, form_key, occurrence_role, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'expected', 'expected')
                """,
                (profile.language, edition, book, chapter, verse, entity_key, name, key),
            )

    for wrong, approved in profile.known_corrections.items():
        upsert_form(conn, profile, wrong, approved, "variant", "manual", "known generated variant")
        conn.execute(
            """
            INSERT INTO approved_names(language, name_key, approved_text, source, notes)
            VALUES (?, ?, ?, 'manual', 'known generated variant')
            ON CONFLICT(language, name_key)
            DO UPDATE SET approved_text=excluded.approved_text, source='manual'
            """,
            (profile.language, normalize_key(wrong), approved),
        )

    if profile.target_dir.exists():
        for path in sorted(profile.target_dir.glob(f"*_{profile.target_edition}.txt")):
            parsed = parse_file(path, profile)
            if not parsed:
                continue
            _conical, book, chapter, verse, edition = parsed
            text = path.read_text(encoding="utf-8").strip()
            for name in extract_names(text, profile):
                key = normalize_key(name)
                row = conn.execute(
                    "SELECT approved_text FROM approved_names WHERE language=? AND name_key=?",
                    (profile.language, key),
                ).fetchone()
                approved = row[0] if row else profile.known_corrections.get(name)
                status = "approved" if approved == name else "variant" if approved else "unmapped"
                entity_key = upsert_form(
                    conn,
                    profile,
                    name,
                    approved or name,
                    status if status != "unmapped" else "candidate",
                    "target" if status == "unmapped" else "manual",
                    "candidate generated form" if status == "unmapped" else "",
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO name_occurrences
                    (language, edition, book, chapter, verse, name_text, name_key, approved_text, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (profile.language, edition, book, chapter, verse, name, key, approved, status),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO entity_occurrences
                    (language, edition, book, chapter, verse, entity_key, form_text, form_key, occurrence_role, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'observed', ?)
                    """,
                    (profile.language, edition, book, chapter, verse, entity_key, name, key, status),
                )
    conn.commit()


def refs_from_manifest(path: pathlib.Path) -> list[tuple[str, int, int]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from translate_ot_smoke_vi import load_refs

    return [(ref.book, ref.chapter, ref.verse) for ref in load_refs(path)]


def validate(
    conn: sqlite3.Connection,
    profile: NameProfile,
    refs_path: pathlib.Path,
    batch: str,
    flags_path: pathlib.Path,
) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from translate_ot_smoke_vi import BOOK_NUMBERS

    conn.execute(
        "DELETE FROM validation_flags WHERE language=? AND batch=?",
        (profile.language, batch),
    )
    refs = refs_from_manifest(refs_path)
    for book, chapter, verse in refs:
        conical = BOOK_NUMBERS.get(book)
        goi_path = profile.target_dir / f"{conical}_{book}_{chapter:03d}_{verse:03d}_{profile.target_edition}.txt" if conical else None
        if not goi_path or not goi_path.exists() or goi_path.stat().st_size == 0:
            continue
        verse_text = goi_path.read_text(encoding="utf-8").strip()
        expected = conn.execute(
            """
            SELECT approved_text
            FROM name_occurrences
            WHERE language=? AND edition=? AND book=? AND chapter=? AND verse=? AND approved_text IS NOT NULL
            GROUP BY approved_text
            """,
            (profile.language, profile.reference_edition, book, chapter, verse),
        ).fetchall()
        target_names = conn.execute(
            """
            SELECT name_text, approved_text, status
            FROM name_occurrences
            WHERE language=? AND edition=? AND book=? AND chapter=? AND verse=?
            """,
            (profile.language, profile.target_edition, book, chapter, verse),
        ).fetchall()

        for (approved,) in expected:
            if approved and approved not in verse_text:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO validation_flags
                    VALUES (?, ?, ?, ?, ?, 'orange', 'missing_expected_name', ?, NULL, ?)
                    """,
                    (
                        profile.language,
                        batch,
                        book,
                        chapter,
                        verse,
                        approved,
                        f"Expected approved name {approved!r} from {profile.reference_edition} occurrence.",
                    ),
                )

        for name_text, approved, status in target_names:
            if status == "variant":
                conn.execute(
                    """
                    INSERT OR IGNORE INTO validation_flags
                    VALUES (?, ?, ?, ?, ?, 'red', 'known_name_variant', ?, ?, ?)
                    """,
                    (
                        profile.language,
                        batch,
                        book,
                        chapter,
                        verse,
                        approved,
                        name_text,
                        f"Observed {name_text!r}; approved form is {approved!r}.",
                    ),
                )
            elif status == "unmapped":
                conn.execute(
                    """
                    INSERT OR IGNORE INTO validation_flags
                    VALUES (?, ?, ?, ?, ?, 'yellow', 'unmapped_candidate_name', NULL, ?, ?)
                    """,
                    (
                        profile.language,
                        batch,
                        book,
                        chapter,
                        verse,
                        name_text,
                        "Candidate name has no approved mapping yet.",
                    ),
                )
    conn.commit()

    flags_path.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        """
        SELECT book, chapter, verse, severity, category, expected_name, observed_name, note
        FROM validation_flags
        WHERE language=? AND batch=?
        ORDER BY CASE severity WHEN 'red' THEN 1 WHEN 'orange' THEN 2 ELSE 3 END, book, chapter, verse
        """,
        (profile.language, batch),
    ).fetchall()
    with flags_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["book", "chapter", "verse", "severity", "category", "expected_name", "observed_name", "note"])
        writer.writerows(rows)
    counts = conn.execute(
        """
        SELECT severity, COUNT(*)
        FROM validation_flags
        WHERE language=? AND batch=?
        GROUP BY severity
        """,
        (profile.language, batch),
    ).fetchall()
    print(dict(counts))
    print(f"Flags: {flags_path}")


def export_confirm(conn: sqlite3.Connection, profile: NameProfile, batch: str, output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        """
        SELECT
          COALESCE(observed_name, expected_name) AS name_seen,
          expected_name AS approved_or_expected,
          severity,
          category,
          COUNT(*) AS occurrences,
          GROUP_CONCAT(book || ' ' || chapter || ':' || verse, '; ') AS refs
        FROM validation_flags
        WHERE language=? AND batch=?
        GROUP BY name_seen, approved_or_expected, severity, category
        ORDER BY CASE severity WHEN 'red' THEN 1 WHEN 'orange' THEN 2 ELSE 3 END,
                 occurrences DESC,
                 name_seen
        """,
        (profile.language, batch),
    ).fetchall()
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name_seen", "approved_or_expected", "severity", "category", "occurrences", "refs"])
        writer.writerows(rows)
    print(f"Confirm: {output}")


def profile_path(name_or_path: str) -> pathlib.Path:
    path = pathlib.Path(name_or_path)
    if path.exists():
        return path
    candidate = DEFAULT_PROFILE_DIR / f"{name_or_path}.json"
    if candidate.exists():
        return candidate
    raise SystemExit(f"Could not find profile {name_or_path!r} or {candidate}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="vi", help="Profile name under translation_configs/name_qa or a JSON path.")
    parser.add_argument("--db", type=pathlib.Path)
    parser.add_argument("--target-dir", type=pathlib.Path)
    parser.add_argument("--refs", type=pathlib.Path, default=META / "staging" / "ot_torah" / "genesis_1_25_refs.json")
    parser.add_argument("--batch", default="genesis_1_25")
    parser.add_argument("--flags", type=pathlib.Path)
    parser.add_argument("--confirm", type=pathlib.Path)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--export-confirm", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = load_profile(profile_path(args.profile))
    if args.target_dir:
        profile = NameProfile(**{**profile.__dict__, "target_dir": args.target_dir})
    db_path = args.db or profile.db
    flags_path = args.flags or profile.flags
    confirm_path = args.confirm or profile.confirm

    conn = connect(db_path)
    if args.rebuild:
        rebuild(conn, profile)
        total = conn.execute(
            "SELECT COUNT(*) FROM name_occurrences WHERE language=?",
            (profile.language,),
        ).fetchone()[0]
        approved = conn.execute(
            "SELECT COUNT(*) FROM approved_names WHERE language=?",
            (profile.language,),
        ).fetchone()[0]
        print(f"Language: {profile.language}")
        print(f"Occurrences: {total}")
        print(f"Approved/mapped names: {approved}")
        print(f"DB: {db_path}")
    if args.validate:
        validate(conn, profile, args.refs, args.batch, flags_path)
    if args.export_confirm:
        export_confirm(conn, profile, args.batch, confirm_path)


if __name__ == "__main__":
    main()
