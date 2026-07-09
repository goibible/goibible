# bible — TR1550/WLC → any-language full-Bible translation pipeline

A pipeline to translate the Hebrew WLC (Old Testament) and Greek Textus
Receptus Stephanus 1550 (New Testament) into any language. Worked, verified
editions exist in English, Simplified Chinese, and Traditional Chinese —
31,102 verse files each, covering the whole Bible (Genesis → Revelation).

## Start here
- **Translating a new language?** → `docs/tr1550_language_translation_instructions.md`
  (master reference) and `docs/TRANSLATION_GUIDE.md` (short walkthrough).
- **What's verified / provenance / copyright?** → `docs/README_GOI.md`
- **Integrity gate:** `python3 validate.py` (run from this dir)
- **Single-file reading copies:** `full_bible/GOI_English_Bible.md`,
  `GOI_Simplified_Chinese_Bible.md`, `GOI_Traditional_Chinese_Bible.md`

## Top-level layout
| Path | What |
| --- | --- |
| `docs/` | all documentation (master instructions, guide, provenance, audit, chinese gameplan) |
| `GOI_Bible_English/`, `GOI_Bible_Chinese_Hans/`, `GOI_Bible_Chinese_Hant/` | finished full-Bible editions (31,102 verse files each) |
| `full_bible/` | consolidated single-markdown-file exports of each GOI edition + the generator script |
| `Bible_Noun_Extraction/` | pipeline tools + `bible_noun.sqlite3` (NT noun/sense DB) + raw Greek `One_Directory_TR1550/`. Local directory, not a git submodule. |
| `GOI_bible.sqlite3` | top-level project DB (current) |
| `English_Bible_KJV/`, `English_Bible_WEBUS/`, `Chinese_Bible_CUV/` | public-domain reference editions |
| `Greek_Bible_TR1550/`, `Hebrew_Bible_WLC/`, `sources/` | source corpora |
| `validate.py`, `normalize_corpus.py` | integrity gate (currently NT-scoped) + punctuation canonicalizer |
| `notes/`, `logs/`, `archive/` | prior-phase notes, run logs, and archived earlier project work (WLC, BCP47, atomizing) |
| `backup/` | archived earlier pipeline snapshots |

**Note:** `validate.py`'s automated checks are still NT-only (noun-occurrence
DB scoped to TR1550). OT and Chinese verification was done via separate
clause-check passes (all fully resolved) — see `docs/README_GOI.md` §3b for
the consolidated status, not yet folded into `validate.py` itself.
