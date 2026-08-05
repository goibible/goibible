# Vietnamese Bible VIE1934 Reference

Public-domain Vietnamese reference Bible from eBible.org, downloaded for QA
reference use while producing a new GOI Vietnamese edition.

Source pages:

- `https://ebible.org/find/details.php?id=vie1934`
- `https://ebible.org/vie1934/copyright.htm`

Downloaded artifacts:

- `ZIP/vie1934_readaloud.zip` - plain text canon-only chapter files
- `ZIP/vie1934_usfm.zip` - structured USFM files
- `SOURCE/details.html` - eBible details page
- `SOURCE/copyright.htm` - public-domain license/provenance page
- `SOURCE/readaloud/` - extracted chapter text files
- `SOURCE/usfm/` - extracted USFM files

License/provenance summary from eBible:

- Title: `Kinh Thánh`
- Language: `Tiếng Việt (Vietnamese)`
- eBible ID: `vie1934`
- Translation by: William Cadman
- Contributor: Christian and Missionary Alliance
- Public Domain

This reference is for comparison and QA only. The GOI Vietnamese edition should
be translated from WLC/TR1550 source texts, not copied from this reference.

## GOI Vietnamese target naming

- Corpus directory: `GOI_Bible_vi`
- Edition id: `GOI_vi`
- BCP 47 tag: `vi`
- Native display name: `Tiếng Việt - Kinh Thánh GOI`
- Verse filename shape: `NNN_BOOK_CCC_VVV_GOI_vi.txt`
- Example: `040_MAT_001_001_GOI_vi.txt`
- SQLite import: `sqlite/versions/GOI_vi.sql`
- Download DB: `goi_db_download/GOI_vi.db`

## Pipeline

Durable edition metadata lives in `sqlite/editions.json`. The repeatable staging
command is:

```bash
python3 scripts/goi_language_pipeline.py stage GOI_vi
```

That command checks flatfile count and names, normalizes the corpus, runs
Vietnamese noun readiness and coverage, builds `sqlite/versions/GOI_vi.sql`,
rebuilds the shell DB metadata, creates `goi_db_download/GOI_vi.db`, and refreshes
`goi_db_download/manifest.json`.
- Markdown export: `full_bible/GOI_Vietnamese_Bible.md`

Use VIE1934 for public-domain Vietnamese book names, reading-flow comparison,
and QA checks. Do not use its eBible file naming for GOI output.
