PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

ATTACH DATABASE 'atomic_bible.sqlite3' AS src;

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
    filename_key TEXT NOT NULL,
    PRIMARY KEY (edition_id, book, chapter, verse),
    FOREIGN KEY (edition_id) REFERENCES editions (edition_id)
);

CREATE UNIQUE INDEX idx_verses_edition_filename_key
    ON verses (edition_id, filename_key);
CREATE INDEX idx_verses_edition_goi ON verses (edition_id, goi);
CREATE INDEX idx_verses_goi ON verses (goi);
CREATE INDEX idx_verses_language_subtag ON verses (language_subtag);
CREATE INDEX idx_verses_canonical ON verses (conical, chapter, verse);
CREATE INDEX idx_verses_version ON verses (version);

INSERT INTO books
SELECT conical, osis, long_name, testament
FROM src.books;

INSERT INTO iso_languages
SELECT subtag, description, suppress_script, deprecated, preferred_value
FROM src.iso_languages;

INSERT INTO iso_scripts
SELECT subtag, description, deprecated, preferred_value
FROM src.iso_scripts;

INSERT INTO iso_regions
SELECT subtag, description, deprecated, preferred_value
FROM src.iso_regions;

INSERT INTO editions (edition_id, bcp47_tag, language_subtag, status, display_name, notes) VALUES
    ('CUV', 'zh', 'zh', 'active', 'Chinese Union Version', NULL),
    ('KJV', 'en', 'en', 'active', 'King James Version', NULL),
    ('WEBUS', 'en-US', 'en', 'active', 'World English Bible (US)', NULL),
    ('TR1550', 'el', 'el', 'active', 'Textus Receptus 1550', 'Partial corpus in current source'),
    ('WLC', 'he', 'he', 'active', 'Westminster Leningrad Codex', 'Partial corpus in current source'),
    ('PENDING_6TH', NULL, NULL, 'pending', 'Pending Sixth Bible', 'Placeholder row for sixth edition not yet imported/mapped');

INSERT INTO verses (
    goi,
    conical,
    edition_id,
    version,
    language_subtag,
    book,
    chapter,
    verse,
    testament,
    filename_key
)
SELECT
    COALESCE(
        v.goi,
        ROW_NUMBER() OVER (
            PARTITION BY v.version
            ORDER BY v.conical, v.chapter, v.verse
        )
    ) AS computed_goi,
    v.conical,
    v.version AS edition_id,
    v.version AS version,
    e.language_subtag,
    v.book,
    v.chapter,
    v.verse,
    v.testament,
    v.filename_key
FROM src.verses v
JOIN editions e ON e.edition_id = v.version;

CREATE VIEW verses_legacy AS
SELECT
    goi,
    conical,
    edition_id AS version,
    book,
    chapter,
    verse,
    testament,
    filename_key
FROM verses;

COMMIT;
