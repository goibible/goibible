# TR1550 Language Translation — Master Instructions

**Single source of truth for translating the Greek Textus Receptus (Stephanus
1550) New Testament into any target language using this pipeline.**

Audience: the next translator — human or AI. This is the encyclopedic reference.
For the short operational walkthrough see `TRANSLATION_GUIDE.md`; for corpus
provenance/copyright see `README_GOI.md`. When those disagree with this file,
this file wins.

---

## Table of contents
1. What this is, and the core idea
2. Repository & file layout
3. Database model (every table)
4. The pipeflow (end to end)
5. Helper scripts — complete inventory
6. Strong's references (senses, polysemy hotspots, false-friends)
7. Gotchas & edge cases
8. Copyright posture
9. Invariants & the validation gate
10. Command cheat-sheet
11. Status of the English reference edition

---

## 1. What this is, and the core idea

One frozen Greek source (TR1550) + a **language-neutral disambiguation layer**
built once. Translating a new language is mostly *supplying words*, not
re-deciding meaning. The hard interpretive calls (this κύριος = a human master,
not the divine Lord; this γυνή = woman, not wife) are stored against **Greek
coordinates** and transfer to every language unchanged.

**The payoff:** 16 sense decisions + a default-word list resolve ~1,060
context-sensitive positions automatically. You fill renderings; the pipeline
enforces that every Greek noun reaches your text.

---

## 2. Repository & file layout

```
bible/
├── docs/                         all documentation
│   ├── tr1550_language_translation_instructions.md   <- THIS FILE
│   ├── TRANSLATION_GUIDE.md      short operational walkthrough
│   ├── README_GOI.md             provenance, what's verified, copyright
│   └── 2026-06-03_gptaudit.md    audit + correction record
├── validate.py                   integrity gate (13 invariants)   ── run from repo root
├── normalize_corpus.py           punctuation/whitespace canonicalizer
├── GOI_Bible_English/            finished English edition (7,957 verse files) — worked example
├── GOI_Bible_<LANGUAGE>/         YOU CREATE THIS — your output, same filenames
├── English_Bible_KJV/, English_Bible_WEBUS/, Chinese_Bible_CUV/   public-domain reference editions
├── Greek_Bible_TR1550/, Hebrew_Bible_WLC/, sources/               source corpora
├── notes/  logs/  archive/       prior-phase notes, run logs, and archived earlier work
├── backup/                       archived earlier pipeline snapshots
└── Greek_Noun_Extraction_NIM/    the pipeline + database (git submodule)
    ├── greek_noun.sqlite3        the database (see §3)
    ├── One_Directory_TR1550/     raw Greek source, one file per verse — FROZEN
    ├── matchers.py               per-language coverage matching
    ├── language_readiness.py     what a language still needs
    ├── verify_coverage.py        generic per-language coverage
    ├── verify_noun_coverage.py   English-specific tuned coverage (en authority)
    ├── falsefriend_sweep.py      false-friend detector (xref + strongs)
    ├── translate_verses.py       generic Greek→target-language verse driver
    ├── gen_default_renderings.py bootstrap default renderings for a language
    ├── senses_worksheet.csv / senses.csv / import_sense_renderings.py
    └── sweep_history/  ... (build/history scripts — see §5)
```

All commands in this guide are run **from the repo root** (paths like
`docs/…` and `Greek_Noun_Extraction_NIM/…` are repo-root-relative).

**Filename scheme everywhere:** `NNN_BOOK_CCC_VVV.txt`
`NNN`=canon order 040–066, `BOOK`=OSIS code (MAT…REV), `CCC`/`VVV`=zero-padded
chapter/verse. Raw Greek files add a `_TR1550` suffix. 7,957 verses, 27 books
(Matthew–Revelation). One verse per file, single line, UTF-8 NFC.

---

## 3. Database model (`greek_noun.sqlite3`)

| Table | Rows | Purpose |
| --- | ---: | --- |
| `books` | 27 | NT books, canon order, codes |
| `verses` | 7,957 | (book, chapter, verse) registry |
| `verse_texts` | 7,957 | the raw Greek verse text in the DB |
| `strongs_nt` | 140,937 | **the morphology** — every Greek token: book/ch/verse/word_pos, beta-code word, `strongs_num`, `morph` (e.g. `N-NSF`), and `in_tr1550` flag |
| `strongs_renderings` | 5,400 | per-Strong's lemma, translit, default `english`, default `chinese` |
| `strongs_lexicon` | 14,298 | Strong's dictionary glosses/definitions |
| `strongs_lang_renderings` | 10,410 | **default word per Strong's per language** `(strongs_num, lang, rendering)` — add your language here |
| `nouns` | 2,369 | distinct noun lemmas |
| `verse_noun_occurrences` | 28,889 | **canonical noun count** — every noun token, reconciled to raw TR1550 |
| `verse_rendering_overrides` | 1,066 | **context overrides** — `(book,chapter,verse,word_pos,strongs_num) → correct_rendering`, with `reference_agreement`, `note`, `sense_key` |
| `senses` | 16 | the disambiguation senses: `sense_key, strongs_num, definition, en_base, is_default_sense` |
| `sense_renderings` | per-lang | **the per-language sense words** `(sense_key, lang, rendering, needs_review)` |
| `noun_categories` | 13 | GOD/PERSON/PLACE/OTHER etc. |
| `versions` | 1 | TR1550 |

View: **`v_effective_rendering`** — resolves, per noun position and language:
sense override → that language's sense word → else the language default.

**Key invariant:** `verse_noun_occurrences` == `strongs_nt WHERE morph LIKE 'N-%'
AND in_tr1550=1`, per verse, and every occurrence's surface physically appears in
its raw TR1550 verse. `strongs_nt` is variant-inclusive; `in_tr1550=0` marks the
~36 alternate-reading tokens not in the raw text (do not count them).

---

## 4. The pipeflow (end to end)

```
  ┌─────────────────────────────────────────────────────────────────┐
  │ SOURCE (frozen):  One_Directory_TR1550/  +  strongs_nt morphology │
  └─────────────────────────────────────────────────────────────────┘
            │
            │  per language L, supply renderings:
            ▼
  ┌──────────────────────────┐   ┌───────────────────────────┐
  │ strongs_lang_renderings  │   │ sense_renderings (16 rows)│
  │   default word / Strong's│   │   context senses for L    │
  └──────────────────────────┘   └───────────────────────────┘
            │            (positions already marked, language-neutral)
            ▼                         ▼
        verse_rendering_overrides  ──►  v_effective_rendering (resolution)
            │
            ▼  translate verses (from Greek), one file/verse:
  ┌──────────────────────────┐
  │ GOI_Bible_<LANGUAGE>/    │
  └──────────────────────────┘
            │
            ├─► normalize_corpus.py        (canonical punctuation)
            ├─► language_readiness.py      (are renderings complete?)
            ├─► verify_coverage.py --lang L (did every noun reach the text?)
            └─► validate.py                (structural integrity gate)
```

**Onboarding steps (per language L, output dir suffix `LANGUAGE`):**

1. **Register a matcher** in `matchers.py` for L (else coverage is meaningless and
   tools refuse to run). See §7 for which matcher type.
2. **Default renderings:** insert `(strongs_num, 'L', rendering)` into
   `strongs_lang_renderings` for the 2,369 noun Strong's numbers. The review-
   first helper is `gen_default_renderings.py` (CSV + optional SQL patch).
3. **The 16 senses:** fill your column in `senses_worksheet.csv`, then
   `import_sense_renderings.py --lang L --column "<your column>"`.
4. **Readiness:** `language_readiness.py --lang L` until it says `READY ✓`.
5. **Translate** the 7,957 verses *from the Greek* into `GOI_Bible_<LANGUAGE>/`,
   using `translate_verses.py` (or a compatible harness), the rendering tables
   as controlled vocabulary, and the English edition / PD references only as
   structural (not source) references. `normalize_corpus.py --dir GOI_Bible_<LANGUAGE>`.
6. **Coverage:** `verify_coverage.py --lang L --output-dir ../GOI_Bible_<LANGUAGE>`;
   chase `--missing-only`.
7. **False-friend pass** (§6) and **validate** (§9). Commit in logical batches.

---

## 5. Helper scripts — complete inventory

### Active pipeline (use these)
| Script | Run / purpose |
| --- | --- |
| `validate.py` | `python3 validate.py` — 13-invariant gate; run after every change |
| `normalize_corpus.py` | `--dir DIR [--check]` — canonical punctuation/whitespace; idempotent |
| `matchers.py` | library: `get_matcher(lang)`; `python3 matchers.py` self-tests. Register new languages here |
| `language_readiness.py` | `--lang L` — reports matcher/defaults/senses/resolution gaps |
| `verify_coverage.py` | `--lang L --output-dir DIR [--missing-only]` — generic noun coverage |
| `verify_noun_coverage.py` | English-specific tuned coverage (rich inflection map); the `en` authority |
| `import_sense_renderings.py` | `WORKSHEET --lang L --column COL [--dry-run]` — load filled senses |
| `senses_worksheet.csv` / `senses.csv` | the 16-sense fill sheet / catalog |
| `gen_default_renderings.py` | review-first bootstrap for `strongs_lang_renderings` (CSV + optional SQL patch; no DB writes by default) |
| `translate_verses.py` | generic Greek→target-language verse driver using noun anchors + optional PD references |
| `falsefriend_sweep.py` | `xref` (cross-ref divergence detector) + `strongs` (per-Strong's targeted sweep) — the §6c method, shipped |
| `audit_noun_count_deficits.py` | multiplicity-aware noun deficit audit → `deficits_audit.csv` |
| `rebuild_noun_occurrences_from_strongs.py` | regenerate `verse_noun_occurrences` from `strongs_nt` (source of truth) |
| `sweep_history/` | provenance: the 35 as-run scripts behind the ~155 English corrections (see its README) |

### Build / history (reference only — already run for English)
`noun_count_nim.py` (original LLM noun extractor — superseded by the rebuild),
`import_strongs.py` / `import_strongs_renderings.py` / `import_renderings.py`
(seed strongs tables), `import_rendering_overrides.py` (create overrides table),
`build_ambiguous_audit.py` / `autonomous_audit.py` (polysemy audit that produced
the overrides), `gen_renderings.py` / `gen_chinese_renderings.py` (rendering
generation), `apply_chinese_fixes.py` / `fix_*` / `retranslate_overrides.py` /
`sync_codex_to_batches.py` (one-off maintenance), `bible_into_sqlite.py` /
`verify_alignment.py` / `remap_wlc.py` / `resolve_wlc.py` (corpus build / Hebrew
WLC tooling, not NT-critical). `old_noun_count.py`, `test.py` — dead.

---

## 6. Strong's references

### 6a. The 16 disambiguation senses (`senses` table)
These Greek words flip meaning by context. The positions are pre-marked; you only
supply the target word per sense (and the default for the non-sense positions).

| sense_key | Strong's | lemma | English | overridden verses |
| --- | --- | --- | --- | ---: |
| ANER.SPOUSE | G435 | ἀνήρ | husband | 51 |
| ARTOS.COUNTABLE | G740 | ἄρτος | loaf | 24 |
| BROSIS.CORROSION | G1035 | βρῶσις | corrosion | 2 |
| GINOMAI.BECOME | G1096 | γίνομαι | become | 199 |
| GINOMAI.HAPPEN | G1096 | γίνομαι | happen | 363 |
| GINOMAI.BE_DONE | G1096 | γίνομαι | be done | 117 |
| GYNE.WOMAN | G1135 | γυνή | woman | 127 |
| THELO.WILL | G2309 | θέλω | will | 33 |
| THEOS.LOWERCASE_GOD | G2316 | θεός | god | 16 |
| KYRIOS.HUMAN_MASTER | G2962 | κύριος | master | 81 |
| LOGOS.DIVINE_TITLE | G3056 | λόγος | Word | 1 |
| PNEUMA.UNCLEAN_SPIRIT | G4151 | πνεῦμα | spirit | 24 |
| PNEUMA.HUMAN_SPIRIT | G4151 | πνεῦμα | spirit | 18 |
| PNEUMA.BREATH | G4151 | πνεῦμα | breath | 2 |
| PNEUMA.WIND | G4151 | πνεῦμα | wind | 1 |
| PNEUMA.DIVINATION_SPIRIT | G4151 | πνεῦμα | spirit | 1 |

The default (non-sense) rendering of each: G435 man, G740 bread, G1035 food,
G1096 become, G1135 wife, G2309 want, G2316 God, G2962 Lord, G3056 word,
G4151 Spirit.

### 6b. Polysemy hotspots (most context overrides)
G1096 γίνομαι (679), G1135 γυνή (127), G2962 κύριος (81), G435 ἀνήρ (51),
G4151 πνεῦμα (46), G2309 θέλω (33), G740 ἄρτος (24), G2316 θεός (16),
G3056 λόγος (2), G2322 θεραπεία (2), G1035 βρῶσις (2), G4371 προσφάγιον (1).

### 6c. False-friend Strong's — verbs/pronouns NOT covered by the noun sense layer
These were the biggest meaning errors in the English machine draft. **Check every
one in context in your language; do not trust the default gloss.**

| Strong's | lemma | default trap | correct senses |
| --- | --- | --- | --- |
| G863 | ἀφίημι | "forgive" | **leave / let / allow / forsake** (forgive only for sins/debts) |
| G4982 | σῴζω | "save" | **heal / make well** in healing contexts |
| G3860 | παραδίδωμι | "deliver" | **betray** (Judas); hand over / deliver up elsewhere |
| G3870 | παρακαλέω | "encourage" | **beg / implore / beseech / comfort / exhort** |
| G1096 | γίνομαι | "happen" | **become / be / be born / be made / come to pass** |
| G5092 | τιμή | "honor" | **price / value** (sale contexts) |
| G1565 | ἐκεῖνος | "that one" | **he / him / that man** |
| G1807 | ἐξαιρέω | "deliver" | **pluck out** (eye); rescue elsewhere |
| G4371 | προσφάγιον | "meat" | **anything to eat / fish** |
| — | μὴ γένοιτο | "may it never happen" | idiom: **"By no means! / Certainly not!"** |

How English was swept: three-way divergence (draft vs two PD references) +
targeted per-Strong's checks — now shipped as `falsefriend_sweep.py`:

```bash
# what does the draft systematically miss vs the PD-reference consensus?
python3 Greek_Noun_Extraction_NIM/falsefriend_sweep.py xref \
    --draft GOI_Bible_<LANGUAGE> --lang L \
    --refs <pd_ref_dir_1>,<pd_ref_dir_2>
# confirm a specific Strong's is mis-rendered (e.g. σῴζω G4982 as "saved")
python3 Greek_Noun_Extraction_NIM/falsefriend_sweep.py strongs \
    --draft GOI_Bible_<LANGUAGE> --strongs 4982 \
    --suspect '<suspect>' --ref-has '<correct>' --refs <pd_ref_dirs>
```

**Hard prerequisite:** `xref` needs ≥1 (ideally ≥2) public-domain reference
edition in your language. With zero PD references, onboarding is still possible
but QA degrades to coverage-only. With one PD reference, targeted
`strongs --ref-has` checks are still useful. With two PD references, the full
cross-reference divergence method becomes high-signal.

### 6d. Other words to watch (defensible-but-context-sensitive)
ἔθνος (nation/Gentile), ἅγιος (holy one/saint), ἐπιθυμία (desire/lust),
ἀρχιερεύς (high/chief priest), σάρξ (flesh/body/human), ψυχή (soul/life/person),
αἰών (age/world/forever), σπλάγχνα (compassion, **not** "bowels"),
ἀγάπη ("love", **not** "charity"), ἀναστροφή (conduct, **not** "conversation").

---

## 7. Gotchas & edge cases

**Source (do not "fix"):** TR readings absent from modern Bibles belong (Comma
Johanneum, Acts 8:37, longer Mark, Romans 16 doxology). TR1550 versification is
canonical — never renumber. Bracketed scribal **colophons** (2 Cor 13:14,
Eph 6:24) are paratext — translate them in brackets.

**Matching by language type:**
- **CJK (zh, ja, th)** — no word spaces; English `\b` matching is meaningless.
  Use `CJKMatcher` (substring). Watch Traditional vs Simplified consistency, NFC.
- **RTL (he, ar)** — store text in logical (typing/reading) order; direction is
  display-only; matching works on logical order.
- **Agglutinative (tr, fi, hu)** — renderings appear with glued case/number
  suffixes; a whole-word matcher under-counts. Write a stem matcher.
- **Gendered/cased** — the sense layer gives a *base* word; your prose inflects
  it; the matcher must accept inflected forms.

**Proper names:** keep one transliteration policy across the whole corpus
(Simon/Simeon, Elias/Elijah, Jonas/Jonah). A name table per language helps; this
is a known weak spot.

**Normalization:** the data layer is straight-ASCII quotes/apostrophes, em-dash
for breaks, NFC, single trailing newline. Run `normalize_corpus.py` on your
output; `validate.py` enforces it.

**The English coverage authority** is `verify_noun_coverage.py` (rich inflection
tables, 99.7%). The generic `verify_coverage.py` uses base forms and will read a
few points lower — that is expected; it is the cross-language tool, not a
regression on English.

---

## 8. Copyright posture

**Goal: a copyright-unencumbered text.** Greek TR1550 is public domain. To check
sense, use **only public-domain references** in your language (English used KJV +
WEBUS, both PD; for zh use CUV; for es use a PD edition such as RVA). **Never**
consult or copy a *modern copyrighted* translation. You cannot infringe a PD
work, so overlap with PD references is fine; overlap with a copyrighted one is
not. Full reasoning in `README_GOI.md §5`.

---

## 9. Invariants & the validation gate

`python3 validate.py` enforces (run after any change; keep it green for English):
file count 7,957 · valid filenames · single-line non-empty verses · canonical
punctuation/NFC · every verse has a TR1550 source · DB foreign-key integrity ·
override positions valid · sense catalog consistency · noun count canonical to
raw TR1550 (count parity + every noun surface present in its raw verse) · English
coverage 0 missing.

For language L, use `verify_coverage.py --lang L` as the coverage gate and treat
`validate.py` as a structural/DB gate plus an English reference check. Non-
English coverage is not yet embedded in `validate.py`.

---

## 10. Command cheat-sheet

```bash
L=es; LANGUAGE=Spanish        # example

# 1. defaults (per Strong's) — generate a reviewable bootstrap artifact first
python3 Greek_Noun_Extraction_NIM/gen_default_renderings.py \
  --lang $L --language-name "$LANGUAGE" \
  --out ${L}_defaults_review.csv --sql-out ${L}_defaults_review.sql

# after review, apply the SQL patch yourself
sqlite3 Greek_Noun_Extraction_NIM/greek_noun.sqlite3 < ${L}_defaults_review.sql

# 2. the 16 senses (fill your column in senses_worksheet.csv first)
python3 Greek_Noun_Extraction_NIM/import_sense_renderings.py \
  Greek_Noun_Extraction_NIM/senses_worksheet.csv --lang $L --column "$L(FILL)"

# 3. readiness
python3 Greek_Noun_Extraction_NIM/language_readiness.py --lang $L

# 4. translate (provider/model configured via env vars or CLI)
python3 Greek_Noun_Extraction_NIM/translate_verses.py \
  --lang $L --language-name "$LANGUAGE" --output-dir GOI_Bible_$LANGUAGE \
  --book MAT --chapter-start 1 --chapter-end 1 \
  --reference-dir GOI_Bible_English

# 5. normalize output
python3 normalize_corpus.py --dir GOI_Bible_$LANGUAGE

# 6. coverage
python3 Greek_Noun_Extraction_NIM/verify_coverage.py --lang $L \
  --output-dir GOI_Bible_$LANGUAGE --missing-only

# 7. false-friend sweep (requires at least one PD reference)
python3 Greek_Noun_Extraction_NIM/falsefriend_sweep.py xref \
  --draft GOI_Bible_$LANGUAGE --lang $L --refs <pd_ref_dir_1>,<pd_ref_dir_2>

# 8. integrity gate
python3 validate.py

# inspect the layer
sqlite3 Greek_Noun_Extraction_NIM/greek_noun.sqlite3 "
  SELECT * FROM senses;
  SELECT * FROM sense_renderings WHERE lang='$L';
  SELECT * FROM strongs_lang_renderings WHERE lang='$L' LIMIT 20;
  SELECT * FROM v_effective_rendering WHERE lang='$L' LIMIT 20;"

# look at how English rendered any verse (your structural reference)
cat GOI_Bible_English/044_ACT_009_029.txt
cat Greek_Noun_Extraction_NIM/One_Directory_TR1550/044_ACT_009_029_TR1550.txt
```

---

## 11. Status of the English reference edition

English (`GOI_Bible_English/`) is the worked, verified example:
- Noun count **canonical to raw TR1550** — 28,889 nouns, every one present in its
  raw verse; `validate.py` green (13/13).
- Noun **coverage 0 missing / 99.7%**.
- **~155 meaning corrections** applied: a 23-item external audit + a corpus-wide
  false-friend sweep (ἀφίημι 28, σῴζω 14, παραδίδωμι 30, παρακαλέω 35, γίνομαι,
  ἐκεῖνος, μὴ γένοιτο, ἐξαιρέω, …) — see `2026-06-03_gptaudit.md` and README §
  changelog.
- Disambiguation **sense layer** complete for English (16/16).
- **Known not-yet-done:** verb/clause-level completeness verification (nouns are
  verified, verbs are not); proper-noun transliteration consistency; other
  false-friend families beyond those swept. These are the same fronts your
  language should expect.

Build on this spine and your edition inherits its rigor.
