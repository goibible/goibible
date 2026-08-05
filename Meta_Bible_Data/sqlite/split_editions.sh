#!/usr/bin/env bash
# Split GOI_bible.sqlite3 into one self-contained .db per edition.
# Each output db carries the same schema (editions, books, verses) so the
# Android app can merge any of them back with ATTACH + INSERT.
set -euo pipefail

SRC="${1:-/home/albert/projects/bible/Meta_Bible_Data/local_backups/GOI_bible.sqlite3}"
OUT_DIR="${2:-/home/albert/projects/bible/Meta_Bible_Data/sqlite/editions}"
mkdir -p "$OUT_DIR"

editions=$(sqlite3 "$SRC" "SELECT edition_id FROM editions;")

for ed in $editions; do
    out="$OUT_DIR/${ed}.db"
    rm -f "$out"
    sqlite3 "$out" <<SQL
ATTACH '$SRC' AS src;
CREATE TABLE editions (
    edition_id TEXT PRIMARY KEY,
    bcp47_tag TEXT,
    language_subtag TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending')),
    display_name TEXT,
    notes TEXT
);
CREATE TABLE books (
    conical INTEGER PRIMARY KEY CHECK (conical BETWEEN 1 AND 66),
    osis TEXT NOT NULL UNIQUE,
    long_name TEXT NOT NULL,
    testament TEXT NOT NULL CHECK (testament IN ('OT','NT'))
);
CREATE TABLE verses (
    goi INTEGER NOT NULL,
    conical INTEGER NOT NULL,
    edition_id TEXT NOT NULL,
    version TEXT NOT NULL,
    language_subtag TEXT NOT NULL,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    testament TEXT,
    verse_text TEXT,
    PRIMARY KEY (edition_id, book, chapter, verse),
    FOREIGN KEY (edition_id) REFERENCES editions (edition_id)
);
INSERT INTO editions   SELECT * FROM src.editions WHERE edition_id = '$ed';
INSERT INTO books      SELECT * FROM src.books;
INSERT INTO verses     SELECT * FROM src.verses WHERE edition_id = '$ed';
CREATE INDEX idx_verses_canonical ON verses (conical, chapter, verse);
DETACH src;
VACUUM;
SQL
    echo "$out  ($(sqlite3 "$out" 'SELECT count(*) FROM verses;') verses)"
done
