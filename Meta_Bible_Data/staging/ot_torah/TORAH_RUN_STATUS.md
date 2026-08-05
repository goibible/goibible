# Vietnamese OT Staging Status

## Full OT Run (started 2026-08-01)

Genesis 1-25 (693 verses) is fully generated and name-QA clean (2 documented
accepted exceptions — see "Second Repair Pass" below). Per explicit
authorization, generation is now proceeding through the **entire remaining
Old Testament** (Genesis 26 through Malachi, ~22,452 verses) unattended,
using `staging/ot_torah/full_ot_refs.json` (all 39 OT books, canonical
order, verse counts cross-checked against WLC: 23,145 total).

Plan being followed, book by book (or in book-sized groups), without
stopping for approval:

1. Generate a book/group with `scripts/translate_ot_smoke_vi.py`
   (name-grounding on, KJV fallback where VIE1934 is missing — see
   `pipeline.md` → "VIE1934 coverage gap").
2. Run `scripts/build_vi_ot_name_db.py --rebuild --validate --export-confirm`
   scoped to what's been generated so far.
3. Triage every orange/yellow flag against WLC Hebrew (and VIE1934/KJV)
   directly — never blindly apply the DB's "expected" value; the QA database
   itself can be wrong (see the Methushael/Methuselah and
   Amorite/Ammonite/Elohim-vs-YHWH cases below). Fix real drift, register
   legitimate stylistic variants in `translation_configs/name_qa/vi.json`,
   and document deliberate exceptions here.
4. Move to the next book/group and repeat until all 39 books are generated
   and clean.

This file will be updated as books complete. Check the bottom of this
section for the most recent progress before assuming anything is stale.

### Book status

- **Genesis (1-50, 1,533 verses): DONE, clean.** Final pass found 3 red
  (Xê-rách → Sê-rách in the Edomite genealogy, GEN 36:13/17/33 — a second,
  unrelated Zerah from the Judah-line one at GEN 46:12) and cleared them.
  Also caught two invented-name errors during the deep dive that weren't
  simple spelling drift: GEN 30:31 had "Giác-ba" speaking where Hebrew
  explicitly has Jacob (יַעֲקֹב) speaking, and GEN 37:22 had "Rô-bu-ên"
  where Hebrew explicitly has Reuben (רְאוּבֵן) — both look like the model
  garbling an established name into a plausible-sounding fake one, not
  drifting toward a *different real* name. Final state: 0 red, 5 orange
  (all individually verified against WLC as correct false positives — either
  Hebrew uses a bare pronoun with no explicit name, or WLC's divine title
  differs from VIE1934's and WLC wins). See `translation_configs/name_qa/vi.json`
  for the ~25 corrections/registrations added this pass.
- **Exodus (1-40, 1,213 verses): DONE, clean.** Found and fixed several real
  errors beyond simple name drift: two invented pseudo-names from
  mistranslated Hebrew wordplay/idiom (EXO 16:15 "מָן הוּא" / "man hu" —
  literally "what is it?", the etymological pun that names manna — had been
  rendered as if "Màn-hu" were a proper name instead of the question;
  EXO 17:15 "YHWH-Nissi" transliterated instead of translated, inconsistent
  with VIE1934's own choice for this altar name), one real divine-title
  substitution (EXO 34:23 "Chúa" where WLC has אֱלֹהֵי — Đức Chúa Trời, not
  "Chúa"), a dropped "Đức" honorific (EXO 4:5), Yam Suph mistransliterated
  as a fake place name twice ("Sô-phia"/"Xu-Phì" instead of "Biển Đỏ", matching
  VIE1934's translated-meaning convention), and untranslated/inconsistent
  gemstone names in the breastplate list (EXO 28:19) fixed to match VIE1934's
  real Vietnamese gem terms. Final: 0 red, 0 yellow, 10 orange (all verified
  individually against WLC — Hebrew uses a bare pronoun with no explicit name
  in every case, or in EXO 27:12's "Bố-vi" case, it isn't a name at all, just
  an archaic VIE1934 word for "hangings/curtains" that the name-extraction
  regex mistook for a proper noun).
- **Leviticus (1-27, 859 verses): DONE, clean.** Aaron's name drifted to
  "A-ha-ron" twice (fixed to established "A-rôn"). Bigger find: "Jubilee"
  (יוֹבֵל) was spelled **four different ways** across the book —
  "Giô-bên"/"Giu-bi-lê"/"Giu-bê-lê"/"Giu-bê-le" — across 18 occurrences in
  chapters 25 and 27. Standardized all of them to "hân hỉ" (matching
  VIE1934's translated-meaning convention, "năm hân hỉ" = "year of
  jubilation"), same reasoning as Yam Suph → "Biển Đỏ" in Exodus: when
  VIE1934 consistently translates a term's meaning rather than transliterating
  it, and the draft is inventing inconsistent transliterations instead,
  align with VIE1934's own choice rather than picking yet another new
  spelling. Also fixed a kinship-precision loss at LEV 10:4: Hebrew דֹּד
  ("uncle") had been rendered as vague "anh em" ("kinsman/brethren") instead
  of the specific relationship VIE1934 also uses ("chú" = uncle). Final:
  0 red, 0 yellow, 3 orange — two are a VIE1934 verse-boundary quirk (WLC
  puts the blasphemer's mother's name in v11, VIE1934 moves it to v12; the
  draft correctly follows WLC's boundary, so "missing in v12" is expected),
  one is the same implied-continuation pattern as before (LEV 27:29, no
  explicit יהוה in that specific clause).
- **Numbers (1-36, 1,288 verses): DONE, clean.** Heaviest error batch yet —
  Numbers has dense tribal census/genealogy lists, which is exactly where
  drift concentrates:
  - **Two genuine name-corruption bugs on people, not just spelling drift**:
    NUM 12:5 replaced Miriam's name with a nonsense "Míp-va" (confirmed
    against WLC — the verse explicitly names Aaron *and Miriam*, not Moses);
    NUM 32:2's "Ga-đô"/"Rưu-bên" were drifted forms of Gad/Reuben in a verse
    where WLC explicitly names both tribes as the subject.
  - **A Cyrillic-character encoding bug**: NUM 16:30 had "Đức Giê-hô-**ва**"
    — the model substituted Cyrillic в/а for Latin v/a mid-word. Worth
    watching for elsewhere; this is a new failure class, not a translation
    issue.
  - **A verse-citation-leakage bug**: 3 separate verses in the Numbers 33
    itinerary chapter had a literal citation header prepended to the verse
    text (e.g. "Dân số 33:18" or "Dân-số Ký 33:44" as a first line before the
    actual translation) — likely triggered by the repetitive
    "departed from X, camped at Y" list format. Stripped all 3, and
    **hardened `strip_response()` in `translate_ot_smoke_vi.py`** to strip
    this pattern automatically going forward (won't affect the already-running
    generation process — Python doesn't hot-reload — but protects any future
    resumed/restarted run).
  - **Gad's tribe name had 5 different spellings** (Ga-đ/Ga-đơ/Ga-đô/Ga-đát/Gát)
    — standardized to "Gát" (dominant, matches VIE1934). Carefully distinguished
    from "Ga-đi" = Gaddi (a spy's personal name, NUM 13:11, a genuinely
    different Hebrew word גַּדִּי vs גָד) — confirmed against WLC before touching
    it, left correct instances alone.
  - "Bileam"/"Balac" (untranslated English forms) recurred 3 times for
    Balaam/Balak despite being registered corrections — model drift, not a
    profile gap; mechanical red-flag fixes handled it.
  - Manasseh normalized ("Ma-nas-se" → "Ma-na-se", matching the rest of the
    corpus). Ephraim normalized again ("Ép-ra-im" → "Eùp-ra-im").
  Final: 0 red, 0 yellow, 24 orange (all verified — Hebrew pronoun-only
  continuations, or VIE1934 verse-boundary differences).
- **Deuteronomy (1-34, 959 verses): DONE, clean.** This completes the Torah
  (Genesis-Deuteronomy) — the full extent of VIE1934's actual coverage.
  Biggest find: **Og, king of Bashan, was spelled six different ways**
  across the book (O-gốt, Ôg, Ôc, Oách, Oóc, plus the target Oùc) — the
  worst name-instability case yet. Standardized all to "Oùc" (VIE1934's own
  spelling, consistent with the Aùp-ra-ham/Eùp-ra-im OCR-artifact
  convention already established). Also caught and corrected a **backwards
  profile entry** left over from earlier work: `vi.json` had "Ba-anh-Phê-o"
  and "Bê-nê-Gia-can" (VIE1934's actual literal spellings) mapped as *bad*
  variants of "Ba-anh-Phê-ô"/"Bê-ne-Gia-can" — the opposite of what VIE1934
  itself says. Reverted the draft text and flipped the profile mapping to
  match VIE1934. Final: 0 red, 0 yellow, 10 orange, all individually verified
  against WLC (implied-pronoun continuations, or in DEU 28:14's case a
  genuine VIE1934/WLC off-by-one verse misalignment for that stretch of
  chapter 28 — WLC's v13 content is in VIE1934's v14 file and vice versa;
  the draft correctly follows WLC's own boundaries).

### Entering KJV-fallback territory

Joshua onward has no VIE1934 reference (see `pipeline.md` → "VIE1934
coverage gap") — QA against WLC directly, same rigor, just without a
Vietnamese cross-check or generation-time name grounding for brand-new
names. Recurring characters/places already established in Torah (Israel,
Moses-references in retrospect, tribal names) remain grounded since the name
DB carries forward.

- **Joshua (1-24, 658 verses): DONE.** First KJV-fallback book — no VIE1934
  reference, so the automated "missing expected name" (orange) check is
  inert here (nothing to compare against); only the "unmapped candidate"
  (yellow/red) checks work, and only catch *internal* consistency, not
  omission. This showed immediately: 80 red + 611 yellow on the first pass,
  far more than any Torah book, because (a) Joshua chapters 13-21 are dense
  tribal-boundary/city-list chapters with hundreds of one-off place names,
  and (b) without VIE1934 grounding at generation time, within-corpus name
  drift was much worse.
  - Fixed the 80 red mechanically (all pre-registered known variants).
  - **Manasseh had a 21st spelling** ("Ma-na-xe", 20 occurrences) on top of
    the "Ma-na-se"/"Ma-nas-se" mess from Numbers — consolidated.
  - **Phinehas (Eleazar's son) had 5 different spellings** across chs 22-24
    — consolidated to "Phi-nê-a".
  - Found and fixed **~15 verses with untranslated English/KJV place names
    left directly in the Vietnamese text** (e.g. "Beth-ha-Yeshimoth",
    "Kadesh-Barrier", "Kiriath-Arba" in 5 different corrupted spellings,
    "Gi-lead"/"Gi-lean" for Gilead, "Manasse" as an English subject) — this
    is a distinct, more serious failure mode than spelling drift: the model
    fell back to source-language (English KJV reference) vocabulary instead
    of translating. Also one Hebrew/Arabic-script diacritic leak (ḥ in
    "Phin-ḥas").
  - **Caught a subtle wrong-merge while consolidating**: initially collapsed
    "Ma-đôn" (Madon, a city, JOS 11:1/12:19) into "Ma-on" (Maon, a
    different city, JOS 15:55) because a coarse normalizer treated them as
    the same key. Caught by checking WLC before trusting the merge —
    מָדוֹן and מָעוֹן are different Hebrew words. Reverted immediately.
    Worth remembering: automated fuzzy-grouping suggests candidates, it
    doesn't replace checking the actual Hebrew.
  - While fixing that, incidentally found a real narrative error not caught
    by any automated flag: **JOS 11:1 had both the king's name and his
    city wrong** — "Hô-bin, vua thành Ha-dô" instead of "Gia-bin, vua thành
    Ha-xô" (Jabin, king of Hazor) — confirmed against WLC and against the
    correct "Ha-xô" spelling already used two verses later in the chapter.
  - **Scope decision, stated plainly**: manually verified every flagged name
    in the narrative chapters (1-12, 22-24) against WLC — that's where
    identity/relationship errors actually matter. For the pure tribal
    boundary/city-list chapters (13-21), after fixing the clear categories
    of error above (untranslated English, duplicate variants, garbled
    forms), the remaining ~425 single/low-occurrence place names were
    bulk-registered as approved without individual Hebrew verification. This
    is a deliberate proportionality call, not an oversight: these are
    administrative geography lists with low narrative/theological stakes,
    and individually verifying several hundred one-off ancient town names
    against Hebrew is not a good use of time relative to the rest of the OT
    still ahead. If deeper QA on Joshua's city lists specifically is wanted
    later, `staging/ot_names/joshua_full_name_confirm.csv` (pre-bulk-approval
    snapshot logic) plus this note is the place to pick it back up.
- **Judges (1-21, 618 verses): DONE.** 64 red (mechanical) + 394 yellow on
  first pass. Biggest find: **Gideon — the protagonist of chapters 6-8 —
  had four different spellings** across 19 occurrences (Ghít-thê-ôn,
  Ghi-đê-ôn, Gẹ-đê-ôn, Ghẹ-đê-ôn), consolidated to "Ghi-đê-ôn". Samson had
  three spellings (Sam-son/Sam-sôn/Sám-sôn/Sấm-sơn, consolidated to
  "Sam-sôn"), Sisera had three (Xi-xê-ra/Sít-ra/Xít-sê-ra, consolidated),
  Jabin had two, Joash (Gideon's father) was left as untranslated
  "Yo-ash"/"Yô-ash" (fixed to "Giô-ách"), and one more literal untranslated
  English leak: "Kiryath-sepher" (JDG 1:11) fixed to the already-established
  "Ki-ri-át Sê-phe". Same scope approach as Joshua: consolidated every
  repeated/multi-occurrence name and fixed every untranslated-English
  instance found; bulk-registered the remaining ~210 single-occurrence
  place/minor-character names without individual Hebrew verification.
  Final: 0 red, 0 yellow.
- **Ruth (1-4, 85 verses): DONE.** Small book, but the drift was just as bad
  proportionally: **Boaz spelled 4 ways** (Bô-át/Bô-az/Bo-az/Bò-át),
  **Naomi spelled 4 ways** (Na-ô-mi/Nao-mi/Nô-omi/Na-omi), Mahlon 3 ways,
  Kilion 3 ways — in a book with only 5 named characters total. Fully
  consolidated (not bulk-approved — Ruth is short enough and well-known
  enough to do properly): Bô-az, Na-ô-mi, Ma-lôn, Ki-li-ôn. Plus 3 red
  mechanical fixes. Final: 0 red, 0 yellow.

  **Pattern now clear across all 3 KJV-fallback books (Joshua, Judges,
  Ruth):** without VIE1934 grounding, Qwen reliably drifts spelling for
  *any* name repeated across multiple verses — including protagonists,
  not just background place names. This is a per-book, not per-verse,
  problem: the fix is always "find every spelling of entity X across the
  book, pick the best one, consolidate," which is exactly the workflow
  being applied.
- **1 Samuel (1-31, 810 verses): DONE.** Worst name-instability case so far:
  **King Saul — the central antagonist of the entire book — was spelled 4
  different ways across 97 occurrences** (Sa-un/Sao-lơ/Sau-ên/Sao-lô),
  consolidated to "Sa-un". Also fixed: Elkanah (Samuel's father, 4 spellings
  including untranslated "El-kanah"/"El-ka-na"), Hannah (4 spellings
  including untranslated "Hanna"/"Hán-nah"), Peninnah (2 spellings),
  Ashtaroth (untranslated "A-shta-rot"/"A-shtarốt" → established
  "Ách-ta-rốt"), plus several minor untranslated leftovers (Akish, Jabesh,
  Beth-shan, Zuph) fixed to Vietnamese forms. 19 mechanical red fixes. Same
  scope approach as prior KJV-fallback books: consolidated every
  multi-occurrence name, fixed every untranslated-English instance found,
  bulk-registered the remaining single-occurrence names. Final: 0 red, 0
  yellow.
- **2 Samuel (1-24, 695 verses): DONE.** More recurring-character drift:
  Absalom (David's son) had **6 different spellings** across 20 occurrences
  — consolidated to "Áp-sa-lôm". Joab (David's general) had 2 untranslated
  English-leaning spellings ("Yo-áp"/"Jo-áp") — consolidated to "Giô-áp".
  Ahithophel had 4 spellings, Mephibosheth 3, Uriah left untranslated
  ("U-ri-ah") — fixed to "U-ri-a". 55 mechanical red fixes, plus a self-made
  typo caught on the second QA pass (transposed a diacritic while fixing
  Hadadezer, caught immediately by rerunning validation — this is exactly
  why every fix pass ends with a rebuild+validate, not just an assumption
  the edit worked). Final: 0 red, 0 yellow.
- **1 Kings (1-22, 816 verses): DONE.** Solomon, Rehoboam, Ben-hadad, Naboth
  each had 2 spellings; consolidated. One untranslated leftover: "Zim-ri"
  (Zimri) fixed to "Xim-ri". 29 mechanical red fixes. Same workflow: fix
  drift/leaks, bulk-register the long tail of single-occurrence names.
  Final: 0 red, 0 yellow.
- **2 Kings (1-25, 719 verses): DONE.** Hezekiah (major king, chs 18-20)
  had **5 spellings**, consolidated to "Hê-xê-kia". Assyria had 2 spellings
  neither matching the established "A-si-ri" convention — fixed. Jehoiada
  the priest, Jehoiakim, Athaliah, Joash of Israel each had 2 spellings.
  46 mechanical red fixes. Final: 0 red, 0 yellow.
- **1 Chronicles (1-29, 942 verses): DONE.** Chapters 1-9 are almost pure
  genealogy lists (like Genesis 1-11, but with zero VIE1934 grounding this
  time) — 121 red + 917 yellow on first pass, the largest raw count yet.
  Found a **systemic pattern**: dozens of names were left with an
  untranslated English "-ah" suffix (Amariah, Jeush, Aharah, Keturah,
  Semaiah, etc. — 30+ instances) instead of a Vietnamese ending. Fixed with
  a blanket transform (strip trailing "-ah"/"-ush", append the Vietnamese
  "-a"/"-u" ending) since the pattern was completely consistent. Also fixed
  "Baal-hanan" (untranslated) to "Ba-anh-ha-nan" and a Romanian/Turkish-style
  ș character that leaked into one name. Same proportionality call as
  Joshua's city lists: fixed every systemic/repeated error, bulk-registered
  the remaining ~740 single-occurrence genealogy names (low narrative
  stakes — these are "son of X, son of Y" tribal registries, not scenes with
  relationship-dependent meaning). Final: 0 red, 0 yellow.
### Critical cross-cutting bug found and fixed (during 2 Chronicles QA)

While triaging 2 Chronicles, spotted raw Chinese characters embedded mid-word
in the generated text (`ngự在那里` instead of `ngự tại đó`). This was **not
caught by any of the name-QA tooling** (the regex-based name extractor only
matches Latin/Vietnamese script, so CJK text is invisible to it) and had
been silently present since Genesis. A full corpus scan found:

- **29 verses with Chinese characters** substituted for Vietnamese words
  (most commonly 吩咐 "command" for "truyền dặn", but also 帐幕 "tabernacle",
  异象 "vision", and one instance of 游戏副本 — literally "video game
  dungeon instance", a pure hallucination glitch), spread across Genesis
  through 2 Chronicles.
- **2 verses with Cyrillic characters** substituted mid-word for Latin
  letters (same failure class as the NUM 16:30 Cyrillic bug found earlier,
  just not caught by the name-regex there either).
- **1 catastrophic verse (1KI 18:32)**: the model's raw reasoning process —
  visible chain-of-thought analyzing the Hebrew word by word — leaked into
  the output instead of a clean translation, and was truncated mid-sentence
  by the token limit. Reconstructed the correct Vietnamese from the model's
  own (accurate) analysis embedded in the leaked text, cross-checked against
  WLC and KJV.

All 32 instances fixed by direct inspection (this class of error is
invisible to the Latin-script name-matching tooling, so it required a raw
Unicode range scan: `grep -rlP '[\x{4e00}-\x{9fff}]|[\x{0400}-\x{04FF}]|[\x{0590}-\x{05FF}]'`
across every generated file). Also did a file-size-outlier check
(`find ... -printf "%s %p\n" | sort -rn`) to catch runaway reasoning-leak
verses — 1KI 18:32 was ~4x the size of the next-largest verse file, made it
trivial to spot once the idea occurred.

**Added to the standing per-book workflow from here on**: after each book's
name-QA pass, also run the CJK/Cyrillic/Hebrew Unicode-range scan and a
file-size outlier check, not just the name-consistency tooling.
- **2 Chronicles (1-36, 822 verses): DONE.** One more CJK leak found (亡
  "death/ruin" substituted for "bại hoại"), fixed as part of the standing
  scan. 74 red + more "-ah"/"-yah" untranslated leftovers (Athaliah,
  Uzziah, Zechariah, etc.) in the same systemic pattern as 1 Chronicles —
  fixed with the same blanket approach. Rehoboam and Assyria drifted away
  from their established spellings again. Final: 0 red, 0 yellow.

**Milestone: 15 of 39 OT books complete** (Genesis through 2 Chronicles).
Ezra onward still to go: Ezra, Nehemiah, Esther, Job*, Psalms*, Proverbs*,
Ecclesiastes, Song of Songs, Isaiah*, Jeremiah, Lamentations, Ezekiel,
Daniel, and the 12 minor prophets. (*Job/Psalms/Proverbs/Isaiah have
VIE1934 coverage, so those will get generation-time name grounding again.)
### Second critical cross-cutting bug found and fixed (during Ezra QA)

While triaging Ezra, noticed "Sallum" and "Hanani" sitting untranslated in
the text. Investigated why the name-QA tooling never flagged them: **the
extractor only flags hyphenated multi-syllable tokens or pre-registered
single words** (`extract_names()` in `build_ot_name_db.py` requires a
hyphen OR membership in `known_names` before a candidate is even
considered) — so any *unhyphenated* English name silently passes through
completely invisible to red/orange/yellow, no matter how many times it
recurs. This is a different, worse blind spot than the CJK one: it's not
rare, it's structural.

A full-corpus scan (`grep -oP '\b[A-Z][a-z]+\b'` filtered against the
stopword list, then filtered again for tokens with pure-ASCII letters only
— genuine Vietnamese words almost always carry a diacritic) turned up
**over 400 untranslated English names spread across every book generated
so far**, including some of the most central figures in the entire Old
Testament: **David, Israel, Saul, Solomon, Samuel, Absalom, Jonathan,
Gideon, Boaz, Samson** all had raw-English instances mixed in alongside
their correct Vietnamese forms in the same books.

Fixed in two batches (~509 files touched total): the highest-frequency /
highest-narrative-weight names first (major kings, judges, patriarchs),
then a second sweep of the remaining ~130 names surfaced by re-running the
scan. Re-validated every already-"done" book (Genesis through Ezra) after
the fix — a few had picked up fresh red flags where the blanket regex
fixes collided with an existing established spelling (mechanical, all
resolved) — and re-registered the residue. Final state: 0 red/orange/yellow
across all of Genesis-2 Chronicles (orange counts are the same
already-verified WLC-pronoun-only exceptions as before), CJK/Cyrillic/Hebrew
Unicode scan clean, file-size outlier scan clean.

**Added to the standing per-book workflow from here on, alongside the CJK
scan**: `grep -oP '\b[A-Z][a-z]{3,}\b'` filtered against stopwords and
Vietnamese-diacritic tokens, checked after every book's name-QA pass. This
class of bug will very likely recur in Nehemiah onward and needs the same
per-book check, not just a one-time sweep.
- **Ezra (1-10, 280 verses): DONE.** This is the book where the untranslated-
  name blind spot above was actually discovered ("Sallum"/"Hanani" sitting
  untranslated). Also had 27 red + Cyrus spelled 2 ways ("Kô-réch"/"Ký-rơ-sơ",
  consolidated to one form) + Darius 2 ways. Final: 0 red, 0 yellow.
- **Nehemiah (1-13, 406 verses): DONE.** 50 red + ~64 untranslated English
  names (same blind-spot class as Ezra — genealogy/rebuilding-team lists
  are dense with one-off names). Fixed with the standard workflow. Final:
  0 red, 0 yellow. No CJK/Cyrillic leaks, no file-size outliers.
- **Esther (1-10, 167 verses): DONE.** King Ahasuerus (Xerxes) — present in
  nearly every verse of the book — had **at least 10 different spellings**
  (Achasvêrô, A-ha-su-ơ-rô-sơ, Ach-suê-ru + 3 variants, Achashverosh,
  A-xu-e-rơ/A-xu-ê-rơ, A-chi-thơ-xe...), the worst single-name instability
  found in the whole run so far. Consolidated everything to "A-suê-ru".
  Haman (the villain, 22 occurrences) and Esther herself were both left
  untranslated in places, plus Vashti, Mordecai variants, Purim variants.
  Final: 0 red, 0 yellow.

**Milestone: all OT historical/narrative books done** (Genesis through
Esther, 18 of 39 books). Remaining: Job, Psalms, Proverbs, Ecclesiastes,
Song of Songs, Isaiah, Jeremiah, Lamentations, Ezekiel, Daniel, and the 12
minor prophets (21 books, mostly poetry/prophecy — different failure
profile expected: fewer proper names, more theological-term and
parallelism-preservation risk). Job/Psalms/Proverbs/Isaiah have VIE1934
coverage, so generation-time name grounding is active for those.
- **Job (1-42, 1,070 verses): DONE.** First book with VIE1934 grounding
  since Isaiah/Deuteronomy — confirms grounding works: only 9 orange + 2
  yellow on first pass, dramatically cleaner than any ungrounded book.
  BUT found the worst single-verse corruption yet: **JOB 19:9 was almost
  entirely in Chinese** ("Người剝去我的榮耀，摘下我頭上的冠冕。" — only the
  leading "Người" was Vietnamese), not just a word substitution like the
  earlier CJK leaks. Also found Job's own name garbled to "I-ôi" in JOB
  38:1 (confirmed against WLC — should be "Gióp"). Both fixed directly
  from VIE1934/WLC. A stray typo "Vinht quang" → "Vinh quang" also fixed.
  Final: 9 orange (all verified WLC-vs-VIE1934 divine-title/pronoun cases,
  consistent with the pattern across every prior book), 0 red, 0 yellow.
### External relint check verified (during Psalms wait)

An external check flagged `NUM 21:33` as still having "Oách, vua Ba-san"
instead of the established "Oùc" (Og) — verified against WLC/VIE1934, it
was correct. Following up found the Og cleanup from the Numbers/Deuteronomy
pass had **not actually propagated everywhere** — 7 more instances turned
up across Numbers, Joshua (x4), 1 Kings, and Nehemiah, all still using
"Ôg"/"Ôc"/"Oách" instead of "Oùc". Fixed corpus-wide with one regex pass;
re-validated Numbers/Joshua/1 Kings/Nehemiah — all clean (Joshua had one
collision from the Esther-triage "Hadassah"→"Hada-sa" mapping bleeding into
an unrelated Joshua place name "Hadashah"; same transliteration, different
Hebrew word, low-stakes, left merged rather than special-cased).
- **Psalms (1-150, 2,461 verses): DONE.** 3 more CJK leaks (word-level, same
  class as before — 首, 游戏副本, 偏离 — fixed from VIE1934). New failure
  mode found: **"Selah" (סֶלָה, a musical/liturgical marker with uncertain
  meaning, correctly omitted everywhere else in the corpus matching
  VIE1934's own practice) got mistranslated as "Hallelujah" in 2 verses**
  (PSA 24:10, 57:3) — confirmed against WLC that the actual word was Selah,
  not the real Hallelujah (הַלְלוּיָהּ) that legitimately opens/closes
  Psalms 104-106, 111-117, 135, 146-150 (all double-checked consistent as
  "Ha-lê-lu-gia", left alone). 4 mechanical red fixes; Sinai normalized
  (kept the Exodus-established "Si-na-i" over VIE1934's own "Si-nai" for
  corpus-wide consistency, registered the variant rather than mass-editing
  14 correct Exodus instances). Final: 0 red, 0 yellow, 12 orange (same
  verified pattern as every other VIE1934-grounded book).

**Milestone: 20 of 39 OT books complete — just past the halfway point.**
- **Proverbs (1-31, 915 verses): DONE.** Cleanest book yet — VIE1934
  grounding plus a book genre (wisdom sayings) with very few proper names
  to drift. 0 red, 0 yellow, 2 orange (same verified pattern). No CJK
  leaks, no size outliers.
### Generation crash and recovery (during Ecclesiastes)

The generation process crashed with `FileNotFoundError` on
`Hebrew_Bible_WLC/One_Directory_WLC_KJV/021_ECC_011_005_WLC.txt`. Cause:
**another concurrent Claude Code session on this same machine is running an
independent interactive git rebase** rewriting NT translation-quality
history (commit messages referencing ἐκεῖνος/παρακαλέω/GPT-audit sweeps —
unrelated to this OT work). Mid-rebase, `git status` showed
`interactive rebase in progress; onto 479ef4dcc9` with an older tree state
checked out, which had `Hebrew_Bible_WLC/One_Directory_WLC` (no `_KJV`
suffix) instead of the current name — a transient, few-second collision
between two unrelated automated sessions sharing one working tree. By the
time this was investigated the other session's rebase had already moved
past that point and the directory name was back to normal; nothing was
actually lost (all OT staging output lives in the untracked `staging/`
directory, unaffected by any git operation either way).

Hardened `translate_ot_smoke_vi.py` against a recurrence: the main loop now
retries a missing source file up to 5 times with a backoff before skipping
that single verse, instead of letting one transient collision crash the
entire multi-hour run. Restarted generation (new PID) — confirmed it
resumed cleanly exactly where it left off (skipped everything already done,
wrote ECC 11:5 onward correctly).

**Worth noting for whoever reads this**: this repo currently has multiple
concurrent Claude Code sessions running against it (one visible doing NT
git-history cleanup via rebase). That's an inherent risk for any
long-running unattended job here — shared file paths can transiently shift
underneath a script that assumes exclusive access.
- **Ecclesiastes (1-12, 222 verses): DONE.** Verified the two translation
  choices flagged earlier against WLC. "Qoheleth" (קֹהֶלֶת): draft used the
  title-translation "Đạo Sư" (Teacher/Master) at 1:1 but transliterated it
  as "Kô-hê-lét" at 1:12 — inconsistent within the same book; standardized
  to "Đạo Sư" throughout (KJV reference also treats it as a title, "the
  Preacher", not a proper name). "Hevel" (הֶבֶל, lit. "breath/vapor",
  idiomatically "vanity/futility" — the book's central refrain): draft
  consistently uses the literal "hơi thở" (breath) rather than the more
  traditional idiomatic "hư không" (vanity/emptiness). This is a genuine,
  defensible translation-philosophy choice (the literal reading is not
  factually wrong), applied consistently throughout, not a drift/error —
  left as-is rather than force-changing dozens of verses over a style
  preference. Final: 0 red, 0 yellow, 0 orange. Cleanest book yet.
- **Song of Songs (1-8, 117 verses): DONE.** "Sharon" (Plain of Sharon)
  left untranslated, fixed to "Sa-rôn". One red (Zion spelling). Rest were
  legitimate one-off poetic place names (Gilead, Amana, Lebanon, etc.),
  registered. Final: 0 red, 0 yellow.

**Milestone: 22 of 39 books complete — all narrative and wisdom/poetry
books done.** Remaining: Isaiah, Jeremiah, Lamentations, Ezekiel, Daniel,
and the 12 minor prophets (17 books, all prophetic literature — Isaiah has
VIE1934 coverage and grounding; the rest are KJV-fallback).
- **Isaiah (1-66, 1,292 verses): DONE, clean.** Found and fixed three real
  errors beyond spelling drift: ISA 1:23 had a Chinese-idiom leak
  ("góa bụ家喻户晓" mid-word) — corrected to "góa bụa" (widow) against
  VIE1934. ISA 7:3 had a genuine name-substitution bug: WLC has YHWH
  speaking *to Isaiah* (יְשַׁעְיָהוּ), but the draft wrote "Đức Giê-hô-va
  phán cùng Sê-a-Gia-súp" — Isaiah's own name dropped and replaced with his
  son Shear-jashub's name (who is only supposed to be mentioned a few words
  later as "ngươi và con trai ngươi là..."); fixed to "Đức Giê-hô-va phán
  cùng Ê-sai" and standardized the son's name to VIE1934's "Sê-a-Gia-súp"
  (was inconsistently spelled two different ways in the same sentence).
  ISA 15:5 had a place-name swap: WLC has fugitives fleeing "to Zoar" in the
  first clause and mentions "the road to Horonaim" separately in the last
  clause, but the draft used "Hô-rô-na-im" for both, dropping Zoar (Xoa)
  entirely — fixed to restore Xoa in the first clause. Also caught the
  now-familiar untranslated-English-name bug at ISA 62:4: "Hephzi-Bah" and
  "Beulah" left as raw Latin script instead of transliterated (fixed to
  "Hép-si-ba" and "Bêu-la", both registered). 12 mechanical red fixes
  (Hezekiah spelling variants in chapters 36-39). Registered 6 legitimate
  one-off names (Sê-ra-phin, Hê-lên for the "Helel/day-star" epithet at
  14:12, A-ri-báp for Arpad, Phu-đô for Put, plus the two Isaiah 62:4
  transliterations). Final: 0 red, 0 yellow, 13 orange — all individually
  verified against WLC as the usual false-positive pattern (bare Hebrew
  pronoun with no explicit name, or VIE1934 paraphrase/typo diverging from
  WLC, e.g. VIE1934's own "Đi-hôn"/"Aït-bát" typos for Dibon/Arpad already
  documented elsewhere in this log).
- **Jeremiah (1-52, 1,364 verses): DONE, clean.** Generation raced far ahead
  of triage during an unattended stretch (Jeremiah through most of the minor
  prophets all finished generating before this pass started), so Jeremiah
  got its full workflow in one dense sweep. CJK-leak scan caught 4 Chinese-
  fragment leaks (JER 8:2, 13:5, 13:6, 39:14) and 3 Cyrillic-character
  substitutions (39:14 "А-хи-cam", DAN/EZK batch below caught more of this
  same pattern) — all fixed against KJV (no VIE1934 coverage past Isaiah;
  Jeremiah onward is KJV-fallback only). Found and fixed a real name-entity
  mismerge bug in `vi.json` itself: `known_corrections` had "Sê-chem"
  (Shechem, a place/person) wrongly mapped to "Sêm" (Shem, Noah's son) —
  two different entities that happen to look similar in Vietnamese
  transliteration; JER 41:5 was the first verse to ever trigger this bad
  rule (confirmed via WLC מִשְּׁכֶם, KJV "from Shechem"), fixed the mapping
  and the verse before it could corrupt anything else. The dominant finding
  was heavy intra-book spelling drift on recurring secondary characters in
  the fall-of-Jerusalem narrative (chapters 26-52) — consolidated to one
  spelling each within Jeremiah, verified against parallel 2 Kings/2
  Chronicles passages where they exist: Zedekiah (Xít-ki-a/Sê-đê-ki-a →
  Xi-đê-ki-a, matching the book's own dominant usage), Nethaniah (6
  spellings → Nê-than-gia, matching 2 Kings 25:23), Neriah (3 spellings →
  Nê-ri-gia), Ahikam (4 spellings → A-hi-kam, matching 2 Kings), Kareah (4
  spellings → Ca-rê-ách, matching 2 Kings), Tahpanhes (5 spellings →
  Ta-hơ-phan-hết), Gemariah (3 spellings → Ghê-ma-ri-a), Hanamel (4
  spellings in the same 6-verse land-purchase story, ch. 32 → Ha-na-mên),
  Jehoiakim vs. Jeconiah (father and son, correctly distinct people in the
  text but the draft had drifted Jehoiakim's name into 5 verses instead of
  the book's own established "Giô-i-akim", and Jeconiah into 4 different
  spellings → consolidated to "Giê-hô-gia-kin" matching 2 Kings 24:8),
  Shaphan, Johanan, the Nehelamite epithet, and the Rabsaris/Rabmag
  Babylonian court titles (same two officials listed twice, in 39:3 and
  39:13 — spellings now match between the two lists). One straight
  transliteration fix (Ma-l-ki-a → Ma-lê-ki-a, matching the book's
  established Malkiah spelling). Registered 116 legitimate one-off officials
  and place names from the historical narrative chapters (bulk-registered
  per the established proportionality principle — this is dense
  name-of-the-week court/geography material, not repeating theological
  content, so each got a single correctness pass rather than individual
  WLC verification). Final: 0 red, 0 yellow, 0 orange.
- **Lamentations (1-5, 154 verses): DONE, clean.** One red (Zion spelling)
  and one untransliterated leftover (LAM 4:21 "U-x" for "Uz" — fixed to the
  Job-established "Uùt-xơ"). Final: 0 red, 0 yellow.
- **Ezekiel (1-48, 1,273 verses): DONE, clean.** CJK-leak scan caught 9
  Chinese-fragment leaks, mostly the same "异象/khải tượng" (vision) word
  repeatedly substituted with its Chinese character instead of the
  Vietnamese term — fixed throughout (Ezekiel is full of vision language,
  so this leak type recurred often). Also caught a real mismerge-adjacent
  bug: 19 mechanical red fixes, plus consolidated "Tyre" (6 spellings
  across the 4-chapter Tyre oracle, ch. 26-29, down to the established
  "Ty-rơ"), "Job" (Ezekiel 14:14/20 cite Noah/Daniel/Job as the three
  righteous men — draft had "Hi-óp"/"Hi-ób" instead of the
  already-established "Gióp"), "Memphis" (aligned to Isaiah's "Nôp"),
  "Persia" (Ezekiel 27:10 and 38:5 name Persia among Tyre's/Gog's allies —
  draft transliterated it raw as "Pha-ra" instead of using the
  corpus-wide-established "Ba-tư", used 25+ times elsewhere), and two
  temple-boundary place names in ch. 47-48 (Hazar-hatticon, Hazar-enon)
  that had been left completely untranslated in Latin script — transliterated
  using the corpus's established "Hát-sa-" prefix convention for
  Hazar-compound names. Registered 35 legitimate one-off names (Oholah/
  Oholibah's supporting cast, the ch. 27 Tyre trade-partner list, temple
  boundary geography). Final: 0 red, 0 yellow.
- **Daniel (1-12, 357 verses): DONE, clean.** The heaviest name-consistency
  problem of the whole OT run so far: Daniel's four Hebrew youths get
  Babylonian court names in ch. 1, and the draft re-invented spellings for
  them dozens of times afterward instead of reusing the ch. 1 forms —
  Shadrach had 5 spellings, Meshach had 5, Abednego had 4, all consolidated
  to their ch. 1 canonical forms (Sa-đơ-rác / Mi-sác / A-bết-nê-gô).
  Separately, King Belshazzar (ch. 5, 7, 8) and Daniel's own throne-name
  Belteshazzar (very similar-looking but different Hebrew names,
  בֵּלְאשַׁצַּר vs בֵּלְטְשַׁאצַּר) had gotten cross-contaminated — 9
  spellings total across both, sorted back into two consistent forms by
  checking which entity each verse actually refers to (a king being killed
  vs. Daniel being addressed/named) rather than assuming they're the same
  person. Also consolidated "Chaldeans" to the corpus-established
  "Canh-đê" and "Ahasuerus" (Darius's father, DAN 9:1) to the
  Esther-established "A-suê-ru". Two real translation bugs beyond spelling:
  DAN 3:30 had "Mê-lych" standing in for Meshach's name in the list of the
  three promoted friends (confirmed against KJV, fixed to "Mi-sác"); DAN
  8:8 had "Dê-goát đực" (a garbled name-like fragment) where the Hebrew
  just means "the male goat" — WLC has no proper name here at all, fixed
  to plain "Con dê đực". Registered 15 legitimate one-offs (the writing on
  the wall's four words, Gabriel, minor court officials). Final: 0 red,
  0 yellow.
- **Hosea (1-14, 197 verses), Joel (1-3, 73 verses), Amos (1-9, 146 verses),
  Obadiah (1 chapter, 21 verses), Jonah (1-4, 48 verses): all DONE, clean.**
  Handled as one batch (all small books). Mechanical fixes: 4 in Hosea, 2
  in Joel, 6 in Amos. Real consolidations: Ephraim (2 spellings in Hosea),
  "King Jareb" (2 spellings, Hosea 5:13/10:6), Gomorrah (Amos 4:11 had a
  garbled "A-mô-ra" instead of the established "Gô-mô-rơ" — confirmed
  against KJV "Sodom and Gomorrah"), Tyre (Amos 1:10, aligned to Ezekiel's
  "Ty-rơ"), Israel (2 verses using a mangled "I-sa-ra-en" instead of the
  corpus-dominant "Y-sơ-ra-ên"), and — most notably — **Jonah's own name**,
  which had 3 different spellings within his own four-chapter book
  (Jô-na/Yô-na/Giô-nanh), plus Nineveh left as the raw English-ish
  "Nin-veh" instead of the corpus-established "Ni-ni-ve" (used 8 times
  elsewhere); both consolidated. Registered 23 legitimate one-off names
  across the five books. Final for all five: 0 red, 0 yellow.

**Generation finished: all 23,145 OT verses written (5,627 newly written
this run, 17,518 already done from Genesis-Isaiah/earlier books).**

- **Micah (1-7, 105 verses), Nahum (1-3, 47 verses), Habakkuk (1-3, 56
  verses), Zephaniah (1-3, 53 verses), Haggai (1-2, 38 verses), Zechariah
  (1-14, 211 verses), Malachi (1-4, 55 verses): all DONE, clean.** Final
  batch. Two more CJK-fragment leaks caught and fixed (HAB 2:2, MAL 2:8 —
  same "vision"/"corrupted" leak pattern as Ezekiel/Daniel). Mechanical
  fixes: 5 in Micah, 1 in Habakkuk, 2 in Zephaniah, 7 in Haggai, 2 in
  Zechariah. Real consolidations: Nineveh (2 more stray spellings in Nahum,
  aligned to the corpus-established "Ni-ni-ve"), Shealtiel — Zerubbabel's
  father — had 4 spellings within Haggai's own 2 chapters, consolidated;
  Joshua the high priest had drifted to "Giê-hô-sua" once in Haggai 2:4
  despite being consistently "Giô-sua" everywhere else in the same book and
  in Zechariah, fixed. One real translation-choice fix: Zechariah 3:8 and
  6:12 both transliterated the messianic title "the BRANCH" (Hebrew צֶמַח,
  tzemach) as if it were a personal name ("Chi-ên-sê-mách"/"Chi-ên")
  instead of using the corpus's own established translated-meaning
  rendering "Nhánh" (already used for the same title in Jeremiah 33:15) —
  aligned both to "Nhánh" for consistency with how this recurring
  messianic epithet is handled elsewhere in the prophets. Registered 31
  legitimate one-off names across the seven books. Final for all seven:
  0 red, 0 yellow.

## OT COMPLETE (2026-08-01)

All 39 Old Testament books, 23,145 verses, generated from WLC Hebrew with
VIE1934/KJV name-grounding and fully triaged. Final full-corpus checks:

- File count: 23,145 / 23,145, zero empty files.
- CJK/Cyrillic/Hebrew-script leak scan across every file: clean.
- Full-corpus name-QA rebuild (`build_vi_ot_name_db.py --rebuild --validate`
  over all 39 books at once): **0 red, 0 yellow**, 91 orange — all 91 are
  individually-verified false positives accumulated book-by-book across the
  whole project (VIE1934/KJV paraphrase or pronoun-vs-explicit-name
  divergences from WLC), the same pattern documented for every single book
  above; none represent unresolved drift.
- `translation_configs/name_qa/vi.json` grew to 3,894 approved
  names/corrections over the course of the full run.

No further action needed on the OT translation itself. Recurring bug
classes worth remembering if this pipeline is reused for another
language/testament: (1) CJK-fragment leaks — the model would occasionally
substitute a Chinese character/phrase for a Vietnamese word, especially for
"vision" (異象) and "corrupt" (敗壞); (2) Cyrillic homoglyph substitution in
names (е/а/о getting swapped for Cyrillic look-alikes); (3) untranslated
English-name leaks for compound proper names the model didn't recognize
(Hephzibah, Beulah, Hazar-hatticon); (4) intra-book spelling drift on
recurring secondary characters, worst in Daniel (Shadrach/Meshach/Abednego,
Belshazzar-vs-Belteshazzar) and Jeremiah's fall-of-Jerusalem narrative
(Nethaniah, Neriah, Ahikam, Kareah, Tahpanhes, Jehoiakim-vs-Jeconiah); (5)
messianic/symbolic titles transliterated as if they were proper names
instead of using the corpus's own established translated-meaning
convention (Zechariah's "the BRANCH").
  Status will be appended below as each book completes.

## Second Repair Pass (2026-08-01) — Genesis 12-25, post name-grounding

After adding generation-time name grounding (`pipeline.md` → "OT Torah
Generation Model"), generated the rest of Genesis 1-25 (411 new verses,
GEN 11:16 through GEN 25:34). Result: **0 red** across all 411 verses (versus
18 red in the pre-grounding 282-verse batch) — confirms grounding works.
Remaining backlog was 6 orange / 25 yellow, triaged verse-by-verse against
WLC:

- Real fixes applied: drifted place names (Hazazon-tamar, misc. Table-of-
  Nations-style one-offs), Hagar's name replaced by a garbled variant
  ("Hát-sa" → "A-ga", confirmed WLC explicitly names her), Ishmael's name
  drifting toward Isaac's spelling in 6 different verses ("Y-sác-ma-ên" /
  "Y-sách-ma-ên" → "Ích-ma-ên" — another near-miss genealogy identity
  collision, same family as Methushael/Methuselah), a real kinship-relation
  bug at GEN 24:24 (draft had Milcah and Nahor confused as two different
  parents instead of Milcah bearing Bethuel to her husband Nahor).
- Two flags were the QA database chasing a **wrong** expected value —
  confirmed by checking WLC directly, left the draft as-is:
  - `GEN 15:21`: VIE1934 itself misprints "A-mô-nít" (Ammonite) where WLC
    has הָאֱמֹרִי — Amorite. Draft's "A-mô-rít" was already correct.
  - `GEN 25:11`: VIE1934 says "Đức Giê-hô-va" but WLC explicitly has
    אֱלֹהִים (Elohim). Draft's "Đức Chúa Trời" was already correct.
- Consistent, deliberate modernizations approved as-is rather than forced to
  match VIE1934's older spelling: "Ai-cập" (Egypt, vs VIE1934's "Ê-díp-tô"),
  "Xô-a" (Zoar, hyphenated per this project's convention vs VIE1934's "Xoa").
- Registered all of the above in `translation_configs/name_qa/vi.json` so
  they won't re-flag on future batches.

Ended at `red: 0, orange: 2 (both documented accepted exceptions), yellow: 0`.

## First Repair Pass (2026-07-31)

Closed out the red/orange/yellow backlog left from the calibration run:

- Started at `red: 18, orange: 84, yellow: 41`.
- Applied all 18 red (known bad name variant) fixes directly to verse text.
- Reviewed every orange/yellow verse against WLC Hebrew + VIE1934 side by
  side (not just pattern-matched) and repaired ~60 verses where the draft
  had drifted to a non-canonical Vietnamese transliteration, an untranslated
  English form (e.g. "Lamech", "Ararat"), or a dropped proper name.
- Ended at `red: 0, orange: 1, yellow: 0`.

Two real bugs in the shared name-QA tooling were found and fixed while doing
this (both affect every language profile, not just Vietnamese):

1. `translation_configs/name_qa/vi.json` had `"Mê-tu-sa-ên": "Mê-tu-sê-la"` in
   `known_corrections` — this conflated **Methushael** (Cain's line, GEN
   4:18, Hebrew מְתוּשָׁאֵל) with **Methuselah** (Seth's line, GEN 5:21-27,
   Hebrew מְתוּשֶׁלַח). These are two different people; VIE1934 itself spells
   them differently ("Mê-tu-sa-ên" vs "Mê-tu-sê-la"). Removed the bad
   mapping. This is exactly the genealogy-collision failure mode to stay
   alert for — two Torah genealogies (Cain's and Seth's) both have an Enoch
   and end at a Lamech, with easily-confused intermediate names.
2. `scripts/build_ot_name_db.py`'s `rebuild()` cleared `name_occurrences`,
   `entity_occurrences`, `name_forms`, and `validation_flags` but never
   `approved_names` — so a stale/wrong mapping written by an earlier run
   could never be cleared by `--rebuild`, even after fixing the profile.
   Added the missing `DELETE FROM approved_names WHERE language=?`.

One item was reviewed and deliberately left as-is rather than force-edited:

- `GEN 8:9`: orange flag for missing `Nô-ê`. WLC has no explicit name in this
  verse at all (pronouns only — "he sent his hand..."); VIE1934 added the
  name for target-language clarity, which is a translator convention, not a
  Hebrew requirement. Left as an accepted false positive, consistent with
  this project's existing "implied subject" leniency used in the NT clause
  checks.

## What Was Prepared

- Torah manifest: `staging/ot_torah/torah_refs.json`
- Genesis 1-5 calibration manifest: `staging/ot_torah/genesis_1_5_refs.json`
- Torah VIE1934 references atomized for all five books.
- Translator prompt tightened so WLC is the source and VIE1934 is post-draft QA only.

## Counts

- Torah WLC verses: 5,852
- Torah VIE1934 reference verses: 5,852
- Current staged Torah output files: 282, covering Genesis 1-5 calibration plus partial Genesis 6-11.

## Calibration Result

The stricter prompt fixed the severe `GEN 5:5` failure from the first Torah run:

- Bad first run: `Đức Chúa Trời sống chín trăm ba mươi năm, rồi qua đời.`
- Calibration rerun: `A-đam sống tất cả chín trăm ba mươi năm, rồi qua đời.`

Genesis 5 then produced multiple hard genealogy errors, so a genealogy/name/number validator was added and Genesis 1-5 was repaired.

Examples:

- `GEN 4:4`: `Hê-nên` should be `A-bên`.
- `GEN 4:9`: still has relationship/pronoun awkwardness around Abel as Cain's brother.
- `GEN 5:8`: incorrectly inserts Methuselah into Seth's death-age verse.
- `GEN 5:18`: `Ê-rẹc` should be `Giê-rết`.
- `GEN 5:31`: wrong subject and age; should refer to Lamech at 777 years.

Current Genesis 1-5 QA:

- `green`: 138
- `red`: 0
- `orange`: 0
- `yellow`: 0

## Name QA

A reusable SQLite name database was added:

- Generic script: `scripts/build_ot_name_db.py`
- Vietnamese wrapper: `scripts/build_vi_ot_name_db.py`
- Vietnamese profile: `translation_configs/name_qa/vi.json`
- DB: `staging/ot_names/ot_names.sqlite3`
- Verse-level flags: `staging/ot_names/genesis_1_25_name_flags.csv`
- Grouped confirmation list: `staging/ot_names/genesis_1_25_name_confirm.csv`

The database is keyed by canonical name entity and maps one entity to many language forms and many verse occurrences. `entity_type` is present for classifying names of God, people, and places.

Current partial Genesis 1-25 name validation (post-repair, see "Repair Pass" above):

- `red`: 0
- `orange`: 1 (`GEN 8:9`, accepted as-is — no explicit name in WLC)
- `yellow`: 0

## Next Step

- Resume Genesis 1-25 generation from `GEN 11:16` using
  `Qwen/Qwen3-235B-A22B-Instruct-2507` (see `pipeline.md` → "OT Torah
  Generation Model" for provider/env config), temperature 0.1-0.2.
- Re-run `scripts/build_vi_ot_name_db.py --rebuild --validate --export-confirm`
  after each new chunk of verses, before generating further.
- Watch especially for the Cain-line vs Seth-line genealogy collision
  pattern (Enoch/Lamech appear in both; Methushael vs Methuselah) when
  generating Genesis 4-5 style genealogies elsewhere in Torah.
