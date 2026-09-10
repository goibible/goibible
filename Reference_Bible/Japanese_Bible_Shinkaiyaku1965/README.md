# Shinkaiyaku 1965 New Testament (新改訳新約聖書)

Public-domain Japanese New Testament, used as the GOI Japanese NT
reference/name-QA text (analogous to RV1909 for Spanish, Almeida1911 for
Portuguese, KORSYS1911 for Korean).

- Edition: Shinkaiyaku (新改訳, "New Reformed Translation") New Testament,
  1965. Gospel of John first published 1963; full NT completed 1965.
- Language: Japanese (`ja`)
- Rights: Public Domain. Copyright expired 2015-12-31 per ebible.org's
  copyright page (https://ebible.org/jpn1965/copyright.htm); once
  dedicated to the public domain the status cannot be restored.
- Catalog record: https://ebible.org/find/details.php?id=jpn1965
- Downloaded source: `source/*.usfm` (27 NT books, clean per-verse USFM —
  not an OCR scan, unlike most other reference editions in this repo)
  from https://ebible.org/Scriptures/jpn1965_usfm.zip
- Coverage: New Testament only. There is no equivalent clean public-domain
  Japanese Old Testament text identified yet; see
  `Reference_Bible/Japanese_Bible_MeijiGenyaku1887/` for the OT reference
  candidate (1887, public domain by age, but OCR quality is currently too
  poor to use — needs real cleanup work before it's usable for QA).

## Alignment to GOI/KJV versification

`atomize_and_align.py` parses the USFM into `One_Directory_Shinkaiyaku1965/`
(native jpn1965 verse numbering) and then into
`One_Directory_Shinkaiyaku1965_GOI/` (KJV-numbered, matching every other
GOI-aligned reference directory in this repo). Because jpn1965 is a modern
translation, alignment is nearly 1:1 with KJV — of 7,957 NT verses, only 21
needed a `BOOK_OVERRIDES` entry (19 verse bridges where jpn1965 covers two
disputed KJV verses with one verse of text, plus two genuine verse-boundary
differences: 2 Corinthians 13:12-14 and the well-known Revelation 12:18/13:1
split). The script verifies 100% key coverage against
`Reference_Bible/English_Bible_KJV/One_Directory_KJV/` (0 missing, 0 extra)
and fails loudly if a future re-run doesn't match.

Rerun after re-downloading source: `python3 atomize_and_align.py`
