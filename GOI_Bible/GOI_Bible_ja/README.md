# GOI Japanese Translation

Normalized, GOI/KJV-versification-aligned Japanese translation.

Filename format: `NNN_BOOK_CCC_VVV_GOI_Ja.txt`

## Status

- **New Testament: complete.** 27 books, 7,957 verses, translated from the
  Greek TR1550; noun coverage 28,840/28,840 (100%).
- **Old Testament: scaffolded, not yet translated.** To be translated from
  the Hebrew WLC with `Meta_Bible_Data/Bible_Noun_Extraction/translate_ot_ja.py`,
  noun anchors from `hebrew_ot_ja.sqlite3`, coverage checked with
  `verify_ja_ot_coverage.py`.

## Reference texts (secondary QA only — never copied here as the translation)

- NT: `Reference_Bible/Japanese_Bible_Shinkaiyaku1965/One_Directory_Shinkaiyaku1965_GOI/`
  (public domain, 100% KJV-aligned)
- OT: sibling GOI editions `GOI_Bible_Chinese_Hant/` and `GOI_Bible_English/`
  for every verse (same Global Ordinal Index, so verse-for-verse with no
  alignment; both translated from the same Hebrew). Supplemented by
  `Reference_Bible/Japanese_Bible_MeijiGenyaku1887/One_Directory_Meiji1887_GOI/`
  (public domain, Wikisource transcription; 21,645/23,145 verses — Numbers
  2-36 and 1 Samuel 2:1-13:21 were never transcribed).
