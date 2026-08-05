from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edition:
    id: str
    display_name: str
    language: str


@dataclass(frozen=True)
class Book:
    conical: int
    osis: str
    long_name: str
    testament: str


@dataclass(frozen=True)
class Verse:
    num: int
    text: str


@dataclass(frozen=True)
class Bookmark:
    id: int
    edition_id: str
    edition_name: str
    conical: int
    book_name: str
    chapter: int
    verse: int
    text: str
    created_at: int


@dataclass(frozen=True)
class SearchHit:
    conical: int
    book_name: str
    chapter: int
    verse: int
    text: str


@dataclass(frozen=True)
class RandomVerse:
    edition_id: str
    edition_name: str
    conical: int
    book_name: str
    chapter: int
    verse: int
    text: str


class BibleRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self._ensure_book_names_table()
        self._ensure_bookmarks_table()

    def close(self) -> None:
        self.db.close()

    def _ensure_book_names_table(self) -> None:
        with self.db:
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS book_names (
                    edition_id TEXT NOT NULL,
                    conical INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (edition_id, conical),
                    FOREIGN KEY (edition_id) REFERENCES editions (edition_id),
                    FOREIGN KEY (conical) REFERENCES books (conical)
                )
                """
            )

    def _ensure_bookmarks_table(self) -> None:
        with self.db:
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    edition_id TEXT NOT NULL,
                    conical INTEGER NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    UNIQUE (edition_id, conical, chapter, verse)
                )
                """
            )

    def editions(self) -> list[Edition]:
        rows = self.db.execute(
            """
            SELECT edition_id, COALESCE(display_name, edition_id) AS name, language_subtag
            FROM editions
            ORDER BY edition_id
            """
        )
        return [Edition(row["edition_id"], row["name"], row["language_subtag"]) for row in rows]

    def books(self, edition_id: str) -> list[Book]:
        rows = self.db.execute(
            """
            SELECT b.conical, b.osis, COALESCE(n.name, b.long_name) AS long_name, b.testament
            FROM books b
            LEFT JOIN book_names n ON n.edition_id = ? AND n.conical = b.conical
            WHERE EXISTS (
                SELECT 1 FROM verses v
                WHERE v.edition_id = ? AND v.conical = b.conical
            )
            ORDER BY b.conical
            """,
            (edition_id, edition_id),
        )
        return [Book(row["conical"], row["osis"], row["long_name"], row["testament"]) for row in rows]

    def chapter_count(self, edition_id: str, conical: int) -> int:
        row = self.db.execute(
            "SELECT MAX(chapter) AS count FROM verses WHERE edition_id = ? AND conical = ?",
            (edition_id, conical),
        ).fetchone()
        return int(row["count"] or 0)

    def verses(self, edition_id: str, conical: int, chapter: int) -> list[Verse]:
        rows = self.db.execute(
            """
            SELECT verse, verse_text
            FROM verses
            WHERE edition_id = ? AND conical = ? AND chapter = ?
            ORDER BY verse
            """,
            (edition_id, conical, chapter),
        )
        return [Verse(row["verse"], row["verse_text"] or "") for row in rows]

    def search(self, edition_id: str, query: str, limit: int = 100) -> list[SearchHit]:
        if not query.strip():
            return []
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = self.db.execute(
            f"""
            SELECT v.conical, COALESCE(n.name, b.long_name) AS long_name, v.chapter, v.verse, v.verse_text
            FROM verses v
            JOIN books b ON b.conical = v.conical
            LEFT JOIN book_names n ON n.edition_id = v.edition_id AND n.conical = v.conical
            WHERE v.edition_id = ? AND v.verse_text LIKE ? ESCAPE '\\'
            ORDER BY v.conical, v.chapter, v.verse
            LIMIT {int(limit)}
            """,
            (edition_id, f"%{escaped}%"),
        )
        return [
            SearchHit(row["conical"], row["long_name"], row["chapter"], row["verse"], row["verse_text"] or "")
            for row in rows
        ]

    def random_verse(self, edition_id: str) -> RandomVerse | None:
        row = self.db.execute(
            """
            SELECT v.edition_id, COALESCE(e.display_name, v.edition_id) AS edition_name,
                   v.conical, COALESCE(n.name, b.long_name) AS book_name,
                   v.chapter, v.verse, v.verse_text
            FROM verses v
            JOIN editions e ON e.edition_id = v.edition_id
            JOIN books b ON b.conical = v.conical
            LEFT JOIN book_names n ON n.edition_id = v.edition_id AND n.conical = v.conical
            WHERE v.edition_id = ?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (edition_id,),
        ).fetchone()
        if row is None:
            return None
        return RandomVerse(
            row["edition_id"],
            row["edition_name"],
            row["conical"],
            row["book_name"],
            row["chapter"],
            row["verse"],
            row["verse_text"] or "",
        )

    def bookmarked_verses(self, edition_id: str, conical: int, chapter: int) -> set[int]:
        rows = self.db.execute(
            "SELECT verse FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ?",
            (edition_id, conical, chapter),
        )
        return {int(row["verse"]) for row in rows}

    def is_bookmarked(self, edition_id: str, conical: int, chapter: int, verse: int) -> bool:
        row = self.db.execute(
            """
            SELECT 1 FROM bookmarks
            WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?
            """,
            (edition_id, conical, chapter, verse),
        ).fetchone()
        return row is not None

    def add_bookmark(self, edition_id: str, conical: int, chapter: int, verse: int) -> None:
        with self.db:
            self.db.execute(
                """
                INSERT OR IGNORE INTO bookmarks (edition_id, conical, chapter, verse, created_at)
                VALUES (?, ?, ?, ?, CAST(strftime('%s', 'now') AS INTEGER))
                """,
                (edition_id, conical, chapter, verse),
            )

    def remove_bookmark(self, edition_id: str, conical: int, chapter: int, verse: int) -> None:
        with self.db:
            self.db.execute(
                """
                DELETE FROM bookmarks
                WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?
                """,
                (edition_id, conical, chapter, verse),
            )

    def remove_bookmark_id(self, bookmark_id: int) -> None:
        with self.db:
            self.db.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))

    def bookmarks_near(self, edition_id: str, conical: int, chapter: int) -> list[Bookmark]:
        rows = self.db.execute(
            """
            SELECT bm.id, bm.edition_id, COALESCE(e.display_name, bm.edition_id) AS edition_name,
                   bm.conical, COALESCE(n.name, b.long_name) AS book_name,
                   bm.chapter, bm.verse, COALESCE(v.verse_text, '') AS verse_text, bm.created_at
            FROM bookmarks bm
            JOIN editions e ON e.edition_id = bm.edition_id
            JOIN books b ON b.conical = bm.conical
            LEFT JOIN book_names n ON n.edition_id = bm.edition_id AND n.conical = bm.conical
            LEFT JOIN verses v ON v.edition_id = bm.edition_id
                AND v.conical = bm.conical
                AND v.chapter = bm.chapter
                AND v.verse = bm.verse
            """
        )
        bookmarks = [
            Bookmark(
                row["id"],
                row["edition_id"],
                row["edition_name"],
                row["conical"],
                row["book_name"],
                row["chapter"],
                row["verse"],
                row["verse_text"],
                row["created_at"],
            )
            for row in rows
        ]
        return sorted(
            bookmarks,
            key=lambda item: (
                0 if item.edition_id == edition_id else 1,
                0 if item.conical == conical else 1,
                0 if item.chapter == chapter else 1,
                abs(item.conical - conical),
                abs(item.chapter - chapter),
                item.verse,
                -item.created_at,
            ),
        )

    def merge_from(self, source: Path) -> str:
        source = source.resolve()
        alias = "src"
        try:
            self.db.execute(f"ATTACH DATABASE ? AS {alias}", (str(source),))
            count = self.db.execute(
                """
                SELECT count(*) AS count
                FROM src.sqlite_master
                WHERE type = 'table' AND name IN ('editions', 'verses')
                """
            ).fetchone()["count"]
            if count != 2:
                raise ValueError("Not an edition database; missing editions or verses table.")

            names = [
                f"{row['edition_id']} - {row['name']}"
                for row in self.db.execute(
                    "SELECT edition_id, COALESCE(display_name, edition_id) AS name FROM src.editions"
                )
            ]
            with self.db:
                self.db.execute("INSERT OR IGNORE INTO books SELECT * FROM src.books")
                self.db.execute("INSERT OR REPLACE INTO editions SELECT * FROM src.editions")
                if self._source_has_table(alias, "book_names"):
                    self.db.execute("INSERT OR REPLACE INTO book_names SELECT * FROM src.book_names")
                self.db.execute("INSERT OR REPLACE INTO verses SELECT * FROM src.verses")
            return ", ".join(names)
        finally:
            try:
                self.db.execute(f"DETACH DATABASE {alias}")
            except sqlite3.Error:
                pass

    def import_copy(self, source: Path, target_dir: Path) -> str:
        target = target_dir / "import.db"
        shutil.copy2(source, target)
        try:
            return self.merge_from(target)
        finally:
            target.unlink(missing_ok=True)

    def remove_edition(self, edition_id: str) -> None:
        with self.db:
            self.db.execute("DELETE FROM bookmarks WHERE edition_id = ?", (edition_id,))
            self.db.execute("DELETE FROM book_names WHERE edition_id = ?", (edition_id,))
            self.db.execute("DELETE FROM verses WHERE edition_id = ?", (edition_id,))
            self.db.execute("DELETE FROM editions WHERE edition_id = ?", (edition_id,))

    def _source_has_table(self, alias: str, table_name: str) -> bool:
        row = self.db.execute(
            f"SELECT 1 FROM {alias}.sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None
