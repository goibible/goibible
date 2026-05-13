#!/usr/bin/env python3

import os
import re
import sqlite3
import sys

DB_NAME = "atomic_bible.sqlite3"

FILENAME_REGEX = re.compile(
    r'^(\d{3})_([A-Z0-9]+)_(\d{3})_(\d{3})_([A-Z0-9]+)\.txt$'
)

def derive_testament(conical_int):
    if 1 <= conical_int <= 39:
        return "OT"
    elif 40 <= conical_int <= 66:
        return "NT"
    else:
        raise ValueError(f"Invalid conical number: {conical_int}")


def main(directory):
    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION;")

        for filename in os.listdir(directory):
            if not filename.endswith(".txt"):
                continue

            match = FILENAME_REGEX.match(filename)
            if not match:
                raise ValueError(f"Invalid filename format: {filename}")

            conical_str, book, chapter_str, verse_str, version = match.groups()



            conical = int(conical_str)
            chapter = int(chapter_str)
            verse = int(verse_str)

            testament = derive_testament(conical)

            filepath = os.path.join(directory, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read().strip()

            filename_key = filename[:-4]  # remove .txt

            cursor.execute("""
                INSERT INTO verses (
                    goi,
                    conical,
                    version,
                    book,
                    chapter,
                    verse,
                    testament,
                    filename_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                None,
                conical,
                version,
                book,
                chapter,
                verse,
                testament,
                filename_key
            ))

        conn.commit()
        print("Import completed successfully.")

    except Exception as e:
        conn.rollback()
        print("Import failed. Transaction rolled back.")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bible_into_sqlite.py <directory>")
        sys.exit(1)

    main(sys.argv[1])