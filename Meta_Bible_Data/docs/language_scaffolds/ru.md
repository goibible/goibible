# Language scaffold intake: `ru` / `GOI_Ru`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolded (Psalms versification resolved; small non-Psalm residual outstanding) |
| GOI edition ID | `GOI_Ru` |
| BCP-47 tag | `ru` |
| Language name (native / English) | русский / Russian |
| Scope | full Bible (reference scaffold only) |
| Scaffold owner | Claude |
| Language reviewer | unresolved |
| Started | 2026-09-16 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | Russian Synodal Bible (Синодальный перевод) / 1876 |
| Source URL | `https://eBible.org/Scriptures/russyn_vpl.zip` |
| Retrieved | 2026-09-16 |
| Licence evidence | `https://ebible.org/find/details.php?id=russyn` (public domain) |
| Jurisdiction and conclusion | eBible explicitly identifies this edition as public domain; preserved for comparison reference only. |
| Rights status | verified public domain |
| GOI use | comparison and noun-rendering reference only, pending versification map |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/Russian_Bible_RUSSYN1876/source/` | 1 | preserved byte-for-byte |
| Normalized reference | `Reference_Bible/Russian_Bible_RUSSYN1876/One_Directory_RUSSYN1876/` | 31,074 | GOI/KJV-coordinate aligned except a 28/30-address non-Psalm residual |
| Psalm versification map | `Reference_Bible/Russian_Bible_RUSSYN1876/psalm_versification_map.csv` | 2,461 GOI addresses + 65 unmapped Russian title verses | status `proposed`; structurally exhaustive, boundary-verified against verse content (8/8 spot checks) |
| Alignment ledger (non-Psalm) | `Reference_Bible/Russian_Bible_RUSSYN1876/alignment_report.json` | 28 absent + 30 Russian-only addresses | small residual (Job, Daniel, Romans, Samuel, Joshua, Song of Songs, Proverbs, etc.), not yet mapped |
| NT noun matcher | `Meta_Bible_Data/Bible_Noun_Extraction/matchers.py::RussianMatcher` | 1 class | registered, self-test passing |
| Source-language noun anchors | not started | 0 | no `ru/` anchor-extraction pipeline yet |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` | header only | not started |
| Audit reports | `Meta_Bible_Data/staging/reports/ru/` | 2 | scaffold-only |

## GOI coordinate alignment

| Measure | Expected | Observed |
|---|---:|---:|
| Full GOI spine | 31,102 | 31,102 |
| Raw Russian source verse markers | n/a | 31,169 |
| Exact address matches (initial, naive) | 31,102 | 30,318 |
| Aligned addresses (after Psalm versification fix) | 31,102 | 31,074 |
| GOI addresses absent from Russian (non-Psalm residual) | 0 | 28 |
| Russian-only addresses (non-Psalm residual) | 0 | 30 |
| Duplicate Russian addresses | 0 | 0 |

Psalms is fully resolved via `psalm_versification_map.csv`, not address
matching -- the Synodal Psalter uses Church-Slavonic/LXX chapter numbering
(9-10 merged, 114-115 merged, 116 split, 147 split, -1 shift elsewhere)
plus a per-Psalm title-verse offset. The initial naive address-match build
silently paired the wrong Russian verse with a GOI address for 1,658 of
1,705 "matched" Psalm flatfiles; this has been corrected and
`atomize_russian_synodal.py` now excludes PSA entirely to prevent
regressing it. See
`Reference_Bible/Russian_Bible_RUSSYN1876/README.md` for the full
methodology and remaining non-Psalm residual.

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-16 | Source/alignment | `atomize_russian_synodal.py --write` | partial (30,318/31,102; mapping required) | `alignment_report.json`, `SOURCE_MANIFEST.json` | 6965c84d49 | Claude |
| 2026-09-16 | NT noun matcher | `matchers.py` self-test + `language_readiness.py --lang ru` | pass (matcher only; renderings/senses/anchors not started) | `Bible_Noun_Extraction/matchers.py`, `staging/reports/ru/scaffold_readiness.md` | 6965c84d49 | Claude |
| 2026-09-16 | Psalms versification | `build_psalm_versification_map.py` + `apply_psalm_versification_map.py` | pass (2,461/2,461 addresses; 8/8 content spot checks) | `psalm_versification_map.csv`, corrected `One_Directory_RUSSYN1876/` | pending | Claude |

## Release record

Not applicable: Russian has no GOI translation, database, or deployed edition.
