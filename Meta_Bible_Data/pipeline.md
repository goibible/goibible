# GOI Bible Translation Pipeline

This file is the handoff runbook for generating, auditing, and packaging GOI
Bible language editions. It is written so another inference engine can resume
the work without relying on chat history.

## Core Rules

- Translation must be made only from the original-language source text.
- NT translation source: Greek, using TR1550 as the default verse spine plus
  documented textual-policy overrides where older reliable evidence governs.
- OT translation source: Hebrew, using WLC/MorphHB plus MorphHB/KJV verse mapping
  notes where source and display verse boundaries differ.
- Any other Bible version, including VIE1934, WEBUS, KJV, GOI English, and GOI
  Chinese, is reference-only. Use those versions mostly for noun/name checks,
  numbers, structure sanity, and inherited terminology review. Do not translate
  from them, copy them, or let them overrule Hebrew/Greek.
- Keep one verse per flatfile. Do not allow all-or-nothing batch generation.
- Every generation step must be incremental, resumable, and verbose.
- Naming uses BCP 47 style edition ids where practical. Vietnamese is `GOI_vi`.
- Flatfile names must follow:

```text
NNN_BOOK_CCC_VVV_EDITION.txt
```

Example:

```text
040_MAT_001_001_GOI_vi.txt
```

## Important Paths

- Edition catalog: `sqlite/editions.json`
- Vietnamese NT flatfiles: `GOI_Bible_vi/`
- Vietnamese OT staging: `staging/ot_torah/GOI_Bible_vi/`
- Public app DB downloads: `goi_db_download/`
- Canonical source-name DB: `staging/source_names/biblical_source_names.sqlite3`
- Textual policy notes: `staging/textual_policy/README.md`
- Textual policy table: `staging/textual_policy/nt_textual_policy.csv`
- Vietnamese name QA profile: `translation_configs/name_qa/vi.json`
- Language orchestrator: `scripts/goi_language_pipeline.py`

## Model Configuration

Most generation scripts use `Bible_Noun_Extraction/llm_client.py`.

Required environment for OpenAI-compatible providers:

```bash
export LLM_PROVIDER=openai
export OPENAI_BASE_URL='http://192.168.1.88:11434/v1'
export OPENAI_MODEL='qwen3.5:9b'
export OPENAI_API_KEY='local'
export LLM_TIMEOUT=120
```

For DeepInfra or another hosted OpenAI-compatible provider, set the provider's
base URL, model, and real API key instead. The local Ollama-style endpoint may
ignore the key, but the client still expects `OPENAI_API_KEY` to be set.

### OT Torah Generation Model

Torah generation (`scripts/translate_ot_smoke_vi.py` pointed at a Torah refs
manifest) is calibrated for `Qwen/Qwen3-235B-A22B-Instruct-2507`. This is a
large MoE model, not one of the local Ollama models — run it through a hosted
OpenAI-compatible provider (e.g. DeepInfra, OpenRouter, Together):

```bash
export LLM_PROVIDER=openai
export OPENAI_BASE_URL='https://api.deepinfra.com/v1/openai'   # or your provider
export OPENAI_MODEL='Qwen/Qwen3-235B-A22B-Instruct-2507'
export OPENAI_API_KEY='<real key>'
export LLM_TIMEOUT=120
```

Required generation settings, already the script defaults:

- Temperature: 0.1-0.2 (`--temperature 0.15` default).
- Exactly one verse per response, no verse number, no markdown, no commentary
  (`strip_response()` cleans stray formatting, but the model must not add notes).

The biggest failure mode with this model is not Vietnamese fluency — it is
smoothing over Hebrew subject/action structure or drifting toward VIE1934's
wording as if it were the source. Genealogies are the sharpest test: the
named person must be the one who lives, begets, and dies, not a neighboring
verse's subject and not God. See `staging/ot_torah/TORAH_RUN_STATUS.md` for
concrete past failures of this kind and how the prompt was hardened in
response.

`scripts/translate_ot_smoke_vi.py` now grounds names at generation time
instead of only catching drift afterward: for each verse it looks up
already-approved Vietnamese name spellings from
`staging/ot_names/ot_names.sqlite3` and injects them into the prompt
(`--names-db`, on by default; `--no-names-db` to disable). This is why the
repair pass mattered before resuming generation — the DB has to be clean for
the grounding to help rather than propagate a bad mapping. Confirmed working
on the Methushael (GEN 4:18) vs Methuselah (GEN 5:21) genealogy collision:
both now generate correctly in one pass with no post-hoc fix needed.

### VIE1934 coverage gap (Joshua onward)

`Vietnamese_Bible_VIE1934/One_Directory_VIE1934` only covers Genesis-Deuteronomy
plus Job, Psalms, Proverbs, and Isaiah — about 11,590 of the OT's 23,145
verses. Everything else (Joshua, Judges, Ruth, Samuel, Kings, Chronicles,
Ezra, Nehemiah, Esther, Ecclesiastes, Song of Songs, Jeremiah, Lamentations,
Ezekiel, Daniel, and the Minor Prophets) has no Vietnamese reference at all.

`get_reference()` in `translate_ot_smoke_vi.py` falls back to
`English_Bible_KJV/One_Directory_KJV` for those verses, with the system
prompt adjusted to explicitly warn the model not to let English phrasing
leak into the Vietnamese (KJV is QA-only, same as VIE1934, just a different
cross-check language).

Important limitation: the per-verse name-grounding lookup only checks
`name_occurrences` for the exact verse, which is populated by scanning
VIE1934 text. For KJV-fallback verses there is no VIE1934 occurrence to
match, so grounding is effectively empty even for names already established
elsewhere (e.g. "Môi-se" for Moses, well-established from Exodus, gets no
grounding boost in Joshua). WLC Hebrew remains the authoritative source
either way; for these books the main quality gate is the same post-hoc
WLC/reference cross-check-and-repair process proven out on Genesis 1-25, run
after generation rather than injected before it.

## Edition Registration

Each edition must be listed in `sqlite/editions.json`.

Vietnamese current entry:

```json
{
  "edition_id": "GOI_vi",
  "bcp47_tag": "vi",
  "language_subtag": "vi",
  "display_name": "Tiếng Việt - Kinh Thánh GOI",
  "status": "pending",
  "flatfile_dir": "GOI_Bible_vi",
  "filename_suffix": "GOI_vi",
  "template_edition": "TR1550"
}
```

Use `GOI_vi` in filenames and package ids. The BCP 47 language tag is `vi`.

## NT Generation

The NT uses the Greek noun-anchored pipeline in `Bible_Noun_Extraction`. The
Greek verse and Greek Strong's anchors are the translation basis. Any
`--reference-dir` is only a noun/name and structure QA aid.

Preflight:

```bash
python3 scripts/goi_language_pipeline.py status GOI_vi
python3 scripts/goi_language_pipeline.py readiness GOI_vi
```

Generate the whole NT incrementally:

```bash
python3 scripts/goi_language_pipeline.py generate-nt GOI_vi \
  --language-name Vietnamese \
  --reference-dir Vietnamese_Bible_VIE1934/One_Directory_VIE1934 \
  --timeout 120 \
  --max-attempts 5
```

The generator skips existing non-empty files and retries failed books. This is
intentional: never delete good work just because a later request failed.

Generate one book directly when debugging:

```bash
python3 Bible_Noun_Extraction/translate_verses.py \
  --lang vi \
  --language-name Vietnamese \
  --output-dir GOI_Bible_vi \
  --filename-suffix GOI_vi \
  --book MAT \
  --reference-dir Vietnamese_Bible_VIE1934/One_Directory_VIE1934
```

## NT Audit Gates

After generation or edits, run coverage:

```bash
python3 scripts/goi_language_pipeline.py coverage GOI_vi
```

This writes a missing-only report to:

```text
staging/reports/GOI_vi_coverage_missing.txt
```

Then run source-name coverage against the canonical source-name database:

```bash
python3 scripts/build_source_name_db.py --rebuild
python3 scripts/audit_vietnamese_nt_source_names.py
```

Expected clean NT gate:

```text
missing expected form: 0
no Vietnamese form available from profile: 0
missing Vietnamese verse files: 0
```

The output files are:

```text
staging/source_names/goi_vi_nt_source_name_audit.csv
staging/source_names/goi_vi_nt_source_name_audit_summary.md
```

Also rerun English after changes to shared textual policy or source-name
suppressions:

```bash
python3 scripts/audit_english_source_names.py
```

## NT Textual Policy

Bracket convention:

- `[]` means conflicted ancient reading. Early evidence exists on both sides.
- `{}` means supplemental traditional material. It is preserved from the TR or
  church tradition but is not the earliest-mainline text.
- No brackets means translate the preferred source reading normally.

Current important decisions:

- `ROM 12:11`: use "serving the Lord"; no brackets.
- `MAT 6:13`: bracket the doxology with `{}`.
- `MRK 16:9-20`: retain with `{}`.
- `LUK 22:43-44`: retain with `[]`.
- `LUK 23:34a`: retain with `[]`.
- `JHN 5:3b-4`: retain with `{}`.
- `JHN 7:53-8:11`: retain with `{}`.
- `ACT 8:37`: retain with `{}`.
- `1TI 3:16`: use the older critical reading, "He who/Đấng..."
- `1JN 5:7-8`: follow the shorter early text.

These decisions are language-neutral. Apply them to every future translation.

## Canonical Source-Name Layer

Build it with:

```bash
python3 scripts/build_source_name_db.py --rebuild
```

This creates:

```text
staging/source_names/biblical_source_names.sqlite3
```

Main tables:

- `source_name_entities`: one canonical source entity per source Strong's key.
- `source_name_occurrences`: every contextual source occurrence by verse.
- `source_verse_references`: MorphHB/WLC source refs and mapped display refs.
- `source_name_links`: Greek-to-Hebrew dictionary links.

This replaces simple noun-count QA for names. It preserves source language,
Strong's id, lemma, morphology, verse context, and cross-testament links.

Do not build canonical entities from VIE1934, KJV, WEBUS, or GOI translations.
Those are target/reference forms mapped onto source entities later.

## OT Generation Strategy

OT work should proceed in small staged batches. The Hebrew WLC/MorphHB verse is
the translation basis. Reference editions are only noun/name, number, and
structure QA aids.

Current conservative plan:

1. Generate Genesis 1-25 in staging.
2. Build and confirm the reusable name database.
3. Repair name/divine-title issues.
4. Only then continue through Torah.

Staged OT output currently belongs here:

```text
staging/ot_torah/GOI_Bible_vi/
```

The target language profile is:

```text
translation_configs/name_qa/vi.json
```

For smoke-test style OT generation, use:

```bash
python3 scripts/translate_ot_smoke_vi.py \
  --refs staging/ot_smoke/ot_smoke_refs.json \
  --output-dir staging/ot_smoke/GOI_Bible_vi \
  --review staging/ot_smoke/GOI_vi_ot_smoke_review.md
```

For Genesis 1-25/Torah staging, use the active OT staging scripts and manifests
already under `staging/ot_torah/`. Keep generation incremental and skip existing
non-empty verse files unless deliberately reviewing a verse.

Current live status is tracked in `staging/ot_torah/TORAH_RUN_STATUS.md` —
check it before resuming generation. As of the last update, generation is
paused at `GEN 11:15` (282 files staged) pending name QA repair; do not resume
past that point until the red/orange rows in the name QA pass below are
closed.

## OT Name QA

Use the generic name QA database so future languages benefit from the same model.

Build and validate the Vietnamese OT name map:

```bash
python3 scripts/build_ot_name_db.py --profile vi --rebuild --validate --export-confirm \
  --refs staging/ot_torah/genesis_1_25_refs.json \
  --batch genesis_1_25
```

Compatibility wrapper:

```bash
python3 scripts/build_vi_ot_name_db.py --rebuild --validate --export-confirm \
  --refs staging/ot_torah/genesis_1_25_refs.json \
  --batch genesis_1_25 \
  --flags staging/ot_names/genesis_1_25_name_flags.csv \
  --confirm staging/ot_names/genesis_1_25_name_confirm.csv
```

Review outputs:

```text
staging/ot_names/genesis_1_25_name_flags.csv
staging/ot_names/genesis_1_25_name_confirm.csv
staging/ot_names/ot_names.sqlite3
```

Severity handling:

- `red`: known bad variant. Repair the verse text.
- `orange`: expected source/reference name missing. Inspect and either repair or
  document why the target wording is acceptable.
- `yellow`: candidate name form not mapped yet. Approve, correct, or suppress.
- `green`: likely acceptable but worth spot-checking when the profile changes.

After fixing forms, rerun the name DB command until red is zero and orange/yellow
rows are closed or intentionally accepted.

## Packaging

Before building app downloads:

```bash
python3 scripts/goi_language_pipeline.py check-flatfiles GOI_vi
python3 scripts/goi_language_pipeline.py normalize GOI_vi
python3 scripts/goi_language_pipeline.py readiness GOI_vi
python3 scripts/goi_language_pipeline.py coverage GOI_vi
```

Package SQL and app download DB:

```bash
python3 scripts/goi_language_pipeline.py stage GOI_vi
```

This runs checks, normalization, readiness, coverage, SQL build, shell rebuild,
and app download DB build.

Direct commands if needed:

```bash
python3 sqlite/build_buffet.py GOI_vi
bash sqlite/build_shell.sh
python3 goi_db_download/build_downloads.py GOI_vi
```

Outputs:

```text
sqlite/versions/GOI_vi.sql
goi_db_download/GOI_vi.db
goi_db_download/manifest.json
```

For English after shared source/text edits:

```bash
python3 full_bible/generate_markdown_bible.py --edition GOI_En --overwrite
python3 sqlite/build_buffet.py GOI_En
python3 goi_db_download/build_downloads.py GOI_En
```

## Clean Release Checklist

Run this before handing off or publishing a language edition:

```bash
python3 scripts/goi_language_pipeline.py status GOI_vi
python3 scripts/goi_language_pipeline.py check-flatfiles GOI_vi
python3 scripts/goi_language_pipeline.py readiness GOI_vi
python3 scripts/goi_language_pipeline.py coverage GOI_vi
python3 scripts/build_source_name_db.py --rebuild
python3 scripts/audit_vietnamese_nt_source_names.py
python3 scripts/goi_language_pipeline.py stage GOI_vi
```

For a clean NT, confirm:

- 7,957 Vietnamese NT flatfiles exist.
- No zero-byte files exist.
- Filename suffix is `GOI_vi`.
- Noun coverage has no unexplained misses.
- Source-name audit has zero active missing/no-form rows.
- Textual-policy bracket verses have been applied.
- `sqlite/versions/GOI_vi.sql` and `goi_db_download/GOI_vi.db` were regenerated.

## Resume Rules

- Prefer status and audit commands before generating more text.
- Never bulk overwrite a whole book unless the user explicitly asks.
- Fix one known class of issues, rerun the relevant audit, then continue.
- If generation stalls, lower batch size before changing models.
- If a local model is too weak on Hebrew or Vietnamese, switch model but keep the
  same files, prompts, and audit gates.
- Treat `staging/` reports as review artifacts. Treat `goi_db_download/` as the
  public app-facing payload.
