-- GOI Bible database schema.
-- Source of truth for the structure of the "shell" database.
-- Apply with: sqlite3 shell.sqlite3 < schema.sql

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

CREATE TABLE iso_languages (
    subtag TEXT PRIMARY KEY,
    description TEXT,
    suppress_script TEXT,
    deprecated INTEGER DEFAULT 0,
    preferred_value TEXT
);

CREATE TABLE iso_scripts (
    subtag TEXT PRIMARY KEY,
    description TEXT,
    deprecated INTEGER DEFAULT 0,
    preferred_value TEXT
);

CREATE TABLE iso_regions (
    subtag TEXT PRIMARY KEY,
    description TEXT,
    deprecated INTEGER DEFAULT 0,
    preferred_value TEXT
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

CREATE INDEX idx_verses_edition_goi ON verses (edition_id, goi);
CREATE INDEX idx_verses_goi ON verses (goi);
CREATE INDEX idx_verses_language_subtag ON verses (language_subtag);
CREATE INDEX idx_verses_canonical ON verses (conical, chapter, verse);
CREATE INDEX idx_verses_version ON verses (version);

CREATE VIEW verses_legacy AS
SELECT
    goi,
    conical,
    edition_id AS version,
    book,
    chapter,
    verse,
    testament,
    verse_text
FROM verses;
