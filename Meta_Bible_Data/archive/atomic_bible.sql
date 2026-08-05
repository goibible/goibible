CREATE TABLE verses (
    goi INTEGER,
    canonical INTEGER NOT NULL,
    version TEXT NOT NULL,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    testament TEXT,
    filename_key TEXT NOT NULL UNIQUE,
    PRIMARY KEY (version, book, chapter, verse)
);
CREATE INDEX idx_version ON verses (version);
CREATE INDEX idx_goi ON verses (version, goi);
CREATE TABLE books (
    canonical INTEGER PRIMARY KEY CHECK (canonical BETWEEN 1 AND 66),
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
CREATE INDEX idx_canonical ON verses (canonical, chapter, verse);
CREATE TABLE apparatus (
    version      TEXT NOT NULL,
    book         TEXT NOT NULL,
    chapter      INTEGER NOT NULL,
    verse        INTEGER NOT NULL,  -- 0 for superscriptions
    apparatus_type TEXT NOT NULL,   -- SUPERSCRIPTION, KETIV, QERE, COLOPHON
    content      TEXT NOT NULL
);
