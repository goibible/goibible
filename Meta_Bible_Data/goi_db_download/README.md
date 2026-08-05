# GOI DB Download

Import-ready SQLite databases for the GOI Bible Android and desktop apps.

Each `*.db` file is a self-contained SQLite database for one Bible edition. The
database is built from `sqlite/goi_bible_shell.db` plus one source SQL file from
`sqlite/versions/`.

Use `manifest.json` from the apps to discover the available downloads, display
names, BCP 47 tags, file sizes, checksums, and verse counts.

## Rebuild

From the repo root:

```bash
python3 goi_db_download/build_downloads.py
```

This regenerates every `*.db` file and rewrites `manifest.json`.

To stage a specific language edition from flatfiles through SQL and the
download DB:

```bash
python3 scripts/goi_language_pipeline.py stage GOI_vi
```

The source-of-truth metadata for generated editions is
`sqlite/editions.json`; app-facing downloads stay in this directory.
