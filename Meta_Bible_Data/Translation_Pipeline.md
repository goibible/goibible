# Translation Pipeline — master overview

This is the top-level "start here" document for the GOI Bible translation
pipeline: what happens before translation, during translation, and every
"gotcha" check that runs after, for every language and both testaments.

It is deliberately an *overview with pointers*, not a replacement for the
detailed docs already in this repo — those stay authoritative for their own
area, and are linked from each section below rather than re-explained. If
this doc and a linked doc ever disagree, the more specific doc wins and this
one needs fixing.

| Doc | Scope |
| --- | --- |
| `Translation_Pipeline.md` (this file) | End-to-end map + consolidated gotcha catalog |
| `pipeline.md` | Per-language operational runbook (commands, current status) — written NT/Vietnamese-first but the commands generalize |
| `docs/TRANSLATION_GUIDE.md` | Deep methodology for onboarding a new NT language: matchers, senses, false-friend discipline |
| `docs/language_scaffold_playbook.md` | Required tracked layout + non-negotiable rules for a new edition |
| `docs/new_language_recipe.md` | DB build, packaging, and deploy sequence |
| `docs/post_translation_checklist.md` | The authoritative release-gate checklist |
| `README_GOI.md` | Project overview, verification status, provenance/copyright posture |

---

## 0. The foundational idea: pre-scrubbed alignment

Everything downstream works because two things are settled **before any
translation happens**:

1. **GOI (Global Ordinal Index) alignment to the KJV verse spine.** Every
   edition, in every language, is keyed by the same integer per verse. This
   turns "does this edition have the right verses in the right order" into a
   database query, not a manual comparison.
2. **Strong's-number tagging of every source noun** (Greek TR1550 for NT,
   Hebrew WLC/MorphHB for OT). This is what makes automated coverage checking
   possible at all: for any translated verse, you can enumerate exactly which
   source concepts must appear in it, without a human re-reading the verse.

Nearly every "gotcha" below is either a violation of one of these two
alignments (versification drift, a mistagged occurrence) or a downstream
consequence of the tooling that verifies them (a dict typo, a stale cache).
Keep that in mind when something looks like a translation bug: check
alignment first, because a misaligned check will pass a bad translation and
fail a good one with equal confidence.

## 0a. Where things live on disk

Structure follows the pipeline, not filename convention — open a folder,
see what's done, don't grep for it.

- **`GOI_Bible/<edition>/`** — the finished per-language translation, one
  edition per folder (`GOI_Bible_English/`, `GOI_Bible_ja/`, etc.).
- **`Reference_Bible/<edition>/`** — every public-domain cross-reference and
  source-language text, one edition per folder, each self-contained: its own
  atomize/align script, `SOURCE/`, `One_Directory_*/` output, `README.md`.
- **`Bible_Noun_Extraction/`** — the Strong's/noun-extraction pipeline.
  Shared, language-agnostic machinery (`matchers.py`, `llm_client.py`,
  `verify_matchers_dedup.py`, the one shared NT DB `greek_noun.sqlite3`,
  import/generation scripts used by every language) lives at this top
  level. Everything specific to one language — its OT Strong's DB (if any),
  its own scripts, its report CSVs — lives in a same-named subfolder:
  `ja/`, `ko/`, `zh/`, `vi/`, `en/`, `es/`, `pt/`. **A language subfolder
  with no `.sqlite3` in it means that language's OT hasn't started yet** —
  that absence is itself the status signal, not a gap to fill in
  speculatively. (Reorganized 2026-09-16, previously ~300 files flat in one
  directory; see that commit for the full move — it also caught a mislabeled
  DB, `hebrew_ot.sqlite3` renamed to `hebrew_ot_ko.sqlite3`, since it held
  Korean OT data with no `ko` anywhere in the old name.)

---

## 1. Pre-translation work

Before generating a single verse of a new language, or before resuming OT
work in an existing one:

- **Register the language.** Edition entry in `sqlite/editions.json`
  (`docs/language_scaffold_playbook.md` §Intake sequence, step 1) and, for
  CJK/RTL/space-delimited handling, a matcher subclass in
  `Bible_Noun_Extraction/matchers.py` (`docs/TRANSLATION_GUIDE.md` Step 1).
- **Establish the coordinate spine.** Confirm GOI/KJV alignment for the
  target verse range before any text goes in (`language_scaffold_playbook.md`
  §3). For OT books, check for known Hebrew/English versification seams
  (Psalms, Isaiah 63/64, Joel 2/3) before trusting any per-verse tooling — see
  §3.6 below.
- **Build the source-name / proper-noun layer.** `build_source_name_db.py`
  (NT, cross-testament) and `build_ot_name_db.py` (OT, per-language profile)
  give every proper name a canonical source entity independent of any one
  translation's spelling choice.
- **Line up your public-domain cross-reference(s).** This is the "old PD
  version to verify proper nouns" instinct, and it's already a formal
  practice, not just a habit: `docs/TRANSLATION_GUIDE.md` §4 (the
  false-friend discipline) runs `falsefriend_sweep.py xref` against PD
  references in the target language (English used KJV + WEBUS; Vietnamese
  uses VIE1934, falling back to KJV where VIE1934 has no coverage — see
  `pipeline.md`'s VIE1934 coverage-gap note). **Only ever use public-domain
  references for this** — never a modern copyrighted translation (§6,
  copyright posture) — and never let a reference *become* the source; it's a
  check on the Hebrew/Greek translation, not a second source to translate
  from.
- **Fill in the disambiguation sense layer** for the 16 shared senses
  (`docs/TRANSLATION_GUIDE.md` Step 3) so high-polysemy Greek/Hebrew words
  resolve correctly by default instead of needing a per-verse fix later.

### Mandatory four-stage rollout for every new language

Do not invent a different rollout for a new language. The project sequence is:

1. **NT pre-fill:** generate and review the noun/Strong's defaults, then
   translate and clean up the **four Gospels** as the NT test corpus.
2. **Finish NT:** only after the four-Gospel noun/Strong's, script,
   coordinate, and duplicate gates pass, complete the remaining NT.
3. **OT pre-fill:** generate and review the OT noun/Strong's defaults, then
   translate and clean up the **Torah** as the OT test corpus.
4. **Finish OT:** only after the Torah passes the same gates, complete the
   remaining OT.

At either test stage, use the established cleanup loop: measure strict
coverage, repair the reported failures, re-measure, and stop only at 100% or
at a documented human-review blocker. Do not jump to a whole testament, and
do not replace the stated test corpus with an ad-hoc smaller pilot.

---

## 2. Translation work

- **Approved model/provider policy.** Automated translation and audit calls
  use the project-approved **DeepSeek** model/provider only. Do not invoke a
  legacy Qwen, Claude, OpenAI, or provider-generic script merely because it
  remains in the repository; those are historical tooling until explicitly
  migrated and approved. Every batch log records the provider, exact model
  identifier, endpoint class (hosted/local), prompt version, temperature,
  source commit, start/end time, request count, and input/output token totals.
  This makes unexpected provider usage attributable instead of discoverable
  only from an external billing dashboard.
- **One verse, one file, always.** Never all-or-nothing batch generation
  (`pipeline.md` §Core Rules). Every generation step is incremental and
  resumable — skip existing non-empty files, retry only what failed.
- **A prompt is not a gate.** `translate_verses.py` must be invoked with
  `--require-noun-anchors` for every production batch. The language matcher
  checks every required source-noun anchor *before the verse is written*;
  missing anchors trigger targeted rewrites and then a hard failure. A verse
  that fails the gate is never counted as translated or silently retained in
  the canonical directory.
- **Production batches require supervision, not a terminal heartbeat.** A
  production runner must use the project Python environment by absolute path,
  hold a single-worker lock, write an append-only batch log, resume from
  existing validated files, and restart from the first incomplete coordinate
  after a process/API failure. A 20-minute heartbeat is an observability
  receipt only; it does not satisfy the restart requirement. Before reporting
  a batch as running, verify the actual child PID, interpreter, provider/model,
  Flex tier when selected, and first output checkpoint. Before reporting it
  complete, verify its expected coordinate count and all quality gates.
- **Translate only from the original-language source.** Greek TR1550 for NT,
  Hebrew WLC/MorphHB for OT. Every other edition (KJV, WEBUS, sibling GOI
  editions, VIE1934, etc.) is reference-only, for noun/name/number/structure
  QA — never a translation source, never allowed to overrule the source
  language.
- **Low temperature, one verse per response, no commentary.** See
  `pipeline.md`'s Model Configuration section for the concrete settings that
  have actually held up in practice (temperature 0.1–0.2, explicit
  instruction against markdown/notes, name-grounding injection from the
  approved-names DB where available).
- **Ground names at generation time, not just after.** Inject
  already-approved name spellings into the prompt from the names DB
  (`--names-db` in `translate_ot_smoke_vi.py`) rather than relying entirely on
  post-hoc repair — cheaper and catches genealogy-collision errors (e.g.
  Methushael vs. Methuselah) before they're written.
- **OT contextual overrides, not blanket fixes.** When a Hebrew word's
  *default* rendering is right almost everywhere but wrong at one verse
  (idiom, Kethib/Qere variant, a common noun doubling as a proper name), the
  right fix is a **per-verse override** in the language's
  `ot_<lang>_contextual_renderings` table, not a global matcher synonym and
  not a rewrite of the default. A global synonym changes what the coverage
  checker accepts *everywhere that key appears*; a per-verse override changes
  it only at that one coordinate. Prefer the narrower fix whenever the issue
  is genuinely one-off. See §3.7 below for when a *global* fix (matcher
  synonym or DB default correction) is instead the right call.
- **Textual policy brackets are language-neutral.** `[]` conflicted-reading,
  `{}` supplemental-traditional. Decided once in `pipeline.md`'s NT Textual
  Policy table, applied identically in every language — don't re-litigate
  per language.

---

## 3. Post-translation "gotcha" checks

Run these after generating or editing any verse text, before calling a book
or language done. Each one exists because it caught a real bug at least once.

### 3.1 Noun / Strong's coverage — the core check

Every source noun occurrence must have its expected rendering (or an
approved synonym, or a per-verse override) present as a substring in the
translated verse. NT: `verify_noun_coverage.py` / `verify_coverage.py --lang
<L>`. OT: language-specific (`verify_ja_ot_coverage.py`,
`verify_ko_ot_noun_coverage.py`, generic `verify_coverage.py` for others).
This is the workhorse check; everything else in this section exists to keep
it trustworthy or to catch what it structurally can't see (see §3.6).

**Known limitation, not a bug:** this is a substring-presence proxy, not a
correctness check. Pushing coverage to literal 100% requires adding enough
synonyms that the checker eventually accepts almost anything plausible for a
common word — every synonym added is individually verified against real
verse text, but the *cumulative* effect is a checker that's less likely to
catch a *future* real error landing on one of those now-permissive words.
Prefer a **per-verse contextual override** over a **global synonym** whenever
the issue is genuinely one-off (§2 above) — it fixes the same miss without
this cumulative erosion.

**Release threshold:** 100% coverage after documented textual-policy
suppression and approved, narrow contextual overrides. A partial percentage
is a failure report, never a completion metric. Do not broaden a matcher or
add global synonyms merely to make the percentage pass; retain the failing
coordinate and repair the rendering or the source-anchor data.

### 3.2 Script/character-set verification ("no Korean in the Chinese text")

```bash
python3 tools/translation_pipeline/verify_language_script.py GOI_<ID>
python3 tools/translation_pipeline/verify_language_script.py --all-active
```

Rejects any Unicode script not explicitly allowed for that language's profile
(`Meta_Bible_Data/translation_qa/script_profiles.json`), on top of shared
punctuation/digits/combining-marks. This is the generalized "extended-ASCII"
gate: it catches leaked source text, leaked English prompt scaffolding, and
one language's script bleeding into another's corpus. **Never add a foreign
script as an allowed exception to make the gate pass** — that's hiding a
defect, not clearing one; if a genuine scholarly quotation needs an
exception, it goes in the scaffold record with a reason and a reviewer, not
into the default allow-list (`docs/post_translation_checklist.md`).

The active-corpus baseline is tracked in
`staging/reports/script_gate_baseline_2026-09-14.md`. A baseline failure is
release-blocking cleanup work, not a reason to loosen a language profile.


### 3.3 Duplicate / doubles checks

Two distinct classes of "doubles" bug, both real, both silent by default:

**(a) Duplicate matcher dict keys.** Every language's acceptable-forms table
in `matchers.py` is a hand-edited Python dict literal. A repeated string key
in one literal is silently resolved to the *last* occurrence — Python raises
no error — so an earlier synonym fix just vanishes. This has actually
happened three times in `JapaneseMatcher` and fifteen times in
`KoreanMatcher`, always discovered by accident. Formalized as a real check
now:

```bash
python3 Meta_Bible_Data/Bible_Noun_Extraction/verify_matchers_dedup.py
```

Walks the AST of `matchers.py` (not a line-range grep, which misses the
merge-loop pattern KoreanMatcher uses) and flags any string key repeated
within the same dict literal. Run this after **any** edit to
`_ACCEPTABLE_FORMS` / `_FORMS` in any language, not just the one you touched
— it takes under a second and checks all of them at once.

**(b) Duplicated/malformed verse files.** File-count, naming,
single-line-per-verse, non-empty, and canonical-punctuation/NFC checks — see
`tools/validate.py` (English gate) and `tools/validate_zh.py` (Chinese gate, which adds a
Traditional↔Simplified OpenCC t2s one-to-one mirror comparison). These catch
concatenated verses, accidental duplicate writes, and drift between sibling
editions that are supposed to be exact scripts of each other.

### 3.4 Cross-edition / sibling-edition consistency

Where two editions of the same language exist (Traditional/Simplified
Chinese), they should be an exact t2s/s2t mapping of each other except for
genuine script differences — `tools/validate_zh.py`'s MIRROR check. Where a
finished GOI edition exists in a related language, use it as a reference for
another language's translation, the same way KJV/WEBUS are used for
English — see `feedback-use-goi-sibling-editions` in project memory: a
finished GOI edition is a verse-aligned parallel reference, not a
KJV-only-fallback situation.

### 3.5 Cross-language regression check

Any defect found in one language's text is a candidate defect in every other
active language at the same coordinate (same underlying source-language
error, or same category of model mistake). Log it in
`cross_language_regressions.csv` and check it everywhere, not just where it
was found (`docs/post_translation_checklist.md`).

### 3.6 Versification / occurrence-alignment seams

Hebrew (Masoretic) and English (KJV) verse numbering disagree at a handful of
well-known seams — Isaiah 63/64, several Psalms, Joel 2/3. If the
noun-occurrence extraction pipeline and the translated-text file naming don't
agree on which verse a word belongs to at one of these seams, you get a
occurrence tagged to the wrong verse — the coverage checker reports a MISSING
at a verse whose translation is actually complete and correct, because the
word it's looking for is one verse over.

**How to recognize it:** a MISSING entry where the WLC/TR text for that exact
verse plainly does not contain any plausible source word for the flagged
Strong's number. Before adding a synonym or override, check the *adjacent*
verse's source text and the translated text's *adjacent* file — if the
"missing" content is sitting one verse away and already translated
correctly, this is what's happening.

**The fix is a data correction, not a translation fix:** correct the
occurrence table's `(chapter, verse, word_pos)` to the correct location.
Adding a synonym or override papers over a data bug and leaves it to bite the
next language that reuses the same occurrence table. Found and fixed twice
in the Japanese OT push (1KI 22:22, ISA 64:1) — worth a quick scan of any
book that touches a known seam before trusting a clean coverage report there.

### 3.7 Homographs and wrong DB defaults (global fixes, not overrides)

Two related but distinct classes where the right fix *is* global:

- **Common noun / proper name homographs.** One Strong's number sometimes
  covers both an ordinary word and a person/place name spelled identically
  in the source (שָׁפָן = both "rock hyrax" and the person Shaphan; the same
  pattern recurs regularly enough to expect it in any OT book with
  genealogies or geography). Fix: extend that Strong's number's accepted
  forms to include the name's standard transliteration, since *every*
  occurrence of that homograph pair benefits, not just one verse.
- **Wrong DB default rendering.** Occasionally the stored default for a
  Strong's number is simply wrong for its dominant real-world sense (H5608
  סֹפֵר defaulted to the bare verb "count" instead of "scribe," which is
  correct in 47 of 49 occurrences; an Aramaic "breast" lexeme defaulted to
  "joy"). Fix: correct the DB default directly — a matcher synonym would work
  too but treats a wrong ground-truth fact as a wording preference, which
  makes it harder for the next person to tell which the DB actually asserts.
  Verify against the lexicon definition and a sample of real occurrences
  before changing a default; it affects every verse with that Strong's
  number.

### 3.8 Release integrity

```bash
python3 tools/translation_pipeline/verify_scaffold_manifests.py
python3 tools/translation_pipeline/verify_cross_language_audit.py
python3 tools/translation_pipeline/verify_language_script.py GOI_<ID>
python3 tools/translation_pipeline/verify_release_integrity.py
```

Full sequence and DB/packaging/deploy steps: `docs/new_language_recipe.md`
and `pipeline.md`'s Packaging + Clean Release Checklist sections. The
authoritative gate list lives in `docs/post_translation_checklist.md` — this
document doesn't duplicate it, just points to it.

---

## 4. Quick reference: which check catches what

| Symptom | Check | Section |
| --- | --- | --- |
| A concept from the source text is missing/mistranslated | Noun/Strong's coverage | 3.1 |
| Wrong-language characters leaked into a corpus | `verify_language_script.py` | 3.2 |
| A synonym fix "isn't working" | `verify_matchers_dedup.py` | 3.3a |
| Duplicate/empty/malformed verse file | `tools/validate.py` / `tools/validate_zh.py` | 3.3b |
| Traditional/Simplified drifted apart | `tools/validate_zh.py` MIRROR | 3.4 |
| Same bug shows up in another language later | `cross_language_regressions.csv` | 3.5 |
| A MISSING verse's source text doesn't contain the flagged word at all | Versification seam | 3.6 |
| A name and a common word share a Strong's number | Homograph bridging | 3.7 |
| One Strong's number is wrong almost everywhere it's used | DB default correction | 3.7 |
| Ready to ship | `docs/post_translation_checklist.md` | 3.8 |

---

## 5. Why this document exists

Written 2026-09-15 after a Japanese OT coverage push (216 → 0 missing) and a
follow-up all-language dedup sweep surfaced several of the gotchas above in
concrete form — most of this pipeline's discipline already existed in
scattered, excellent, but not-cross-referenced docs and one-off scripts. This
file's job is to be the thing a new session (human or AI) reads first, so
the next hard-won lesson gets written here instead of re-discovered by
accident a fourth time.
