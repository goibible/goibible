# GOI Bible

Full-Bible GOI editions in English, Simplified Chinese, and Traditional
Chinese, plus a diffable SQLite distribution. Each GOI edition contains 31,102
verse files covering Genesis through Revelation.

## Start here
- **Provenance, verification, and copyright notes:** `README_GOI.md`
  in the public GitHub repo, or `docs/README_GOI.md` in the full working
  source tree.
- **Single-file reading copies:** `full_bible/GOI_English_Bible.md`,
  `GOI_Simplified_Chinese_Bible.md`, `GOI_Traditional_Chinese_Bible.md`
- **Queryable SQLite data:** `sqlite/goi_bible_shell.db` plus
  `sqlite/versions/*.sql`

## Top-level layout
| Path | What |
| --- | --- |
| `GOI_Bible_English/`, `GOI_Bible_Chinese_Hans/`, `GOI_Bible_Chinese_Hant/` | finished full-Bible editions (31,102 verse files each) |
| `full_bible/` | consolidated single-markdown-file exports of each GOI edition + the generator script |
| `README_GOI.md` | provenance, verification, and copyright notes for the GOI editions |
| `sqlite/` | SQLite schema, reference seed data, import-ready shell DB, and one SQL import file per edition |

The full private/working source tree also contains translation-pipeline tools,
reference corpora, audit logs, and notes. The public GitHub repo is intentionally
smaller: it publishes the finished corpora and the diffable SQLite data needed
to inspect or rebuild release databases.

## SQLite distribution

Git tracks the diffable SQL source, not generated release databases.

- `sqlite/goi_bible_shell.db` is a small import-ready SQLite database with the
  schema and reference tables already loaded, but zero verse rows.
- `sqlite/versions/<edition>.sql` files are plain-text imports for each edition:
  `GOI_En`, `GOI_Zh_Hans`, `GOI_Zh_Hant`, `KJV`, `WEBUS`, `TR1550`, and `WLC`.
- Generated `.db`, `.sqlite3`, and app binaries belong in GitHub Releases or a
  download bucket, not normal Git history.

To build a full database locally:

```sh
cd sqlite
./assemble.sh ../GOI_bible.sqlite3
```

To build only selected editions:

```sh
cd sqlite
./assemble.sh ../GOI_bible_en.sqlite3 GOI_En
```

To import manually, copy `sqlite/goi_bible_shell.db` and load one or more
`sqlite/versions/*.sql` files into the copy:

```sh
cp sqlite/goi_bible_shell.db GOI_bible_en.db
sqlite3 GOI_bible_en.db < sqlite/versions/GOI_En.sql
```
