# Language scaffold intake: `ru` / `GOI_Ru`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolded (versification mapping outstanding) |
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
| Normalized reference | `Reference_Bible/Russian_Bible_RUSSYN1876/One_Directory_RUSSYN1876/` | 30,318 | GOI/KJV-coordinate matches only (not full spine) |
| Alignment ledger | `Reference_Bible/Russian_Bible_RUSSYN1876/alignment_report.json` | 784 absent + 851 Russian-only addresses | needs a hand-built versification map, not yet an exceptions ledger |
| NT noun matcher | `Meta_Bible_Data/Bible_Noun_Extraction/matchers.py::RussianMatcher` | 1 class | registered, self-test passing |
| Source-language noun anchors | not started | 0 | no `ru/` anchor-extraction pipeline yet |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` | header only | not started |
| Audit reports | `Meta_Bible_Data/staging/reports/ru/` | 2 | scaffold-only |

## GOI coordinate alignment

| Measure | Expected | Observed |
|---|---:|---:|
| Full GOI spine | 31,102 | 31,102 |
| Raw Russian source verse markers | n/a | 31,169 |
| Exact address matches | 31,102 | 30,318 |
| GOI addresses absent from Russian | 0 | 784 (756 in Psalms) |
| Russian-only addresses (no GOI match) | 0 | 851 (821 in Psalms) |
| Duplicate Russian addresses | 0 | 0 |

This is overwhelmingly a Psalm-division/numbering difference in the Synodal
tradition, not missing content -- see
`Reference_Bible/Russian_Bible_RUSSYN1876/README.md` for the book-by-book
breakdown. It is a mapping project, not a completeness problem.

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-16 | Source/alignment | `atomize_russian_synodal.py --write` | partial (30,318/31,102; mapping required) | `alignment_report.json`, `SOURCE_MANIFEST.json` | pending | Claude |
| 2026-09-16 | NT noun matcher | `matchers.py` self-test + `language_readiness.py --lang ru` | pass (matcher only; renderings/senses/anchors not started) | `Bible_Noun_Extraction/matchers.py`, `staging/reports/ru/scaffold_readiness.md` | pending | Claude |

## Release record

Not applicable: Russian has no GOI translation, database, or deployed edition.
