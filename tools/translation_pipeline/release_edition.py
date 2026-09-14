#!/usr/bin/env python3
"""Guarded local release for one GOI edition.

It rebuilds the edition's SQL/download DB, rebuilds the reader from every
active manifest edition, then proves flatfile-to-download-DB parity. It does
not deploy to production; use the rollback/rsync command in new_language_recipe.md.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*command: str) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition_id")
    parser.add_argument("--reader-target", help="reader SQLite DB to rebuild; omit to skip reader rebuild")
    args = parser.parse_args()
    run("python3", "tools/translation_pipeline/goi_language_pipeline.py", "check-flatfiles", args.edition_id)
    run("python3", "tools/translation_pipeline/verify_scaffold_manifests.py")
    run("python3", "tools/translation_pipeline/verify_cross_language_audit.py")
    run("python3", "Meta_Bible_Data/sqlite/build_buffet.py", args.edition_id)
    run("bash", "Meta_Bible_Data/sqlite/build_shell.sh")
    run("python3", "Meta_Bible_Data/goi_db_download/build_downloads.py", args.edition_id)
    if args.reader_target:
        run("python3", "tools/build_reader_db.py", "--target", args.reader_target)
    run("python3", "tools/translation_pipeline/verify_release_integrity.py")


if __name__ == "__main__":
    main()
