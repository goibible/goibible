# Codex BCP47 Migration Plan

## Summary
- Source database remains unchanged: `atomic_bible.sqlite3`.
- New migrated database is created: `bcp_bible.sqlite3`.
- Edition identity (`CUV`, `KJV`, `WEBUS`, `TR1550`, `WLC`) is preserved as `edition_id`.
- Language identity is attached separately through BCP47 (`bcp47_tag`) and base language (`language_subtag`).
- `goi` (Global Ordinal Index) remains first-class for universal cross-edition search.

## Implemented Design
- Added `editions` table to separate edition identity from language identity.
- Added new `verses` schema in target DB with:
  - `edition_id` for edition identity
  - `language_subtag` for fast language grouping
  - retained `version` for compatibility reads
  - `goi` indexed for universal search/join
- Added `verses_legacy` view exposing the old shape with `version` for compatibility.
- Copied `books`, `iso_languages`, `iso_scripts`, `iso_regions` into target DB.
- Added `PENDING_6TH` row in `editions` as placeholder for the sixth Bible.

## Canonical Edition-to-Language Mapping
- `CUV -> zh`
- `KJV -> en`
- `WEBUS -> en-US` (base language: `en`)
- `TR1550 -> el`
- `WLC -> he`

## Build Steps
1. Remove any stale target database:
   - `rm -f bcp_bible.sqlite3`
2. Create new target database using migration script:
   - `sqlite3 bcp_bible.sqlite3 < migrate_to_bcp47.sql`

## Verification Queries
1. Per-edition verse counts:
   - `SELECT edition_id, COUNT(*) FROM verses GROUP BY edition_id ORDER BY edition_id;`
2. Mapping check:
   - `SELECT edition_id, bcp47_tag, language_subtag, status FROM editions ORDER BY edition_id;`
3. GOI integrity by edition:
   - `SELECT edition_id, MIN(goi), MAX(goi), COUNT(*) FROM verses GROUP BY edition_id ORDER BY edition_id;`
4. Cross-edition GOI search example:
   - `SELECT v1.goi, v1.edition_id, v2.edition_id FROM verses v1 JOIN verses v2 ON v1.goi = v2.goi WHERE v1.edition_id = 'KJV' AND v2.edition_id = 'WEBUS' LIMIT 20;`
5. Legacy compatibility shape:
   - `SELECT * FROM verses_legacy LIMIT 5;`

## Notes
- This migration is intentionally non-destructive and does not alter `atomic_bible.sqlite3`.
- The placeholder edition `PENDING_6TH` is metadata only and has no verse rows until the sixth Bible is imported.
