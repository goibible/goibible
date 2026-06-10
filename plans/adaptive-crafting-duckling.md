# Plan: Hebrew OT (WLC) → Traditional Chinese — Pipeline Gameplan

## Context

The Greek NT → Traditional Chinese pass is complete and gated (`validate_zh.py` passes
all 12 checks, 97.3% noun coverage, `clause_check_nt_zh.py` running clean). To
produce a **complete, copyright-free Traditional Chinese Bible**, the same rigor needs
to be applied to the Hebrew Old Testament (39 books, 23,213 verses, WLC source).

This plan does **not** execute the translation — it defines the staged build-out of
the OT pipeline (mirroring the proven NT architecture) so a fresh session can pick it
up phase by phase. Output target: Traditional Chinese only, written into the **same**
`GOI_Bible_Chinese_Hant/` directory (OT books use canon prefixes 001–039, NT uses
040–066 — no filename collision, yields one unified 31,170-verse corpus).

**Decision:** extend the existing `Bible_Noun_Extraction/bible_noun.sqlite3`
rather than spinning up a parallel DB. In practice, the shared DB is only
partially language-neutral: `senses` / `sense_renderings` are shared, but OT noun
resolution now correctly uses `noun_translations(noun_id, target_lang, zh_translation)`
because Greek and Hebrew Strong's integers collide in the same numeric space.

---

## Session Log

The implementation log requested in the original planning session has been written:

- `logs/ot_phase2_noun_extraction_and_kjv_crosscheck.log`

That log now includes:
1. Phase 1 alignment final resolution
2. Phase 2 noun extraction and the WLC-vs-KJV cross-check bug/fix cycle
3. Phase 3 completion on the OT-safe `noun_translations` path
4. Final verification figures and targeted proper-name QC notes

---

## Status / Checkpoint Log (READ THIS FIRST in every session)

Update this table at the end of every session — it is the single source of truth for
"where are we." Each phase has a hard **Definition of Done** gate; do not start the
next phase until the current one's gate is checked off and verified by query/script
output (not by memory or assumption).

| Phase | Status | Definition of Done (gate to pass before moving on) | Last verified |
|---|---|---|---|
| 0. Open questions resolved | ☐ not started | All 3 open questions below have explicit answers recorded in this file | — |
| 1. Schema + `strongs_ot` parse | ✅ done | `strongs_ot` covers all 23,213 WLC verses, 100% aligned (0 unmatched); `books` has 66 rows ✓ | 2026-06-07 |
| 2. Noun extraction | ✅ done | `verse_noun_occurrences` populated for all OT verses; hand-count match on Ruth | 2026-06-07 |
| 3. Bootstrap renderings | ✅ done | `noun_translations(target_lang='zho')` populated for all 6,007 OT Hebrew noun lemmas; 145,869 / 145,869 OT noun occurrences resolve non-empty; deterministic 10-position spot-check across ≥5 books passes | 2026-06-08 |
| 4. Translation pass | ☐ not started | `GOI_Bible_Chinese_Hant/` file count == 31170; OT translation driver writes 001–039 files cleanly; small-book OT smoke pass (e.g. RUT) completes end-to-end | — |
| 5. Coverage + clause gates | ☐ not started | `verify_noun_coverage_ot_zh.py` reports ≥95% coverage; `clause_check_nt_zh.py` run across all 39 OT books with flagged list triaged | — |
| 6. Validation gate | ☐ not started | `validate_ot_zh.py` (or unified `validate_zh.py`) reports ALL CHECKS PASSED for the full 31,170-verse corpus | — |

**Session handoff rule:** before ending a session, write one line under the relevant
phase row noting exactly what was run, what the output was, and what the very next
command/step is — so the next session can resume without re-deriving context.

### 2026-06-07 — Phase 1 session notes

Ran `parse_morphhb_to_db.py` (new script, with `--book`/`--redo`/resume support) for
all 39 OT books. **Corrected fact at that time**: the early corpus count estimate was
too low. This note is superseded by the later alignment/build pass that drove the OT
source corpus to **23,213** verse files in `One_Directory_WLC` (+ 7,957 NT
= **31,170** total for the unified Bible).

Results:
- `strongs_ot` created (297,733 token rows), `books` extended to 66 rows (book_id 28-66
  = OT canon order 1-39)
- **23,052 / 23,100 verses (99.8%)** aligned cleanly by content (consonantal-text
  diff via `difflib.SequenceMatcher`, handles chapter-boundary versification shifts —
  e.g. correctly resolved Joel's Hebrew ch.4 vs corpus's ch.3 split automatically)
- **209 verse-keys flagged** to `alignment_review_ot.csv` for manual triage:
  - 161 `xml_only` — verses present in morphhb XML with no matching corpus file
    (mostly Joel 4:1-5, plus scattered chapter-end verses — genuine content the
    corpus omits; these will simply have no `strongs_ot` rows / no noun-coverage
    gate / no translation source unless resolved)
  - 48 `wlc_only` — corpus verses with no confident XML match (mostly short
    genealogy lines in 1CH/EZR/NEH/PSA/PRO/JOB where SequenceMatcher's 0.85
    similarity threshold correctly refused an ambiguous pairing rather than risk
    a wrong one)

**Next step**: triage `alignment_review_ot.csv` — likely acceptable to proceed to
Phase 2 with 23,052 aligned verses and treat the 209 as a known, documented gap
(update Phase 1 DoD gate to reflect 23,052, not 23,100, as the practical ceiling),
OR spend a short pass lowering the match threshold for the 48 short-genealogy cases
specifically (they're short enough that fuzzy matching is risky either way).

**Resolution (superseded by later session)**: alignment was driven to 100%
(23,213/23,213, zero unmatched) by (a) a same-key fallback pairing pass for
textual-variant cases, (b) extracting 112 genuinely-missing verses directly from
the morphhb XML, and (c) finding the true gap was Lev 5:20 (not the falsely
flagged Lev 6:1, a recurring-formula masking artifact). `One_Directory_WLC` now
has 23,213 files; `verses`/`verse_texts` scaffolded for OT (WLC version_id=2).

### 2026-06-07 — Phase 2 session notes

Wrote `Bible_Noun_Extraction/rebuild_noun_occurrences_ot.py`:
- Selects `strongs_ot WHERE morph LIKE 'N%'` (both `Nc*` common and `Np*` proper
  nouns, per the approved plan)
- `nouns` keyed by Strong's H-number → dictionary headword `lemma` (not inflected
  surface form), `language_code='hbo'`, sourced from `/tmp/strongs_hebrew.json`
  (Node-parsed Hebrew Strong's dictionary, 8,674 entries)
- `infer_category_id`: keyword buckets against `strongs_def` gloss (PLACE, TIME,
  MONEY, BODY_PART, FOOD, ANIMAL), `GOD_LEMMAS` hard-coded set for Elohim/El/YHWH/
  Adonai/Shaddai, `Np*` defaults to PERSON unless gloss says otherwise, else OTHER
- `surface_form` = `strongs_ot.word` with `/` morphological separators stripped

Results:
- Dry run `--book RUT --redo`: 351 tokens inserted; hand-verified Ruth 1:1 token
  breakdown and GOD-category rows (17 YHWH + 1 Elohim + 2 Shaddai = 21, all correct)
- Full run `--redo` (39 books): **119,115 noun tokens inserted**, matching
  `strongs_ot WHERE morph LIKE 'N%'` exactly (0 per-verse mismatches across all
  22,394 OT verses containing nouns); 5,568 distinct Hebrew lemmas in `nouns`
  (language_code='hbo'); 0 Strong's numbers without a dictionary entry

**Cross-language sanity check (WLC noun-count vs KJV noun-count via spaCy POS tagging,
stored in new `kjv_noun_counts` table)** — this surfaced two real systemic bugs in
`strongs_ot`/`core_morph()` that the internal-consistency check couldn't catch:
  1. Aramaic nouns (Dan 2:4b-7:28, parts of Ezra) use morph codes like `ANcmsc` —
     the `morph LIKE 'N%'` filter never matched the `A`-language-marker prefix (704
     tokens entirely excluded)
  2. `core_morph()` took `segs[-1]` on compound codes — for nouns with possessive
     suffixes (`HNcmsc/Sp3ms` = "his X", extremely common) this grabbed the
     suffix-pronoun code instead of the noun code (~26,000 tokens mis-tagged)
Fixed `core_morph()` to resolve the actual lexical-core POS segment (first segment
whose POS letter ∈ {N,V,A,P,D}, after stripping the H/A language marker) instead of
blindly taking the last segment. Re-ran full 39-book parse (still 100% aligned, 0
unmatched, 299,556 tokens) and noun extraction: **119,115 → 145,869 noun tokens
(+26,754, +22%)**. Internal consistency (`strongs_ot` vs `verse_noun_occurrences`)
re-verified at 0 mismatches.

Residual WLC-vs-KJV count mismatch (~67%) is **not** a bug — traced to (a)
versification differences (WLC=23,213 vs KJV=23,145 verses, with cascading
chapter-internal shifts, e.g. WLC 2Chr 2:13 = KJV 2:14 content) and (b) inherent
cross-language noun-count variance (1 Hebrew noun often → 0 or 2+ English nouns).
Same rationale as the NT pipeline's ≥95% *coverage* threshold rather than count
parity — exact parity across languages was never a realistic target.

**Next step**: Phase 3 — bootstrap OT Chinese noun defaults. This later changed in
implementation: the shared OT+NT DB cannot safely use `strongs_lang_renderings`
for OT because Greek and Hebrew Strong's numbers collide in the same integer space.
The shipped OT path therefore uses `noun_translations(target_lang='zho')` keyed by
`noun_id`, not `v_effective_rendering`.

### 2026-06-08 — Phase 3 session notes

Implemented OT Chinese noun bootstrap on the OT-safe key already present in the
schema: `noun_translations(noun_id, target_lang='zho', zh_translation)`.

Reason for design pivot:
- `strongs_lang_renderings(strongs_num, lang)` is NT-safe but not OT-safe in the
  shared DB because Greek and Hebrew Strong's numbers share the same integer space
  (`1`, `430`, etc.). Existing zh rows there are Greek-side rows and would falsely
  appear to "cover" Hebrew OT nouns with the same integer.
- Verified collision scope during implementation:
  - 5,624 overlapping Strong's integers between `strongs_lexicon language='G'` and `H`
  - all 5,205 existing zh rows in `strongs_lang_renderings` were Greek-side rows
  - naive OT lookup by integer Strong's number would have falsely resolved 96,860 OT
    noun positions through Greek defaults

Shipped artifacts:
- `Bible_Noun_Extraction/gen_ot_noun_translations.py`
- `Bible_Noun_Extraction/verify_ot_noun_translations.py`
- `Bible_Noun_Extraction/fix_ot_proper_name_translations.py`
- `Bible_Noun_Extraction/ot_noun_translations_zh.csv`
- `Bible_Noun_Extraction/ot_proper_name_fixes_zh.csv`

Generation/verification results:
- `noun_translations(target_lang='zho')` populated for **6,007 / 6,007** OT Hebrew
  noun lemmas (`language_code='hbo'`)
- OT noun occurrences resolved through `noun_id`: **145,869 / 145,869**
- Missing OT occurrence translations: **0**
- Deterministic 10-position sample across GEN/EXO/LEV/1KI/2KI/EZR/PSA/JER/MAL
  passed after a narrow proper-name cleanup pass
- Exact-name title spillovers (e.g. `雅各王`) reduced from **33 -> 0**

Regression checks after Phase 3:
- `python3 validate.py` -> ALL 13 CHECKS PASSED
- `python3 validate_zh.py` -> ALL 12 CHECKS PASSED

**Next step**: Phase 4 — translation pass. This is not ready to execute yet because
the current translation / clause / coverage tooling is still NT/TR1550-shaped and
must be adapted to WLC + `noun_translations` before OT verse generation can begin.

---

## What already exists (verified in exploration)

- **Source text**: `Hebrew_Bible_WLC/One_Directory_WLC/` — 23,213 single-line WLC
  verse files, e.g. `001_GEN_001_001_WLC.txt` containing
  `בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃`
- **Morphology**: `sources/morphhb/wlc/*.xml` — 39 OSIS/OSHB XML files (Gen.xml…Mal.xml)
  with per-word `<w lemma="..." morph="..." n="...">` elements, e.g.
  `<w lemma="d/8064" morph="HTd/Ncmpa">הַ/שָּׁמַ֖יִם</w>` (definite article + H8064,
  noun common masculine plural absolute)
- **Hebrew Strong's lexicon**: `sources/strongs/hebrew/strongs-hebrew-dictionary.js`
  (+ XML/dat/spellings variants)
- **Reference corpus** for divergence sweeps: none yet for Hebrew OT in Chinese
  (would need a PD Chinese OT, e.g. extending `Chinese_Bible_CUV/` coverage if it
  includes OT — verify before relying on it)

---

## Phase 1 — Extend schema + parse WLC morphology into `strongs_ot`

Add to `bible_noun.sqlite3`:
- New rows in `books` for the 39 OT books (book_id 28–66, canon order 1–39,
  matching the `001_GEN…039_MAL` filename prefixes)
- New table `strongs_ot`, mirroring `strongs_nt`:
  ```sql
  CREATE TABLE strongs_ot (
      id          INTEGER PRIMARY KEY,
      book_id     INTEGER NOT NULL REFERENCES books(book_id),
      chapter     INTEGER NOT NULL,
      verse       INTEGER NOT NULL,
      word_pos    INTEGER NOT NULL,
      word        TEXT NOT NULL,       -- pointed Hebrew surface form
      prefix      TEXT,                -- e.g. 'd', 'c/d', 'b' (article/conj/prep chain)
      strongs_num INTEGER NOT NULL,    -- primary H-number (last numeric in lemma)
      morph       TEXT,                -- OSHB code, e.g. HNcmpa
      in_wlc      INTEGER DEFAULT 1
  );
  ```
- New script `Bible_Noun_Extraction/parse_morphhb_to_db.py`:
  - Walk all 39 XML files, iterate `<verse osisID="Gen.1.1">` → `<w>` children
  - Parse `lemma` (handle `"b/7225"`, `"c/d/776"`, `"1254 a"` forms — split on `/`,
    take the last token, strip trailing letter-suffix variants like `" a"`/`" b"`)
  - Parse `morph` by stripping the leading `H` and any prefix-segment codes
    (`Td`, `C`, `R`, `To`) to isolate the core POS code for noun detection
  - Insert one row per `<w>` in document order (word_pos = 1-indexed within verse)
  - Cross-check resulting verse count == 23,213 and `in_wlc=1` token totals are
    plausible against `One_Directory_WLC` raw file word counts (sanity, not exact —
    WLC raw text includes maqqef/sof-pasuq markers that aren't `<w>` elements)

**Reuse**: this is structurally identical to how `strongs_nt` was populated from
TR1550 — read `tr1550_language_translation_instructions.md` for the exact ingestion
pattern before writing the parser, so the OT table stays consistent.

---

## Phase 2 — Canonical noun extraction

- New script `Bible_Noun_Extraction/noun_count_ot.py` (adapt
  `noun_count_nim.py` / `rebuild_noun_occurrences_from_strongs.py`):
  - Select `strongs_ot` rows where `morph` indicates a noun (OSHB: `Nc*` common noun,
    `Np` proper noun — decide whether proper nouns count toward coverage; the NT
    pipeline used `morph LIKE 'N-%'` uniformly, so likely include both, flagged by
    category)
  - Populate `verse_noun_occurrences` for OT verses (reusing existing `nouns`,
    `noun_categories` tables — extend `noun_categories` only if OT introduces new
    categories beyond GOD/PERSON/PLACE/OTHER)
- Expect roughly proportional scale: NT had 28,889 noun tokens across 7,957 verses
  (~3.6/verse); OT landed at 145,869 noun tokens across 23,213 verses after the
  extraction fixes, so any LLM-assisted steps should be sized for that actual volume

---

## Phase 3 — Bootstrap renderings

Phase 3 is complete and the original design assumption here was wrong.

Shipped implementation:
- `Bible_Noun_Extraction/gen_ot_noun_translations.py`
- `Bible_Noun_Extraction/verify_ot_noun_translations.py`
- `Bible_Noun_Extraction/fix_ot_proper_name_translations.py`

Actual OT resolution path:
- Parse Hebrew lexicon data for the dominant OT Strong's row linked to each `noun_id`
- Generate/update `noun_translations(target_lang='zho', zh_translation)`
- Verify OT noun resolution through `noun_id`, not through `strongs_lang_renderings`

Why this differs from the original plan:
- `strongs_lang_renderings(strongs_num, lang)` is safe for the NT Greek pipeline
  but unsafe for OT in the shared DB because Greek and Hebrew Strong's integers
  overlap massively
- therefore OT noun defaults live in `noun_translations`, while NT still uses the
  existing `strongs_lang_renderings` + `sense_renderings` path

OT-specific sense work is still future scope:
- the existing 16 `senses` are NT-specific (ANER.SPOUSE, KYRIOS.HUMAN_MASTER,
  PNEUMA.UNCLEAN_SPIRIT…)
- OT will surface its own polysemy set (e.g. רוּחַ spirit/wind/breath, חֶסֶד
  lovingkindness/mercy/loyalty, נֶפֶשׁ soul/life/person)
- after an OT draft exists, run an OT ambiguity / false-friend pass and add any
  required OT-specific sense rows deliberately

---

## Phase 4 — Translation pass

- New script `Bible_Noun_Extraction/translate_ot_verses.py` (adapt
  `translate_verses.py`, but do not force the NT resolver model onto OT):
  - Drive verse-by-verse from `One_Directory_WLC/`, write to
    `GOI_Bible_Chinese_Hant/{NNN}_{BOOK}_{CCC}_{VVV}.txt`
  - Resolve OT noun anchors from `noun_translations(target_lang='zho')`, not from
    `strongs_lang_renderings`
  - System prompt needs an OT-specific briefing: poetic books (Psalms, Job,
    Proverbs, Song of Songs, Lamentations) need different register guidance than
    narrative (Genesis–Esther) or prophetic (Isaiah–Malachi) — consider staging by
    genre rather than canon order, mirroring how the NT gameplan staged by error class
  - Apply `normalize_corpus.py` on output exactly as for NT (already language-agnostic)

---

## Phase 5 — Coverage + clause-completeness gates

- Add `verify_noun_coverage_ot_zh.py`:
  - Same `CJKMatcher` + `_ACCEPTABLE_FORMS` infrastructure in `matchers.py`, but
    expect a **fresh round of expansion** — OT vocabulary (sacrificial system,
    genealogies, geography, agrarian/pastoral terms) barely overlaps NT vocabulary.
    Budget for the same iterative "run → inspect top-missing → expand forms" cycle
    that took NT from 94.7% → 97.3%
  - Coverage resolution must key off OT `noun_id` / `noun_translations`, not NT
    `strongs_nt` / `strongs_lang_renderings`
- Extend the clause-check tooling for OT or add `clause_check_ot.py`:
  - current script is TR1550/NT-shaped (`One_Directory_TR1550`, NT-only `BOOK` dict)
  - OT clause checking must read `One_Directory_WLC` and understand OT book codes

---

## Phase 6 — Validation gate

- New script `validate_ot_zh.py` (or extend `validate_zh.py` to check both Testaments):
  - File count: 23,213 OT + 7,957 NT = 31,170 total in `GOI_Bible_Chinese_Hant/`
  - Same CORPUS / canonical / CJK-presence checks (language-agnostic, reuse as-is)
  - SOURCE check → WLC source for OT, TR1550 source for NT if unified
  - DB INTEGRITY checks extend naturally (FK, override positions, sense_key catalog)
    once `strongs_ot` and OT `books` rows exist
  - NOUN COUNT check: `verse_noun_occurrences` vs `strongs_ot` (mirrors the NT
    `strongs_nt` comparison)
  - COVERAGE: delegate to `verify_noun_coverage_ot_zh.py`, same ≥95% threshold
    rationale (legitimate paraphrase rate makes 0-missing unrealistic)

---

## Open questions / future decisions

1. **Proper nouns in noun coverage**: OT genealogies (1 Chronicles 1–9, Numbers
   census lists) are dense with proper names. Decide whether `Np` (proper noun)
   tokens count toward the coverage gate or are excluded — this materially affects
   both the denominator and the realistic threshold.
2. **PD reference edition for divergence sweeps**: the NT pass leaned on KJV/WEBUS
   (English) and CUV (Chinese, 1 reference). Confirm whether `Chinese_Bible_CUV/`
   already contains OT text — if yes, the three-way divergence sweep pattern
   (`falsefriend_sweep.py`) can be reused directly; if no, decide whether to proceed
   with zero references (riskier, more reliant on the clause-check tooling).
3. **Staging order**: canon order (Genesis→Malachi) vs. genre/difficulty order
   (e.g., narrative first as the "easy" pass, poetry last as the hardest) — the NT
   gameplan staged by error class, not canon order, and that paid off.

---

## Verification (after each phase, before moving on)

- Phase 1: `SELECT COUNT(*) FROM strongs_ot` should land near the total `<w>` count
  across all 39 XML files; `SELECT COUNT(DISTINCT book_id||'-'||chapter||'-'||verse)
  FROM strongs_ot` must equal 23,213
- Phase 2: noun token count sanity-checked against a hand count for a sample book
  (e.g. Ruth, small enough to verify manually)
- Phase 3: spot-check OT `noun_translations` resolves for 10 random OT noun
  positions across different books
- Phase 4: run the OT clause checker (once the clause-check tooling is extended for OT, or
  `clause_check_ot.py`) on a small book such as RUT before scaling to all 39 books
- Phase 5/6: `validate_ot_zh.py` (or extended `validate_zh.py`) must reach
  ALL CHECKS PASSED before declaring the OT pass complete, exactly as NT did
