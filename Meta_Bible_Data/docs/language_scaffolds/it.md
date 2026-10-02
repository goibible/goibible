# Language scaffold intake: `it` / `GOI_It`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolding in progress: reference acquired; alignment, noun boards, Strong's defaults and validation cube pending; translation not started |
| GOI edition ID | `GOI_It` |
| BCP-47 tag | `it` |
| Language name (native / English) | italiano / Italian |
| Scope | full Bible |
| Scaffold owner | Claude |
| Language reviewer | unresolved |
| Started | 2026-10-02 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | Riveduta 1927 (Giovanni Luzzi revision; Bible Society in Italy), eBible.org `ita1927` (ITARIV) verse-per-line distribution |
| Source URL | `https://ebible.org/Scriptures/ita1927_vpl.zip` |
| Retrieved | 2026-10-02 |
| Licence evidence | `https://ebible.org/find/details.php?id=itaRIV` -- "The Holy Bible in Italian, Riveduta 1927 — Public Domain" (page snapshot preserved in `source/`) |
| Jurisdiction and conclusion | Reviser Giovanni Luzzi died 1948 (life+70 expired 2018); first edition 1927; eBible explicitly identifies the edition as public domain. Diodati 1885 (also PD) considered and not chosen: the Riveduta is the modern-register counterpart of Louis Segond. |
| Rights status | verified public domain |
| GOI use | comparison, versification and noun-rendering reference only; never copied into GOI output |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/Italian_Bible_RIV1927/source/` + `SOURCE_MANIFEST.json` | 2 | preserved byte-for-byte (VPL zip + eBible rights page) |
| Normalized reference | `Reference_Bible/Italian_Bible_RIV1927/One_Directory_RIV1927_GOI/` | 31,102 | every GOI/KJV coordinate, content-verified |
| Alignment ledger | `Reference_Bible/Italian_Bible_RIV1927/alignment_exceptions.csv` | 166 | all resolved; 80 hand-reviewed |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/it_noun_renderings.csv` | pending | |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-10-02 | Intake | this record created; Riveduta 1927 acquired (VPL: 31,102 lines) | planned | this file | | Claude |
| 2026-10-02 | Alignment | `align_riv1927.py --write`: Qwen3-Embedding-8B (local `/data/llama.cpp/models/qwen3-embedding-8b`) similarity vs KJV; banded DP run on every chapter with a first-pass flag (equal verse counts hid content shifts: JOS 15 off by one, JOB 2:8 = KJV 2:9, MAT 16:15 = KJV 16:16); DP score weighted by verses covered with merge/split penalty 0.5 (tuned: 0.35 over-restructures, 0.7 misses the shifts); Riveduta's embedded Hebrew verse markers "(H40-32)" stripped (223 verses) | **pass: 31,102/31,102; 0 missing; 0 duplicates; 0 open review** (31,015 exact, 55 split, 28 merged, 2 shifted, PHP 1:16-17 reordered as in LSG; 80 flags hand-read: paraphrase/lists/textual variants) | `alignment_report.json`, `alignment_exceptions.csv` | | Claude |
| 2026-10-02 | OT noun anchors | `it/build_hebrew_ot_nouns.py` | pass: 23,145 verses, 146,502 occurrences, 6,488 Strong's (= fr/ru/ja) | `it/hebrew_ot_it.sqlite3` | | Claude |

