# Greek TR1550 → Traditional Chinese (繁體中文) — Staged Translation Gameplan

**Purpose:** The English NT (GOI_Bible_English) was a deliberate test run — a language
we know, with two PD reference editions, specifically to shake out every class of error
before tackling other languages. This document is the result: everything we learned,
translated into a staged operational plan for Greek → Traditional Chinese. Hand this to
a fresh AI translator as its primary briefing.

**Target output:** `GOI_Bible_Chinese_Hant/` — 7,957 verse files, same naming as
`GOI_Bible_English/`, Traditional Chinese, one verse per file, single line, UTF-8 NFC.

---

## Part 0 — Copyright Free
The goal is to have a Chinese Translation directly from TR1550 so that there is no copyright restrictions; and so while CUV can be used for reference; remember that the goal is to generate ORIGINAL translations so it's not copyright encumbered.

## Part 1 — Lessons from the English Pass

### 1.1 What worked (inherit unchanged)

| Mechanism | Why it worked | Chinese status |
|---|---|---|
| Sense layer (16 language-neutral senses) | Polysemy decided once, all languages inherit positions | ✓ positions ready; Chinese words need filling |
| Canonical noun count via strongs_nt morphology | Deterministic, reproducible, verifiable | ✓ 28,889 nouns canonical |
| Three-way divergence sweep (draft vs 2 PD refs) | Found ~155 meaning corrections with no word list | ⚠ only 1 PD ref for Chinese (CUV) |
| validate.py standing gate (13 invariants) | Prevents regression after every change | ✓ runs for any language |
| meaning_checks.py negation check | Caught 2TH 3:7 dropped "not" (reversed Paul's meaning) | ⚠ needs Chinese NEG_TARGET override |
| meaning_checks.py numbers check | Confirmed numbers clean; found classifier issues | ⚠ needs Chinese NUM_TARGET override |
| normalize_corpus.py | Canonical punctuation/whitespace/NFC across corpus | ✓ applies to Chinese |

### 1.2 What went wrong — the error catalogue (every class found in English)

These are organized by severity. **Expect all of them in Chinese too**, with Chinese-specific variants.

#### Class A: Systematic false-friends (one Greek word, one wrong default, many verses)

| Strong's | Greek | Wrong default | Correct senses | Scale |
|---|---|---|---|---|
| G863 | ἀφίημι | "forgive" everywhere | **leave / let / allow / forsake** (forgive only for sins/debts) | 28 verses fixed |
| G4982 | σῴζω | "saved" everywhere | **heal / make well** in physical healing contexts | 14 verses fixed |
| G3860 | παραδίδωμι | "deliver" everywhere | **betray** (Judas); hand-over elsewhere | 30 verses fixed |
| G3870 | παρακαλέω | "encourage" everywhere | **beg / implore / comfort / exhort** | 35 verses fixed |
| G1096 | γίνομαι | "happened" everywhere | **became / be made / born / come to pass** | 11 verses fixed |
| G5092 | τιμή | "honor" everywhere | **price / value** in sale contexts | 1 verse fixed |
| G1565 | ἐκεῖνος | "that one" everywhere | **he / him / that man** (mechanical literal) | 20 verses fixed |
| G1807 | ἐξαιρέω | "deliver" everywhere | **pluck out** (eye-plucking context) | 2 verses fixed |
| G4371 | προσφάγιον | "meat" | **anything to eat** | 2 verses fixed |
| μὴ γένοιτο | idiom | "may it never happen" | **"By no means! / Certainly not!"** | 12 verses fixed |

**Total systematic false-friend fixes: ~103 verses** (corpus-wide sweep using falsefriend_sweep.py).

#### Class B: GPT audit findings (single-verse meaning errors requiring deep reading)

- **Clause corruption:** MAT 9:35 "disease...disease" → dropped the sickness/disease contrast pair
- **Dropped negation:** 2TH 3:7 "we behaved disorderly" → should be "we did NOT behave disorderly" (reversed Paul's self-example)
- **Mistranslations:** θεραπεία "healing" → "household" (MAT 24:45, LUK 12:42); συλλαμβάνω "seized" → "conceived" (LUK 1:24); διάβολος "devils" → "slanderers" (1TI 3:11)
- **Over-literal pronouncing:** ἐκεῖνος "that one's" → "his" (2CO 8:9, TIT 3:7, JHN 20:15)

#### Class C: Archaic/register leakage (English-specific, but analogous risk exists in Chinese)

"disannul," "unto," "brethren," "conversation" (= conduct), "beguile," "raiment," "peradventure," "sundry," "divers," "smote," "quickened," "fourscore." These were KJV-isms leaking into the draft. Chinese equivalent: Classical (文言) words leaking into 白話 (vernacular) prose — a real machine-translation failure mode.

### 1.3 What the English pass did NOT verify (open gaps — fix for Chinese)

These were *not* verified systematically in English and must be tackled deliberately in Chinese:

| Gap | Risk | Chinese tool needed |
|---|---|---|
| Verbs | Dropped predicates, tense confusion | `clause_check_nt_en.py` / `clause_check_nt_zh.py` |
| Clause/predicate completeness | Fragments, whole ideas absent | `clause_check_nt_en.py` / `clause_check_nt_zh.py` |
| Proper-noun transliteration consistency | Simon/Simeon, Elias/Elijah inconsistencies | Proper-noun frequency audit (Stage 7) |
| Register consistency | Archaic/classical words mixed with vernacular | Manual + LLM review |
| Adjectives, adverbs, particles | No check at all | Partially caught by the clause-check scripts |

---

## Part 2 — Greek-Side Gotchas (language-independent; all apply to Chinese)

### 2.1 The 16 disambiguation senses — your controlled vocabulary for polysemy

The positions are already marked language-neutrally in `verse_rendering_overrides`. You only
supply the Chinese word for each sense. **Never use the default; always use the sense word at
these positions.**

| sense_key | Strong's | Greek | Default (WRONG at these positions) | Chinese to supply |
|---|---|---|---|---|
| ANER.SPOUSE | G435 | ἀνήρ | 男人 (man) | 丈夫 (husband) |
| ARTOS.COUNTABLE | G740 | ἄρτος | 餅 (bread) | 個餅/餅 (a loaf, countable) |
| BROSIS.CORROSION | G1035 | βρῶσις | 食物 (food) | 鏽蝕/腐蝕 (corrosion/rust) |
| GINOMAI.BECOME | G1096 | γίνομαι | 成了 (became) | *(this = the default; fall through)* |
| GINOMAI.HAPPEN | G1096 | γίνομαι | 成了 (became) | 發生 (happen/occur) |
| GINOMAI.BE_DONE | G1096 | γίνομαι | 成了 (became) | 完成/成就 (be done/accomplished) |
| GYNE.WOMAN | G1135 | γυνή | 妻子 (wife) | 婦人/女人 (woman, not wife) |
| THELO.WILL | G2309 | θέλω | 願意 (want) | 旨意/意願 (will/desire) |
| THEOS.LOWERCASE_GOD | G2316 | θεός | 神 (God) | 假神/神明 (false/pagan god) |
| KYRIOS.HUMAN_MASTER | G2962 | κύριος | 主 (Lord) | 主人 (master/owner) |
| LOGOS.DIVINE_TITLE | G3056 | λόγος | 道/話語 (word) | 道 (the Word, divine title) |
| PNEUMA.UNCLEAN_SPIRIT | G4151 | πνεῦμα | 靈 (Spirit) | 邪靈 (unclean/evil spirit) |
| PNEUMA.HUMAN_SPIRIT | G4151 | πνεῦμα | 靈 (Spirit) | 心靈/人靈 (human spirit) |
| PNEUMA.BREATH | G4151 | πνεῦμα | 靈 (Spirit) | 氣息 (breath of life) |
| PNEUMA.WIND | G4151 | πνεῦμα | 靈 (Spirit) | 風 (wind — JHN 3:8) |
| PNEUMA.DIVINATION_SPIRIT | G4151 | πνεῦμα | 靈 (Spirit) | 占卜的靈 (spirit of divination — ACT 16:16) |

**Fill these 16 in `senses_worksheet.csv` and run `import_sense_renderings.py`. That is the first gating step.**

### 2.2 Known false-friend Strong's — check every occurrence in Chinese

Same patterns that bit English will bite Chinese in Chinese-dressed form:

| Strong's | Greek | Danger pattern |
|---|---|---|
| G863 | ἀφίημι | 離開/讓/允許/離棄 (leave/let/allow/forsake) vs 赦免 (forgive) |
| G4982 | σῴζω | 痊癒/得醫治 (made well) vs 得救 (saved spiritually) in healing contexts |
| G3860 | παραδίδωμι | 出賣/背叛 (betray — Judas) vs 交給/傳遞 (hand over) |
| G3870 | παρακαλέω | 懇求/哀求 (beg/implore) or 安慰 (comfort) vs 鼓勵 (encourage) |
| G1096 | γίνομαι | 造/生/成為/發生/完成 (made/born/become/happen/done) — context-critical |
| G5092 | τιμή | 價格/價錢 (price) vs 尊榮/尊重 (honor) in sale contexts |
| G1565 | ἐκεῖνος | 他/那人 (he/that man) vs 那一個 (that one — over-literal) |

### 2.3 TR1550-specific content and textual policy

- Apply `staging/textual_policy/nt_textual_policy.csv` to Chinese exactly as to
  English: `[]` marks conflicted ancient readings, `{}` marks supplemental
  traditional material, and unbracketed critical overrides such as Romans 12:11
  use the preferred older reading.
- **Johannine Comma (1 Jn 5:7-8):** use the shorter early text in the main
  translation; show the heavenly-witness phrase only as supplemental tradition.
- **Acts 8:37:** translate and retain with `{}`.
- **Mark 16:9-20:** translate all 12 verses and retain with `{}`.
- **Matthew 23:14 / Mark 7:16 / etc.:** TR1550 versification may add verses absent in critical texts.
- **Scribal colophons (2 Cor 13:14, Eph 6:24):** Translate in brackets as the English did.

### 2.4 The μὴ γένοιτο idiom

Occurs 12 times (ROM 3:31, 6:2, 6:15, 7:7, 7:13, 9:14, 11:1, 11:11; 1CO 6:15; GAL 2:17, 3:21; LUK 20:16).
English fixed to "By no means!" Chinese: **絕對不是！** or **斷乎不可！** — strong rhetorical negation, not "may it never happen" / 願不如此.

---

## Part 3 — Chinese-Side Gotchas

### 3.1 Script and encoding

- **Target script: Traditional Chinese (繁體中文).** Not Simplified (簡體). The CUV is Traditional.
- The CUV corpus in this repo has inter-character spaces (起 初 ， 神 創 造 天 地 。) — that is CUV formatting. **Your output should NOT have inter-character spaces** — that is unusual for Chinese prose. Write natural continuous Chinese: 起初，神創造天地。
- NFC normalization applies (normalize_corpus.py handles this).
- CJKMatcher does substring matching (no word boundaries, no inflection needed — already built and tested).

### 3.2 Grammar divergences from Greek (structural)

**No grammatical gender.** Greek gender (masculine/feminine/neuter) drives English pronoun choice but simply doesn't exist in Chinese. You're free of this — but the sense layer still distinguishes husband/man and wife/woman semantically.

**No verb inflection.** Greek has rich verb morphology (aorist, perfect, imperfect, present, subjunctive, optative). Chinese has none. Tense and aspect are conveyed by time expressions and aspect particles (了, 過, 著). Machine translation tends to over-use 了 (completion marker) — use it where natural, not mechanically on every past-tense Greek aorist.

**Measure words (量詞) are mandatory.** Counting nouns in Chinese requires a classifier between number and noun:
- 一個人 (one-CL person) — not 一人 (except in classical/poetic register)
- 一條魚 (one-CL fish)
- 一個餅 (one-CL bread/loaf) — ARTOS.COUNTABLE applies here
- 五個餅 (five loaves) and 兩條魚 (two fish) — MAT 14:17
Using the wrong classifier or none at all is an immediate readability failure.

**Topic-comment structure.** Chinese can front-load the topic: 那個病人，他的信心使他痊癒了 (That sick person, his faith made him well). Greek often embeds the topic in case endings. The translation should prefer natural Chinese topic structure over Greek word order.

**Serial verb constructions.** Where Greek uses aorist participle + main verb (having gone, he said), Chinese often chains verbs: 他去了，說 (he went, said). Do not over-translate Greek participles as subordinate clauses — Chinese often naturalizes them as serial verbs.

### 3.3 Theological vocabulary — the highest-stakes decisions

These terms have divided Chinese Christianity and have established CUV conventions. **Always match CUV.** Do not innovate transliterations or theological terms.

| Greek | Standard CUV | Notes / Gotcha |
|---|---|---|
| θεός (G2316) | 神 (shén) | Catholic preference: 上帝 (shàng dì); CUV uses 神; match CUV |
| κύριος (G2962) | 主 (zhǔ) | Divine Lord = 主; human master = 主人 (KYRIOS.HUMAN_MASTER sense) |
| πνεῦμα (G4151) | 靈 / 聖靈 | Full divine title: 聖靈 (Holy Spirit); generic: 靈; wind: 風; breath: 氣息 |
| λόγος (G3056) | 道 (dào) | JHN 1:1 "In the beginning was the Word" = 太初有道 — one of most famous lines in Chinese theology |
| Ἰησοῦς | 耶穌 (Yēsū) | Standard CUV; never deviate |
| Χριστός | 基督 (Jīdū) | Standard CUV transliteration |
| ἅγιος (Holy) | 聖 (shèng) | Holy Spirit = 聖靈; holy ones/saints = 聖徒; holy = 聖潔 |
| εὐαγγέλιον | 福音 (fúyīn) | Gospel — standard |
| ἁμαρτία | 罪 (zuì) | Sin — standard; sin offering = 贖罪祭 |
| δικαιοσύνη | 義/公義 (yì/gōngyì) | Righteousness — 義 simple; 公義 emphasizes justice |
| πίστις | 信心 (xìnxīn) | Faith — CUV uses 信心; 信仰 (religion/faith system) is different |
| ἀγάπη | 愛 (ài) | Love — 慈愛 for God's love (lovingkindness); 愛 for general |
| ἐκκλησία | 教會 (jiàohuì) | Church/assembly — 教會 in CUV; not 聚會 (gathering) or 集會 |
| ἀπόστολος | 使徒 (shǐtú) | Apostle — standard |
| προφήτης | 先知 (xiānzhī) | Prophet — standard |

### 3.4 Proper-name transliteration — match CUV, never invent

A proper-noun audit is **mandatory** (Stage 7). The following are the most-used names in the NT; any deviation from CUV standard is an error:

| Name | CUV Standard |
|---|---|
| Jesus | 耶穌 |
| Christ | 基督 |
| God | 神 |
| Lord | 主 |
| Holy Spirit | 聖靈 |
| Abraham | 亞伯拉罕 |
| David | 大衛 |
| Moses | 摩西 |
| Isaiah / Elijah | 以賽亞 / 以利亞 |
| Peter | 彼得 |
| John | 約翰 |
| Paul | 保羅 |
| James | 雅各 |
| Mary | 馬利亞 |
| Joseph | 約瑟 |
| Jerusalem | 耶路撒冷 |
| Galilee | 加利利 |
| Nazareth | 拿撒勒 |
| Bethlehem | 伯利恆 |
| Jordan (river) | 約旦河 |
| Judea | 猶太 |
| Israel | 以色列 |
| Pharisee | 法利賽人 |
| Sadducee | 撒都該人 |
| Synagogue | 會堂 |
| Sanhedrin | 公會 |

### 3.5 Sentence-final particles and discourse markers

Chinese uses sentence-final particles to convey mood. Machine translation over-applies them — this is a major naturalness failure mode:

| Particle | Use | Greek approximate |
|---|---|---|
| 了 (le) | Completion / change of state | Often applied to aorist — use sparingly |
| 吧 (ba) | Mild assertion / suggestion | May suit certain rhetorical questions |
| 啊 / 呀 (a/ya) | Exclamation | Woe-sayings, strong emotion |
| 嗎 (ma) | Yes-no question | Greek interrogative particle μή (with negative expectation) or no explicit marker |
| 呢 (ne) | Continuation / soft question | Use sparingly |

Rule: if a particle is not present in the CUV for that verse, it probably is not needed.

### 3.6 Negation patterns in Chinese

`meaning_checks.py` needs a Chinese override for the `--neg-target` flag:

| Chinese | Pinyin | Use |
|---|---|---|
| 不 (bù) | bù | Present/future negation, habitual, stative |
| 沒有 (méiyǒu) | méiyǒu | Past action or non-existence of something |
| 別 (bié) | bié | Imperative negative ("don't") |
| 不要 (bùyào) | bùyào | Imperative negative (stronger) |
| 非 (fēi) | fēi | Formal/classical negation |
| 無 (wú) | wú | Absence/non-existence (classical) |
| 未 (wèi) | wèi | Not yet |
| 莫 (mò) | mò | Classical: do not (poetic/proverbial) |

**Greek negation mapping:**
- οὐ / οὐκ / οὐχ + indicative → 不 (present/habitual) or 沒有 (past)
- μή + imperative/subjunctive → 別 / 不要
- μή + negated question expecting "no" → 難道…不 (rhetorical question framing)
- οὐδέ / μηδέ (neither/not even) → 也不 / 也沒有

### 3.7 Numbers in Chinese — important structural difference

Chinese uses 萬 (wàn = 10,000) where English uses thousand-multiples. This is a readability and accuracy critical gotcha:

| Quantity | English | Chinese |
|---|---|---|
| 1,000 | one thousand | 一千 (qiān) |
| 10,000 | ten thousand | 一萬 (wàn) — NOT 十千 |
| 5,000 | five thousand | 五千 (wǔ qiān) |
| 4,000 | four thousand | 四千 (sì qiān) |
| Greek μυριάς (myriad = 10,000) | ten thousand / myriad | 一萬 |
| 10,000 × 10,000 (REV 5:11) | ten thousand times ten thousand | 億萬 or 千千萬萬 |

`meaning_checks.py` NUM_TARGET for Chinese:
`一|二|兩|三|四|五|六|七|八|九|十|百|千|萬|億`

### 3.8 Register and style — the 文言 leakage risk

CUV itself is a slightly formal translation (early 20th century); some of its vocabulary has 文言 (Classical Chinese) flavour. Machine translation can amplify this. The output should be readable, dignified Modern Chinese (白話) — matching CUV's register, not going more classical. Signals of a style problem:
- 之 (zhī) used as possessive instead of 的 (de) everywhere
- 其 (qí, classical "his/its") instead of 他的 / 它的
- 乃 (nǎi, "then/thus") instead of 就 / 然後
- 故 (gù, "therefore") instead of 所以 / 因此
- Any chengyu (四字成語) that wasn't in the Greek

---

## Part 4 — Staged Execution Plan

### Stage 0: Prerequisite audit (no verse translation yet)

**Goal:** Confirm infrastructure is ready; fix any gaps before touching translation.

```bash
# 1. Check current readiness (will show senses=0/16 GAP)
python3 Bible_Noun_Extraction/language_readiness.py --lang zh

# 2. Audit a sample of zh defaults
sqlite3 Bible_Noun_Extraction/bible_noun.sqlite3 \
  "SELECT slr.strongs_num, sr.lemma, sr.english, slr.rendering
   FROM strongs_lang_renderings slr
   JOIN strongs_renderings sr ON sr.strongs_num=slr.strongs_num
   WHERE slr.lang='zh' ORDER BY RANDOM() LIMIT 50"

# 3. Find the ~195 Strong's with no zh default
sqlite3 Bible_Noun_Extraction/bible_noun.sqlite3 \
  "SELECT DISTINCT snt.strongs_num, sr.lemma, sr.english
   FROM strongs_nt snt
   JOIN strongs_renderings sr ON sr.strongs_num=snt.strongs_num
   WHERE snt.morph LIKE 'N-%' AND snt.in_tr1550=1
     AND NOT EXISTS (SELECT 1 FROM strongs_lang_renderings slr
                     WHERE slr.strongs_num=snt.strongs_num AND slr.lang='zh')
   ORDER BY snt.strongs_num"
```

**Done when:** language_readiness.py shows defaults complete (step 2 of 4 = OK).

### Stage 1: Fill the 16 disambiguation senses

**Goal:** `sense_renderings` lang='zh' has all 16 rows, validated against CUV.

1. Open `Bible_Noun_Extraction/senses_worksheet.csv`
2. For each sense, look up the example verse in `Chinese_Bible_CUV/One_Directory_CUV/`
3. Fill `chinese(FILL)` using the guidance in Part 2 §2.1 above
4. Fill `chinese_source_ref` with the CUV verse reference confirming the choice
5. Import:
```bash
python3 Bible_Noun_Extraction/import_sense_renderings.py \
    Bible_Noun_Extraction/senses_worksheet.csv \
    --lang zh --column "chinese(FILL)" --confirmed
```
6. Re-check:
```bash
python3 Bible_Noun_Extraction/language_readiness.py --lang zh
```

**Done when:** `language_readiness.py --lang zh` reports `READY ✓`

### Stage 2: Pilot translation — Philemon (25 verses)

**Goal:** Validate the translation pipeline on a single short epistle before scaling.

```bash
python3 Bible_Noun_Extraction/translate_verses.py \
    --lang zh --language-name "Traditional Chinese" \
    --output-dir GOI_Bible_Chinese --book PHM \
    --reference-dir Chinese_Bible_CUV/One_Directory_CUV
python3 normalize_corpus.py --dir GOI_Bible_Chinese
python3 Bible_Noun_Extraction/verify_coverage.py --lang zh \
    --output-dir GOI_Bible_Chinese --missing-only
```

Manually compare 5 verses against CUV. Check:
- Are proper names matching CUV (保羅, 耶穌基督)?
- Are 主 vs 主人 correctly differentiated?
- Is the text natural 白話 Chinese (no 文言 leakage)?
- Are numbers correct (千/萬)?

**Done when:** Coverage 0 missing; 5 spot-checks against CUV look correct; no systematic pattern failure.

### Stage 3: Full NT translation (7,957 verses)

```bash
python3 Bible_Noun_Extraction/translate_verses.py \
    --lang zh --language-name "Traditional Chinese" \
    --output-dir GOI_Bible_Chinese \
    --reference-dir Chinese_Bible_CUV/One_Directory_CUV
python3 normalize_corpus.py --dir GOI_Bible_Chinese
```

**Done when:** 7,957 files exist, validate.py structural checks pass (file count, naming, single-line, NFC, canonical punct).

### Stage 4: Noun coverage verification

```bash
python3 Bible_Noun_Extraction/verify_coverage.py \
    --lang zh --output-dir GOI_Bible_Chinese
python3 Bible_Noun_Extraction/verify_coverage.py \
    --lang zh --output-dir GOI_Bible_Chinese --missing-only
```

Chase every MISSING:
- Is the Chinese word there but the CJKMatcher missed it? → Add acceptable form to CJKMatcher
- Is the word genuinely absent? → Fix the verse
- Is it a legitimate synonym/paraphrase? → Add `verse_rendering_override` for that position

**Done when:** 0 MISSING. (English achieved this.)

### Stage 5: False-friend sweep (Chinese)

```bash
# Cross-reference divergence (CUV as single PD reference — less powerful than 2 refs)
python3 Bible_Noun_Extraction/falsefriend_sweep.py xref \
    --draft GOI_Bible_Chinese \
    --lang zh \
    --refs Chinese_Bible_CUV/One_Directory_CUV

# For each systematic hit, validate per-Strong's
# Example: check G863 ἀφίημι — if zh draft uses 赦免 where CUV says 離開
python3 Bible_Noun_Extraction/falsefriend_sweep.py strongs \
    --draft GOI_Bible_Chinese \
    --strongs 863 \
    --suspect '赦免' \
    --ref-has '離開|讓|允許|離棄' \
    --refs Chinese_Bible_CUV/One_Directory_CUV
```

Also run targeted checks on the known dangerous theological list:
- G863, G4982, G3860, G3870, G1096, G2962, G1135, G4151, G3056, G5092, G1565

**Note:** With only one PD reference (CUV), this sweep is less powerful than the English pass (which had KJV + WEBUS). Some errors will escape it. The LLM clause_check (Stage 8) and the proper-noun audit (Stage 7) compensate.

**Done when:** Top 20 systematic divergences reviewed and addressed (or confirmed benign).

### Stage 6: Negation + number integrity

Add Chinese overrides to meaning_checks.py (or use the CLI flags if added):

```bash
# Negation — needs Chinese negation pattern
python3 Bible_Noun_Extraction/meaning_checks.py negation \
    --draft GOI_Bible_Chinese
# (Add --neg-target '不|沒有|別|不要|非|無|未|莫' flag or override in script)

# Numbers — needs Chinese number pattern
python3 Bible_Noun_Extraction/meaning_checks.py numbers \
    --draft GOI_Bible_Chinese
# (Add --num-target '一|二|兩|三|四|五|六|七|八|九|十|百|千|萬|億' flag or override)
```

**Done when:** All flagged verses triaged (genuine errors fixed; false positives documented).

### Stage 7: Proper-noun consistency audit

Build a proper-noun frequency table and compare against CUV standards:

```bash
# Extract all Chinese proper names from the translation
python3 - <<'PY'
import pathlib, re, collections
GOI=pathlib.Path('GOI_Bible_Chinese'); counts=collections.Counter()
for f in GOI.glob('*.txt'):
    text=f.read_text(encoding='utf-8')
    # rough: any sequence of 2-5 CJK chars that might be a name — human review needed
    for m in re.finditer(r'[耶基彼約保雅亞伯大摩以][^\s，。；：！？]{1,4}', text):
        counts[m.group()]+=1
for name,n in counts.most_common(100): print(f'{n:5d}  {name}')
PY
```

Cross-reference the top names against the CUV table in §3.4 above. Any divergence from CUV = fix.

**Done when:** Top 30 proper names confirmed matching CUV standards.

### Stage 8: Clause completeness — LLM pass

```bash
# Pilot on one book to calibrate false-positive rate
python3 Bible_Noun_Extraction/clause_check_nt_zh.py \
    --draft GOI_Bible_Chinese --book PHM
# Review: how many flags are genuine vs false positive?
# If false-positive rate is acceptable, run full NT
python3 Bible_Noun_Extraction/clause_check_nt_zh.py \
    --draft GOI_Bible_Chinese --resume
# Review flagged list
python3 Bible_Noun_Extraction/clause_check_nt_zh.py \
    --draft GOI_Bible_Chinese --missing-only
```

For each FLAG: compare against CUV; fix if genuine; document if benign.

**Done when:** Flagged list reviewed; genuine drops fixed.

---

## Part 5 — Quality criteria (pass/fail per stage)

| Stage | Pass criteria |
|---|---|
| 0 | `language_readiness.py` defaults=OK; ~195 missing defaults filled |
| 1 | `language_readiness.py --lang zh` reports `READY ✓` (16/16 senses, all resolve) |
| 2 | Pilot coverage 0 missing; 5 spot-checks vs CUV pass |
| 3 | 7,957 files; `validate.py` 13/13 structural checks pass |
| 4 | `verify_coverage.py` 0 MISSING |
| 5 | Top systematic xref divergences reviewed; per-Strong's sweeps done for the 11 known false-friends |
| 6 | Negation: all flags triaged. Numbers: all flags triaged |
| 7 | Top 30 proper names match CUV standard |
| 8 | clause_check flagged list reviewed; genuine drops fixed |

**Final gate:** `python3 validate.py` → 13/13.

---

## Part 6 — English vs Chinese: key differences at a glance

| Dimension | English (done) | Chinese (this pass) |
|---|---|---|
| Noun matching | word-boundary + rich inflection map | CJK substring, no inflection (already built) |
| PD references for sweep | KJV + WEBUS (2) | CUV only (1) — expect weaker false-friend detection |
| Measure words | none | Mandatory (一個/一條/一隻/一塊 etc.) |
| Core theological terms | settled by user (propitiation/wives) | New decisions required (神 vs 上帝; 道) — match CUV |
| Proper names | Anglicized (David, Peter, Paul) | Must match CUV transliterations (大衛/彼得/保羅) |
| Negation check pattern | not/no/never/nor/etc. | 不/沒有/別/非/無/未/莫 |
| Number check pattern | two/three/hundred/thousand | 二/三/百/千/萬 (萬=10,000 not 1,000!) |
| Verb inflection in output | past/present/gerund etc. | None — tense by context/時間詞/了 |
| Article system | the/a/an | None — but classifiers carry some semantic weight |
| Register risk | KJV archaisms | 文言 (classical) vs 白話 (vernacular) leakage |
| Sentence particles | none | 了/吧/啊/嗎 — use sparingly, match CUV naturalism |
| Proper-noun audit | not done | Required (Stage 7) |

---

## Part 7 — Tooling cheat-sheet

All commands run from the repo root `/home/albert/projects/bible/`:

```bash
# Stage 0: readiness
python3 Bible_Noun_Extraction/language_readiness.py --lang zh

# Stage 1: import senses (after filling senses_worksheet.csv)
python3 Bible_Noun_Extraction/import_sense_renderings.py \
    Bible_Noun_Extraction/senses_worksheet.csv --lang zh --column "chinese(FILL)"

# Stage 2-3: translate
python3 Bible_Noun_Extraction/translate_verses.py \
    --lang zh --language-name "Traditional Chinese" \
    --output-dir GOI_Bible_Chinese \
    --reference-dir Chinese_Bible_CUV/One_Directory_CUV [--book PHM]

# Normalize
python3 normalize_corpus.py --dir GOI_Bible_Chinese

# Stage 4: noun coverage
python3 Bible_Noun_Extraction/verify_coverage.py \
    --lang zh --output-dir GOI_Bible_Chinese [--missing-only]

# Stage 5: false-friend sweep
python3 Bible_Noun_Extraction/falsefriend_sweep.py xref \
    --draft GOI_Bible_Chinese --lang zh \
    --refs Chinese_Bible_CUV/One_Directory_CUV
python3 Bible_Noun_Extraction/falsefriend_sweep.py strongs \
    --draft GOI_Bible_Chinese --strongs <G_NUMBER> \
    --suspect '<zh_suspect_pattern>' --ref-has '<zh_correct_pattern>' \
    --refs Chinese_Bible_CUV/One_Directory_CUV

# Stage 6: negation + numbers
python3 Bible_Noun_Extraction/meaning_checks.py negation --draft GOI_Bible_Chinese
python3 Bible_Noun_Extraction/meaning_checks.py numbers  --draft GOI_Bible_Chinese

# Stage 8: clause check (fill API_KEY / OPENAI_API_KEY first)
python3 Bible_Noun_Extraction/clause_check_nt_zh.py --draft GOI_Bible_Chinese [--resume]
python3 Bible_Noun_Extraction/clause_check_nt_zh.py --draft GOI_Bible_Chinese --missing-only
python3 Bible_Noun_Extraction/triage_clause_flags_nt_zh.py

# Integrity gate (run constantly)
python3 validate.py

# DB inspection
sqlite3 Bible_Noun_Extraction/bible_noun.sqlite3 "SELECT * FROM senses;"
sqlite3 Bible_Noun_Extraction/bible_noun.sqlite3 "SELECT * FROM sense_renderings WHERE lang='zh';"
sqlite3 Bible_Noun_Extraction/bible_noun.sqlite3 \
    "SELECT * FROM strongs_lang_renderings WHERE lang='zh' LIMIT 20;"
```
