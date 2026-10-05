# Arabic tasks — OT + NT

**Status: NOT GTG.** Last audited 2026-10-04. This file is the live checklist for Arabic. Check a release task only after its exit evidence is recorded against the final corpus; a verse edit invalidates affected checks. Keep unverified work unchecked. The detailed baseline is in [the Arabic release-gate plan](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_release_gate_plan.md).

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

### 3. Number, plurals, duals, and gender

- [x] Rerun a **diagnostic** gender screen on the current draft with effective OT defaults/overrides and Arabic NT occurrence renderings. Evidence: [OT matrix](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_gender_matrix_ot.md) (31 candidates after the lexical pilot) and [NT matrix](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_gender_matrix_nt.md) (25 candidates), generated 2026-10-04. These are unadjudicated; rerun after final text changes.
- [ ] OT: adjudicate 7,102 current number-screen candidates and the repeated-ID, phrase, and inconclusive occurrences against Hebrew context and Arabic spans.
- [ ] NT: adjudicate 1,725 number-screen candidates and the repeated-ID, phrase, and inconclusive occurrences against Greek context and Arabic spans.
- [ ] Verify Arabic singular/plural/dual and numeral meaning in context, including broken plurals, collectives, counted nouns, and accepted exceptions; record source-position decisions.
- [ ] Refresh OT and NT gender screens against final text. The September reports do not certify either testament.
- [ ] Verify Arabic lexical gender and agreement for aligned noun phrases; adjudicate conflicts and unknowns. Do not treat a difference from source-language gender as an error by itself.
- [ ] Produce current morphology/agreement receipts with zero unreviewed actionable cases.

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
- [x] Generate a current exact-normalized duplicate diagnostic with source context. Evidence: [duplicate report](Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/release/ar_exact_duplicate_diagnostic.json) and review queue. After the latest corrections, it has 182 groups involving 530 verses; 102 groups have identical normalized source text and 80 differ. The rest are not fully adjudicated, and near duplicates remain unscreened.
- [ ] Rerun exact coordinate, nonempty, one-line, Arabic-script, duplicate/near-duplicate, noun/Strong's, morphology, semantic, and cube checks on the **same frozen corpus hash**.
- [ ] Adjudicate duplicate findings, including legitimate parallel verses and refrains; confirm no failed or quarantined candidate is packaged.
- [ ] Issue a single dated release receipt listing each gate and its evidence. Mark Arabic **GTG** only when all required items above pass.

German noun/Strong's scaffolding and vector-cube work begins only after Arabic is GTG, per the requested sequence.
