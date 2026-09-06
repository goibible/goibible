# Portuguese Bible Almeida 1911 Reference

Public-domain Portuguese reference Bible from Project Gutenberg ebook 62383.
This is the 1911 Lisbon reprint of João Ferreira d'Almeida, Revista e
Corrigida, with old Portuguese orthography.

Source:

- `https://www.gutenberg.org/ebooks/62383`
- `SOURCE/gutenberg_62383_almeida1911.txt`

License/provenance summary:

- Title: `A Biblia Sagrada`
- Translator tradition: João Ferreira d'Almeida
- Edition: Revista e Corrigida, Lisbon, 1911 reprint
- Project Gutenberg metadata: Public domain in the USA

Generated artifacts:

- `atomize_gutenberg.py` parses the Gutenberg plain text into native
  one-verse-per-file output.
- `One_Directory_Almeida1911/` contains 31,094 native Almeida verse files.
- `align_versification.py` maps native Almeida numbering onto the GOI/KJV spine.
- `One_Directory_Almeida1911_GOI/` contains 31,102 files and has a zero-diff
  filename match against `Reference_Bible/English_Bible_KJV/One_Directory_KJV`.

Use `One_Directory_Almeida1911_GOI/` as the Portuguese `--reference-dir` for
GOI generation and QA. Do not use the native directory directly downstream.

Known source/parser notes:

- Gutenberg prints verse 1 of each chapter with the chapter number.
- Lamentations uses acrostic labels before verse numbers.
- Some verse starts are printed inline after the previous verse.
- Mark 4:34 is printed as `31`; `atomize_gutenberg.py` maps that source marker
  to the correct GOI key.
- The GOI alignment currently has 8 native verses that map to multiple KJV/GOI
  keys: Numbers, 1 Samuel, 2 Samuel, 2 Chronicles, Jonah, Acts, and
  2 Corinthians. Hosea and Job were checked and follow the KJV split in this
  Portuguese source.

