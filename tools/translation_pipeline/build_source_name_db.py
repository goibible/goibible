#!/usr/bin/env python3
"""Build canonical Bible name entities from source Hebrew and Greek texts."""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
WLC_DIR = META / "sources" / "morphhb" / "wlc"
HEBREW_STRONGS = META / "sources" / "strongs" / "hebrew" / "StrongHebrewG.xml"
TR_DIR = META / "sources" / "greektext-textus-receptus" / "parsed"
GREEK_STRONGS = META / "sources" / "strongs" / "greek" / "StrongsGreekDictionaryXML_1.4" / "strongsgreek.xml"
DEFAULT_DB = META / "staging" / "source_names" / "biblical_source_names.sqlite3"

OSIS_NS = {"osis": "http://www.bibletechnologies.net/2003/OSIS/namespace"}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

BOOK_MAP_OT = {
    "Gen": (1, "GEN"),
    "Exod": (2, "EXO"),
    "Lev": (3, "LEV"),
    "Num": (4, "NUM"),
    "Deut": (5, "DEU"),
    "Josh": (6, "JOS"),
    "Judg": (7, "JDG"),
    "Ruth": (8, "RUT"),
    "1Sam": (9, "1SA"),
    "2Sam": (10, "2SA"),
    "1Kgs": (11, "1KI"),
    "2Kgs": (12, "2KI"),
    "1Chr": (13, "1CH"),
    "2Chr": (14, "2CH"),
    "Ezra": (15, "EZR"),
    "Neh": (16, "NEH"),
    "Esth": (17, "EST"),
    "Job": (18, "JOB"),
    "Ps": (19, "PSA"),
    "Prov": (20, "PRO"),
    "Eccl": (21, "ECC"),
    "Song": (22, "SNG"),
    "Isa": (23, "ISA"),
    "Jer": (24, "JER"),
    "Lam": (25, "LAM"),
    "Ezek": (26, "EZK"),
    "Dan": (27, "DAN"),
    "Hos": (28, "HOS"),
    "Joel": (29, "JOL"),
    "Amos": (30, "AMO"),
    "Obad": (31, "OBA"),
    "Jonah": (32, "JON"),
    "Mic": (33, "MIC"),
    "Nah": (34, "NAM"),
    "Hab": (35, "HAB"),
    "Zeph": (36, "ZEP"),
    "Hag": (37, "HAG"),
    "Zech": (38, "ZEC"),
    "Mal": (39, "MAL"),
}

BOOK_MAP_NT = {
    "MT": (40, "MAT"),
    "MR": (41, "MRK"),
    "LU": (42, "LUK"),
    "JOH": (43, "JHN"),
    "AC": (44, "ACT"),
    "RO": (45, "ROM"),
    "1CO": (46, "1CO"),
    "2CO": (47, "2CO"),
    "GA": (48, "GAL"),
    "EPH": (49, "EPH"),
    "PHP": (50, "PHP"),
    "COL": (51, "COL"),
    "1TH": (52, "1TH"),
    "2TH": (53, "2TH"),
    "1TI": (54, "1TI"),
    "2TI": (55, "2TI"),
    "TIT": (56, "TIT"),
    "PHM": (57, "PHM"),
    "HEB": (58, "HEB"),
    "JAS": (59, "JAS"),
    "1PE": (60, "1PE"),
    "2PE": (61, "2PE"),
    "1JO": (62, "1JN"),
    "2JO": (63, "2JN"),
    "3JO": (64, "3JN"),
    "JUDE": (65, "JUD"),
    "RE": (66, "REV"),
}

HEBREW_DIVINE_STRONGS = {
    "H136": "name_of_god",
    "H410": "name_of_god",
    "H430": "name_of_god",
    "H433": "name_of_god",
    "H3068": "name_of_god",
    "H3069": "name_of_god",
    "H5945": "name_of_god",
    "H7706": "name_of_god",
}

HEBREW_NAME_EXCLUSIONS = {
    "H4693",  # matsor: fortified/besieged places, not a proper-name obligation here
    "H7585",  # sheol: common noun/place term, not a proper name obligation
    "H8227",  # shaphan: coney/rock badger, not the proper name Shaphan in context
}

GREEK_DIVINE_STRONGS = {
    "G2424": "name_of_god",  # Jesus
    "G5547": "name_of_god",  # Christ
    "G2316": "name_of_god",  # God
    "G2962": "name_of_god",  # Lord
    "G4151": "name_of_god",  # Spirit, only included in Holy Spirit contexts
}

TOKEN_RE = re.compile(
    r"(?:([a-z]+)\s+((?:\d+\s+)*\d+)|\|\s*([a-z]+)(?:\s*\|\s*[a-z]+)*\s*\|\s*((?:\d+\s+)*\d+))\s+\{([^}]+)\}",
    re.IGNORECASE,
)
VERSE_START_RE = re.compile(r"^(\d+):(\d+)\s+(.*)$")
MORPH_VARIANT_GROUP_RE = re.compile(
    r"\|\s*([a-z]+(?:\s+\d+)+\s+\{[^}]+\})(?:\s*\|\s*[a-z]+(?:\s+\d+)+\s+\{[^}]+\})+\s*\|",
    re.IGNORECASE,
)
KJV_NOTE_RE = re.compile(r"\bKJV:([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)\b")
CRITICAL_NT_READING_OVERRIDES = {
    # Project translation policy: Romans 12:11 follows the earlier/stronger
    # critical reading "to the Lord" rather than the TR1550 "to the time".
    ("ROM", 12, 11): (
        re.compile(r"\bkairw\s+2540\s+\{N-DSM\}", re.IGNORECASE),
        "kuriw 2962 {N-DSM}",
    ),
}


def connect(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS source_name_entities (
          entity_key TEXT PRIMARY KEY,
          testament TEXT NOT NULL,
          source_language TEXT NOT NULL,
          source_edition TEXT NOT NULL,
          strongs TEXT NOT NULL,
          source_lemma TEXT NOT NULL DEFAULT '',
          transliteration TEXT NOT NULL DEFAULT '',
          canonical_label TEXT NOT NULL DEFAULT '',
          entity_type TEXT NOT NULL DEFAULT 'unknown',
          source_morph TEXT NOT NULL DEFAULT '',
          gloss TEXT NOT NULL DEFAULT '',
          definition TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_source_entities_testament
          ON source_name_entities(testament, source_language, strongs);

        CREATE TABLE IF NOT EXISTS source_name_occurrences (
          entity_key TEXT NOT NULL,
          testament TEXT NOT NULL,
          source_language TEXT NOT NULL,
          source_edition TEXT NOT NULL,
          book_num INTEGER NOT NULL,
          book TEXT NOT NULL,
          chapter INTEGER NOT NULL,
          verse INTEGER NOT NULL,
          strongs TEXT NOT NULL,
          source_lemma TEXT NOT NULL DEFAULT '',
          surface_text TEXT NOT NULL,
          morphology TEXT NOT NULL DEFAULT '',
          source_file TEXT NOT NULL DEFAULT '',
          mapped_book TEXT NOT NULL DEFAULT '',
          mapped_chapter INTEGER,
          mapped_verse INTEGER,
          source_note TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (entity_key, book, chapter, verse, surface_text, morphology)
        );
        CREATE INDEX IF NOT EXISTS idx_source_occ_ref
          ON source_name_occurrences(testament, book_num, chapter, verse);
        CREATE INDEX IF NOT EXISTS idx_source_occ_entity
          ON source_name_occurrences(entity_key);

        CREATE TABLE IF NOT EXISTS source_verse_references (
          testament TEXT NOT NULL,
          source_language TEXT NOT NULL,
          source_edition TEXT NOT NULL,
          book_num INTEGER NOT NULL,
          book TEXT NOT NULL,
          chapter INTEGER NOT NULL,
          verse INTEGER NOT NULL,
          mapped_book TEXT NOT NULL DEFAULT '',
          mapped_chapter INTEGER,
          mapped_verse INTEGER,
          source_note TEXT NOT NULL DEFAULT '',
          source_file TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (source_edition, book, chapter, verse)
        );
        CREATE INDEX IF NOT EXISTS idx_source_refs_mapped
          ON source_verse_references(mapped_book, mapped_chapter, mapped_verse);

        CREATE TABLE IF NOT EXISTS source_name_links (
          from_entity_key TEXT NOT NULL,
          to_entity_key TEXT NOT NULL,
          link_type TEXT NOT NULL,
          confidence TEXT NOT NULL DEFAULT 'dictionary',
          source TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (from_entity_key, to_entity_key, link_type)
        );
        """
    )
    ensure_occurrence_columns(conn)
    return conn


def ensure_occurrence_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(source_name_occurrences)")}
    columns = {
        "mapped_book": "TEXT NOT NULL DEFAULT ''",
        "mapped_chapter": "INTEGER",
        "mapped_verse": "INTEGER",
        "source_note": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE source_name_occurrences ADD COLUMN {name} {definition}")


def text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def strong_key(prefix: str, number: str) -> str:
    return f"{prefix}{int(number)}"


def clean_hebrew_lemma(raw: str) -> str | None:
    for part in reversed(raw.split("/")):
        match = re.match(r"(\d+)", part)
        if match:
            return strong_key("H", match.group(1))
    return None


def load_hebrew_dictionary() -> dict[str, dict[str, str]]:
    root = ET.parse(HEBREW_STRONGS).getroot()
    entries: dict[str, dict[str, str]] = {}
    for div in root.findall(".//osis:div[@type='entry']", OSIS_NS):
        n = div.attrib.get("n", "")
        if not n:
            continue
        w = div.find(".//osis:w", OSIS_NS)
        if w is None:
            continue
        key = strong_key("H", n)
        definition = text_content(div)
        morph = w.attrib.get("morph", "")
        xml_lang = w.attrib.get(XML_LANG, "")
        entity_type = "proper_name" if "n-pr" in morph or xml_lang == "x-pn" else HEBREW_DIVINE_STRONGS.get(key, "")
        entries[key] = {
            "lemma": w.attrib.get("lemma", ""),
            "transliteration": w.attrib.get("xlit", ""),
            "canonical_label": w.attrib.get("xlit", "") or w.attrib.get("lemma", ""),
            "entity_type": entity_type,
            "source_morph": morph,
            "gloss": w.attrib.get("gloss", ""),
            "definition": definition,
        }
    return entries


def load_greek_dictionary() -> dict[str, dict[str, str]]:
    root = ET.parse(GREEK_STRONGS).getroot()
    entries: dict[str, dict[str, str]] = {}
    for entry in root.findall(".//entry"):
        n = entry.attrib.get("strongs") or text_content(entry.find("strongs"))
        if not n:
            continue
        key = strong_key("G", n)
        greek = entry.find("greek")
        definition = text_content(entry)
        strongs_def = text_content(entry.find("strongs_def"))
        kjv_def = text_content(entry.find("kjv_def"))
        hebrew_refs = []
        for ref in entry.findall(".//strongsref"):
            if ref.attrib.get("language", "").upper() == "HEBREW":
                hebrew_refs.append(strong_key("H", ref.attrib.get("strongs", "0")))
        kjv_rendering = kjv_def.replace(":--", "").replace("--", "").strip()
        first_rendering = kjv_rendering.split(",", 1)[0].strip(" .;:")
        entity_type = GREEK_DIVINE_STRONGS.get(key, "")
        if not entity_type and hebrew_refs and first_rendering[:1].isupper():
            entity_type = "proper_name"
        entries[key] = {
            "lemma": greek.attrib.get("unicode", "") if greek is not None else "",
            "transliteration": greek.attrib.get("translit", "") if greek is not None else "",
            "canonical_label": greek.attrib.get("translit", "") if greek is not None else key,
            "entity_type": entity_type,
            "source_morph": "",
            "gloss": kjv_def,
            "definition": strongs_def or definition,
            "hebrew_refs": ",".join(hebrew_refs),
        }
    return entries


def upsert_entity(
    conn: sqlite3.Connection,
    entity_key: str,
    testament: str,
    language: str,
    edition: str,
    strongs: str,
    meta: dict[str, str],
    entity_type: str,
) -> None:
    conn.execute(
        """
        INSERT INTO source_name_entities
        (entity_key, testament, source_language, source_edition, strongs, source_lemma,
         transliteration, canonical_label, entity_type, source_morph, gloss, definition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_key) DO UPDATE SET
          canonical_label=excluded.canonical_label,
          entity_type=excluded.entity_type,
          source_morph=excluded.source_morph,
          gloss=excluded.gloss,
          definition=excluded.definition
        """,
        (
            entity_key,
            testament,
            language,
            edition,
            strongs,
            meta.get("lemma", ""),
            meta.get("transliteration", ""),
            meta.get("canonical_label", ""),
            entity_type,
            meta.get("source_morph", ""),
            meta.get("gloss", ""),
            meta.get("definition", ""),
        ),
    )


def insert_occurrence(
    conn: sqlite3.Connection,
    entity_key: str,
    testament: str,
    language: str,
    edition: str,
    book_num: int,
    book: str,
    chapter: int,
    verse: int,
    strongs: str,
    lemma: str,
    surface: str,
    morphology: str,
    source_file: str,
    mapped_book: str = "",
    mapped_chapter: int | None = None,
    mapped_verse: int | None = None,
    source_note: str = "",
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO source_name_occurrences
        (entity_key, testament, source_language, source_edition, book_num, book, chapter,
         verse, strongs, source_lemma, surface_text, morphology, source_file,
         mapped_book, mapped_chapter, mapped_verse, source_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_key,
            testament,
            language,
            edition,
            book_num,
            book,
            chapter,
            verse,
            strongs,
            lemma,
            surface,
            morphology,
            source_file,
            mapped_book,
            mapped_chapter,
            mapped_verse,
            source_note,
        ),
    )


def morphhb_kjv_note_ref(verse_el: ET.Element) -> tuple[str, int | None, int | None, str]:
    for note in verse_el.findall("osis:note", OSIS_NS):
        text = text_content(note)
        match = KJV_NOTE_RE.search(text)
        if not match:
            continue
        source_book, chapter, verse = match.groups()
        mapped = BOOK_MAP_OT.get(source_book)
        if mapped:
            return mapped[1], int(chapter), int(verse), text
    return "", None, None, ""


def upsert_verse_reference(
    conn: sqlite3.Connection,
    testament: str,
    language: str,
    edition: str,
    book_num: int,
    book: str,
    chapter: int,
    verse: int,
    mapped_book: str,
    mapped_chapter: int | None,
    mapped_verse: int | None,
    source_note: str,
    source_file: str,
) -> None:
    conn.execute(
        """
        INSERT INTO source_verse_references
        (testament, source_language, source_edition, book_num, book, chapter, verse,
         mapped_book, mapped_chapter, mapped_verse, source_note, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_edition, book, chapter, verse) DO UPDATE SET
          mapped_book=excluded.mapped_book,
          mapped_chapter=excluded.mapped_chapter,
          mapped_verse=excluded.mapped_verse,
          source_note=excluded.source_note,
          source_file=excluded.source_file
        """,
        (
            testament,
            language,
            edition,
            book_num,
            book,
            chapter,
            verse,
            mapped_book,
            mapped_chapter,
            mapped_verse,
            source_note,
            source_file,
        ),
    )


def build_ot(conn: sqlite3.Connection, hebrew_entries: dict[str, dict[str, str]]) -> None:
    for path in sorted(WLC_DIR.glob("*.xml")):
        if path.name == "VerseMap.xml":
            continue
        book_id = path.stem
        if book_id not in BOOK_MAP_OT:
            continue
        book_num, book = BOOK_MAP_OT[book_id]
        root = ET.parse(path).getroot()
        for verse_el in root.findall(".//osis:verse", OSIS_NS):
            osis_id = verse_el.attrib.get("osisID", "")
            parts = osis_id.split(".")
            if len(parts) < 3:
                continue
            chapter, verse = int(parts[-2]), int(parts[-1])
            mapped_book, mapped_chapter, mapped_verse, source_note = morphhb_kjv_note_ref(verse_el)
            upsert_verse_reference(
                conn,
                "OT",
                "hebrew",
                "WLC",
                book_num,
                book,
                chapter,
                verse,
                mapped_book,
                mapped_chapter,
                mapped_verse,
                source_note,
                path.name,
            )
            for w in verse_el.findall(".//osis:w", OSIS_NS):
                lemma_raw = w.attrib.get("lemma", "")
                strongs = clean_hebrew_lemma(lemma_raw)
                if not strongs:
                    continue
                if strongs in HEBREW_NAME_EXCLUSIONS:
                    continue
                morphology = w.attrib.get("morph", "")
                meta = hebrew_entries.get(strongs, {})
                if strongs in HEBREW_DIVINE_STRONGS:
                    entity_type = HEBREW_DIVINE_STRONGS[strongs]
                elif meta.get("entity_type") and "Np" in morphology:
                    entity_type = meta["entity_type"]
                else:
                    continue
                entity_key = f"OT:{strongs}"
                upsert_entity(conn, entity_key, "OT", "hebrew", "WLC", strongs, meta, entity_type)
                insert_occurrence(
                    conn,
                    entity_key,
                    "OT",
                    "hebrew",
                    "WLC",
                    book_num,
                    book,
                    chapter,
                    verse,
                    strongs,
                    lemma_raw,
                    "".join(w.itertext()).strip(),
                    morphology,
                    path.name,
                    mapped_book,
                    mapped_chapter,
                    mapped_verse,
                    source_note,
                )


def iter_tr_verses(path: pathlib.Path) -> list[tuple[int, int, str]]:
    verses: list[tuple[int, int, str]] = []
    current: tuple[int, int] | None = None
    chunks: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = VERSE_START_RE.match(line)
        if match:
            if current:
                verses.append((current[0], current[1], " ".join(chunks)))
            current = (int(match.group(1)), int(match.group(2)))
            chunks = [match.group(3)]
        elif current:
            chunks.append(line.strip())
    if current:
        verses.append((current[0], current[1], " ".join(chunks)))
    return verses


def select_primary_tr_readings(text: str) -> str:
    """Keep the first reading in parsed TR variant groups.

    The project's plain TR1550 verse flatfiles are the default source of record.
    In the parsed files, pipe groups can include alternate readings; the first
    reading matches the plain source in checked cases.
    """
    previous = None
    while previous != text:
        previous = text
        text = MORPH_VARIANT_GROUP_RE.sub(lambda match: match.group(1), text)
    return text


def apply_critical_nt_reading_override(book: str, chapter: int, verse: int, text: str) -> str:
    override = CRITICAL_NT_READING_OVERRIDES.get((book, chapter, verse))
    if not override:
        return text
    pattern, replacement = override
    return pattern.sub(replacement, text)


def build_nt(conn: sqlite3.Connection, greek_entries: dict[str, dict[str, str]]) -> None:
    for path in sorted(TR_DIR.glob("*.UTR")):
        book_id = path.stem
        if book_id not in BOOK_MAP_NT:
            continue
        book_num, book = BOOK_MAP_NT[book_id]
        for chapter, verse, text in iter_tr_verses(path):
            text = select_primary_tr_readings(text)
            text = apply_critical_nt_reading_override(book, chapter, verse, text)
            tokens = [
                (token or variant_token, next(num for num in reversed((strong_number or variant_strong).split()) if num != "0"), morphology)
                for token, strong_number, variant_token, variant_strong, morphology in TOKEN_RE.findall(text)
                if any(num != "0" for num in (strong_number or variant_strong).split())
            ]
            verse_strongs = {strong_key("G", strong_number) for _token, strong_number, _morphology in tokens}
            for token, strong_number, morphology in tokens:
                strongs = strong_key("G", strong_number)
                meta = greek_entries.get(strongs, {})
                entity_type = meta.get("entity_type") or ("proper_name" if "N-PRI" in morphology else "")
                if strongs == "G4151" and "G40" not in verse_strongs:
                    entity_type = ""
                if not entity_type:
                    continue
                entity_key = f"NT:{strongs}"
                upsert_entity(conn, entity_key, "NT", "greek", "TR1550", strongs, meta, entity_type)
                insert_occurrence(
                    conn,
                    entity_key,
                    "NT",
                    "greek",
                    "TR1550",
                    book_num,
                    book,
                    chapter,
                    verse,
                    strongs,
                    meta.get("lemma", ""),
                    token,
                    morphology,
                    path.name,
                )
                for hebrew_ref in filter(None, meta.get("hebrew_refs", "").split(",")):
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO source_name_links
                        (from_entity_key, to_entity_key, link_type, confidence, source)
                        VALUES (?, ?, 'greek_hebrew_origin', 'dictionary', ?)
                        """,
                        (entity_key, f"OT:{hebrew_ref}", "Strong Greek dictionary"),
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=pathlib.Path, default=DEFAULT_DB)
    parser.add_argument("--rebuild", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(args.db)
    if args.rebuild:
        conn.executescript(
            """
            DELETE FROM source_name_links;
            DELETE FROM source_name_occurrences;
            DELETE FROM source_verse_references;
            DELETE FROM source_name_entities;
            """
        )
    hebrew_entries = load_hebrew_dictionary()
    greek_entries = load_greek_dictionary()
    build_ot(conn, hebrew_entries)
    build_nt(conn, greek_entries)
    conn.commit()
    print(f"DB: {args.db}")
    for row in conn.execute(
        """
        SELECT testament, source_language, COUNT(DISTINCT entity_key), COUNT(*)
        FROM source_name_occurrences
        GROUP BY testament, source_language
        ORDER BY testament
        """
    ):
        print(row)
    print("links", conn.execute("SELECT COUNT(*) FROM source_name_links").fetchone()[0])
    print("verse_refs", conn.execute("SELECT COUNT(*) FROM source_verse_references").fetchone()[0])


if __name__ == "__main__":
    main()
