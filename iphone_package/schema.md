# SQLite schema — GOI Bible edition databases

Each bundled `.db` file in `data/` (`GOI_En.db`, `GOI_vi.db`, `GOI_Zh_Hans.db`, `GOI_Zh_Hant.db`)
carries one Bible edition and shares this schema. Pulled directly from the SQL used against them
in the Android app's `BibleRepo.kt` — not guessed.

## `editions`
One row per edition contained in the file.

| column | type | notes |
|---|---|---|
| `edition_id` | TEXT | primary key, e.g. `GOI_En` |
| `display_name` | TEXT | human-readable name; may be NULL — fall back to `edition_id` |
| `language_subtag` | TEXT | e.g. `en`, `vi`, `zh-Hans`, `zh-Hant` |

## `books`
Canonical book list (shared structure across editions, but only a subset of rows will actually
have verses in any one edition — e.g. WLC-based Hebrew editions are OT-only, TR1550-based Greek
editions are NT-only).

| column | type | notes |
|---|---|---|
| `conical` | INTEGER | canonical book number (spelling is "conical" in the source, not "canonical" — a preexisting typo, kept intentionally for compatibility) |
| `osis` | TEXT | OSIS book code |
| `long_name` | TEXT | default English long name |
| `testament` | TEXT | e.g. `OT` / `NT` |

## `book_names`
Per-edition localized book names (overrides `books.long_name` when present). Not guaranteed to
exist in every source `.db` — the Android app does `CREATE TABLE IF NOT EXISTS` for it at
startup because older DBs predate this table.

| column | type | notes |
|---|---|---|
| `edition_id` | TEXT | part of composite PK |
| `conical` | INTEGER | part of composite PK |
| `name` | TEXT | localized book name, e.g. 創世記 |

Primary key: `(edition_id, conical)`.

## `verses`
The actual text.

| column | type | notes |
|---|---|---|
| `edition_id` | TEXT | |
| `conical` | INTEGER | |
| `chapter` | INTEGER | |
| `verse` | INTEGER | |
| `verse_text` | TEXT | may be NULL — treat as empty string |

Queried as `WHERE edition_id = ? AND conical = ? AND chapter = ? ORDER BY verse`.

## `bookmarks` (app-created, not shipped in the source `.db` files)
Created by the app itself on first launch — not present in the bundled data.

```sql
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id TEXT NOT NULL,
    conical INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE (edition_id, conical, chapter, verse)
)
```

`created_at` is a Unix epoch millis timestamp.

## Search

Full-text-ish search is a plain `LIKE` scan, not FTS5:

```sql
SELECT v.conical, COALESCE(bn.name, b.long_name), v.chapter, v.verse, v.verse_text
FROM verses v JOIN books b ON b.conical = v.conical
LEFT JOIN book_names bn ON bn.conical = v.conical AND bn.edition_id = v.edition_id
WHERE v.edition_id = ? AND v.verse_text LIKE ? ESCAPE '\'
ORDER BY v.conical, v.chapter, v.verse LIMIT 100
```

Query param is `%` + user text with `\`, `%`, `_` escaped + `%`. Keep this exact escaping —
don't switch to FTS5 unless you also verify result parity, since it's a deliberate simplicity
choice in the original.
