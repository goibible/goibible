# Meiji Genyaku Bible (明治元訳聖書, 1887)

Public-domain full Japanese Bible (OT+NT), preserved as a candidate GOI
Japanese Old Testament reference/name-QA text. **Not yet usable** — see
Status below.

- Edition: Meiji Genyaku ("Meiji Original Translation") Bible, 1887 —
  the first complete Bible translation into Japanese, published in 5
  volumes by the National Bible Society of Scotland, Yokohama.
- Language: Japanese (`ja`), historical/classical register (文語)
- Rights: Public Domain (1887 publication; also cataloged under
  archive.org's Folkscanomy collection as JPNKYZ "Public Domain" on
  https://find.bible/bibles/JPNKYZ/)
- Source records / downloads (5 volumes, archive.org, OCR'd djvu text
  export):
  - pt1 Genesis-Deuteronomy: https://archive.org/details/meijigenyaku-pt1-genesis-deuteronomy
  - pt2 Joshua-Esther: https://archive.org/details/meijigenyaku-pt2-josh-esther
  - pt3 Job-Song of Songs: https://archive.org/details/meijigenyaku-pt3-job-song
  - pt4 Isaiah-Malachi: https://archive.org/details/meijigenyaku-pt4-isa-mal
  - pt5 Matthew-Revelation (NT): https://archive.org/details/meijigenyaku-pt5-matt-rev
  - Downloaded as `source/meijigenyaku-pt{1..5}-*.txt` (`_djvu.txt` OCR
    text layer from each item)

## Status: OCR quality too poor to use as-is

Unlike the Shinkaiyaku 1965 NT (clean structured USFM), this text is an
OCR export of a 19th-century vertical-print scan with historical kana
orthography and furigana. The uploader's own notes say image processing
"eaten away" characters, and spot-checking confirms the OCR text is not
usable even as loose reading material — it is a scramble of kanji,
katakana, and stray Latin/digit noise with no reliable verse markers
surviving the OCR pass.

This directory is retained as source material and provenance record only.
It is **not** atomized into GOI/KJV-aligned verse files (no
`One_Directory_MeijiGenyaku1887*/` exists yet), and must not be used for
name QA or any other purpose until someone either re-OCRs the underlying
scans with a CJK-vertical-text-aware engine, or a cleaner public-domain
Japanese OT source is found. The future `GOI_Ja` translation itself will
still be generated directly from the Hebrew WLC / Greek TR1550 sources,
same as every other GOI edition — this text is reference/QA material only,
never a translation base.
