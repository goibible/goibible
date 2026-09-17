# Language scaffold intake: `ru` / `GOI_Ru`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolded, FULLY versification-aligned (100%: 66/66 books, 1,189/1,189 chapters, 31,102/31,102 verses) |
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
| GOI use | comparison and noun-rendering reference; versification fully resolved and verified |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/Russian_Bible_RUSSYN1876/source/` | 1 | preserved byte-for-byte |
| Normalized reference | `Reference_Bible/Russian_Bible_RUSSYN1876/One_Directory_RUSSYN1876/` | 31,102 | **100% GOI/KJV-coordinate aligned** (verified: `verify_output_alignment.py`) |
| Full versification audit | `Reference_Bible/Russian_Bible_RUSSYN1876/full_versification_audit_summary.md` | 1,189 chapters checked | every chapter, Hebrew WLC (OT) / Greek TR1550 (NT) vs Russian source, not sampled |
| Psalm versification map | `Reference_Bible/Russian_Bible_RUSSYN1876/psalm_versification_map.csv` | 2,461 GOI addresses + 65 unmapped Russian title verses | content-verified at every merge/split boundary (8/8 checks) |
| Non-Psalm versification map | `Reference_Bible/Russian_Bible_RUSSYN1876/non_psalm_versification_map.csv` | 300 rows across 16 books | content-verified at every shift/merge/relocation boundary (both endpoints, every range) |
| NT noun matcher | `Meta_Bible_Data/Bible_Noun_Extraction/matchers.py::RussianMatcher` | 1 class | registered, self-test passing |
| Source-language noun anchors | not started | 0 | no `ru/` anchor-extraction pipeline yet |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` | header only | not started |
| Audit reports | `Meta_Bible_Data/staging/reports/ru/` | 2 | scaffold-only |

## GOI coordinate alignment

| Measure | Expected | Observed |
|---|---:|---:|
| Full GOI spine | 31,102 | **31,102** |
| OT spine (Hebrew WLC) | 23,145 | **23,145** |
| NT spine (Greek TR1550) | 7,957 | **7,957** |
| Psalms | 2,461 | **2,461** |
| Chapters matching exactly | 1,189 | **1,189** |
| Duplicate/extra Russian addresses | 0 | **0** |
| Missing GOI addresses | 0 | **0** |

Fully resolved via two verified maps, not address matching:
- **Psalms**: the Synodal Psalter uses Church-Slavonic/LXX chapter
  numbering (9-10 merged, 114-115 merged, 116 split, 147 split, -1 shift
  elsewhere) plus a per-Psalm title-verse offset.
- **16 more books** (1 Samuel, 2 Corinthians, 3 John, Acts, Daniel,
  Ecclesiastes, Hosea, Isaiah, Job, Jonah, Joshua, Leviticus, Numbers,
  Proverbs, Romans, Song of Songs): chapter-boundary shifts, verse
  merges, Job's 3-chapter Behemoth/Leviathan re-division, and a
  relocated Romans doxology.

The initial naive address-match build silently paired the wrong Russian
verse with a GOI address for 1,658/1,705 "matched" Psalm flatfiles plus
more across the 16 other books -- this has been corrected, and
`atomize_russian_synodal.py` now excludes all 17 versification-mapped
books from its naive matcher to prevent regressing it. Full methodology
in `Reference_Bible/Russian_Bible_RUSSYN1876/README.md`.

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-16 | Source/alignment | `atomize_russian_synodal.py --write` | partial (30,318/31,102; mapping required) | `alignment_report.json`, `SOURCE_MANIFEST.json` | 6965c84d49 | Claude |
| 2026-09-16 | NT noun matcher | `matchers.py` self-test + `language_readiness.py --lang ru` | pass (matcher only; renderings/senses/anchors not started) | `Bible_Noun_Extraction/matchers.py`, `staging/reports/ru/scaffold_readiness.md` | 6965c84d49 | Claude |
| 2026-09-16 | Psalms versification | `build_psalm_versification_map.py` + `apply_psalm_versification_map.py` | pass (2,461/2,461 addresses; 8/8 content spot checks) | `psalm_versification_map.csv`, corrected `One_Directory_RUSSYN1876/` | c28c93c145 | Claude |
| 2026-09-16 | Full versification alignment | `build_full_versification_audit.py` + `build_non_psalm_versification_map.py` + `apply_non_psalm_versification_map.py` + `verify_output_alignment.py` | **pass: 100%, 1,189/1,189 chapters, 31,102/31,102 verses** | `full_versification_audit_summary.md`, `output_alignment_by_chapter.csv` | pending | Claude |

## Release record

Not applicable: Russian has no GOI translation, database, or deployed edition.
