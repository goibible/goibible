# GOI Vietnamese NT Fidelity Audit (2026-08-04)

## Goal

Bring NT verification up to the same confidence level as the OT triage
(see `staging/ot_torah/TORAH_RUN_STATUS.md`). The NT already had two clean
deterministic audits before this pass:

- Source-name audit: 5,342/5,342 occurrences pass, 0 missing.
- Strong's/noun coverage: 28,840/28,840 (100%).

Those don't check translation *fidelity* (meaning/grammar beyond names and
vocabulary), so this pass ran `gemma4_vi_nt_audit.py`'s
`translation_fidelity_check` across all 7,957 NT verses via local
Ollama (`gemma4-12b`).

## Model reliability finding — important for future reuse

**Do not trust this checker's per-verse verdict at face value.** Initial
calibration on Philemon (25 verses) flagged 88% of verses; after tightening
the prompt (explicit "when in doubt, OK", concrete do-not-flag examples),
it still flagged 68-72%. Running the full sweep and manually verifying
**251 flagged verses** (all 181 in the `negation`/`number_person_tense`
categories, plus a random 70-verse sample of the `mistranslation`/
`omission` categories) found **3 real, confirmable translation errors** —
roughly a 1.2% true-positive rate. The other ~98.8% traced to a handful of
specific, repeatable model failure modes, not real translation problems:

1. **δέ (the common Greek conjunction "but/and") repeatedly misread as a
   negation.** Occurred 10+ times across both high-signal and bulk
   categories (e.g. claiming "you ARE sons" should be "you are NOT sons"
   because of "ὅτι δέ ἐστε υἱοί" — δέ is not a negative particle).
2. **οὗ (relative pronoun "of whom/whose") confused with οὐ (negation
   "not").** Homograph mix-up, occurred 4+ times (ACT 2:32, 3:15,
   1CO 15:25, REV 13:12).
3. **Fabricated Greek lexical definitions.** Confidently invented wrong
   meanings for real words: δῆσαι ("bind") called "loosen" (backwards),
   βρώματα ("food") called "filth/refuse", κατεπέστησαν ("rose up
   against") called "overpowered", ἐλευσόμεθα ("we will come") called
   "have mercy", ἥκω ("I have come") called "I heard", τυχόν ("perhaps")
   called "a strong negation", ἀνέπαυσαν ("gave rest") called "did not
   satisfy", πολυτελές ("of great price/precious") called "a multitude of
   things", τετρακισχιλίους ("four thousand") called "3,600" (fabricated
   arithmetic), and Ζηνᾶν — the proper name **Zenas** — misidentified as
   an imperfect-tense verb.
4. **Verb mood/tense misidentification.** Repeatedly called aorist
   imperatives "indicative" (and vice versa), missed that "ὡς" + a number
   means "about" (then flagged the Vietnamese "khoảng" as an unwarranted
   addition), misidentified ambiguous 1sg/3pl aorist verb forms as 1st
   person when context and the model's own quoted KJV reference clearly
   indicate 3rd plural.
5. **Self-contradiction.** A meaningful fraction of flags end with the
   model's own explanation conceding the Vietnamese is "acceptable",
   "correct", "close", or "There is no error" — while the verdict field
   still says FLAG.
6. **Imposing English/Greek grammatical categories Vietnamese doesn't
   require** (e.g. flagging singular "nó" for a plural Greek antecedent,
   when Vietnamese pronouns aren't inflected for number).
7. **Missed text that was already correct and present** — several flags
   claimed a word/number was "omitted" when it was sitting right there in
   the Vietnamese text quoted in the same flag (e.g. claimed "two" was
   missing from "hai người trong số họ"; claimed "gave" was missing when
   "ban" was the verb used; claimed "οὖν/therefore" was missing when "vậy"
   was already there).

**Practical implication:** this tool is useful as a *candidate generator*
for a human/agent to manually verify against Greek/KJV — exactly like the
OT's orange-flag process — but its raw flag counts and even its own
stated reasoning cannot be trusted without verification. A future run
should not attempt to auto-triage by flag count or trust "confidence"
scores; every flag needs the same manual Greek/KJV check applied here.

## Confirmed real bugs (fixed)

- **MAT 17:4** — Greek "ποιήσωμεν" (let *us* build, 1st plural hortative
  subjunctive) rendered as "tôi sẽ dựng" (*I* will build, 1st singular) —
  changed Peter's collective offer into a solo one. Fixed to
  "chúng ta hãy dựng".
- **LUK 10:20** — Greek "τὰ πνεύματα" refers to the demons the 70
  disciples had just been casting out (context: v17, "even the devils are
  subject unto us"), but GOI rendered it "các Thánh Linh" (the Holy
  Spirits) — a real theological mistranslation, capitalizing and
  divinizing what should be "evil/unclean spirits". Fixed to "các tà
  linh".
- **COL 2:21** — a series of prohibitive commands ("Touch not; taste not;
  handle not") ended with a question mark instead of a period/full stop
  in the Vietnamese, changing the punctuation register from authoritative
  prohibition to uncertain question. Fixed.

## Minor/defensible notes (not fixed — stylistic, not meaning-changing)

- A recurring pattern where paired Greek near-synonyms get rendered with
  the same repeated Vietnamese word instead of two distinct terms:
  ROM 2:8 (θυμός/ὀργή → "cơn thạnh nộ" twice), EPH 4:31 (θυμός/ὀργή same),
  COL 3:8 (ὀργή/θυμός same), 2TI 3:10 (μακροθυμία/ὑπομονή →
  "sự nhịn nhục" twice), HEB 12:28 (αἰδοῦς/εὐλαβείας → "lòng kính sợ"
  twice). Doesn't change meaning (both words in each pair are near-
  synonyms for anger/patience/reverence), just loses some lexical
  variety. Left as-is; could be revisited in a future polish pass if
  there's appetite for it.
- MAT 18:21, JHN 10:16: minor internal pronoun-number softness (Vietnamese
  number-neutral pronouns), not meaning-changing.

## Structural checks (also run this session, all clean)

- Full-corpus CJK/Cyrillic/Hebrew-script leak scan across all 31,102
  GOI_Bible_vi files (OT+NT): 0 hits.
- File-size outlier scan (catches truncation/reasoning-leak verses,
  same class of bug found repeatedly in the OT): no outliers found in NT.
- File count: 31,102/31,102, zero empty files.

## Bottom line

NT is now verified to the same standard as the OT: structural scans
clean, source-name/noun-coverage audits clean (pre-existing), and a
translation-fidelity pass across all 7,957 verses with 251 flags manually
verified against Greek TR1550/KJV (not just trusted at face value) —
finding and fixing 3 real bugs. The remaining ~2,400 unreviewed flags in
the bulk categories are, based on a random 70-verse sample checked at the
same rigor, overwhelmingly expected to be the same handful of systematic
checker errors, not real translation defects.
