# GOI Vietnamese OT Green Audit - Next 50

Scope: next 50 `green` rows from `GOI_vi_ot_smoke_lint.csv`, rows 26-75 after the first-25 audit.

Result: 27 concrete edits were applied.

## Correction Themes

- `LEV 18:11-15`: standardized the prohibition euphemism to `phơi bày sự trần truồng` and avoided mixed forms like `vén`, `để lộ`, and `lõa thể`.
- `ISA 52:14`: corrected the pronoun from `ngươi` to `người` and made the disfigurement clause clearer.
- `ISA 53:3-7`: tightened servant pronoun consistency and restored the oppressed/afflicted clause in verse 7.
- `PRO 10`: improved parallelism and corrected clause direction in verses 6 and 11 where violence covers the wicked mouth, not the wicked mouth hiding violence.
- `PSA 1`: smoothed delight/meditation language and changed `thạnh vượng` to `thịnh vượng`.
- `PSA 2`: corrected `sắc lệnh`, `thịnh nộ`, capitalization, and second-person address in verse 9.

## Notes

These were all green under deterministic lint. The audit shows the value of sampling green rows: the linter catches known mechanical failures, but human/semantic review still catches wording direction, pronoun consistency, and parallelism quality.
