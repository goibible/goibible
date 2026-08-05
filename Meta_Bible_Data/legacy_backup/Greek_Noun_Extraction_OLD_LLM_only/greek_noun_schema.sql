CREATE TABLE books (
    book_id        INTEGER PRIMARY KEY,
    canon_order    INTEGER NOT NULL UNIQUE,
    book_code      TEXT NOT NULL UNIQUE,      -- MAT, MRK, etc.
    book_name      TEXT NOT NULL
);
CREATE TABLE verses (
    verse_id        INTEGER PRIMARY KEY,      -- global ordinal
    book_id         INTEGER NOT NULL,
    chapter_number  INTEGER NOT NULL,
    verse_number    INTEGER NOT NULL,

    UNIQUE (book_id, chapter_number, verse_number),

    FOREIGN KEY (book_id)
        REFERENCES books(book_id)
        ON DELETE CASCADE
);
CREATE TABLE versions (
    version_id     INTEGER PRIMARY KEY,
    version_code   TEXT NOT NULL UNIQUE,      -- TR1550, ESV, OCTB
    language_code  TEXT NOT NULL              -- grc, eng, zho
);
CREATE TABLE verse_texts (
    verse_id    INTEGER NOT NULL,
    version_id  INTEGER NOT NULL,
    verse_text  TEXT NOT NULL,

    PRIMARY KEY (verse_id, version_id),

    FOREIGN KEY (verse_id)
        REFERENCES verses(verse_id)
        ON DELETE CASCADE,

    FOREIGN KEY (version_id)
        REFERENCES versions(version_id)
        ON DELETE CASCADE
);
CREATE TABLE nouns (
    noun_id        INTEGER PRIMARY KEY,
    lemma          TEXT NOT NULL,
    language_code  TEXT NOT NULL,

    UNIQUE (lemma, language_code)
);
CREATE TABLE noun_categories (
    category_id    INTEGER PRIMARY KEY,
    category_code  TEXT NOT NULL UNIQUE      -- GOD, PERSON, PLACE, OTHER
);
CREATE TABLE verse_noun_occurrences (
    occurrence_id  INTEGER PRIMARY KEY,

    verse_id       INTEGER NOT NULL,
    version_id     INTEGER NOT NULL,
    noun_id        INTEGER NOT NULL,

    surface_form   TEXT NOT NULL,
    category_id    INTEGER NOT NULL,

    token_index    INTEGER,        -- position in verse
    confidence     REAL,           -- LLM confidence (0.0 - 1.0)
    needs_review   INTEGER DEFAULT 0 CHECK (needs_review IN (0,1)),

    FOREIGN KEY (verse_id)
        REFERENCES verses(verse_id)
        ON DELETE CASCADE,

    FOREIGN KEY (version_id)
        REFERENCES versions(version_id)
        ON DELETE CASCADE,

    FOREIGN KEY (noun_id)
        REFERENCES nouns(noun_id)
        ON DELETE CASCADE,

    FOREIGN KEY (category_id)
        REFERENCES noun_categories(category_id)
        ON DELETE CASCADE
);
CREATE INDEX idx_occurrence_verse
    ON verse_noun_occurrences (verse_id);
CREATE INDEX idx_occurrence_version
    ON verse_noun_occurrences (version_id);
CREATE INDEX idx_occurrence_noun
    ON verse_noun_occurrences (noun_id);
CREATE INDEX idx_occurrence_category
    ON verse_noun_occurrences (category_id);
