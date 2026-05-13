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