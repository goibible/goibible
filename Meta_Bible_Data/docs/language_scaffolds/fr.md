# Language scaffold intake: `fr` / `GOI_Fr`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolded: reference aligned, noun/Strong's fill complete, fr_lsg validation cube complete; translation not started |
| GOI edition ID | `GOI_Fr` |
| BCP-47 tag | `fr` |
| Language name (native / English) | français / French |
| Scope | full Bible |
| Scaffold owner | Claude |
| Language reviewer | unresolved |
| Started | 2026-09-23 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | Louis Segond 1910 (Bible Segond), eBible.org `fraLSG` verse-per-line distribution |
| Source URL | `https://eBible.org/Scriptures/fraLSG_vpl.zip` |
| Retrieved | 2026-09-23 |
| Licence evidence | `https://ebible.org/find/details.php?id=fraLSG` -- "Cette Bible est dans le domaine public. Il n'est pas protégé par copyright. This Bible is in the Public Domain. It is not copyrighted." (page snapshot preserved in `source/`) |
| Jurisdiction and conclusion | Translator Louis Segond died 1885; first edition 1910; eBible explicitly identifies the edition as public domain. |
| Rights status | verified public domain |
| GOI use | comparison, versification and noun-rendering reference only; never copied into GOI output |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/French_Bible_LSG1910/source/` + `SOURCE_MANIFEST.json` | 2 | preserved byte-for-byte (VPL zip + eBible rights page) |
| Normalized reference | `Reference_Bible/French_Bible_LSG1910/One_Directory_LSG1910_GOI/` | 31,102 | every GOI/KJV coordinate, content-verified |
| Alignment ledger | `Reference_Bible/French_Bible_LSG1910/alignment_exceptions.csv` | 1,508 | all resolved; 85 hand-reviewed |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/fr_noun_renderings.csv` | 8,857 | NT 2,369 + OT 6,488, 0 empty; AI-drafted, LSG-checked |
| Audit reports | `Meta_Bible_Data/staging/reports/fr/` | 2 | `lsg_default_agreement.{csv,md}` |

## GOI coordinate alignment

| Measure | Expected | Observed | Report / commit |
|---|---:|---:|---|
| Full GOI spine | 31,102 | 31,102 | `alignment_report.json` |
| OT spine | 23,145 | 23,145 | |
| NT spine | 7,957 | 7,957 | |
| Declared exceptions | ledger count | 1,342 shifted, 69 merged, 10 split, 2 reordered | `alignment_exceptions.csv` |
| Duplicate GOI coordinates | 0 | 0 | |
| Missing GOI coordinates | 0 | 0 (and 0 LSG verses unused) | |

## Source-language noun anchors

| Testament | Source | Occurrences | Distinct Strong's | Rendering coverage | Missing | Duplicate anchors | Report / commit |
|---|---|---:|---:|---:|---:|---:|---|
| NT | Greek TR1550 (`greek_noun.sqlite3`, shared) | 28,889 | 2,369 | 100% | 0 | 0 | 7c42ddf (nested) |
| OT | WLC + MorphHB (`fr/hebrew_ot_fr.sqlite3`) | 146,502 | 6,488 | 100% | 0 | 0 | 7c42ddf (nested) |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-23 | Intake | this record created before acquisition | planned | this file | 57d2e0ebfd | Claude |
| 2026-09-24 | Alignment | `align_lsg1910.py --write`: Qwen3-Embedding-8B cross-lingual similarity (FR vs KJV EN) for every coordinate; order-preserving banded DP over differing chapters (padded +-1); neighbour test for hidden shifts | **pass: 31,102/31,102; 0 missing; 0 duplicates; 0 LSG verses unused; 0 open review** (first pass caught PSA 13 equal-count shift, ISA 63:19/64:1 cross-chapter move, PHP 1:16-17 critical-text reorder -- all fixed in the aligner, not by hand-editing output) | `alignment_report.json`, `alignment_exceptions.csv` | this commit | Claude |
| 2026-09-24 | Matcher | `FrenchMatcher` + self-test | pass | `Bible_Noun_Extraction/matchers.py` | 83dc5aa (nested) | Claude |
| 2026-09-24 | OT noun anchors | `fr/build_hebrew_ot_nouns.py` | pass: 23,145 verses, 146,502 occurrences, 6,488 Strong's (= ru/ja) | `fr/hebrew_ot_fr.sqlite3` (rebuildable) | 83dc5aa (nested) | Claude |
| 2026-09-24 | NT defaults + senses | `gen_default_renderings.py --lang fr`; `fr/gen_fr_sense_renderings.py` | 2,369/2,369 defaults, 217/217 senses | `fr/proposed_fr_defaults.csv` | 7c42ddf (nested) | Claude |
| 2026-09-24 | OT defaults | `fr/gen_fr_ot_renderings.py` (sample verse + unordered-gloss instruction) | 6,488/6,488 (1 hand-filled: H2298 un) | `fr/proposed_fr_ot_defaults.csv` | 7c42ddf (nested) | Claude |
| 2026-09-24 | Validation cube | `translation_cube/build_fr_cube.py build` (target text = aligned LSG) + `report_fr_lsg_validation.py` | 173,844 occurrences, 204,946 chunks; LSG agreement 71.9% | `staging/reports/fr/lsg_default_agreement.md` | 6dba81f (nested) | Claude |
| 2026-09-24 | LSG default check | `fr/check_fr_defaults_lsg.py` + `--apply` | 764 judged: 336 ok, 248 wrong, 180 name spelling; 421 applied, 7 polysemous kept, 6 hand-set; agreement -> 73.9% (NT 80.6%) | `fr/lsg_default_check.tsv` | 7c42ddf (nested) | Claude |
| 2026-09-24 | Dense index | `build_fr_cube.py embed` (Qwen3-Embedding-8B Q8_0, last-token pooling, first 1024 dims, L2) | **pass: 204,946/204,946 rows; shape (204946, 1024); finite; cube_built_at == cube metadata built_at; smoke test JHN 1:29 -> JHN 1:36 (Agneau de Dieu)** | `cubes/fr_lsg_semantic_qwen3_1024.*` (local, rebuildable) | | Claude |

## Policy decisions awaiting owner confirmation

- Divine name follows the reference (LSG 1910): YHWH (H3068/H3069) -> «l'Éternel», Adonai YHWH -> «le Seigneur,
  l'Éternel», NT kyrios -> «Seigneur». Alternative: «Seigneur» throughout (as Russian followed the Synodal).

## Release record (complete only when active)

Not applicable: no GOI French translation exists yet.
