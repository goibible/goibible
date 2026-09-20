# Arabic Resurrection Handoff — 2026-09-20

This file is the complete restart point for Arabic work after a reboot or a
fresh agent session.  Read it before starting any Arabic model request.

## Current checkpoint

- Root-repository Arabic Gospel draft commit: `029f17abb1` — 3,779 verse files
  in `GOI_Bible/GOI_Bible_ar/`:
  - Matthew: 1,071
  - Mark: 678
  - Luke: 1,151
  - John: 879
- This is a **draft checkpoint**, not a release or upload candidate.
- Current four-Gospel noun/Strong's gate: **95.2%** (`11,439 / 12,021`), with
  **582 unresolved anchors**.  One bracketed TR subscription anchor is skipped.
- Do not describe this draft as 100% complete or put it online.

## Durable QA queue

The nested repository `Meta_Bible_Data/Bible_Noun_Extraction` holds Arabic
tooling and its own Git history.

- QA report commit: `febce20`.
- Exact unresolved-anchor queue:
  `Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_gospels_noun_coverage_issues.md`.
- Generator:
  `Meta_Bible_Data/Bible_Noun_Extraction/ar/report_ar_gospel_coverage.py`.
- It records every unresolved coordinate, source word position, Strong's number,
  expected Arabic rendering, and the current verse text.  This report—not chat
  memory—is the repair queue.

Regenerate it after every repair batch:

```bash
cd /home/albert/projects/bible/Meta_Bible_Data/Bible_Noun_Extraction
/home/albert/miniconda3/bin/python3 ar/report_ar_gospel_coverage.py
/home/albert/miniconda3/bin/python3 verify_coverage.py \
  --lang ar --output-dir ../../GOI_Bible/GOI_Bible_ar --filename-suffix GOI_Ar \
  --book MAT --book MRK --book LUK --book JHN --require-complete
```

`--require-complete` must fail until the result is actually 100%; that is
expected during repair and is the release blocker.

## Completed pre-fill (not yet imported)

The DeepSeek/Flex, sequential, remaining-NT noun/Strong's pre-fill completed
all **1,164 / 1,164** requested entries.  Its review-only artifacts live in:

```text
Meta_Bible_Data/Bible_Noun_Extraction/ar/proposed_ar_rest_nt_defaults.csv
Meta_Bible_Data/Bible_Noun_Extraction/ar/proposed_ar_rest_nt_defaults.sql
```

The corresponding Gospel proposal ledger is also retained under `ar/`.
These are suggestions, not approved database changes.  Review/deduplicate them
and import only through the project’s normal noun-rendering gate; do not blindly
run the SQL patch.

## Mandated Arabic sequence

1. Repair the four-Gospel QA queue in bounded, reviewed batches.  Prefer
   legitimate Arabic orthography/inflection additions with positive examples;
   never loosen matching broadly just to raise the number.
2. Run structural, Arabic-script, duplicate, and noun/Strong's gates.  Keep
   evidence in the `ar/reports/` directory.
3. Do not start remaining-NT verse translation until the Gospel test corpus is
   at 100% and its gates pass.
4. Then translate the rest of the NT as one sequential DeepSeek Flex worker,
   with a durable systemd service and a separate 20-minute journal heartbeat.
5. Only after NT gates pass, do the OT noun/Strong's pre-fill, Torah pilot,
   Torah gates, and then the remaining OT.

## Model and process restrictions

- Only the consolidated DeepSeek configuration may be used.  Do not introduce
  NVIDIA/Nemotron or another LLM provider/model.
- Use Flex and **one** model worker.  A heartbeat reports state; it does not
  supervise or restart a failed process.
- Before launching, verify the exact configured model is `deepseek-*`, record
  output/log paths, and use absolute Python/config paths in the service.
- Never run a noun-anchor repair loop that retries the same coordinate without
  a changed matcher, prompt, or input.
- Never delete, overwrite, or zero-byte scaffold/reference material.  Preserve
  rejected drafts and audit artifacts.

## Relevant committed guardrails

Within the nested noun repository:

- `14b43b6` — translation execution guardrails (`AGENTS.md`)
- `2077102` — reviewed Arabic Gospel matcher forms
- `febce20` — Arabic exact QA report and generator

Root-repository policies and Arabic recovery documentation are under
`Meta_Bible_Data/Translation_Pipeline.md` and
`Meta_Bible_Data/docs/language_scaffolds/`.

## Worktree boundaries at handoff

- Arabic Gospel verse draft is committed in the root repository.
- Arabic pre-fill/review artifacts are intentionally retained in the nested
  repository; they are not database imports.
- Russian OT work may also exist in the nested repository.  Do not stage,
  edit, revert, or delete any `ru/` files while resuming Arabic.
- Root `Meta_Bible_Data/staging/reports/ar/recovery_2026-09-18/` is an existing
  recovery artifact.  Preserve it; do not move or delete it during Arabic work.
