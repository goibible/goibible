# Spanish Bible RV1909 Reference

Public-domain Spanish reference Bible (Reina-Valera, 1909 revision) from
eBible.org, downloaded for QA reference use while producing a new GOI Spanish
edition. **Not** the same as RVR1960 (Reina-Valera 1960), which is still
copyrighted (Sociedades Bíblicas Unidas) — do not substitute it here.

Source pages:

- `https://ebible.org/details.php?id=spaRV1909`
- `https://ebible.org/spaRV1909/copyright.htm`

Downloaded artifacts:

- `ZIP/spaRV1909_readaloud.zip` - plain text canon-only chapter files
- `ZIP/spaRV1909_usfm.zip` - structured USFM files (with inline Strong's tags)
- `SOURCE/details.html` - eBible details page
- `SOURCE/copyright.htm` - public-domain license/provenance page
- `SOURCE/readaloud/` - extracted chapter text files
- `SOURCE/usfm/` - extracted USFM files
- `atomize_usfm.py` - converts `SOURCE/usfm/*.usfm` into one-verse-per-file
  `One_Directory_RV1909/`; adapted from the Vietnamese VIE1934 atomizer, with
  an added strip step for this edition's inline `\w word|strong="G0976"\w*`
  Strong's-tagged word markers (VIE1934's USFM has no such markers)
- `One_Directory_RV1909/` - 31,084 atomized verse files (all 66 books; full
  OT + NT, unlike VIE1934 which only covers Genesis-Deuteronomy plus
  Job/Psalms/Proverbs/Isaiah), in RV1909's **native** (Hebrew/Byzantine
  tradition) versification — do not use this directory directly as a
  `--reference-dir`; see the alignment step below
- `align_versification.py` - realigns native RV1909 numbering onto the GOI
  project's own canonical spine (KJV-style, matching
  `Hebrew_Bible_WLC/One_Directory_WLC_KJV` and `Greek_Bible_TR1550`)
- `One_Directory_RV1909_GOI/` - **31,102 files, 0-diff filename match against
  `English_Bible_KJV/One_Directory_KJV`** — this is the directory to pass as
  `--reference-dir` for any Spanish generation/QA work

License/provenance summary from eBible:

- Title: `Santa Biblia — Reina Valera 1909`
- Language: `Español (Spanish)`, dialect `Castellano 1909`
- eBible ID: `spaRV1909` (abbreviation `RV1909`, alt id `SPNR09`)
- Translation by: Casiodoro de Reina (1569), revised by Cipriano de Valera
  (1602), this revision dated 1909
- Public Domain

This reference is for comparison and QA only. The GOI Spanish edition should
be translated from WLC/TR1550 source texts, not copied from this reference.
Never use a copyrighted Spanish edition (RVR1960, NVI, etc.) as a translation
source or sense-check.

## Versification alignment (done 2026-08-27)

RV1909 was atomized straight from its USFM at 31,084 verses — 18 short of the
project's 31,102-verse KJV/WLC/TR1550 spine. That 18-verse gap was **not**
missing content; it was a real, verified Hebrew/Byzantine-tradition
versification difference in 9 books, individually content-checked verse by
verse against KJV before writing `align_versification.py`'s correction table:

| Book | What happens in RV1909's native numbering |
|---|---|
| JON | 1:17 (KJV) becomes the native 2:1; whole ch2 runs one verse "ahead" until the last two verses (KJV 2:9-10) recombine into one native verse |
| HOS | same pattern, at the 11:12 -> 12:1 boundary |
| 1SA | same pattern, at the 23:29 -> 24:1 boundary |
| NUM | same pattern, twice: 12:16 -> 13:1, and 29:40 -> 30:1 |
| 2SA | no chapter-boundary carry; native 20:25 alone merges KJV 20:25+20:26 |
| ACT | no carry; native 19:40 alone merges KJV 19:40+19:41 |
| 2CO | no carry; native 13:12 merges KJV 13:12+13:13, native 13:13 = KJV 13:14 (the closing colophon after that has no KJV counterpart at all — paratext, not content loss) |
| 2CH | merge starts mid-chapter (native 33:10 merges KJV 33:10+11), then ch33 runs one verse "behind" through the end of the chapter; ch34 resyncs cleanly |
| JOB | the big one — the classic Behemoth/Leviathan (ch38-41) versification split: ch38 hands its last 3 verses to ch39; ch39 runs 3 "ahead" until a single native verse (39:30) absorbs 9 KJV verses (39:27-30 + 40:1-5) in one merge; ch40 then runs a constant 5 verses "ahead" of KJV to its end; ch41 (Leviathan) resyncs exactly, 41:1 = 41:1 |

Where a native RV1909 verse merges 2+ KJV verses, `align_versification.py`
writes that same (combined) Spanish text into **every** target verse-key it
covers, rather than guessing where to split it — this is reference-only
material, so preserving full information at each key beats silently dropping
half a merged verse. The remaining 57 books were a straight identity copy;
native numbering already matched KJV/GOI there.

Result: `One_Directory_RV1909_GOI/` has exactly 31,102 files, and
`diff <(ls One_Directory_RV1909_GOI | sed s/_RV1909//) <(ls ../English_Bible_KJV/One_Directory_KJV | sed s/_KJV//)`
is empty.

## GOI Spanish target naming (planned, not yet built)

- Corpus directory: `GOI_Bible/GOI_Bible_es`
- Edition id: `GOI_Es`
- BCP 47 tag: `es`
- Native display name: `Español - Biblia GOI`
- Verse filename shape: `NNN_BOOK_CCC_VVV_GOI_Es.txt`
- Example: `040_MAT_001_001_GOI_Es.txt`

See `/home/albert/projects/bible/PLANS_ES.md` for the full staged build plan.
