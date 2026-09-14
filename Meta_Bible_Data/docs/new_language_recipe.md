# New Language Recipe

This is the release checklist for bringing a GOI language online. It is the
single list of canonical data, databases, app distribution, and website
destinations. Do not mark a language `active` until every applicable item is
complete.

## 1. Establish the preserved scaffold

1. Create `Meta_Bible_Data/docs/language_scaffolds/<lang>.md` from the intake
   template and commit it first.
2. Preserve the public-domain or licensed comparison edition under
   `Reference_Bible/<Language>_Bible_<Edition>/source/`; create a tracked
   `SOURCE_MANIFEST.json` (copy
   `Meta_Bible_Data/docs/source_manifest_template.json`) containing its file sizes, SHA-256 values, source
   URLs, acquisition date, and verified rights status.
3. Normalize it to `One_Directory_<Edition>_GOI/` with a tracked script and
   create `alignment_exceptions.csv`. Account for all 31,102 GOI/KJV
   coordinates (23,145 OT + 7,957 NT), or explicitly declare partial scope.
4. Build Greek TR1550 NT and WLC/MorphHB OT noun occurrence anchors with
   Strong's numbers and positions. Save language rendering decisions in a
   tracked `<lang>_noun_renderings.csv`, not only in SQLite.
5. Run the scaffold, alignment, noun, and structural checks; append their
   reports to `Meta_Bible_Data/staging/reports/<lang>/`.

## 2. Add GOI metadata and canonical text

1. Add the edition to `Meta_Bible_Data/sqlite/editions.json` with BCP-47 tag,
   output directory, suffix, template edition, `expected_verse_count`, notes,
   and initial `pending` status.
2. Add matching metadata to `Meta_Bible_Data/sqlite/reference_seed.sql`.
3. Create canonical UTF-8 verse files below `GOI_Bible/GOI_Bible_<lang>/`.
   Each filename must use the GOI coordinate and edition suffix; no blank,
   duplicate, or shifted coordinate is permitted.
4. For every discovered translation error, add an append-only row to
   `Meta_Bible_Data/staging/cross_language_regressions.csv`, then review the
   same coordinate/issue class in every active GOI language. Attach an
   evidence receipt for each language before the originating issue is closed.
   Start the review with:

   ```bash
   python3 tools/translation_pipeline/show_cross_language_coordinate.py 001_GEN_001_001
   ```

## 3. Promote and build every derived database

After the corpus is complete and its audit reports pass, change the edition to
`active` in both metadata sources, then run from repository root:

```bash
python3 tools/translation_pipeline/release_edition.py GOI_<ID> \
  --reader-target /var/www/goibible.org/read/data/bible.sqlite3
```

This updates and verifies these derived artifacts:

| Destination | Required action |
|---|---|
| `Meta_Bible_Data/sqlite/versions/GOI_<ID>.sql` | Build from canonical flatfiles |
| `Meta_Bible_Data/sqlite/goi_bible_shell.db` | Rebuild schema/seed shell |
| `Meta_Bible_Data/goi_db_download/GOI_<ID>.db` | Build application-download database |
| `Meta_Bible_Data/goi_db_download/manifest.json` | Publish status, count, size, checksum |
| `Meta_Bible_Data/local_backups/GOI_bible.sqlite3` | Refresh aggregate registry when required by the buffet build |
| `/var/www/goibible.org/read/data/bible.sqlite3` | Rebuild live-reader source from every active manifest edition |

`verify_release_integrity.py` must pass: it compares every active canonical
flatfile corpus byte-for-byte (after normal whitespace trimming) with its
published download DB and confirms the manifest checksum/count.

## 4. Commit, publish, and deploy the reader

Commit source/scaffold work, GOI text/audits, and generated release artifacts
in distinct reviewable commits. Push the release commit to `origin/main`; this
publishes the app payload at:

```
https://raw.githubusercontent.com/goibible/goibible/main/Meta_Bible_Data/goi_db_download/manifest.json
https://raw.githubusercontent.com/goibible/goibible/main/Meta_Bible_Data/goi_db_download/GOI_<ID>.db
```

Android and Windows/desktop discover new editions dynamically at that manifest
path; rebuild an installer only if its code or deliberately bundled assets
change. Verify the client URL rather than assuming an older path is valid.

Deploy the reader only after making a rollback copy on `dsvx`:

```bash
TS=$(date +%Y%m%d-%H%M%S)
ssh dsvx "mkdir -p /var/www/goibible.org/.rollback/${TS}/read/data && \
  cp /var/www/goibible.org/read/data/bible.sqlite3 \
  /var/www/goibible.org/.rollback/${TS}/read/data/bible.sqlite3"
rsync -av --checksum /var/www/goibible.org/read/data/bible.sqlite3 \
  dsvx:/var/www/goibible.org/read/data/bible.sqlite3
ssh dsvx "sqlite3 /var/www/goibible.org/read/data/bible.sqlite3 \
  \"SELECT edition_id,status,COUNT(*) FROM editions JOIN verses USING(edition_id) \
  WHERE edition_id='GOI_<ID>' GROUP BY edition_id,status;\""
```

Record the rollback timestamp, remote query result, release commit, and
manifest checksum in the language scaffold record. Finally check
`https://read.goibible.org/` and the raw GitHub manifest.
