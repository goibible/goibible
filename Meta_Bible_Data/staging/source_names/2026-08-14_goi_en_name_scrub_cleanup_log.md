# GOI English Name Scrub Cleanup Log

Date: 2026-08-14

Scope: reduce the `goi_en_kjv_webus_name_scrub.csv` active review queue by category rather than one-off row edits.

Baseline before this pass:

- Source-name occurrences audited: 42,322
- Flagged occurrences: 5,482
- Active review occurrences: 4,869
- Accepted policy occurrences: 605
- Documented closures: 8

## Pass 1: Deterministic Policy Closures

Added generated policy closures for categories that do not indicate GOI English verse debt:

- Reference-witness gaps where GOI has the source-name candidate but KJV or WEBUS has no comparable form.
- Known proper-name spelling, alias, or demonym variants already present in the source-name lexicon.
- Narrow YHWH/Yehovih title-style variants.
- Narrow NT title/reference variants such as Holy Ghost/Holy Spirit, inscription casing, Christ/Messiah, and lord/master/sir/owner.

Result after pass 1:

- Active review occurrences: 372
- Accepted policy occurrences: 5,102
- Documented closures: 8

Remaining active rows are all divine/title-sensitive and concentrated in:

- H136 Adonai
- H430 Elohim
- H5945 Elyon
- H410 El
- G2316 Theos
- G2962 Kyrios
- H433 Eloah
- H7706 Shaddai

## Pass 2: H136 Adonai Policy Closure

Reviewed `H136` / Adonai rows where the source distinction was masked by English title casing.
An initial casing edit pass was rejected because mixed-title verses can contain both `H3068` / YHWH and `H136` / Adonai, and an unaligned string replacement can touch the wrong occurrence.

Closed this category as metadata policy instead:

- `Lord`, `LORD`, `O Lord`, `O LORD`, and possessive/article variants are accepted as English title-style renderings for the same `H136` source entity.
- No broad H136 verse-casing edits are committed in this cleanup.

Validation after this pass:

- `python3 tools/validate.py` passed all 13 checks.

Result after DB rebuild and scrub regeneration:

- Flagged occurrences: 5,459
- Active review occurrences: 0
- Accepted policy occurrences: 5,451
- Documented closures: 8

## Pass 3: Divine/Common-Noun Sense Fixes

Applied targeted verse edits for remaining obvious sense mismatches where the source and both reference witnesses supported a correction.

Examples:

- `my god` -> `my gods` in Genesis 31:30.
- `the gods of Ekron` -> `the god of Ekron` in 2 Kings 1:2.
- `sons of the gods` -> `sons of God` in Job 1:6 and Job 2:1.
- `divine fire` -> `fire of God` in Job 1:16.
- `curse his king and his gods` -> `curse his king and his God` in Isaiah 8:21.

Validation after this pass:

- `python3 tools/validate.py` passed all 13 checks.

## Pass 4: Final Policy Closures

Added generated closures for the remaining non-actionable categories:

- Shared source-entity candidate present in all witnesses, where the single-form matcher picked different valid words in the same verse.
- Context-sensitive source-valid divine/common-noun renderings such as `Shaddai`/`Almighty`, `divine beings`/`angels`, `Most High`/`highest`, and `according to God`/`godly`.
- One-reference disagreements where GOI already agrees with either KJV or WEBUS.

Final result after scrub regeneration:

- Source-name occurrences audited: 42,322
- Flagged occurrences: 5,459
- OK occurrences: 36,863
- Active review occurrences: 0
- Accepted policy occurrences: 5,451
- Documented closures: 8
- Active `no_goi_form` occurrences: 0

The raw flagged rows remain in `goi_en_kjv_webus_name_scrub.csv` for traceability, but none remain active.

## Artifact Rebuild and Verification

Rebuilt downstream artifacts after the English flatfile edits:

- Markdown Bible exports via `generate_markdown_bible.py --all --overwrite`.
- SQL version buffet via `build_buffet.py`.
- Shell database via `build_shell.sh`.
- Combined local backup database via `assemble.sh`.
- Per-edition split databases via `split_editions.sh`.
- Download manifest/databases via `build_downloads.py`.

Verification:

- `python3 tools/validate.py` -> all 13 checks passed.
- `python3 tools/validate_zh.py --variant both` -> all 25 checks passed.
- `Meta_Bible_Data/local_backups/GOI_bible.sqlite3` counts:
  - GOI_En: 31,102
  - GOI_Zh_Hans: 31,102
  - GOI_Zh_Hant: 31,102
  - GOI_vi: 31,102
  - KJV: 31,102
  - WEBUS: 31,102
  - TR1550: 7,957
  - WLC: 23,145
- Split edition DB counts match their expected verse totals.
- Shell DB intentionally has 0 verses.
