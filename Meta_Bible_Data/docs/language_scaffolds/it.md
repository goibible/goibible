# Language scaffold intake: `it` / `GOI_It`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolding: reference aligned; OT noun board, Strong's defaults (OT + NT) and rendering ledger done; validation cube built + embedded + validated; NT senses 490/490 reviewed; translation not started |
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
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/it_noun_renderings.csv` (`it/export_it_ledger.py`) | 8,857 | OT 6,488 + NT 2,369 Strong's defaults; 0 pending under policy (a) |
| OT noun board | `Meta_Bible_Data/Bible_Noun_Extraction/it/hebrew_ot_it.sqlite3` | 6,488 | every OT Strong's has an Italian default |
| NT Strong's board | `greek_noun.sqlite3` rows `lang='it'`, replayable via `it/nt_defaults_it.sql` (`it/export_it_nt_sql.sh`) | 2,369 + 490 senses | |
| Verse overrides | `it/ot_verse_overrides.tsv` | 203 | cross-language sense classes pre-applied (H4397 messaggero, H7307 vento, H905 stanga, H8227 irace, ...) |
| Default change log | `it/default_fixes.tsv` | 1,444 | every post-draft default change with reason |
| Validation cube | `translation_cube/cubes/it_riv_cube.sqlite3` (profile `it_riv`, untracked build output) | 173,844 occurrences / 204,946 chunks | Qwen3-Embedding-8B dense vectors (local) |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-10-02 | Intake | this record created; Riveduta 1927 acquired (VPL: 31,102 lines) | planned | this file | | Claude |
| 2026-10-02 | Alignment | `align_riv1927.py --write`: Qwen3-Embedding-8B (local `/data/llama.cpp/models/qwen3-embedding-8b`) similarity vs KJV; banded DP run on every chapter with a first-pass flag (equal verse counts hid content shifts: JOS 15 off by one, JOB 2:8 = KJV 2:9, MAT 16:15 = KJV 16:16); DP score weighted by verses covered with merge/split penalty 0.5 (tuned: 0.35 over-restructures, 0.7 misses the shifts); Riveduta's embedded Hebrew verse markers "(H40-32)" stripped (223 verses) | **pass: 31,102/31,102; 0 missing; 0 duplicates; 0 open review** (31,015 exact, 55 split, 28 merged, 2 shifted, PHP 1:16-17 reordered as in LSG; 80 flags hand-read: paraphrase/lists/textual variants) | `alignment_report.json`, `alignment_exceptions.csv` | | Claude |
| 2026-10-02 | OT noun anchors | `it/build_hebrew_ot_nouns.py` | pass: 23,145 verses, 146,502 occurrences, 6,488 Strong's (= fr/ru/ja) | `it/hebrew_ot_it.sqlite3` | | Claude |
| 2026-10-02 | Strong's defaults (OT + NT) | LLM drafts (`gen_it_ot_renderings.py`, `gen_it_sense_renderings.py`; singular, nouns only); plural-only sweep (47); name alignment to Riveduta spellings (1,041 OT + 113 NT, 42 plural picks reverted); collision scan + Riveduta evidence (6) | pass: 0 Strong's without a default | `it/default_fixes.tsv`, `it/ot_collisions.tsv` | | Claude |
| 2026-10-02 | Default review, policy (a) (carried from fr; **owner-confirmed 2026-10-02**) | `check_it_defaults_riv.py --strict` (DeepSeek V4 Flash, 1 stream) on 2,675 defaults below 25% Riveduta agreement; corrections gated on Riveduta evidence (new word in more verses than old and >= 25%): 1,085 applied, 579 rejected; then every applied correction swept by hand for plural-only output, new shared renderings and sense drift: 93 reverted or singularized (e.g. H842 Astarte -> Asera, conflated H6252; H5959 vergine kept; «stereo» typo -> sterco; H5769 eternità kept off «eterno»); English leaks fixed (bath -> bato, Asherah); 6 unparsed judge rows ruled by hand | **pass: cube pending 0** (Riveduta agreement 6,998, judged 1,704, unreachable 155) | `it/riv_default_check.tsv`, `.applied.tsv`, `staging/reports/it/riv_default_agreement.md` | | Claude |
| 2026-10-02 | NT sense review | `check_it_defaults_riv.py --senses --strict` (490 senses; 342 ok, 148 wrong) then `it/apply_it_sense_verdicts.py` (same Riveduta evidence gate; 9 non-noun/no-op proposals vetoed, 17 plural/misspelt proposals set by hand) | **pass: 490/490 reviewed, 91 renderings changed; cube lexemes 9,347/9,347 reviewed** | `it/riv_default_check.tsv`, `it/default_fixes.tsv`, `it/nt_defaults_it.sql` | | Claude |
| 2026-10-02 | Validation cube | `translation_cube/build_it_cube.py build` then `embed` (Qwen3-Embedding-8B Q8_0, llama-server :12025) | **pass: validate_cubes.py — 173,844 occurrences, 204,946 chunks, 204,946 dense Qwen3 vectors x 1024**; semantic query smoke test (ISA 40:11, JHN 10:11) | `translation_cube/cubes/it_riv_cube.sqlite3` | | Claude |

Owner decisions 2026-10-02: policy (a) confirmed for Italian (same rule as French); proper names use MODERN Italian spelling (CEI-style), not Riveduta 1927 forms -- the 1,154 Riveduta name alignments in it/default_fixes.tsv are to be converted. Open: divine name for YHWH (placeholder «l'Eterno»).

