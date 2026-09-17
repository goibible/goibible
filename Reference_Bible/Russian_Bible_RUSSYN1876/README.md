# Russian Synodal Bible (RUSSYN)

This directory preserves the public-domain Russian reference text used for a
future GOI Russian translation pipeline.

- Edition: Russian Synodal Bible (Синодальный перевод), catalog identifier `RUSSYN`
- Language: Russian (`ru`)
- Rights: Public Domain, per eBible.org's Find a Bible record
- Source record: https://ebible.org/find/details.php?id=russyn
- Downloaded source: `source/russyn_vpl.zip` (verse-per-line export)
- SHA-256: `1ac0035cbcbdfcd07a89d50c5e11e87822a74c61b85c18a892278ce4cd4b09a8`

## Versification: FULLY ALIGNED (100%), verified book by book, chapter by chapter

`One_Directory_RUSSYN1876/` covers all 31,102 GOI/KJV spine addresses
exactly — 66/66 books, 1,189/1,189 chapters, 23,145 OT + 7,957 NT + 2,461
Psalms verses, no missing, no extra, no duplicates. Verified two ways:

- `build_full_versification_audit.py` compares every chapter of the
  Russian source directly against Hebrew WLC (OT) and Greek TR1550 (NT) —
  not KJV as a proxy, the actual source-language spine trees this project
  already has fully realigned onto GOI addresses. Output:
  `full_versification_audit_summary.md` / `.csv`.
- `verify_output_alignment.py` checks the actual written flatfiles in
  `One_Directory_RUSSYN1876/` against the spine, per book and per chapter.
  Output: `output_alignment_by_chapter.csv`. Current result: **1,189/1,189
  chapters match exactly.**

Getting there took three passes, because Russian is **not** drop-in
GOI-aligned the way Arabic is:

1. **Direct address matching** (`atomize_russian_synodal.py`) handles the
   ~28,600 addresses where Russian's own chapter/verse numbers already
   match the spine.
2. **Psalms** (`build_psalm_versification_map.py` +
   `apply_psalm_versification_map.py`) — the Synodal Psalter follows
   Church-Slavonic/LXX numbering, not KJV/Masoretic. See the dedicated
   section below.
3. **16 more books** (`build_non_psalm_versification_map.py` +
   `apply_non_psalm_versification_map.py`) — 1 Samuel, 2 Corinthians,
   3 John, Acts, Daniel, Ecclesiastes, Hosea, Isaiah, Job, Jonah, Joshua,
   Leviticus, Numbers, Proverbs, Romans, Song of Songs each have at least
   one chapter where Russian's verse boundaries diverge from KJV's —
   chapter-boundary shifts (Jonah 1:17/2:1, Hosea 13:16/14:1, Numbers
   12:16/13:1 and 29:40/30:1, Song of Songs 6:13/7:1), verse merges (2
   Corinthians 11 and 13, Leviticus 14, Acts 19, 3 John 14/15),
   Job's three-chapter Behemoth/Leviathan re-division (39/40/41), a
   relocated Romans 16:25-27 doxology (placed after 14:23 in the
   Byzantine/Synodal tradition), and a handful of genuine Byzantine/LXX
   textual additions with no KJV counterpart at all (Joshua 24:34-36,
   Proverbs 4:28-29 and 13:14) — logged, not force-mapped, since they
   have nothing to map to.

Every one of these boundaries was confirmed by reading actual verse
content on **both** sides at **both** endpoints of every shifted range
before being encoded into a map — not inferred from verse counts alone.
That matters: a within-chapter shift silently pairs the wrong Russian
verse with a GOI address for every verse from the shift point to the end
of the chapter under naive matching, not just the boundary verse. The
first build of this directory hit exactly that bug — see below.

`atomize_russian_synodal.py` **excludes all 17 versification-mapped
books** (Psalms + the 16 above) from its naive address matcher, so
running `--write` can never silently reintroduce wrong pairings for them.
Full rebuild, in order:

```
python3 atomize_russian_synodal.py --write
python3 build_psalm_versification_map.py && python3 apply_psalm_versification_map.py
python3 build_non_psalm_versification_map.py && python3 apply_non_psalm_versification_map.py
python3 verify_output_alignment.py   # must print "100% MATCH"
```

### Psalms: resolved via a verified chapter/verse map, not address matching

The Synodal Psalter follows the traditional Church-Slavonic/LXX Psalm
numbering (Psalms 9-10 merged, 114-115 merged, 116 split, 147 split, and a
-1 chapter shift through most of the rest), not KJV/Masoretic numbering —
plus most individual Psalms carry an extra title/superscription verse that
Hebrew/Slavonic tradition numbers as verse 1 and KJV does not count
separately. Naive address matching on Psalms therefore doesn't just miss
content, it silently **pairs the wrong Russian verse with a GOI address**
whenever both happen to have a same-numbered chapter/verse — verified
against the first build of this directory, where 1,658 of 1,705
"matched" Psalm flatfiles turned out to have the wrong text.

`build_psalm_versification_map.py` derives the correct chapter/verse
mapping from the documented Hebrew/LXX correspondence table plus exact
verse-count arithmetic (every merge/split total matches exactly), and
`apply_psalm_versification_map.py` applies it, replacing all Psalms
flatfiles. The map covers all 2,461 KJV/GOI Psalm addresses and was
spot-verified against actual verse content at every merge and split
boundary (Psalms 9/10, 114/115, 116, 147) plus a title-shifted chapter —
all 8 checks matched. Full mapping in `psalm_versification_map.csv`.

Rebuild Psalms with:

```
python3 build_psalm_versification_map.py
python3 apply_psalm_versification_map.py
```

## Noun / Strong's tooling readiness

Checked via `Meta_Bible_Data/Bible_Noun_Extraction/language_readiness.py --lang ru`:

- [OK] matcher registered — `RussianMatcher` added to `matchers.py`. Russian
  declines nouns across 6 cases x 2 numbers, so rather than hand-listing
  acceptable forms with no real coverage data to draw from (unlike
  Spanish/Portuguese, which grew their tables from actual
  `verify_coverage.py` runs), it strips a coarse Snowball-style case-ending
  suffix from both the rendering and each output token and compares stems.
  Grow `RussianMatcher._ACCEPTABLE_FORMS` from real MISSING output once
  translation starts, the same way Spanish/Portuguese did.
- [GAP] default renderings for noun Strong's (2,369 used) — none yet
- [GAP] sense renderings (0/17) — none yet
- [GAP] noun positions resolvable (28,889 total) — none yet

The three GAP items are real lexicographic work (Russian glosses per Greek
Strong's number, plus the 17 disambiguation senses) and are not fabricated
here. That work — and the analogous Hebrew-OT noun scaffolding other
languages have (see `Bible_Noun_Extraction/ko/`) — is future work once
translation begins.
