# OT Name QA

This staging area keeps the reusable proper-name database for OT translation work.

## Files

- `ot_names.sqlite3`: reusable SQLite database of canonical name entities, language forms, verse occurrences, and validation flags.
- `genesis_1_25_name_flags.csv`: verse-level flags for the current partial Genesis 1-25 staging output.
- `genesis_1_25_name_confirm.csv`: grouped confirmation list for deciding whether each observed form is approved, a variant to fix, or a new mapping.

## Database Shape

The generic model is one canonical name entity to many verse occurrences:

- `name_entities`: one row per canonical name key. This will hold names of God, people, and places via `entity_type`.
- `name_forms`: language-specific approved/candidate/variant spellings mapped to the canonical entity.
- `entity_occurrences`: every observed or expected occurrence of that entity in a verse.
- `validation_flags`: batch-level QA flags used to build confirmation reports.

The next language should add a profile under `translation_configs/name_qa/` and reuse `scripts/build_ot_name_db.py`.

## Current Batch

- Batch: `genesis_1_25`
- GOI output directory: `staging/ot_torah/GOI_Bible_vi`
- Manifest: `staging/ot_torah/genesis_1_25_refs.json`
- Current staged files: 282, ending at `GEN 11:15`

Fresh name validation:

- `red`: 18 known bad variants to repair.
- `orange`: 84 expected names missing from generated text; these need review because some are paired with an alternate candidate form.
- `yellow`: 41 unmapped candidate names needing approval or correction.

## Workflow

1. Generate a staged batch incrementally.
2. Rebuild the name DB from the configured reference edition and staged GOI output.
3. Review `*_name_confirm.csv` by name form, not verse by verse.
4. Add approved forms or known corrections to that language's profile.
5. Repair red variants in staged GOI files.
6. Re-run validation until red is zero and yellow/orange rows are either mapped or intentionally accepted.
7. Resume generation only after the current name map is stable.

Run:

```bash
python3 scripts/build_vi_ot_name_db.py --rebuild --validate --export-confirm \
  --refs staging/ot_torah/genesis_1_25_refs.json \
  --batch genesis_1_25 \
  --flags staging/ot_names/genesis_1_25_name_flags.csv \
  --confirm staging/ot_names/genesis_1_25_name_confirm.csv
```

Generic command:

```bash
python3 scripts/build_ot_name_db.py --profile vi --rebuild --validate --export-confirm \
  --refs staging/ot_torah/genesis_1_25_refs.json \
  --batch genesis_1_25
```
