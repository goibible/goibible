# Active GOI script-gate baseline — 2026-09-14

Command:

```bash
python3 tools/translation_pipeline/verify_language_script.py --all-active
```

| Edition | Result | Findings |
|---|---|---|
| `GOI_En` | pass | Latin/common/inherited only |
| `GOI_Zh_Hant` | pass | Han/Latin/common/inherited only |
| `GOI_Zh_Hans` | pass | Han/Latin/common/inherited only |
| `GOI_vi` | fail | 2 Arabic characters in `PSA 148:3` |
| `GOI_Es` | fail | 224 Hebrew characters, beginning `EST 2:3` |
| `GOI_Pt` | fail | 24 Han characters in `NUM 7:81`; 422 Hebrew characters, beginning `DEU 28:18` |
| `GOI_Ko` | fail | 90 Hebrew characters in `EXO 12:34`; 111 Bengali characters in `2CH 10:4`; 10 Greek characters in `ROM 3:16` |

These are blocking post-translation character-quality defects. They are not
profile exceptions and must be removed/retranslated, then retro-checked in all
active GOI languages through `cross_language_regressions.csv`.
