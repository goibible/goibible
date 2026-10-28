# GOI Bible Icelandic

Status: **full Bible drafted, 31,102 verse files** (NT 7,957 + OT 23,145). Registered in `Meta_Bible_Data/sqlite/editions.json` as `GOI_Is`, status `pending` until `verify_language.py --lang is` reports ALL PASS.

- NT: translated from TR1550 by Claude, then hand-revised verse by verse against the Greek (2026-10-26/27, MAT 1 - REV 22: suffixed articles, case, register, TR sense). Fixes are recorded in `Meta_Bible_Data/Bible_Noun_Extraction/is/translation/text_fixes.tsv`. TR bracketed subscriptions and end titles are left out (owner ruling 2026-10-24); their translations are in `is/translation/batches/*/quarantine/`.
- OT: translated from the WLC by Claude (463 batches, `is/translation_ot/`), assembled with `is/translation_ot/assemble_ot.py`. Divine names: YHWH = Jahve, Adonai = Drottinn, Elohim = Guð (owner 2026-10-26). OT text fixes: `is/translation_ot/text_fixes.tsv`. Not yet hand-revised like the NT.
- No native review. Machine draft quality: expect case and idiom errors, more in the OT poetic books.

Target edition only. Not a source and not a reference. The 1912 Icelandic Bible is never consulted for the text.
