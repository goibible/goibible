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
| 2026-09-20 | OT translation | `ru/translate_ot_ru.py` (per-verse noun-anchor retry, single stream) | pass: 23,145/23,145 verses | `GOI_Bible/GOI_Bible_ru` | 832165458d | Claude |
| 2026-09-23 | OT triage + wrong-sense | `ru/triage_ot.py`, `ru/check_defaults_ot.py`, `ru/sweep_senses_ot.py`, `ru/fix_senses_ot.py` + hand review | **pass: RED/ORANGE/YELLOW 0, GREEN 23,145; sense state 6,220 fixed / 948 kept / 0 open** | `staging/.../ru/reports/triage_ot_summary.md`, `ru/sense_fix_state.tsv` | 142d0e2 (nested) | Claude |
| 2026-09-23 | NT coverage + wrong-sense | `verify_coverage.py --lang ru`, `ru/sweep_senses_nt.py`, `ru/check_defaults_nt.py`, `ru/fix_senses_nt.py` + hand review | **pass: coverage 100%; sense state 429 fixed / 65 kept / 0 open** | `ru/sense_fix_state_nt.tsv` | d522079 (nested) | Claude |
| 2026-09-23 | Script gate | `verify_language_script.py GOI_Ru` (now with `forbidden_chars` і ї є ґ ў) | pass (ACT 15:23 had been Ukrainian; rewritten) | `translation_qa/script_profiles.json` | 81191076ce | Claude |
| 2026-09-23 | Renderings ledger | export to `Bible_Noun_Extraction/ru_noun_renderings.csv` | 2,369 NT + 6,488 OT, 0 empty | `ru_noun_renderings.csv` | this release | Claude |
| 2026-09-23 | Release (local) | `release_edition.py GOI_Ru --reader-target /var/www/goibible.org/read/data/bible.sqlite3` | pass: flatfiles 31,102; manifests OK; cross-language audit OK; RELEASE INTEGRITY OK (13 active) | `goi_db_download/GOI_Ru.db`, `manifest.json` | this release | Claude |

## Release record

Status **active** (2026-09-23). Local release built and verified; manifest checksum `519f3f9ee4d1b43c25e62057ddfd680bc55197dc96b2be637313701513fd2618`.
Not yet pushed to GitHub and not yet deployed to `dsvx` (awaiting owner go-ahead); record the rollback
timestamp and remote query here when deployed.

Unmet checklist items, stated plainly: no native-speaker semantic review (AI review only); the
cross-language regression ledger was not used for these Russian-specific default fixes (same precedent
as GOI_Ja/GOI_Ko). From activation on, any changed Russian verse must be entered in
`staging/cross_language_regressions.csv` first.
