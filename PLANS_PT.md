# Plan: GOI Bible — Portuguese (`pt`) Edition

Target: a full 66-book Portuguese GOI edition, with NT translated from Greek
TR1550 and OT translated from Hebrew WLC. The public-domain noun/reference text
is Almeida 1911 from Project Gutenberg, aligned first to the GOI/KJV spine.

## Stage 0 — Reference Acquisition And Alignment

Done:

- Downloaded Project Gutenberg ebook 62383 to
  `Reference_Bible/Portuguese_Bible_Almeida1911/SOURCE/gutenberg_62383_almeida1911.txt`.
- Built native atomization with `atomize_gutenberg.py`.
- Built GOI/KJV-aligned reference with `align_versification.py`.
- Verified `One_Directory_Almeida1911_GOI/` has 31,102 files and a zero-diff
  filename match against KJV.

Use this path for downstream reference work:

```bash
Reference_Bible/Portuguese_Bible_Almeida1911/One_Directory_Almeida1911_GOI
```

## Stage 1 — Portuguese Readiness Layer

Done:

- Registered `GOI_Pt` in `Meta_Bible_Data/sqlite/editions.json`.
- Added `PortugueseMatcher` to
  `Meta_Bible_Data/Bible_Noun_Extraction/matchers.py`.
- Generated and imported 2,369 Portuguese noun Strong's defaults from
  `proposed_pt_defaults.sql`.
- Added 17 Portuguese sense renderings.
- Added the name-QA profile at
  `Meta_Bible_Data/translation_configs/name_qa/pt.json`.
- Created the full GOI/KJV-aligned verse skeleton in `GOI_Bible/GOI_Bible_pt`
  with 31,102 pending files.

Verification:

```bash
python3 Meta_Bible_Data/Bible_Noun_Extraction/language_readiness.py --lang pt
python3 tools/translation_pipeline/goi_language_pipeline.py status GOI_Pt
```

Current state: readiness reports `pt` ready, and `GOI_Pt` has 31,102 files,
zero empty files, and zero bad filenames. The skeleton files contain
`__PT_TRANSLATION_PENDING__`; they are structural placeholders, not translated
verses.

## Stage 2 — NT Pilot

Done:

- Generated Philemon first as the live pilot.
- Added resume-safe `--overwrite-pending` support to
  `Meta_Bible_Data/Bible_Noun_Extraction/translate_verses.py`.
- Used the Almeida 1911 GOI-aligned reference as a structural QA hint, not as
  source text.

Pilot command shape:

```bash
python3 Meta_Bible_Data/Bible_Noun_Extraction/translate_verses.py \
  --lang pt --language-name "Portuguese" \
  --output-dir GOI_Bible/GOI_Bible_pt --filename-suffix GOI_Pt \
  --book PHM --overwrite-pending --reasoning-effort '' \
  --reference-dir Reference_Bible/Portuguese_Bible_Almeida1911/One_Directory_Almeida1911_GOI
```

Then normalized and ran noun coverage.

## Stage 3 — Full NT

Done:

- Generated all 7,957 NT verses into `GOI_Bible/GOI_Bible_pt`.
- Replaced every NT `__PT_TRANSLATION_PENDING__` placeholder.
- Normalization reported `normalized 0 of 31102 files`.
- Full NT noun coverage currently reports 28,840 ok / 0 missing, 100.0%.

Open QA:

- `Meta_Bible_Data/staging/reports/GOI_Pt_nt_coverage_missing.txt` is empty.
- Run false-friend checks, negation/number checks, proper-name consistency, and
  a clause completeness pass before staging a release DB.

## Stage 4 — OT Pipeline

Use the Spanish/Vietnamese OT playbook:

- WLC is the source.
- Almeida 1911 GOI-aligned text is reference/QA only.
- Build a Portuguese name QA profile before generation.
- Generate OT in book batches, then run name validation and corpus scans.

Progress:

- Added `tools/translation_pipeline/translate_ot_pt.py`, a WLC-first Portuguese
  generator with Almeida 1911 QA input, PT name grounding, resumable pending-file
  writes, and threaded verse generation.
- Completed the full OT: all 39 books and 23,145 verses are translated.
- Current PT OT status: 23,145 translated, 0 pending. The complete 31,102-file
  corpus has valid filenames and no empty files.
- Four non-overlapping resumable book-group processes were used for the final
  rollout; all completed successfully.

Torah command:

```bash
set -a; source .env; set +a
python3 tools/translation_pipeline/translate_ot_pt.py \
  --book GEN --book EXO --book LEV --book NUM --book DEU \
  --workers 4 --overwrite-pending --reasoning-effort ''
```

The generated verses are machine-drafted. Structural validation passes, while the
PT name validator currently reports 9 orange review flags. Name, number, negation,
clause, and Portuguese editorial QA passes remain before release staging.

## Vocabulary Decisions To Lock Early

- Divine name in OT: decide whether GOI Portuguese should use `SENHOR`,
  `Senhor`, or `JEHOVAH/Jeová`; Almeida 1911 commonly uses `Senhor JEHOVAH`.
- Register: decide whether to keep older Almeida-style second-person forms or
  normalize to modern European/Brazilian-neutral Portuguese.
- Orthography: Almeida 1911 is a reference, not a target style. The GOI output
  should probably use modern Portuguese spelling unless you explicitly want an
  archaic public-domain-style register.
