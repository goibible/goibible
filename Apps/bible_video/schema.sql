PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS corpus_chapters (
    id INTEGER PRIMARY KEY,
    book_number INTEGER NOT NULL CHECK (book_number BETWEEN 1 AND 66),
    osis_code TEXT NOT NULL,
    book_name TEXT NOT NULL,
    testament TEXT NOT NULL CHECK (testament IN ('OT', 'NT')),
    chapter_number INTEGER NOT NULL CHECK (chapter_number > 0),
    verse_count INTEGER NOT NULL CHECK (verse_count > 0),
    language TEXT NOT NULL DEFAULT 'English',
    language_code TEXT NOT NULL DEFAULT 'en',
    translation TEXT NOT NULL DEFAULT 'GOI Bible',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (book_number, chapter_number, language_code, translation),
    UNIQUE (osis_code, chapter_number, language_code, translation)
);

CREATE TABLE IF NOT EXISTS media_assets (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES corpus_chapters(id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL UNIQUE,
    duration_seconds REAL NOT NULL CHECK (duration_seconds > 0),
    duration_display TEXT NOT NULL CHECK (duration_display GLOB '[0-9]*:[0-5][0-9]'),
    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0),
    sha256 TEXT NOT NULL UNIQUE CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    fps REAL NOT NULL CHECK (fps > 0),
    audio_codec TEXT NOT NULL,
    video_codec TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (chapter_id),
    CHECK (relative_path NOT LIKE '/%'),
    CHECK (relative_path NOT LIKE '%/../%' AND relative_path NOT LIKE '../%'),
    CHECK (relative_path LIKE 'output/%')
);

CREATE TABLE IF NOT EXISTS youtube_distribution (
    id INTEGER PRIMARY KEY,
    media_asset_id INTEGER NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
    youtube_title TEXT NOT NULL,
    youtube_description TEXT NOT NULL,
    youtube_tags TEXT NOT NULL DEFAULT '[]',
    youtube_playlist TEXT,
    youtube_video_id TEXT UNIQUE,
    youtube_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (youtube_status IN ('pending', 'ready', 'uploading', 'uploaded', 'failed', 'skipped', 'private', 'unlisted', 'public')),
    uploaded_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (media_asset_id),
    CHECK (json_valid(youtube_tags)),
    CHECK ((youtube_status IN ('uploaded', 'private', 'unlisted', 'public')) = (youtube_video_id IS NOT NULL AND uploaded_at IS NOT NULL)
        OR youtube_status NOT IN ('uploaded', 'private', 'unlisted', 'public'))
);

CREATE TRIGGER IF NOT EXISTS youtube_distribution_updated_at
AFTER UPDATE ON youtube_distribution
FOR EACH ROW
BEGIN
    UPDATE youtube_distribution
    SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = NEW.id;
END;

CREATE INDEX IF NOT EXISTS idx_corpus_chapters_book_chapter
    ON corpus_chapters(book_number, chapter_number);

CREATE INDEX IF NOT EXISTS idx_media_assets_chapter_id
    ON media_assets(chapter_id);

CREATE INDEX IF NOT EXISTS idx_media_assets_relative_path
    ON media_assets(relative_path);

CREATE INDEX IF NOT EXISTS idx_youtube_distribution_status
    ON youtube_distribution(youtube_status);

CREATE INDEX IF NOT EXISTS idx_youtube_distribution_uploaded_at
    ON youtube_distribution(uploaded_at);

INSERT OR IGNORE INTO schema_migrations(version) VALUES (1);
