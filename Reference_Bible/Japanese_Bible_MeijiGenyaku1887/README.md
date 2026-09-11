# Meiji Genyaku Bible (明治元訳聖書) — Old Testament reference

Public-domain Japanese Old Testament used as the GOI Japanese OT
reference/name-QA text (the NT counterpart is
`Reference_Bible/Japanese_Bible_Shinkaiyaku1965/`). It is a secondary
reference only: GOI_Ja is translated from the Hebrew WLC.

- Translation: Meiji Genyaku ("Meiji Original Translation"), the first
  complete Japanese Bible; OT completed 1887. Classical (文語) register.
- Rights: Public Domain (`{{PD-old}}` on Wikisource).

## Usable source: Wikisource transcription (`source_wikisource/`)

Raw wikitext of all 39 books of 明治元訳旧約聖書 (文語訳) from
ja.wikisource.org, hand-typed from the Japan Bible Society 舊新約聖書
printing (1937/1953; the 1937 printing is NDL digital collection
3456426). Fetched with `action=raw`; 16 book titles are redirects to a
variant title with a space before the parenthesis, and those were
followed.

`atomize_and_align.py` handles both markup styles found on the pages
(`{{verse|C|V}}` and `==== C:V ====`), strips ruby/links/templates,
decodes HTML entities, and writes:

- `One_Directory_Meiji1887/` — native verse numbering
- `One_Directory_Meiji1887_GOI/` — KJV-keyed, 21,645 of 23,145 OT verses
- `alignment_report.txt` — per-book result

Alignment status: **0 misaligned, 0 extra.** 37 books match KJV
exactly. The rest:

- **Merged verses (20 places):** the Meiji text folds a KJV verse into a
  neighbouring verse (e.g. Exodus 7:24 ends with 7:25's 七日たちぬ,
  Proverbs 26:17 carries 26:18-19, Psalm superscriptions). Each was
  confirmed by reading the Meiji text against the KJV; the merged text is
  copied to every KJV verse it covers (`BOOK_OVERRIDES`).
- **Not transcribed on Wikisource (1,500 verses):** Numbers 2-36 and
  1 Samuel 2:1-13:21. No Meiji text exists for these. This is not a
  coverage gap for the translator: its main secondary references are the
  sibling GOI editions (GOI_Zh_Hant and GOI_En), which share the Global
  Ordinal Index and cover every verse; the Meiji text is a supplement
  where it exists.

## Unusable source: archive.org OCR (`source/`)

`source/meijigenyaku-pt{1..5}-*.txt` are the `_djvu.txt` OCR layers of
the five-volume 1887 scan on archive.org. The OCR of the vertical,
furigana-set print is unreadable (scrambled kanji/kana with stray
Latin/digits). Kept only as a provenance record; do not use.
