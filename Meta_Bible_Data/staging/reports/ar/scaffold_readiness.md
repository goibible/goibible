# Arabic Van Dyck scaffold readiness — 2026-09-16

| Gate | Result | Evidence |
|---|---|---|
| Provenance | pass | `Reference_Bible/Arabic_Bible_VanDyck1865/SOURCE_MANIFEST.json` |
| Preservation | pass | `tools/translation_pipeline/verify_scaffold_manifests.py` validates the immutable raw archive hash. |
| Raw source inventory | pass | 66 books; 31,104 unique source verse markers. |
| GOI alignment | pass | 31,102 normalized unique GOI coordinates; four source rows in two explicit merge groups. |
| Source-language noun anchors | pass | 28,889 NT Greek TR1550 and 144,955 OT WLC/MorphHB noun occurrences, with no duplicate Arabic scaffold anchors. |
| Arabic renderings | not started | `Meta_Bible_Data/Bible_Noun_Extraction/ar_noun_renderings.csv` is intentionally header-only; all 8,702 distinct Strong's numbers await qualified Arabic review. |
| Translation / script gate / release | not started | No GOI Arabic flatfiles or derived artifacts exist. |

The Arabic translation may start only after the source-manifest verifier is
recorded as passing and source-language noun-anchor work is established.
