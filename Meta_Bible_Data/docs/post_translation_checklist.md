# Post-Translation Checklist

Run this checklist after a translated book, testament, or full language corpus
is complete and before changing its edition status to `active`. Save dated
outputs under `Meta_Bible_Data/staging/reports/<lang>/`; record completion in
the language scaffold record. A database build is not a substitute for these
checks.

## Required language-quality gates

- [ ] **Character/script quality:** create or review the language's entry in
  `Meta_Bible_Data/translation_qa/script_profiles.json`, then run:

  ```bash
  python3 tools/translation_pipeline/verify_language_script.py GOI_<ID>
  ```

  It rejects foreign scripts and control characters while allowing only the
  language's declared script(s), shared punctuation/digits, and valid combining
  marks. Do not add a foreign script as an exception just to make the gate
  pass; remove leaked source text, prompts, or model artifacts. If a genuine
  scholarly quotation is required, document a coordinate-specific exception,
  reason, and reviewer in the language scaffold record.
- [ ] **UTF-8 and structure:** substantive text only; no blank, duplicated,
  malformed, or concatenated verse files.
- [ ] **GOI alignment:** all expected KJV/GOI coordinates present exactly once;
  every versification difference recorded in the alignment exception ledger.
- [ ] **Noun/Strong's coverage:** Greek TR1550 NT and WLC/MorphHB OT anchors
  resolved or documented at each intentional grammatical divergence.
- [ ] **Per-verse enforcement receipt:** production batch log proves the
  runner used `--require-noun-anchors`; every output verse passed the
  language matcher before it was written. A post-hoc partial coverage report
  does not substitute for this gate.
- [ ] **Supervised-batch receipt:** record the absolute Python interpreter,
  DeepSeek model/provider, service tier, single-worker lock, start/end time,
  restart/resume count, expected/final coordinate counts, and 20-minute
  heartbeat entries. A heartbeat alone is not a supervisor; the runner must
  resume after a worker/API failure.
- [ ] **Native-language semantic review:** reviewer, scope, defects, and
  resolutions recorded.
- [ ] **No partial pass:** noun coverage is 100% after documented exclusions
  and contextual overrides. Any lower result blocks commit/promotion and
  requires targeted repair plus re-check.
- [ ] **Cross-language regression:** every discovered defect is entered in
  `cross_language_regressions.csv`, then checked in every active GOI language.

## Release gates

- [ ] `verify_scaffold_manifests.py`
- [ ] `verify_cross_language_audit.py`
- [ ] `verify_language_script.py GOI_<ID>`
- [ ] `verify_release_integrity.py` after building derived databases
- [ ] GitHub manifest checksum/count and app download URL checked
- [ ] Reader database rebuilt, backed up remotely, rsynced to `dsvx`, queried,
  and smoke-tested at `read.goibible.org`

The full database and deployment sequence is in `new_language_recipe.md`.
The initial active-corpus baseline is retained in
`../staging/reports/script_gate_baseline_2026-09-14.md`; its failures are
cleanup work, not allowed exceptions.
