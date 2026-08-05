# GOI Vietnamese OT Green Audit - Final 31

Scope: green rows 126-156 from `GOI_vi_ot_smoke_lint.csv`.

Result: 20 concrete edits were applied.

## Correction Themes

- `PSA 51:11-19`: removed over-inserted `Đức Giê-hô-va` where the Hebrew uses direct address, `Adonai`, or `Elohim`; improved penitential vocabulary (`tâm linh đau thương`, `thống hối`, `sự cứu rỗi của Chúa`).
- `JOB 1:1`: corrected `kính sợ Đức Giê-hô-va` to `kính sợ Đức Chúa Trời`, matching Hebrew `Elohim`.
- `JOB 1:5`: corrected the key euphemism from "secretly reject YHWH" to "curse God in their heart."
- `JOB 1:11`: corrected the same curse/bless euphemism to `nguyền rủa Ngài trước mặt Ngài`.
- `JOB 1:12`: clarified that the possessions are Job's possessions.
- `JOB 1:16`: changed `trai trẻ` to `đầy tớ` in the report about destroyed servants.
- `JOB 1:18-19`: improved direct-address consistency and casualty wording.
- `JOB 1:21-22`: smoothed the closing confession and corrected "speak wrong about God" wording.

## Notes

This completes manual review coverage for all 156 smoke verses. The deterministic linter remains useful, but this full smoke audit shows that OT generation needs a second semantic-review/repair pass as a normal pipeline stage.
