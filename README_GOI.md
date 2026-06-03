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
`Greek_Noun_Extraction_NIM/One_Directory_TR1550/` (same filename stems, `_TR1550` suffix).

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

Verification tooling: `Greek_Noun_Extraction_NIM/verify_noun_coverage.py`
(checks `strongs_nt … AND in_tr1550 = 1` against the English output).
Canonical rebuild: `rebuild_noun_occurrences_from_strongs.py`.

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
