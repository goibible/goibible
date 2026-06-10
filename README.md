# bible — TR1550 → any-language NT translation pipeline

A pipeline to translate the Greek Textus Receptus (Stephanus 1550) New Testament
into any language, with a worked, verified English edition.

## Start here
- **Translating a new language?** → `docs/tr1550_language_translation_instructions.md`
  (master reference) and `docs/TRANSLATION_GUIDE.md` (short walkthrough).
- **What's verified / provenance / copyright?** → `docs/README_GOI.md`
- **Integrity gate:** `python3 validate.py` (run from this dir)

## Top-level layout
| Path | What |
| --- | --- |
| `docs/` | all documentation (master instructions, guide, provenance, audit, chinese gameplan) |
| `GOI_Bible_English/` | finished English edition (7,957 verse files) |
| `Bible_Noun_Extraction/` | the pipeline + database (submodule): tools, `bible_noun.sqlite3`, raw Greek `One_Directory_TR1550/` |
| `English_Bible_KJV/`, `English_Bible_WEBUS/`, `Chinese_Bible_CUV/` | public-domain reference editions |
| `Greek_Bible_TR1550/`, `Hebrew_Bible_WLC/`, `sources/` | source corpora |
| `validate.py`, `normalize_corpus.py` | integrity gate + punctuation canonicalizer |
| `notes/`, `logs/`, `archive/` | prior-phase notes, run logs, and archived earlier project work (WLC, BCP47, atomizing) |
| `backup/` | archived earlier pipeline snapshots |
