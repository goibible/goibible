# Russian Synodal scaffold readiness — 2026-09-16 (updated)

| Gate | Result | Evidence |
|---|---|---|
| Provenance | pass | `Reference_Bible/Russian_Bible_RUSSYN1876/SOURCE_MANIFEST.json` |
| Raw source inventory | pass | 66 books; 31,169 unique source verse markers; no duplicates. |
| Psalms versification | **pass** | `psalm_versification_map.csv`: all 2,461 KJV/GOI Psalm addresses mapped via the documented Church-Slavonic/LXX chapter correspondence + per-Psalm title-verse offset, arithmetic-exhaustive and spot-verified against actual verse content at every merge/split boundary (8/8 checks). Fixed a real bug: naive address matching had paired the wrong Russian verse with a GOI address for 1,658/1,705 "matched" Psalm flatfiles. |
| GOI alignment (non-Psalm) | **fail (small residual)** | 31,074/31,102 GOI addresses now aligned (28,613 direct non-Psalm matches + 2,461 mapped Psalms). 28 GOI addresses absent, 30 Russian-only, scattered across Job, Daniel, Romans, Samuel, Joshua, Song of Songs, Proverbs, etc. See `Reference_Bible/Russian_Bible_RUSSYN1876/alignment_report.json`. |
| NT noun matcher | pass | `RussianMatcher` registered in `matchers.py`, self-test passing (coarse case-ending stem match; grow `_ACCEPTABLE_FORMS` from real coverage runs once translation starts). |
| Source-language noun anchors | not started | No `Meta_Bible_Data/Bible_Noun_Extraction/ru/` anchor-extraction pipeline exists yet (compare `.../ar/build_ar_source_noun_anchors.py`). |
| Russian renderings | not started | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` is intentionally header-only; `language_readiness.py --lang ru` reports 2,369/2,369 NT Strong's renderings and 0/17 senses missing. |
| Translation / script gate / release | not started | No GOI Russian flatfiles or derived artifacts exist. |

The Psalms versification gap (the large majority of the original 784/851
mismatch) is now closed. What remains is a small (28/30-address) non-Psalm
residual — the same kind of individual chapter-boundary difference, just
much smaller in scope, and not yet mapped.
