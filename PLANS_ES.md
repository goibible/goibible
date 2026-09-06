# Plan: GOI Bible — Spanish (`es`) Edition

**Status as of 2026-09-05: SHIPPED.** Full 66-book Bible (31,102 verses)
generated, QA'd, and staged — `editions.json` flipped to `active`,
`sqlite/versions/GOI_Es.sql` and `goi_db_download/GOI_Es.db` built via
`goi_language_pipeline.py stage GOI_Es`. See §5 below for the closing QA log.
This document originally started as a readiness audit + staged gameplan,
mirroring the Chinese (`GOI_Bible_Chinese_Hant`) and Vietnamese (`GOI_Bible_vi`)
builds; all stages it laid out are now complete.

Target: a **full 66-book Bible** (NT from Greek TR1550, OT from Hebrew WLC),
same precedent as Vietnamese (the only other full-Bible edition so far; the
two Chinese editions are NT-only).

---

## 1. Where things stand today

```
$ python3 Meta_Bible_Data/Bible_Noun_Extraction/language_readiness.py --lang es
=== Language readiness: 'es' ===
  [GAP] matcher registered
  [GAP] default renderings for noun Strong's (2369 used) — 2369 missing
  [GAP] sense renderings (0/17) — all 17 missing
  [GAP] noun positions resolvable (28889 total) — 28889 resolve to nothing
'es' is NOT ready.
```

Everything is a gap — nothing Spanish-specific has been built yet. But the
scaffolding *expects* Spanish to be next: `translate_verses.py --lang`'s own
help text uses `es` and `../GOI_Bible_Spanish` as its examples, and
`goi_language_pipeline.py` / `editions.json` are already generic enough to
register a new edition without code changes (Vietnamese needed zero pipeline
changes beyond adding its `editions.json` row and a QA config).

**No Spanish reference Bible exists in `Reference_Bible/` yet.** That's the
first concrete blocker — every other language had a public-domain reference
in hand before translation started (KJV/WEBUS for en, CUV for zh, VIE1934 for
vi).

---

## 2. Decisions to make before writing any code

### 2.1 Public-domain Spanish reference edition (blocking)

The obvious modern choice — **Reina-Valera 1960 (RVR1960)** — is **not**
public domain (held by Sociedades Bíblicas Unidas / United Bible Societies).
Do not use it for anything beyond a sighted human's private sanity-check;
never feed it to the model as reference text, never quote it in a worksheet.

Public-domain Spanish options, cleanest first:

| Edition | Year | PD status | Notes |
|---|---|---|---|
| Reina-Valera 1909 (RV1909 / "Antigua") | 1909 | Public domain | Closest in spirit to RVR1960's register; widely mirrored on eBible.org the same way VIE1934 was sourced |
| Sagradas Escrituras (Reina 1569 / Valera 1602, modernized spelling) | 1569/1602 | Public domain | Older register, useful as a second cross-check |
| Traducción en lenguaje actual-type modern PD editions | varies | Verify per-edition | Only use if license is explicitly confirmed PD |

**Recommendation:** RV1909 as primary (same role KJV played for English, CUV
for Chinese), pulled from eBible.org exactly like `Vietnamese_Bible_VIE1934/`
was (see `Reference_Bible/Vietnamese_Bible_VIE1934/README.md` for the
provenance-doc pattern to copy). Optionally add the 1569/1602 Sagradas
Escrituras as a second reference — two PD references make the false-friend
`xref` sweep meaningfully stronger (this was the single biggest quality gap
Chinese had vs. English: only 1 PD ref instead of 2).

**Open question for you:** confirm RV1909 (+ optionally Escrituras) as the
reference, or name a different PD edition to use instead.

### 2.2 Matcher design (blocking for coverage checks)

`matchers.py` has no `es` entry. Spanish is space-delimited like English, so
it's a `SpaceDelimitedMatcher` subclass — but Spanish inflects much harder
than English:

- **Gender/number agreement:** adjectives and articles inflect
  (`bueno/buena/buenos/buenas`), nouns pluralize with `-s`/`-es`, and some
  nouns are only ever used in one gender-inflected default form.
- **Verb conjugation is heavy** (person, number, tense, mood — including the
  subjunctive) — irrelevant for noun-coverage matching *if* `strongs_lang_renderings`
  is filled mostly with nouns (28,889 noun positions, same as other
  languages), but any verb-adjacent sense words need a wider acceptable-forms
  set.
- **Diacritics:** matching must be accent-aware but tolerant of the model
  occasionally dropping accents (é/í/ó/ñ etc.) — normalize both sides (NFC,
  optionally accent-fold as a fallback comparison) before substring matching,
  the way `CJKMatcher` normalizes CJK forms.

Plan: write `SpaceDelimitedMatcher` subclass with an `acceptable_forms()`
that generates `{lemma, lemma+s, lemma+es, masc/fem/plural variants}` per
noun, register `register("es", SpanishMatcher)`, self-test via
`python3 matchers.py`.

### 2.3 Theological vocabulary — needs the same settled-terms table Chinese got

Spanish Christian vocabulary is far less contested than Chinese's 神/上帝
split, but a few terms still need an explicit, locked decision so 2,369
Strong's defaults don't drift verse-to-verse:

| Greek/Hebrew | Candidate Spanish | Note |
|---|---|---|
| θεός / אֱלֹהִים | Dios | uncontested |
| κύριος (divine) | Señor | vs. κύριος (human master) = amo/señor (lowercase, KYRIOS.HUMAN_MASTER sense) |
| πνεῦμα (Holy Spirit) | Espíritu (Espíritu Santo) | vs. spirit/wind/breath senses — same sense-layer split as en/zh |
| Ἰησοῦς | Jesús | uncontested |
| Χριστός | Cristo | uncontested |
| ἐκκλησία | iglesia | not "asamblea" — standard usage |
| ἀγάπη | amor | vs. caridad (older/Vulgate-influenced choice) — pick amor, matches RV1909 |
| δικαιοσύνη | justicia | uncontested |
| register: tú vs. vos vs. usted | **tú** | Reina-Valera tradition uses tú throughout; do not introduce voseo (Argentina/Central America regional) or ustedeo — keep it neutral/pan-Hispanic like RV1909 |

**Open question for you:** confirm `tú` (not `vos`) as the fixed second-person
register — this is a one-time decision that touches every dialogue verse and
should not be revisited mid-corpus.

### 2.4 Known false-friend Strong's — same list, new Spanish glosses needed

The 11 systematic false-friends that bit both English and Chinese will bite
Spanish too (they're properties of the Greek, not the target language):

| Strong's | Greek | Danger pattern in Spanish |
|---|---|---|
| G863 | ἀφίημι | dejar/permitir/abandonar vs. perdonar (only for sins/debts) |
| G4982 | σῴζω | sanar/curar (physical healing) vs. salvar (spiritual) |
| G3860 | παραδίδωμι | traicionar (Judas) vs. entregar |
| G3870 | παρακαλέω | rogar/suplicar/consolar/exhortar vs. animar (default over-used) |
| G1096 | γίνομαι | llegar a ser/nacer/suceder/hacerse — context-critical, no single default |
| G5092 | τιμή | precio (sale contexts) vs. honor |
| G1565 | ἐκεῖνος | él/aquel hombre vs. over-literal "aquel" everywhere |
| G2316 | θεός (lowercase) | dios falso/ídolo vs. Dios |
| G2962 | κύριος | amo/señor (human) vs. Señor (divine) |
| G1135 | γυνή | mujer vs. esposa |
| G3056 | λόγος | palabra/razón/asunto vs. Verbo (JHN 1:1 divine title) |

---

## 3. Staged execution plan (mirrors the zh/vi playbooks)

### Stage 0 — Reference acquisition — **DONE 2026-08-27**

1. ~~Download RV1909~~ Done: `Reference_Bible/Spanish_Bible_RV1909/ZIP/spaRV1909_{readaloud,usfm}.zip`,
   confirmed Public Domain from `SOURCE/copyright.htm` / `SOURCE/details.html`
   (eBible id `spaRV1909`, translation by Reina/Valera, 1909 revision).
2. ~~Create README~~ Done: `Reference_Bible/Spanish_Bible_RV1909/README.md`,
   following `Vietnamese_Bible_VIE1934/README.md`'s shape.
3. Atomized to one-verse-per-file: `One_Directory_RV1909/` — **31,084 verses,
   all 66 books** (full OT+NT — a strictly better reference than VIE1934,
   which only covers Genesis-Deuteronomy + Job/Psalms/Proverbs/Isaiah and
   needed a KJV fallback for the rest). Built via `atomize_usfm.py`, adapted
   from the Vietnamese atomizer with one addition: this USFM edition tags
   words inline (`\w word|strong="G0976"\w*`), which needed an extra strip
   step the VIE1934 source didn't need.
4. **Correction to the original plan:** reference-only editions like this are
   *not* added to `editions.json` — checked the actual precedent and VIE1934
   isn't registered there either, only the primary source texts
   (KJV/WEBUS/TR1550/WLC) and GOI output editions are. So no `editions.json`
   change was made; the README is the provenance record, same as VIE1934's.
5. **Versification aligned to the GOI spine — DONE.** RV1909's native
   atomization was 31,084 verses, 18 short of the project's 31,102-verse
   KJV/WLC/TR1550 spine. Verified this was a real (not a bug) Hebrew/Byzantine
   versification difference across 9 books — content-checked verse by verse
   against KJV, including the classic Job 38-41 Behemoth/Leviathan chapter
   split. Wrote `Spanish_Bible_RV1909/align_versification.py` with the
   verified correction table; its output, `One_Directory_RV1909_GOI/`, is
   **31,102 files with a 0-diff filename match against
   `English_Bible_KJV/One_Directory_KJV`**. Full breakdown in
   `Reference_Bible/Spanish_Bible_RV1909/README.md`. **Use
   `One_Directory_RV1909_GOI/`, not `One_Directory_RV1909/`, as
   `--reference-dir` everywhere from Stage 2 onward** — the native directory
   is kept only as the reproducible raw atomization.

### Stage 1 — Matcher + readiness infrastructure

```bash
# 1. Add SpanishMatcher to Bible_Noun_Extraction/matchers.py, register("es", ...)
python3 Meta_Bible_Data/Bible_Noun_Extraction/matchers.py   # self-test

# 2. Bootstrap noun defaults (2,369 Strong's)
python3 Meta_Bible_Data/Bible_Noun_Extraction/gen_default_renderings.py \
    --lang es --language-name "Spanish" \
    --out proposed_es_defaults.csv --sql-out proposed_es_defaults.sql
# review the CSV by hand, then apply the SQL

# 3. Fill senses_worksheet.csv "es(FILL)" column (17 sense rows, using RV1909
#    as the check reference per row) and import:
python3 Meta_Bible_Data/Bible_Noun_Extraction/import_sense_renderings.py \
    Meta_Bible_Data/Bible_Noun_Extraction/senses_worksheet.csv \
    --lang es --column "es(FILL)"

# 4. Confirm
python3 tools/translation_pipeline/goi_language_pipeline.py readiness GOI_Es
```

**Done when:** `language_readiness.py --lang es` reports `READY ✓`.

### Stage 2 — Register the edition + pilot NT book

Add to `editions.json`:
```json
{
  "edition_id": "GOI_Es",
  "bcp47_tag": "es",
  "language_subtag": "es",
  "display_name": "Español - Biblia GOI",
  "status": "pending",
  "flatfile_dir": "GOI_Bible/GOI_Bible_es",
  "filename_suffix": "GOI_Es",
  "template_edition": "GOI_En"
}
```

Pilot on Philemon (25 verses) or one short NT book, same as Chinese's Stage 2:

```bash
python3 Meta_Bible_Data/Bible_Noun_Extraction/translate_verses.py \
    --lang es --language-name "Spanish" \
    --output-dir GOI_Bible/GOI_Bible_es --filename-suffix GOI_Es \
    --book PHM \
    --reference-dir Reference_Bible/Spanish_Bible_RV1909/One_Directory_RV1909_GOI
python3 tools/normalize_corpus.py --dir GOI_Bible/GOI_Bible_es
python3 Meta_Bible_Data/Bible_Noun_Extraction/verify_coverage.py --lang es \
    --output-dir GOI_Bible/GOI_Bible_es --filename-suffix GOI_Es --missing-only
```

Manually spot-check 5 verses: proper names match RV1909 conventions,
Señor/amo distinction correct, tú register consistent, no dropped negation.

### Stage 3 — Full NT (7,957 verses) — **DONE 2026-08-28**

Generated via `goi_language_pipeline.py generate-nt` against DeepInfra
(`deepseek-ai/DeepSeek-V4-Flash-0731`, already configured in `.env`). All
27 books, 7,957/7,957 files, `check-flatfiles` clean.

### Stage 4 — QA passes — **DONE 2026-08-28**

1. **Noun coverage** — 98.6% final (28,440/28,840), *above* the finished
   English edition's own shipped 95.3%. Fixed 3 real `SpanishMatcher` bugs
   found via triage (fused "Jesucristo" compound; multi-word noun-phrase
   plural agreement — the single largest error class; irregular -s plurals
   like mes→meses/dios→dioses), plus 2 bad DB defaults (γυνή defaulted to
   "mujer" instead of "esposa"; ὄρος defaulted to "montaña" instead of the
   ~30×-more-common RV1909 convention "monte").
2. **False-friend sweep** — found and fixed **two pre-existing bugs in
   `falsefriend_sweep.py` itself** (not Spanish-specific — confirmed broken
   for the finished English edition too): the xref reference-file lookup
   required matching the draft's *entire* filename including its edition
   suffix (never worked once draft/ref suffixes differ), and the tokenizer
   was ASCII-only and shredded every accented word. Both fixed. Checked all
   11 known false-friend Strong's numbers by hand; found and fixed:
   ἀνομία defaulting to the fabricated non-word "anomia" (13 verses →
   "iniquidad"), τιμή rendering "honor" in 5 sale/price contexts (→
   "precio", matches RV1909 and the English edition exactly), and
   παραδίδωμι rendering "entregó" for Judas's betrayal in 11 verses — left
   matching RV1909's own convention initially, then changed to "traicionó"
   per explicit user decision to match the English edition's documented
   correction.
3. **Negation + numbers** — added real Spanish support to `meaning_checks.py`
   (`--lang` flag, `ES_NEG_TARGET`/`ES_NUM_TARGET`, did not exist before).
   Negation: 0 flags. Numbers: 44→14 after two regex fixes (Spanish fuses
   compound numbers into one word with no internal `\b` — veinticuatro,
   dieciocho — and apocopates ordinals — "tercer día" not "tercero día");
   the remaining 14 are checker-side false positives (compound-number
   fusion, a scribal colophon getting tokenized as verse content, and
   legitimate "again"/"both" idioms for δεύτερος), individually sampled
   and confirmed, not real drops.
4. **Proper-noun consistency audit** — lightweight frequency-table check
   (not a new permanent script) across the 40 most common names/places in
   the whole NT: clean, zero real spelling/casing inconsistencies.
5. **Clause completeness LLM pass** — no `es`-specific script was needed;
   `clause_check.py` was already fully language-agnostic. Full-NT run found
   12 flags; fixed 10 genuine drops (MAT 2:16 "children" mistranslated as
   "servants"; ἀκοή "report/fame" mistranslated as literal "ear" in 6
   verses; 3 list-of-distinct-words verses where a repeated word masked a
   dropped second term — ROM 11:9, COL 1:11, COL 3:8; a person mismatch at
   1JN 1:4; a dropped predicate noun at HEB 7:20; προσφάγιον narrowed to
   "fish" at JHN 21:5). 2 flags reviewed and left as-is (LUK 6:26 — checker
   itself confirmed no real omission; JHN 7:4 — RV1909 paraphrases just as
   loosely here).

Result: 0 open QA flags across every gate. See git history / session log for
the full list of individual fixes if auditing later.

### Stage 5 — Old Testament (23,145 verses, WLC → Spanish)

**In progress, started 2026-08-28.** Went with a variant of option (a):
the discovery pass found `build_ot_name_db.py` was *already* generalized
(language profiles under `translation_configs/name_qa/*.json`, `vi.json`
being the existing one) — only the verse-generation script itself
(`translate_ot_smoke_vi.py`) was still vi-hardcoded. Also found
`tools/OT_to_English.py`/`OT_to_Chinese.py` — a different, DB-anchor-driven
OT pipeline used for those two languages — but its `bible_noun.sqlite3`
dependency (Hebrew `strongs_ot` + `noun_translations` tables) is currently a
stale 0-byte file in this checkout (not tracked in git, apparently cleared
since those runs), so that path is not usable right now without rebuilding
it from scratch. Went with the proven, currently-working vi playbook instead:

- Wrote `tools/translation_pipeline/translate_ot_es.py`, adapted from
  `translate_ot_smoke_vi.py`: WLC Hebrew source, RV1909 as post-draft QA
  reference (not a source), Spanish system/user prompts, "Jehová"/"Dios"
  divine-name convention, same genealogy-collision warning, same
  citation-header-leak stripping.
- **RV1909 turned out to have full OT+NT coverage** (31,102 verses, all 39 OT
  books present in `One_Directory_RV1909_GOI`) — unlike VIE1934's
  Torah/Job/Psalms/Proverbs/Isaiah-only coverage, so no KJV fallback branch
  was needed for Spanish.
- Added `translation_configs/name_qa/es.json` (RV1909 reference edition,
  `GOI_Bible_es`/`GOI_Es` target, Spanish-tuned stopword list to suppress
  sentence-initial capitals and generic capitalized religious nouns like
  Dios/Señor/Padre from being tracked as proper-name drift targets).
  `build_ot_name_db.py --profile es --rebuild` seeded 213 approved names /
  10,964 occurrences from RV1909 before generation started.
- Reused `staging/ot_torah/full_ot_refs.json` as-is (book/chapter refs only,
  already language-agnostic).
- Full 23,145-verse generation launched via `nohup` in the background
  (DeepSeek-V4-Flash-0731 via DeepInfra), name-grounded from the start
  (the vi run's own log shows grounding from verse one drastically reduces
  red-flag rate vs. bolting it on after — reused that lesson directly rather
  than re-learning it).

Known OT-specific traps carried forward from the Vietnamese log
(`staging/ot_torah/TORAH_RUN_STATUS.md`) to watch for during Spanish QA:
genealogy subject-smearing, CJK/Cyrillic character leaks mid-word, raw
chain-of-thought leaking into output on token-limit truncation, untranslated
English name leaks (esp. unhyphenated ones — the name extractor requires a
hyphen or profile membership to flag a candidate, so a lone untranslated
English word is otherwise invisible), and intra-book name-spelling drift on
recurring characters (worst case in vi: 10+ spellings of one name in one
book). QA plan: per-book (or batched) `build_ot_name_db.py --validate`
passes plus the CJK/Cyrillic/oversized-file corpus scans, not full manual
verse-by-verse Hebrew verification for every low-stakes list/genealogy name
— same proportionality calls the vi log documents.

---

## 4. Summary — what's actually blocking a start

| # | Blocker | Owner action needed |
|---|---|---|
| 1 | No PD Spanish reference in repo | confirm RV1909 (§2.1) and fetch it |
| 2 | No `es` matcher | write it (§2.2) — mechanical, no decision needed |
| 3 | No `es` noun defaults / senses | bootstrap + fill worksheet (§Stage 1) — needs a human pass over ~2,369 + 17 rows, same volume Chinese/Vietnamese required |
| 4 | Register register (tú/vos/usted) | **your call** (§2.3) — recommend tú |
| 5 | No generic OT translator | decide (a) fork vi scripts vs (b) generalize first (§Stage 5) — recommend (b) |

Nothing here is technically hard — it's the same shape of work already done
twice (zh, vi). The realistic first milestone is Stage 2 (pilot NT book)
once Stage 0/1 close, which mainly needs the RV1909 reference in hand and an
LLM provider configured (`Meta_Bible_Data/pipeline.md` §"Model Configuration").

---

## 5. Closing QA log (2026-09-04/05) — done at ship time

Full OT generation (Stage 5) finished 2026-09-03 (~2.5 days at 4x concurrency
after the single-threaded run was diagnosed as reasoning-token-bound, not
rate-limit-bound — DeepInfra account cap is ~200 tok/s, single-stream usage
was ~42 tok/s). Closing passes run before flipping `editions.json` to active:

1. **6 verses that exhausted all retries during generation** (all plain
   read-timeouts, no content issue) — resumed and filled: `2CH 1:13`,
   `SNG 2:7`, `ISA 9:1`, `EZK 5:7`, `EZK 29:7`, `EZK 47:8`.
2. **Noun/name-consistency re-audit** (`build_ot_name_db.py --rebuild
   --validate`, full OT refs) — DB had only ever been seeded with 213
   pre-generation names; rebuilt against the finished corpus. Found and
   fixed: 1 encoding bug (`PRO 16:5`, literal `\u00XX` escapes — isolated),
   1 citation-header-leak (`1CH 14:17` was just the string "1 Crónicas
   14:17" — **root cause patched** in `translate_ot_es.py`'s
   `strip_response()`, which didn't handle numbered-book headers or a
   header-only response), 3 real spelling-variant fixes (Aram-Naharaim ×2,
   Baal-hanán) + 7 more standardized (Ezión-geber recurring 7×,
   Poqueret-hasebaim, Hor-hagidgad). ~30 "missing name" flags spot-checked
   directly against WLC — all false positives from RV1909's own 1909-era
   divine-title looseness (Elohim/Adonai rendered "Jehová") or its leftover
   versification quirks (e.g. 1CH 21, 1KI 22, Job 39-40 title block), not
   GOI_Es defects.
3. **False-friend / negation-numbers checks**: confirmed N/A for OT — both
   `falsefriend_sweep.py` and `meaning_checks.py` are hardcoded to the
   Greek NT source (`Greek_Bible_TR1550`); no Hebrew equivalent exists.
4. **Clause-completeness LLM pass**: built `clause_check_ot.py` (WLC-sourced
   variant of the NT tool, added `--workers` concurrency). Full 23,145-verse
   run, ~262 verses/min. Result: 23,068 OK, 77 flagged. Hand-triaged every
   flag against WLC — ~74 were checker false positives (several literally
   self-contradicting, quoting the "missing" text from the same CSV row);
   **3 genuine errors fixed**: `GEN 15:19` (wrong nation-name list, copied
   from v21 instead of translating its own Kenite/Kenizzite/Kadmonite list),
   `EXO 2:21` ("Moisés accedió a **morir**" — should be "**habitar**" — a
   full meaning reversal), `EZK 16:43` (verb substitution, "cometido"→
   "considerado").
5. **Register audit (tú/vosotros)**: found the `translate_ot_es.py` prompt
   never actually encoded the tú/vosotros decision from §2.3 — 72 OT verses
   had drifted to "ustedes" (ustedeo). NT (`translate_verses.py` output) was
   unaffected (0 occurrences, 734 "vosotros"). Patched the OT prompt with an
   explicit rule, deleted and regenerated the 72 affected verses; confirmed
   0 "usted"/"ustedes" corpus-wide afterward.
6. **Deep-scrub scans** (CJK/Cyrillic leaks, chain-of-thought/reasoning
   leaks, untranslated-English leaks, oversized files): all 0 hits.
   Duplicate-word stutter scan: 1 real hit (`PRO 4:23`, "guarda guarda" —
   fixed to "cosa guardada, guarda"). A double-negation scanner was
   attempted but abandoned — Spanish's negative-concord exceptions
   (pre-verbal subjects, "sin que"/"para que" clauses) made a regex-only
   check ~100% false positives; would need real dependency parsing to be
   reliable, not built this pass.

Final state: 31,102/31,102 verses, `editions.json` → `active`,
`template_edition` → `GOI_En` (was still `TR1550`/NT-only), staged via
`goi_language_pipeline.py stage GOI_Es` (also required adding a `GOI_Es` row
to `sqlite/reference_seed.sql`, which `build_shell.sh` reads independently of
`editions.json` — that gap caused the first `stage` attempt to fail on
`build_downloads.py`).
