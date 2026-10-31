# Arabic tasks — OT + NT

**Status: NOT GTG.** Last audited 2026-10-09. This file is the live checklist for Arabic. Check a release task only after its exit evidence is recorded against the final corpus; a verse edit invalidates affected checks. Keep unverified work unchecked. The detailed baseline is in [the Arabic release-gate plan](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_release_gate_plan.md).

## Current state — 2026-10-09

- **Release receipt** (`ar/reports/release/ar_release_receipt.json`, re-checked 2026-10-09): NOT_GTG. Only `integrity` passes. Failure: `cube_freshness` (cube lexical fingerprint stale). All noun, number, gender, semantic, cube, and duplicate gates are missing.
- **Corpus hash** unchanged since 2026-10-05 (`33a29…8092`). New baseline snapshot taken 2026-10-09 (`ar_baseline.json`).
- **Alignment diagnostic** (2026-10-09 rerun): OT 144,955 occurrences — 59,562 unique surface match, 20,297 repeated Strong's, 810 multiple matches, **64,286 blank renderings**, 2,029 no surface match (the blank count is the committed figure). NT 28,889 — 24,914 unique surface match, 3,505 repeated, 421 multiple, 49 approved exclusions. Surface matches are not sense or position certification.
- **Semantic screen**: 584 OT verses input-current, 5,597 batches missing, 44 stale. No screen process running. Not certification.
- **Process hazard found and contained (2026-10-09):** `ar/reports/ar_ot_top150_reviewed_defaults.tsv` (144 blanket defaults, marked "draft approved after gloss check", no occurrence review) matched the `ar_*_reviewed_defaults.tsv` glob used by `run_ar_torah.py`, `ar_torah_heartbeat.py` and `release_gate.py`. It was treated as approved and filled 18,221 blank OT occurrences in the diagnostic (for example H1697 "word" across 1,412 occurrences where the source also covers "thing/matter"). It is now at `ar/reports/unreviewed_candidates/ar_ot_top150_candidate_defaults.tsv`, outside the glob. Its blanket defaults are not approved; each needs occurrence-level review before promotion.
- Verse text: no GOI_Ar verse changed since 2026-10-05. Blanket defaults have not been written into verses.

## Ambiguous IDs — 2026-10-09 (overrides `af7a260`, verse queue `2f6a1d1`)

- **H1697 דָּבָר** (1,455 occurrences): 43 existing reviewed rows kept. 547 singular cases hand-labelled by Hebrew context and KJV sense; plurals and suffix forms by rule. Two rows left blank as likely H1698 (pestilence): 1CH 21:12, 2SA 24:13.
- **H1471 גּוֹי** (566): singular → أمة, plural → أمم. Matches verse usage.
- **H8269 שַׂר** (342 new rows): singular → رئيس, plural → رؤساء. This is the project's term across captain, prince, and chief senses; the verses use it throughout.
- **Verse mismatch — resolved 2026-10-09 (verse-by-verse, by hand):** the 338 `no_surface_match` rows (325 H1697, 13 H1471) are now 0. The verse text said كَلِمَة where Hebrew meant thing, matter, speech, report, cause, or plural. 280 verse files changed (single-line format kept; integrity PASS, 31,102 verses). Where the verse was already right, the override was corrected instead. Queue: `Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_verse_queue_ambiguous_ids_2026-10-09.tsv`.
- **Phantom anchor rows removed:** GEN 25:23 pos3 and EZK 36:14 pos3 (H1471). The WLC has no goy word at those positions. The anchor table has other phantom rows; these are unchecked.
- New corpus baseline snapshot 2026-10-09 (`corpus_sha256` `abb653af…`). Release receipt: NOT_GTG, failing only `cube_freshness` (the cube must be rebuilt from the edited corpus).
- Blank OT renderings: 64,286 → 61,968.

## Next steps (in order)

1. Read the 280 changed verses in the git diff (sample reads passed; every change is one-for-one and reversible). Check the phantom anchor rows in the anchor table, which the audit cannot detect on its own.
2. Hand-review the 144 candidate Strong's defaults before any promotion.
3. Work the remaining blank OT renderings, grouped by Strong's frequency, against Hebrew context. H1697, H1471 and H8269 are done.
4. Freeze and rebuild the cube after OT text stops changing; re-run `ar/release_gate.py check`.

## Established draft facts (not release passes)

- [x] All expected verse files exist: 23,145 OT + 7,957 NT = 31,102. Existing one-line/Arabic-script/populated-anchor draft checks passed. Recheck on the final corpus.
- [x] Current number screens exist: OT 4,939 plural-form + 2,163 singular-form candidates after the latest corrections; NT 719 plural-form + 1,006 singular-form candidates. These are review candidates, not verified errors.
- [x] The starting reviewed OT anchor ledger was counted: 81,173 of 144,955 source noun occurrences lacked a rendering (54,391 number-marked; 26,782 uninflected/proper). This was a ledger gap, not proof that words were absent from translated verses. Current remainder is tracked below.
- [x] The Arabic cube is known to be stale for release: built before later OT edits, with 8,141 translated verse chunks in its metadata. An internal `ready` preflight is not a current-corpus pass.

## Release tasks — all required

### 1. Baseline and fail-closed release receipt

- [x] Freeze a corpus manifest with file count and content hashes for all 31,102 Arabic verses; record source inventory and lexical-ledger hashes. Evidence: [baseline](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_baseline.json) and [per-verse manifest](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_corpus_manifest.jsonl), generated 2026-10-04. This is the starting snapshot; later edits require a new snapshot.
- [x] Implement a combined release receipt that reports **NOT GTG** if any gate is missing, stale, incomplete, or has unresolved findings. Evidence: [release_gate.py](Meta_Bible_Data/Bible_Noun_Extraction/ar/release_gate.py) and [current NOT_GTG receipt](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_release_receipt.json). Gate-specific evidence producers remain to be completed.

### 2. Nouns, Strong's, and sense alignment

- [x] Run an occurrence **diagnostic** over 144,955 OT and 28,889 NT noun anchors. Evidence: [alignment report](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_occurrence_alignment_diagnostic.json) and OT/NT review queues beside it. The latest completed run recorded 64,286 OT blank renderings, 20,297 repeated-ID cases, and 810 multiple matches. NT had 3,505 repeated-ID cases and 421 multiple matches; 40 subscription and 9 textual-policy occurrences are explicitly excluded. Surface matches alone do not pass this gate.
- [x] Screen the 5,972 remaining OT machine-draft default IDs for visible Arabic forms without promoting them. Evidence: [candidate screen](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_ot_machine_default_screen.csv). Seven IDs have surface misses; 5,965 have a visible draft form in every corresponding verse, which does **not** establish correct sense or reviewed status.
- [x] Review and add 23 OT proper-name defaults. Their 9,787 current source occurrences have a bounded Arabic name match. Evidence: [reviewed defaults](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_ot_reviewed_defaults.tsv) and [reproducible lexical pilot receipt](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_ot_lexical_pilot.json). This proves a base citation and visible match, not unique source-position alignment.
- [x] Review and add five common OT noun defaults (fire, war, king, prophet, servant). Their 4,330 formerly blank occurrences have a bounded Arabic form match; 13 prophet occurrences retain existing contextual plural overrides. The same [lexical pilot receipt](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_ot_lexical_pilot.json) verifies 14,130 total occurrences across the 28 selected IDs with zero missing forms. This does not certify contextual sense or number.
- [x] Review and add eight more unambiguous proper-name defaults (Absalom, Ahab, Hezekiah, Isaac, Jeroboam, Esau, Samuel, Samaria). Their 892 occurrences have bounded Arabic matches. The pilot now verifies 15,022 occurrences across 36 IDs; exact position still needs review.
- [x] Review and add 29 additional proper-name defaults, covering 1,831 occurrences with bounded matches. That pilot stage verified 16,853 occurrences across 65 IDs with no missing citation forms. This is surface evidence only; exact position and contextual sense remain open.
- [x] Remove fixed nominative endings from the reviewed Enosh, Kenan, and Mahalalel defaults after direct Hebrew review exposed reversed parent/child roles. The lexical pilot now checks 16,873 visible citation occurrences across 68 IDs with zero missing forms; exact alignment and sense remain open. Five other case-marked proper-name defaults were also made case-neutral and rechecked.
- [x] Correct eight occurrence-specific Strong's renderings discovered during direct-source duplicate review: Diphath, Rodanim, two instances each of “thing,” “heron,” and “strength.” Their ten edited verses passed the current per-verse anchor validator; see [direct-source corrections](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_direct_source_corrections_2026_10_04.tsv).
- [x] Correct 2CH 8:14 (daily requirement, not a spoken word) and 2CH 23:14 (army officers, not wealth officials); add occurrence-specific H1697 and H2428 renderings. Both edited verses pass validation for all currently nonblank anchors. Their other blank anchors remain open.
- [ ] OT: review the remaining 64,286 blank noun-anchor occurrences, including proper names; populate reviewed defaults/occurrence senses or record justified textual-policy exemptions.
- [ ] OT: align every source noun occurrence and Strong's ID to the final Arabic word/phrase span or approved exemption; resolve repeated IDs and ambiguous/missing matches.
- [ ] NT: rerun full occurrence-level Strong's/sense alignment against the final 7,957 verses and resolve every missing/ambiguous match or approved exemption.
- [ ] Produce current OT and NT coverage receipts showing zero unexplained gaps. Rerun verse validation after each accepted correction.

### 3. Number, plurals, duals, and gender — completed 2026-10-26

- [x] **Plurals / number review complete:** all 4,164 frozen OT/NT candidates adjudicated, including singular, plural, dual, numeral grammar, collectives and contextual exceptions. Six newly surfaced flags from the regenerated screen also adjudicated; zero unreviewed candidates.
- [x] **Gender review complete:** refreshed OT/NT cue screens; all 74 candidates adjudicated and current hashes reconciled. Earlier genuine gender repairs remain applied.
- [x] Apply and validate corrections; reconcile final text and record the completed review receipt. Evidence: [closeout receipt](Meta_Bible_Data/staging/reports/ar/plural_closeout_20261026/closeout_receipt.json) and [review scope/evidence](Meta_Bible_Data/staging/reports/ar/plural_closeout_20261026/README.md).

These completed reviews stay checked off. Broader unmatched, ambiguous and repeated-ID occurrence alignment belongs to the noun/Strong's work in section 2; full semantic certification belongs to section 4. Subsequent text changes require targeted revalidation of affected decisions.

### 4. Full semantic review

- [x] Calibrate DeepSeek V4 Flash 0731 with clean, reversed-negation, dropped-clause, wrong-number, and omitted-star cases; all five single-verse probes passed. Three four-verse probes also passed. A wider locked screen checkpointed 190 four-verse OT batches through roughly verse 760, then stopped. After source-backed corrections, the [current coverage check](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_semantic_audit/ot_screen_coverage.json) finds 584 input-current screened verses, 44 stale batches to rerun, and 5,597 batches missing. This is a model-screen diagnostic, not semantic release certification. No paid screen process is running.
- [ ] Review all 23,145 OT verses against Hebrew with a verse-level ledger and direct-source evidence.
- [ ] Review all 7,957 NT verses against Greek with a verse-level ledger and direct-source evidence.
- [ ] Check omissions, additions, negation, agency, names, divine titles, numerical values, chronology, contextual senses, and clause relationships; correct and re-review affected verses.
- [ ] Resolve every material semantic finding. Model screening may suggest cases but cannot certify a verse unattended; the pilot missed injected errors.
- [x] Correct ten material OT verses exposed by comparing exact Arabic duplicates with their Hebrew sources: two names, two counts, two “thing” senses, two bird names, and two “strength” senses. A DeepSeek candidate led to a Genesis 1:17 vowel correction, and direct Hebrew review corrected four Genesis 5 parent/child agency errors. The [direct-source correction ledger](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_direct_source_corrections_2026_10_04.tsv) and [DeepSeek adjudication ledger](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_deepseek_findings_adjudicated.tsv) record decisions. This is a limited reviewed subset, not a full semantic pass.
- [x] Correct 100 additional OT verses using direct Hebrew review of model findings and noun-number candidates. This includes 2 Chronicles 8/23, Genesis 10–48, Exodus 9, Numbers 4/13/18/26/29/35, Deuteronomy 28, Joshua 10/12/21/24, Judges 3/11, 2 Samuel 1, 1 Kings 12/17/21, Ezra 7, and 1 Chronicles 1–27. Eight of these correct the recurring Hebrew narrative phrase “after these matters” where Arabic said “after these words”; Genesis 24 fixes include the half-shekel weight, oath agency, and two bracelets. Record exact changes in the [direct-source correction ledger](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_direct_source_corrections_2026_10_04.tsv), with model findings in the [DeepSeek adjudication ledger](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_deepseek_findings_adjudicated.tsv). All edited verses pass validation for their currently nonblank noun anchors; GEN 16:13 remains unresolved; the full noun and semantic gates remain open.
- [ ] Produce a 31,102-verse reviewed ledger with zero unresolved material findings.

### 5. Current language cube and vectors

- [x] Make the release checker compare Arabic cube corpus/lexicon fingerprints and verse text with the current files; make future Arabic cube builds record those fingerprints. Evidence: [release gate](Meta_Bible_Data/Bible_Noun_Extraction/ar/release_gate.py) and [cube builder](Meta_Bible_Data/Bible_Noun_Extraction/translation_cube/build_cube.py). The existing cube fails this check.
- [ ] Rebuild the Arabic canonical cube from the final verses and reviewed lexicon; include OT and NT target chunks and grammar.
- [ ] Rebuild sparse and Qwen dense vectors; verify every required chunk has matching vector rows.
- [ ] Verify cube freshness passes with the final corpus/lexicon fingerprints and verse-coverage comparison; run source Hebrew/Greek and target Arabic OT/NT preflight/validation.
- [ ] Produce a current-corpus cube receipt with no unresolved alignment concealed by structural readiness.

### 6. Final integrity and GTG decision

- [x] Run current-corpus coordinate, nonempty, one-line, newline, whitespace, and Arabic-script integrity checks on all 31,102 verses. Evidence: [integrity validator](Meta_Bible_Data/Bible_Noun_Extraction/ar/audit_ar_integrity.py) and [gate receipt](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/integrity.json): zero findings on the current baseline. This gate passes individually, but overall release does not.
- [x] **Duplicate review complete:** all 154 current exact-normalized groups / 484 verses adjudicated legitimate; two earlier lost source distinctions remain corrected. Both candidate pairs from the bounded near-duplicate screen are adjudicated. Evidence: [final duplicate audit](Meta_Bible_Data/staging/reports/ar/plural_closeout_20261026/luna_gender_duplicate_audit.json). The near-duplicate screen's threshold and limits are documented in the closeout.
- [ ] Run the combined noun/Strong's, semantic, cube-freshness and release checks against one final frozen corpus hash; include the completed morphology, duplicate and integrity evidence.
- [ ] Confirm no failed or quarantined candidate is packaged.
- [ ] Issue a single dated release receipt listing each gate and its evidence. Mark Arabic **GTG** only when all required items above pass.

German noun/Strong's scaffolding and vector-cube work begins only after Arabic is GTG, per the requested sequence.

## 7. Batch driver (autonomous loop)

Work is run in batches of 50 rows, four Haiku subagents per round. Each batch writes `scratchpad/<gate>/res_NNN.tsv`. Mark a batch done here when its result file exists and reports `DONE`.

Sources and state (updated 2026-10-11):

- Duplicates gate: 181 groups reviewed. OK 167; DEFECT 5 (EXO 29:39 / NUM 28:4 plural الخرفان with singular ordinals; 2CH 33:2 plural תועבות vs singular رجس; EZR 2:32, 2:39, 2:43 / NEH 7:35, 7:42, 7:46 clan بن read as number error, likely clan label, move to UNSURE); UNSURE 9. Outputs: `Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/subagent_results/dup_result_{1..4}.tsv`.
- Number gate: 9,617 candidate rows (OT 7,892, NT 1,725) in 193 batches of 50 (`num_000`–`num_192`). Review pass complete: all 193 batches (000–192, 9,617 rows) have results in `scratchpad/num/res_NNN.tsv`. Final tally: 8,678 MATCH, 457 MISMATCH, 482 UNSURE (all rows classified, no gaps). Adjudication pass complete (Sonnet reviewer, all 939 flagged rows in `scratchpad/num/adj_000–018.tsv`, combined list `scratchpad/num/adj_errors.tsv` for the ERROR rows). Result: 132 ERROR (clear number error, to correct), 650 POLICY, 157 OK. POLICY buckets: mass 261, distributive 222, idiom 56, clan 56, other 37, tsevaot 18. Policy decided (Arabic reader ruling): mass, distributive, idiom, clan and tsevaot POLICY rows are OK; Opus reviewed the 37 "other" rows (5 ERROR, 32 OK). Applied: 129 number corrections to `GOI_Bible/GOI_Bible_ar` from `scratchpad/num/fix_out_{0,1,2}.tsv`, each old substring verified to occur exactly once before replacement (script `apply_fixes.py`). Also applied by hand: the 3 SKIP rows (AMO 5:16, MIC 7:10, ZEP 3:6: خارج → شوارع) and the 5 "other" errors (2KI 2:16, 2KI 8:21, NEH 7:2, ZEP 2:8, MAL 3:3), file `scratchpad/num/manual_fixes.tsv`. Number-correction queue is now empty (132 of 132). Not yet started: the 31,102-verse semantic pass, cube rebuild, gate receipts, commit. Mismatches are not yet adjudicated or edited. Judgment call to settle at adjudication: res_093 idx 9, 31, 49 (singular noun with plural suffix, observed plural) marked MATCH by the subagent.

Clan-label rule for adjudication: EZR 2:3–2:39 (and NEH 7 equivalents) rows with plural "sons of" rendered singular ابن (res_085 idx 23–45) are clan-name headers, the same class as the duplicates-gate EZR/NEH group. Move them to UNSURE, do not count them as number errors. Mismatches so far: 003 (GEN 10:20), 008 (GEN 33:7, 33:14, 39:21), 009 (7 rows), 012 (GEN 50:22, EXO 6:19), 014 (EXO 15:5), 015 (EXO 21:22, EXO 25:15), 016 (EXO 30:4), 019 (LEV 8:13). Each mismatch goes to a stronger review before any edit.
- Semantic pass: 31,102 verses in batches of 50 (622 full batches + one batch of 2 = 623 files `scratchpad/sem/sem_in_000–622.json`, each verse paired with its English GOI reference). Progress (2026-10-11): batches 000–622 verified from `scratchpad/sem/sem_out_NNN.tsv` (31,102 verses; semantic pass COMPLETE). 668 semantic corrections applied, recorded in `scratchpad/num/sem_fix_*.tsv` (each old substring checked to occur exactly once; not yet cube-rebuilt or gate-checked). Kept as-is, for owner decision: JOS 4:23 "بحر الحلفاء" for Red Sea (name policy; same term used elsewhere in corpus); reference-side disagreements (DEU 14:15 ostrich vs owl, 1SA 2:10, 1SA 18:21, JDG 17:1-2 English); poetic Judges 5 readings (5:2, 5:11, 5:14, 5:18). Haiku reviewers, findings-only; findings adjudicated by reading the verse and the English/KJV-style reference, corrections applied only after the exact-once check. Findings get adjudicated and corrected in the same way as the number gate (exact-once substitution check). Order after the semantic pass: cube rebuild from the final verses, then the gate receipts, then rerun all gates on the same frozen corpus hash, then commit.

Next: finish number batches 017–192, then the semantic batches in verse order, then the cube and gate receipt. Commit only after all gates show PASS.

## Gate status (2026-10-12)
- Semantic pass: COMPLETE, batches 000–622 (31,102 verses). Manual fixes (not in the 668 TSV ledger): 1PE 3:3/3:4, 1JN 2:16, 2PE 3:11, HEB 13:4, REV 19:8; log in scratchpad `num/sem_manual_fixes_608_612.tsv`.
- `release_gate.py check`: NOT_GTG. integrity PASS (31,102 verses, 0 findings). Corpus changed since baseline, so all receipts are stale.
- number_ot / number_nt screens: surface review queues 55,456 (OT) and 1,724 (NT) — not zero.
- duplicates: diagnostic_only, 180 exact groups (80 with different source) — adjudication pending.
- occurrence alignment: OT 20,800 repeated-Strong's needing alignment, 61,970 blank renderings; NT 3,503 repeated, 417 multiple-surface.
- gender_ot/nt, noun_strongs, cube: not run / not PASS.
- Not committed: gates not all PASS.

## Verifier status (verify_language.py --lang ar, 2026-10-16)
- PASS: sense layer 491/491 (drafted 62 via gen_sense_renderings.py, hand-corrected 6, all needs_review=0); unknown gender 0 (4 manual, POS classified 489 rows); NT anchors 0 missing (40 judged, 3 text repairs LUK 7:21, ACT 19:27, JUD 1:12 + ROM 14:1); proper names 0 missing (16 judged; H8227 table entry is the animal, names correct in text).
- FAIL/STALE: gender agreement report (gender_ngram.py has no Arabic functions); plural candidates 2441 -> 1694 judged open: 190 judge errors in plural_errors_ar.tsv NOT yet hand-read or repaired (105 P, 61 S, 24 D); OT triage (staging/reports/ar/ot_triage): RED 2, ORANGE 36, YELLOW 2937 (anchor 2702, form 235, check 235), 3761 missing anchors; cube stale (rebuild after all table edits).
- Not committed. Not pushed.

## Current gender / plurality / duplicate checkpoint — 2026-10-26

This checkpoint supersedes the older saved diagnostic counts above. Evidence: [plural closeout](Meta_Bible_Data/staging/reports/ar/plural_closeout_20261026/README.md).

- [x] All 4,164 frozen plural candidates adjudicated. Fresh diagnostic: 3,995 flags, including six new source-anchor flags; all six individually resolved. No unreviewed candidate remains in these screens. Diagnostic flags are not error counts.
- [x] Corrections/clarifications applied to 189 unique verse files, with 192 validated receipt rows. Final populated-anchor, source-coordinate, format and receipt-chain audit: zero failures. This includes contextual sense and agreement repairs, not just number errors.
- [x] All 74 gender-cue candidates reconciled; hashes unchanged. Three earlier gender repairs remain applied. Unscreened/ambiguous agreement constructions remain outside this screen.
- [x] Current 154 exact duplicate groups / 484 verses adjudicated legitimate. Two earlier lost source distinctions remain corrected. Newly formed Kings/Chronicles pair verified as plural in both sources, differing only in spelling.
- [x] Bounded near-duplicate screen (TF-IDF cosine >= .96, minimum six tokens): both pairs legitimate and source distinctions preserved. Lower-similarity paraphrase duplicates remain outside this screen.
- [x] Full 31,102-verse coordinate/file integrity passes. Nine number/matcher regression methods and existing Arabic gender-cue regressions pass.
- [ ] Rebuild target cube from final stable corpus/lexicons; complete full noun/Strong's, occurrence-alignment, morphology/semantic and same-snapshot release gates. Arabic remains **NOT_GTG**; readiness colors are not certified by this closeout.

## Vocabulary and grammar batches — started 2026-10-26

- [x] Batch 001: first 100 currently blank effective OT occurrence renderings, GEN 9:2–31:7. All 100 source meanings linked to exact current Arabic spans. Grammar: 76 new rows and 25 existing rows reviewed; eight existing mapping repairs in the same verses. All populated-anchor/format checks pass across 64 verses; no canonical verse changes. Fifteen unmarked place-name citation genders remain explicitly unspecified rather than inferred. [Evidence](Meta_Bible_Data/staging/reports/ar/vocab_grammar_20261026/README.md).
- [ ] Batch 002: next 100 blank effective occurrence renderings in canonical order. Remaining blank mappings: 3,659 (starting live count 3,759). This count does not include all other occurrence-alignment work.

### Occurrence review continuation — 2026-10-27

- Five additional occurrences have been applied with source and target hash, exact-span, and populated-anchor checks: GEN 31:41, 32:16, 35:5; EXO 16:33 and 21:6. Their receipts are in `Meta_Bible_Data/staging/reports/ar/vocab_grammar_20261027/`. The effective blank count is 3,654. No verse text changed.
- The frozen `blank_occurrence_queue.jsonl` in that directory contains the 3,656 entries remaining after the first three of these five applications. Its row numbers are stable review coordinates, not the current live blank count. Parallel review artifacts are candidate evidence, not applied mappings or release certification.
- EXO 12:4 and 14:25 have proposed mappings but their full verse checks exposed existing missing-anchor findings (respectively طَعَام and مِصْرَايِم). Investigate the source, Arabic, and existing anchors before applying those proposals.
- 1CH 4:12: restored the omitted first element of WLC's Ir-nahash in Arabic; existing populated anchors validate. Evidence: `vocab_grammar_20261027/1ch_4_12_correction.json`. The frozen queue and candidate packets for this verse now have stale target hashes and must be refreshed before application.
- 2026-10-28: applied 50 independently reviewed Joshua place-name occurrences and two independently reviewed Exodus occurrences, with source/target hashes, exact target spans and full populated-anchor validation. Receipts: `joshua_names_applied.json`, `joshua_names_501_550_applied.json`, and `exodus_second_applied.json` in the same staging directory. Independently rechecked 52 mappings across 34 verses. Live blank count: 3,602. Cases with existing anchor failures, grammatical conflicts or uncertain correspondence remain held; this does not certify occurrence alignment or release.
- Later 2026-10-28: corrected six Joshua village occurrences and applied 11 newly unblocked names (`joshua15_villages_and_names_applied.json`); corrected three existing Exodus occurrence renderings and filled two blanks (`exo_12_4_14_25_applied_receipt.json`). Both sets passed the full populated-anchor checks and retain backups. Live blank count: 3,589.
- Further 2026-10-28: applied 26 independently audited Joshua names (`prepared_651_700_applied_c.json`) and both components of the corrected Ir-nahash name (`1ch_4_12_ir_nahash_receipt.json`). Live blank count: 3,561. The Tehinnah anchor at 1CH 4:12 remains held because the same Arabic citation is already stored as a common noun; source-specific grammar support is needed before applying it.

## Claude takeover — 2026-10-29/30 (bar: `verify_language.py --lang ar` ALL PASS)

Codex grounded; Claude owns Arabic. Gate = the shared verifier, not `ar/release_gate.py`. Nothing committed.

- **OT anchors 5,775 -> 0** (all 23,018 verses GREEN). Path: mine accepted forms -> triage -> `judge_coverage.py` (DeepSeek-V4.1-Flash-1017, low, flex) -> hand-read every omitted/wrong/unclear verdict -> `ar/apply_reviews.py ar/reviews/cov_20261030*.tsv`.
- **NT anchors:** 12 hand accepts (corpus `nt`, reviewer `claude:nt_20261030`). **Names:** missing 0 (`matcher_ar.py`: الرب += ورب/لرب/برب).
- **Clause check** (`ar/clause_check_ar.py`, every verse changed since 8398d00ba7): 0 open.
- **Systemic Hebrew sound-alike calques**, fixed corpus-wide (logs in `staging/reports/ar/to_zero_20261029/*_calque.tsv`):
  - names: مصرايم -> مصر, فلشتيم -> فلسطينيين;
  - titles: الرب الجنود -> رب الجنود (115 verses);
  - nouns: חצר حضرة -> دار/ديار/قرى; רכב ركب -> مركبات; לשכה منسك -> حجرة; עזבון/מערב عزبون/معرب -> بضائع/تجارة; עמק عمق -> وادي; שחת نقع -> حفرة; נצח نصيح -> إلى الأبد; סופר القائد -> الكاتب; חמר حمر -> حومر/طين; גבורה نصرة -> جبروت; חיל ثروة -> جيش; עלילות أسباب -> أعمال; אתיק أساطين -> رواق; תרשיש stone -> زبرجد;
  - משפט عدل -> حكم/عادة/أحكام by sense;
  - leftover transliterations (متوم, ترمة, جمول, سوفة, يهلوم…) translated.
- **apply_reviews bug fixed:** NFC matching, and accepted words stored in raw verse spelling (the gates test plain substring; the corpus mixes shadda/vowel order). 88 old accepted_hand rows re-spelled.
- **Grammar:** reconcile dropped 1,698 orphans; 8 unknown-gender N/ADJ rows hand-set; gender report regenerated; plural regenerated + judged.
- **Open owner-policy items:**
  - TR subscriptions are omitted edition-wide (1TI 6:21);
  - "بحر سوف" Red Sea convention;
  - PSA 13:5/6 YHWH row bug (shared hebrew_ot_* DBs);
  - 1,195 foreign ar edits were already in the tree at takeover;
  - no native review yet.
- **2026-10-30 ~05:30: `verify_language.py --lang ar` ALL PASS.**
  - Cube rebuilt from the live `ot_ar_renderings`: `checks_ar.cube_ot_renderings` no longer reads the frozen `ar/reports/*_reviewed_defaults.tsv`, which still held مصرايم/فلشتيم.
  - 12 Philistine/Egypt calque overrides dropped from `ar_torah_occurrence_overrides.tsv` and `ot_ar_contextual_renderings`.
  - `checks_ar.preload_grammar` now seeds only renderings that are still in use (it was re-creating 1,698 orphans).
