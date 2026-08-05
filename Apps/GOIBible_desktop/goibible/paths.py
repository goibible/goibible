from __future__ import annotations

import shutil
import sqlite3
import sys
import hashlib
import json
from pathlib import Path


APP_NAME = "GOIBible"
BUNDLE_SYNC_VERSION = 2


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / "goibible" / "resources"
    return Path(__file__).resolve().parent / "resources"


def data_root() -> Path:
    root = app_root() / "data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def bundled_db() -> Path:
    return resource_root() / "GOI_En.db"


def bundled_databases() -> list[Path]:
    return sorted(resource_root().glob("*.db"))


def working_db() -> Path:
    target = data_root() / "bible.db"
    if not target.exists():
        shutil.copy2(bundled_db(), target)
    merge_bundled_databases(target)
    return target


def applied_bundles_file() -> Path:
    return data_root() / "bundled_editions.json"


def file_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merge_bundled_databases(target: Path) -> None:
    dbs = [db for db in bundled_databases() if db.resolve() != target.resolve()]
    if not dbs:
        return

    applied_path = applied_bundles_file()
    try:
        applied = json.loads(applied_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        applied = {}

    conn = sqlite3.connect(str(target))
    try:
        ensure_book_names_table(conn)
        for index, source in enumerate(dbs):
            fingerprint = f"v{BUNDLE_SYNC_VERSION}:{file_fingerprint(source)}"
            if applied.get(source.name) == fingerprint:
                continue
            alias = f"bundle{index}"
            conn.execute(f"ATTACH DATABASE ? AS {alias}", (str(source),))
            try:
                count = conn.execute(
                    f"""
                    SELECT count(*)
                    FROM {alias}.sqlite_master
                    WHERE type = 'table' AND name IN ('books', 'editions', 'verses')
                    """
                ).fetchone()[0]
                if count != 3:
                    continue
                with conn:
                    conn.execute(f"INSERT OR IGNORE INTO books SELECT * FROM {alias}.books")
                    conn.execute(f"INSERT OR REPLACE INTO editions SELECT * FROM {alias}.editions")
                    if source_has_table(conn, alias, "book_names"):
                        conn.execute(f"INSERT OR REPLACE INTO book_names SELECT * FROM {alias}.book_names")
                    conn.execute(f"INSERT OR REPLACE INTO verses SELECT * FROM {alias}.verses")
                applied[source.name] = fingerprint
            finally:
                conn.execute(f"DETACH DATABASE {alias}")
    finally:
        conn.close()
    applied_path.write_text(json.dumps(applied, indent=2, sort_keys=True), encoding="utf-8")


def ensure_book_names_table(conn: sqlite3.Connection) -> None:
    conn.execute(
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


def source_has_table(conn: sqlite3.Connection, alias: str, table_name: str) -> bool:
    return conn.execute(
        f"SELECT 1 FROM {alias}.sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


def settings_file() -> Path:
    return data_root() / "settings.json"


def font_file() -> Path:
    return resource_root() / "literata.ttf"


def icon_file() -> Path:
    return resource_root() / "goibible-icon.png"
