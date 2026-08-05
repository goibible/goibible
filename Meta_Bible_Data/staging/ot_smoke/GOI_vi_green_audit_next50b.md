# GOI Vietnamese OT Green Audit - Next 50b

Scope: green rows 76-125 from `GOI_vi_ot_smoke_lint.csv`.

Result: 22 concrete edits were applied.

## Correction Themes

- `PSA 22:1-2`: corrected address from `Đức Giê-hô-va tôi` to `Đức Chúa Trời tôi` because the Hebrew has `Eli/Elohai`, not `YHWH`.
- `PSA 22:4-5, 10, 20-22, 25`: removed inserted divine-name wording where the Hebrew uses direct address or pronouns.
- `PSA 22:8`: repaired the mockery line, which had become an awkward command instead of "He trusted in YHWH; let Him deliver him."
- `PSA 22:18`: changed `ta` to `tôi` to match the rest of the psalm.
- `PSA 22:29`: fixed a serious semantic error: `linh hồn Ngài` was wrong; the line refers to those who cannot keep themselves alive.
- `PSA 23:4-5`: restored direct address to `Chúa` where the psalm turns from speaking about YHWH to speaking to Him.
- `PSA 23:6`: changed `Nhưng` to `Quả thật`.
- `PSA 51:1, 4, 8-10`: corrected divine address/pronouns and improved repentance-language fluency.

## Notes

This pass confirms Psalms need the highest human-review density. The deterministic linter was green, but the poetry still had divine-name over-insertion, pronoun drift, and one major meaning error.
