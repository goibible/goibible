# GOI English Missing-File Queue - First 50

Scope: first 50 rows from the original `missing_file` queue in `goi_en_source_name_audit.csv`.

Result:

- `mapped_pass`: 50
- `mapped_review`: 0
- `no_map_found`: 0

Conclusion: the first 50 are not missing English content. They are WLC source-addresses that landed at KJV/GOI addresses after the earlier OT realignment.

Examples:

- `GEN 32:33` maps to `GEN 32:32`.
- `EXO 7:26` maps to `EXO 8:1`.
- `LEV 5:20` maps to `LEV 6:1`.
- `NUM 17:14` maps to `NUM 16:49`.
- `DEU 28:69` maps to `DEU 29:1`.

CSV detail: `staging/source_names/goi_en_missing_file_first50_prelim.csv`

Follow-up applied: `scripts/audit_english_source_names.py` now accepts the existing WLC-to-GOI/KJV realignment map and treats mapped hits as passes.
