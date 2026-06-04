# Translation Trail Guide — Greek TR1550 → any language

You are an AI about to translate the New Testament into a new target language
using this repository's pipeline. Read this once, top to bottom, before touching
anything. It tells you the mental model, the exact steps, the tools, and the
traps. The English edition (`GOI_Bible_English/`) is the worked reference — when
in doubt, look at how English did it.

---

## 0. Mental model (read this first)

There is **one Greek source of truth** (Textus Receptus, Stephanus 1550) and a
**disambiguation layer** that was built once, language-neutrally. Your job for a
new language is mostly **filling in renderings**, not re-deciding meaning.

```
  Greek TR1550 (raw text + Strong's morphology)        <- source of truth, frozen
        │
        ├── strongs_lang_renderings (default word per Strong's, per language)
        │
        ├── senses + sense_renderings (16 context senses, per language)   <- the clever part
        │       e.g. κύριος default = "Lord", but at 81 tagged positions
        │            sense KYRIOS.HUMAN_MASTER => "master" (en) / "主人" (zh)
        │
        └── verse_rendering_overrides (which Greek positions take which sense)  <- language-neutral, reused
        ↓
  translated verses: one file per verse in GOI_Bible_<LANGUAGE>/
        ↓
  verify_coverage.py --lang <L>   (did every Greek noun make it into the text?)
  validate.py                     (did anything structural break?)
```

The disambiguation decisions (this κύριος is a human master, not the divine
Lord; this γυνή is a woman, not a wife) are **already made** and stored against
Greek coordinates. They transfer to your language unchanged. You only supply the
*word* your language uses for each sense.

---

## 1. The repository map

| Path | What it is |
| --- | --- |
| `Greek_Noun_Extraction_NIM/One_Directory_TR1550/` | the raw Greek source, one file per verse (`NNN_BOOK_CCC_VVV_TR1550.txt`) — **frozen, never edit** |
| `Greek_Noun_Extraction_NIM/greek_noun.sqlite3` | the database (morphology, renderings, senses, overrides) |
| `GOI_Bible_English/` | the finished English edition — your worked example |
| `GOI_Bible_<LANGUAGE>/` | **you create this** — your translated output |
| `docs/README_GOI.md` | provenance, what's verified, copyright posture |
| `docs/TRANSLATION_GUIDE.md` | this file |
| `validate.py` | project integrity gate (run after every change) |
| `normalize_corpus.py` | punctuation/whitespace canonicalizer |
| `Greek_Noun_Extraction_NIM/matchers.py` | per-language "did the word appear" logic |
| `Greek_Noun_Extraction_NIM/language_readiness.py` | what your language still needs |
| `Greek_Noun_Extraction_NIM/verify_coverage.py` | generic per-language coverage checker |
| `Greek_Noun_Extraction_NIM/senses_worksheet.csv` | the 16-sense fill-in sheet |
| `Greek_Noun_Extraction_NIM/import_sense_renderings.py` | load a filled worksheet into the DB |
| `Greek_Noun_Extraction_NIM/gen_default_renderings.py` | review-first bootstrap for noun defaults (CSV + optional SQL patch) |
| `Greek_Noun_Extraction_NIM/translate_verses.py` | generic Greek→target-language verse driver |
| `Greek_Noun_Extraction_NIM/falsefriend_sweep.py` | PD-reference-driven false-friend detection (`xref` + `strongs`) |

File naming everywhere: `NNN_BOOK_CCC_VVV.txt` — `NNN` canon order (040–066),
`BOOK` OSIS code (MAT…REV), `CCC`/`VVV` zero-padded chapter/verse. 7,957 verses.

---

## 2. Know the source's nature (do not "fix" these)

- It is **Textus Receptus**, not a modern critical text. It contains readings
  modern Bibles omit (Johannine Comma 1 Jn 5:7–8, Acts 8:37, longer Mark ending,
  Romans 16 doxology). Translate them; they belong.
- **Versification is TR1550's** and is the canonical spine. The noun database is
  reconciled to the raw text (`in_tr1550 = 1`). Do not renumber.
- Some epistles end with **bracketed scribal colophons** (e.g. 2 Cor 13:14,
  Eph 6:24). They are paratext — translate them in brackets, as English did.

---

## 3. Onboarding your language — step by step

Let `L` be your ISO code (e.g. `es`, `fr`, `ar`, `sw`). Let `LANGUAGE` be the
output dir suffix (e.g. `Spanish`).

### Step 1 — Register a matcher (`matchers.py`)

Coverage checking is language-specific. **You must register a matcher before any
coverage number means anything** — the tools refuse undefined languages on purpose.

- Space-delimited language with light inflection (Romance, Germanic): subclass or
  reuse `SpaceDelimitedMatcher` (optionally pass a better `acceptable_forms` for
  your morphology).
- No-space script (zh, ja, th): use / adapt `CJKMatcher` (substring, no `\b`).
- Agglutinative (tr, fi, hu): write a stem-based matcher.
- RTL (he, ar): logical-order substring is fine; direction is display-only.

Then `register("L", YourMatcher)`. Run `python3 matchers.py` to self-test.

### Step 2 — Default renderings (`strongs_lang_renderings`)

Provide the default target word for each Greek Strong's number used as a noun
(2,369 of them). Generate a reviewable bootstrap artifact first with
`gen_default_renderings.py`, then review and import/apply it into
`strongs_lang_renderings`. This is the fallback used wherever no sense override
applies.

### Step 3 — The 16 disambiguation senses (`sense_renderings`)

Open `senses_worksheet.csv`. Each row is a sense with its Greek lemma, an
example verse, the English word, and the **default target word (which is *wrong*
when the sense applies)**. Fill your language's column, verifying against a
trusted edition in your language (for zh: CUV; for es: RVR1960; etc.). Then:

```
python3 import_sense_renderings.py senses_worksheet.csv --lang L --column "L(FILL)"
```

This resolves all ~1,060 contextual positions automatically. **16 decisions →
1,060 verses correct.** (Sense `GINOMAI.BECOME` equals the default, so it may be
left blank — it falls back correctly.)

### Step 4 — Check readiness

```
python3 language_readiness.py --lang L
```

Close every `GAP` it reports. When it says `READY ✓`, proceed.

### Step 5 — Translate the verses

Create `GOI_Bible_<LANGUAGE>/` with one file per verse (same filenames as
`GOI_Bible_English/`). Translate **from the Greek** (`One_Directory_TR1550/`),
using `translate_verses.py` or an equivalent harness, with:
- `strongs_lang_renderings` + `sense_renderings` as your controlled vocabulary
  for nouns (query `greek_noun.sqlite3`),
- the English edition as a structural reference (not as the source — see §6),
- one or two **public-domain** references in your language if available, to check sense.

Keep one verse per file, single line. Run `normalize_corpus.py --dir
GOI_Bible_<LANGUAGE>` to canonicalize punctuation.

### Step 6 — Verify coverage

```
python3 verify_coverage.py --lang L --output-dir ../GOI_Bible_<LANGUAGE>
python3 verify_coverage.py --lang L --output-dir ../GOI_Bible_<LANGUAGE> --missing-only
```

Every `MISSING` is a Greek noun whose target word did not appear in your verse —
a probable drop or wrong-sense. Fix the verse, or (if your word is a legitimate
synonym) record it the way English did (see §5).

### Step 7 — Validate and commit

`validate.py` currently gates English coverage only. Use it as a structural/DB
gate, and use `verify_coverage.py --lang L` as your language-specific coverage
gate. Commit in logical batches with clear messages.

---

## 4. The false-friend discipline (this is where quality is won)

The raw machine translation that produced English had a systematic tendency to
render a Greek word by one default gloss regardless of context. Hundreds of real
errors were fixed (see `2026-06-03_gptaudit.md` and the README changelog).
**Expect the same class in your language** and hunt it the same way:

1. **Cross-reference divergence scan.** Use `falsefriend_sweep.py xref`. Where
   trusted PD references in your language agree on a word your draft lacks,
   that's a high-signal candidate. With zero PD references, this method cannot
   run; with one, targeted `strongs --ref-has` checks are still useful; with
   two, `xref` becomes much stronger. (English used GOI vs KJV vs WEBUS.)
2. **Known polysemy traps** — verify each in context, do not trust the default:
   - ἀφίημι = forgive **/ leave / let / allow / forsake**
   - σῴζω = save **/ heal / make well** (healing contexts)
   - παραδίδωμι = deliver / hand over **/ betray** (Judas)
   - παρακαλέω = encourage **/ beg / implore / comfort / exhort**
   - γίνομαι = become **/ happen / be / be born / be made**
   - τιμή = honor **/ price**
   - κύριος = Lord **/ master / sir**; γυνή = wife **/ woman**; ἀνήρ = man **/ husband**
   - πνεῦμα = Spirit **/ spirit / wind / breath**; λόγος = word **/ account / matter / reason**
   - ἐκεῖνος = "that one" → usually just **he / him / that man**
3. The high-polysemy items are already in the **sense layer** — if your
   `sense_renderings` are right, those positions resolve correctly for free.

---

## 5. How to record a legitimate non-default rendering

If at a specific verse the correct word differs from the default **and it is a
real context sense** (not just inflection), add a row to
`verse_rendering_overrides` keyed by `(book_id, chapter, verse, word_pos,
strongs_num)` with `correct_rendering`, a `reference_agreement` note, and — if it
belongs to one of the 16 senses — the `sense_key`. This is exactly how English
recorded θεραπεία→household, λόγος→cause, ἱλαστήριον→propitiation, etc. Keeping
it in the data (not just the text) means the decision is auditable and reusable.

---

## 6. Copyright — protect the unencumbered status

The **goal is a copyright-unencumbered** text. The Greek TR1550 is public domain.
**Only use public-domain references** to check sense (for English: KJV + WEBUS,
both PD). **Never** consult or copy from a *modern copyrighted* translation in
your language (e.g. for es do not use the NVI; for zh do not use copyrighted CCB
editions — CUV is public domain and safe). You cannot infringe a PD work, so
overlap with PD references is fine; overlap with a copyrighted one is not. See
README_GOI.md §5.

---

## 7. Language-type gotchas

- **CJK (zh, ja, th)**: no spaces — the English `\b` matching is meaningless;
  use the CJK matcher. Use the language's standard NFC form. Watch
  Traditional vs Simplified consistency.
- **RTL (he, ar)**: store text in logical order (as typed/read); direction is a
  display concern. Matching works on logical order.
- **Agglutinative (tr, fi, hu)**: a noun's rendering will appear with case/number
  suffixes glued on — a whole-word matcher will under-count. Write a stem matcher.
- **Gendered/cased languages**: the sense layer gives you a *base* word; your
  translation inflects it. The matcher must accept the inflected forms.
- **Proper names**: keep a consistent transliteration policy across the whole
  corpus (a known weak spot — see README checklist). Consider a name table.

---

## 8. Invariants you must not break (the gate)

Run `python3 validate.py` after any change. It enforces:
file count 7957, valid names, single-line non-empty verses, canonical
punctuation/NFC, every verse has a TR1550 source, DB foreign-key integrity,
override positions valid, sense catalog consistency, noun count canonical to raw
TR1550 (count parity + every noun surface physically present in its raw verse),
and English coverage 0 missing. For non-English languages, keep `validate.py`
green and separately require `verify_coverage.py --lang L` to be clean.

---

## 9. Command cheat-sheet

```bash
# what does my language still need?
python3 Greek_Noun_Extraction_NIM/language_readiness.py --lang L

# generate review-first noun defaults
python3 Greek_Noun_Extraction_NIM/gen_default_renderings.py \
        --lang L --language-name "<LANGUAGE>" \
        --out proposed_defaults.csv --sql-out proposed_defaults.sql

# load the filled sense worksheet
python3 Greek_Noun_Extraction_NIM/import_sense_renderings.py \
        Greek_Noun_Extraction_NIM/senses_worksheet.csv --lang L --column "L(FILL)"

# translate a small slice first
python3 Greek_Noun_Extraction_NIM/translate_verses.py \
        --lang L --language-name "<LANGUAGE>" \
        --output-dir GOI_Bible_<LANGUAGE> --book MAT --chapter-start 1 --chapter-end 1 \
        --reference-dir GOI_Bible_English

# canonicalize my output punctuation
python3 normalize_corpus.py --dir GOI_Bible_<LANGUAGE>

# coverage: did every Greek noun reach the text?
python3 Greek_Noun_Extraction_NIM/verify_coverage.py --lang L \
        --output-dir GOI_Bible_<LANGUAGE> [--missing-only]

# integrity gate (run constantly)
python3 validate.py

# false-friend scan (needs PD references for your language)
python3 Greek_Noun_Extraction_NIM/falsefriend_sweep.py xref \
        --draft GOI_Bible_<LANGUAGE> --lang L --refs <pd_ref_dir_1>,<pd_ref_dir_2>

# inspect senses / renderings
sqlite3 Greek_Noun_Extraction_NIM/greek_noun.sqlite3 \
   "SELECT * FROM senses;"
   "SELECT * FROM sense_renderings WHERE lang='L';"
   "SELECT * FROM strongs_lang_renderings WHERE lang='L' LIMIT 20;"
```

When `language_readiness.py` says READY, coverage is high with no unexplained
MISSING, `validate.py` is green, and your false-friend checks are clean when PD
references exist — you have a faithful, verified, copyright-
clean edition built on the same spine as the English reference.
