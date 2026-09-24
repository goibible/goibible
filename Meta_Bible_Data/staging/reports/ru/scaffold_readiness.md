# Russian Synodal scaffold readiness — 2026-09-16 (fully versification-aligned)

| Gate | Result | Evidence |
|---|---|---|
| Provenance | pass | `Reference_Bible/Russian_Bible_RUSSYN1876/SOURCE_MANIFEST.json` |
| Raw source inventory | pass | 66 books; 31,169 unique source verse markers; no duplicates. |
| Full versification audit | **pass** | `build_full_versification_audit.py`: every chapter (1,189/1,189) of Hebrew WLC (OT) and Greek TR1550 (NT) compared directly against the Russian source, not sampled. 172 chapters flagged (138 Psalms + 34 across 16 other books) -- see `full_versification_audit_summary.md`. |
| GOI alignment | **pass -- 100%** | `verify_output_alignment.py`: `One_Directory_RUSSYN1876/` covers all 31,102 GOI/KJV spine addresses exactly -- 66/66 books, 1,189/1,189 chapters, 0 missing, 0 extra, 0 duplicates. See `output_alignment_by_chapter.csv`. |
| Psalms versification | pass | `psalm_versification_map.csv`: all 2,461 KJV/GOI Psalm addresses mapped via the documented Church-Slavonic/LXX chapter correspondence + per-Psalm title-verse offset, content-verified at every merge/split boundary (8/8 checks). |
| Non-Psalm versification | pass | `non_psalm_versification_map.csv`: 300 rows resolving 16 books (1 Samuel, 2 Corinthians, 3 John, Acts, Daniel, Ecclesiastes, Hosea, Isaiah, Job, Jonah, Joshua, Leviticus, Numbers, Proverbs, Romans, Song of Songs), each boundary content-verified at both endpoints. 6 genuine Byzantine/LXX textual additions (Joshua 24:34-36, Proverbs 4:28-29, 13:14) have no GOI counterpart and are logged, not force-mapped. |
| Bug fixed | -- | Naive address matching had silently paired the wrong Russian verse with a GOI address for 1,658/1,705 "matched" Psalm flatfiles plus more across the 16 other books (any within-chapter shift mis-pairs every verse from the shift point onward, not just the boundary). Fixed; `atomize_russian_synodal.py` now excludes all 17 versification-mapped books from its naive matcher so a rerun can't reintroduce it. |
| NT noun matcher | pass | `RussianMatcher` registered in `matchers.py`, self-test passing (coarse case-ending stem match; grow `_ACCEPTABLE_FORMS` from real coverage runs once translation starts). |
| Source-language noun anchors | not started | No `Meta_Bible_Data/Bible_Noun_Extraction/ru/` anchor-extraction pipeline exists yet (compare `.../ar/build_ar_source_noun_anchors.py`). |
| Russian renderings | not started | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` is intentionally header-only; `language_readiness.py --lang ru` reports 2,369/2,369 NT Strong's renderings and 0/17 senses missing. |
| Translation / script gate / release | not started | No GOI Russian flatfiles or derived artifacts exist. |

Versification is fully closed: `Reference_Bible/Russian_Bible_RUSSYN1876/`
is now a sound, 100%-aligned reference for GOI-coordinate QA. What remains
before translation can begin is lexicographic, not structural: source-language
noun anchors and Russian Strong's renderings/senses (still at zero,
intentionally not fabricated).

## 2026-09-23 -- activation gates

| Gate | Result | Evidence |
|---|---|---|
| Flatfiles | pass: 31,102 files, none empty | `goi_language_pipeline.py check-flatfiles GOI_Ru` |
| Script | pass (Ukrainian letters now forbidden) | `verify_language_script.py GOI_Ru` |
| NT noun coverage | pass: 100% | `verify_coverage.py --lang ru` |
| OT triage | pass: 0/0/0/23,145 Green | `ru/triage_ot.py` |
| Wrong-sense | pass: OT 6,220 fixed / 948 kept / 0 open; NT 429 fixed / 65 kept / 0 open | `ru/sense_fix_state*.tsv` |
| Renderings ledger | pass: 8,857 rows, 0 empty | `Bible_Noun_Extraction/ru_noun_renderings.csv` |
| Release integrity | pass: 13 active editions | `verify_release_integrity.py` |
| Native review | **not done** (AI review only) | -- |
