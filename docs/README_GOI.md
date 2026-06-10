# README — GOI_Bible_English

A briefing for any human or AI reading the `GOI_Bible_English/` corpus.

---

## 1. What it is

- An English **New Testament** (27 books, Matthew→Revelation; file prefixes `040`–`066`).
- Translated from the **Greek Textus Receptus, Stephanus 1550 edition (TR1550)** — *not* a modern critical text (NA28/UBS).
- **7,957 plain-text files**, one verse per file, single line, UTF-8.
- Filename format: `NNN_BOOK_CCC_VVV.txt`
  (e.g. `044_ACT_009_029.txt` = canon-order 044, Acts, chapter 9, verse 29).
  `NNN` is canon order, `BOOK` is the OSIS-style abbreviation.
- AI-generated translation. "GOI" is the author's project label; it does **not**
  denote any published edition.

The matching Greek source lives at
`Bible_Noun_Extraction/One_Directory_TR1550/` (same filename stems, `_TR1550` suffix).

## 2. Because it is TR-based

Expect **Textus Receptus readings** that modern Bibles omit or footnote:
the Johannine Comma (1 John 5:7–8), Acts 8:37, the longer ending of Mark,
the Romans 16 doxology, etc.

**Versification follows TR1550**, which can diverge from KJV/modern numbering.
Do not "correct" these against a modern Bible — divergences are usually the
source, not errors.

Some epistles carry **scribal colophons** — bracketed subscriptions at the end
of the final verse, e.g.:
- 2 Cor 13:14 ends `[The second epistle to the Corinthians was written from Philippi of Macedonia by Titus and Lucas.]`
- Eph 6:24 ends `[The epistle to the Ephesians was written from Rome by Tychicus.]`

These are **present in the TR1550 source as bracketed scribal notes**, not
apostolic text. Treat them as paratext.

## 3. What has been verified

- **Noun count is canonical to raw TR1550.** The noun database
  (`verse_noun_occurrences`) is a strict projection of the scholarly morphology
  (`strongs_nt`, `morph N-*`) **intersected with the raw `One_Directory_TR1550`
  text the English was translated from.** Every one of the **28,889** counted
  nouns has been verified to physically appear in its own raw verse
  (multiplicity-aware, 0 exceptions). The earlier LLM-extracted noun table was
  discarded; this set is deterministic and reproducible.
- **How the canonical set was reached:** `strongs_nt` is variant-inclusive (it
  tags alternate TR readings). Reconciling to the raw text removed 36
  variant/duplicate noun tags (e.g. `σιμων` vs `συμεων` 2 Pet 1:1; the 1 John
  2:23 long-reading doublet) and realigned 23 verse-boundary tags to the verse
  where the word actually occurs (MAT 15:6→15:5, MAT 23:13↔14, ACT 13:33→32,
  HEB 1:2→1:1, …). Stripped tags are retained in `strongs_nt` with
  `in_tr1550 = 0` (non-destructive; scholarly provenance preserved).
- **Noun coverage in English: 0 missing**, 99.7% exact-match, rest via
  inflection/stem. English verse boundaries follow raw TR1550, consistent with
  the noun count.
- **NOT yet verified:** verbs, adjectives, adverbs, particles, and clause-level
  completeness. That is the biggest open gap.

Verification tooling: `Bible_Noun_Extraction/verify_noun_coverage.py`
(checks `strongs_nt … AND in_tr1550 = 1` against the English output).
Canonical rebuild: `rebuild_noun_occurrences_from_strongs.py`.

## 3a. Sense layer — the multilingual disambiguation contract

Polysemous Greek words (γυνή = wife/woman, ἀνήρ = man/husband, κύριος =
Lord/master, γίνομαι = become/happen/be, πνεῦμα = Spirit/spirit/wind/breath, …)
are disambiguated **once, language-neutrally**, so every future language
inherits the decision instead of re-deriving it.

How it is codified (in `bible_noun.sqlite3`):

- **`verse_rendering_overrides`** — 1,060 rows keyed by Greek coordinates
  (`book, chapter, verse, word_pos, strongs_num`) marking every token that
  departs from its default sense. Each now carries a **`sense_key`**
  (e.g. `ANER.SPOUSE`, `GYNE.WOMAN`, `KYRIOS.HUMAN_MASTER`, `GINOMAI.HAPPEN`).
  This list of positions + senses is **language-independent** and transfers to
  every target language unchanged.
- **`senses`** — catalog of the 16 distinct senses (key → Strong's → definition
  → English base word). Exported human-readable to `senses.csv`.
- **`sense_renderings`** `(sense_key, lang, rendering)` — the per-language word
  for each sense. English is fully populated (16/16). **A new language fills in
  ~16 rows once**, and all 1,060 contextual overrides resolve automatically.
- **`v_effective_rendering`** — view that resolves, per noun position and
  language: sense override → that language's sense word → else the language's
  default rendering. This is the canonical resolution interface the translation
  pipeline should query.

Why this matters: without it, the contextual fixes were English-only — e.g. at
the spouse-sense positions Chinese would fall back to 男人 (*man*) instead of
丈夫 (*husband*). With it, the judgment ("this κύριος is a human master, not the
divine Lord") is made once against KJV/WEBUS and reused by every language.

**To onboard a new language:** populate `sense_renderings` for its `lang` code
(16 rows, using `senses.csv` as the spec), supply its default
`strongs_renderings`, then query `v_effective_rendering`. Note: English
*verification* still uses the inflected `verse_rendering_overrides.correct_rendering`
(husband vs husbands); the sense layer supplies the base word other languages
inflect themselves.

## 4. What to look out for (reviewer checklist)

1. **Clause / verb completeness** — weakest-checked dimension. Look for dropped
   predicates or fragment-like verses. (Noun-presence was enforced, which can
   mask a missing verb.)
2. **Polysemy collapse** — wrong sense of a multi-meaning Greek word for the
   context (λόγος "word" vs "account/matter"; σάρξ "flesh" vs "body";
   κρίσις "judgment" vs "condemnation").
3. **Register inconsistency** — mixes archaic/literal ("disannulled", "sundry
   times", "divers manners") with plain modern English, sometimes verse-to-verse.
4. **Proper-noun form variation** — same name under Greek vs Anglicized forms
   (Simon/Simeon, Elias/Elijah, Judas/Judah, Jonas/Jonah). Check consistency.
5. **Bracketed scribal colophons** — see §2; analyze as paratext, not scripture.
6. **Punctuation not normalized** — quote style is mixed corpus-wide (~982 files
   straight `"`, ~567 curly `“ ”`; apostrophes and em-dashes likewise mixed).
   Normalize before NLP/typesetting.
7. **Pronoun antecedent clarity** — literal renderings can leave "he/him/it"
   ambiguous where Greek case/gender disambiguated.

**One-line summary:** *A faithful-to-TR1550, AI-drafted NT whose nouns are
verified complete but whose verbs, sense-disambiguation, and style consistency
are not. Don't reconcile it against a modern critical Bible — divergences are
usually the Textus Receptus, not errors.*

## 5. Provenance & licensing (copyright posture)

**Goal:** a copyright-unencumbered English NT.

**Source of record:** Greek **TR1550** (public domain). Confirmed by the parallel
`One_Directory_TR1550/` Greek files, the `strongs_nt` tagging keyed to TR1550,
and colophons that match the TR1550 bracketed source verbatim.

**Reference texts used during QA:** KJV and WEBUS only.
Both are **public domain**:
- **WEBUS (World English Bible)** — explicitly dedicated to the public domain
  (eBible.org / Michael Paul Johnson). No restrictions.
- **KJV (King James Version)** — public domain in the United States and
  effectively worldwide. (UK Crown copyright via letters patent is a perpetual
  but outside-UK-unenforceable technicality.)

**Empirical overlap audit** (word-set Jaccard, whole corpus):
- Mean similarity GOI↔KJV ≈ 0.55, GOI↔WEBUS ≈ 0.64 — broadly **distinct**, i.e.
  not a wholesale copy of either.
- A real tail of **verbatim / near-verbatim** verses exists: ~107 verses ≥0.95
  identical word-set to KJV, ~270 to WEBUS, including some longer verses
  (e.g. 1 John 1:8 and Romans 3:24 are word-for-word KJV).

**What this means for copyright:** because **both reference texts are themselves
public domain**, even verbatim-overlapping verses **do not encumber** the GOI's
copyright status — you cannot infringe a public-domain work. The corpus remains
copyright-unencumbered.

**The one rule to preserve that status:** never introduce text from a
*modern copyrighted* translation (NIV, ESV, NASB, NRSV, CSB, NLT, etc.).
Keep references limited to TR1550 + KJV + WEBUS.

**Honest caveat:** the original 7,957 files were generated by a pipeline not run
or logged in the auditable history here, so no one can *certify* "translated
fresh, zero copying." The statements above are what the text **empirically shows**.
The conclusion holds regardless, because the only texts it overlaps are public domain.

## Changelog — 2026-06-03 integrity pass

Meaning-accuracy review of the English corpus (TR1550 + KJV/WEBUS as references):

1. **GPT audit (23 verses):** false-friend mistranslations + clause corruption
   fixed (forgive/leave, healing/household, seized/conceived, honor/price,
   encouraged/begged, devils/slanderers, MAT 9:35 "disease…disease", etc.).
   Recorded in `2026-06-03_gptaudit.md`.
2. **Corpus-wide false-friend sweep (103 verses):** data-driven sweep of the
   patterns the audit sampled —
   - ἀφίημι→"forgive" → leave/let/allow/forsake (28; incl. JHN 14:27 "Peace I
     leave with you")
   - τιμή→"honor" → price (ACT 5:3)
   - παρακαλέω→"encourage" → beg/implore/comfort (23) and urge/exhort (12)
   - γίνομαι→"happened" → made/born/became/be (11; incl. JHN 1:3, GAL 4:4) and
     μὴ γένοιτο → "By no means!" (12)
   - ἐκεῖνος→"that one" → he/him/that man (16 + 4 residual)
3. **Interpretive items settled (user decision):** 1TI 3:11 "wives" (vs women);
   ROM 3:25 "propitiation" (vs atoning sacrifice / mercy seat); MAT 5:32
   "sexual immorality".
4. **Style polish:** LUK 12:42, MRK 5:19, 1PE 3:7, residual demonstratives.

Noun coverage held at **0 missing / 99.7%** throughout; five rendering changes
that moved off a strongs default are recorded as `verse_rendering_overrides`.
Remaining known work: other false-friend families not yet swept (e.g. σπλάγχνα,
σάρξ, ἵστημι/καθίστημι) and the verb/clause-completeness verification noted in §3.

## 6. Pipeline tooling & multilingual plumbing

This repo is the de-facto plumbing for translating TR1550 into further languages.
The operational walkthrough for the next translator (human or AI) is
**`TRANSLATION_GUIDE.md`**. Key tools:

| Tool | Purpose |
| --- | --- |
| `validate.py` | integrity gate — 13 invariants; run after any change |
| `normalize_corpus.py` | canonicalize punctuation/whitespace (`--check` for CI) |
| `Bible_Noun_Extraction/matchers.py` | per-language "rendering appears in output" (refuses undefined langs) |
| `Bible_Noun_Extraction/language_readiness.py` | what a language still needs before its numbers mean anything |
| `Bible_Noun_Extraction/verify_coverage.py` | generic per-language noun coverage |
| `Bible_Noun_Extraction/verify_noun_coverage.py` | English-specific, tuned coverage (the en authority) |
| `Bible_Noun_Extraction/senses_worksheet.csv` + `import_sense_renderings.py` | the 16-sense per-language fill sheet + loader |

Data model for adding a language (no schema change needed): default words go in
`strongs_lang_renderings(strongs_num, lang, rendering)`; the 16 contextual senses
go in `sense_renderings(sense_key, lang, rendering)`; positions are already marked
language-neutrally in `verse_rendering_overrides`. **16 sense decisions resolve
~1,060 contextual positions automatically.**

## Changelog — 2026-06-04 non-noun checks

Added negation + number integrity checks (`Bible_Noun_Extraction/meaning_checks.py`)
— the catastrophic-but-noun-invisible classes. Negation found one real dropped
negation (**2 Thess 3:7** "we did **not** behave disorderly" — restored).
Numbers came back clean (all flags were etymological collisions / surface forms).
