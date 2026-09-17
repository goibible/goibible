# Russian Synodal scaffold readiness — 2026-09-16

| Gate | Result | Evidence |
|---|---|---|
| Provenance | pass | `Reference_Bible/Russian_Bible_RUSSYN1876/SOURCE_MANIFEST.json` |
| Raw source inventory | pass | 66 books; 31,169 unique source verse markers; no duplicates. |
| GOI alignment | **fail (mapping required)** | 30,318/31,102 GOI addresses match the source directly; 784 GOI addresses absent, 851 Russian-only addresses. 756/784 and 821/851 are in Psalms (Synodal versification differs there); remainder scattered across Job, Daniel, Song of Songs, Romans, Samuel, Joshua, Proverbs. See `Reference_Bible/Russian_Bible_RUSSYN1876/alignment_report.json`. |
| NT noun matcher | pass | `RussianMatcher` registered in `matchers.py`, self-test passing (coarse case-ending stem match; grow `_ACCEPTABLE_FORMS` from real coverage runs once translation starts). |
| Source-language noun anchors | not started | No `Meta_Bible_Data/Bible_Noun_Extraction/ru/` anchor-extraction pipeline exists yet (compare `.../ar/build_ar_source_noun_anchors.py`). |
| Russian renderings | not started | `Meta_Bible_Data/Bible_Noun_Extraction/ru_noun_renderings.csv` is intentionally header-only; `language_readiness.py --lang ru` reports 2,369/2,369 NT Strong's renderings and 0/17 senses missing. |
| Translation / script gate / release | not started | No GOI Russian flatfiles or derived artifacts exist. |

Unlike Arabic, Russian cannot proceed straight to a "translation may start"
gate once source-anchor work lands: the 784/851-address versification gap
is a real mapping problem (chiefly Psalm renumbering), not a handful of
mergeable exceptions. That map must be built and verified before this
reference can anchor GOI-coordinate QA.
