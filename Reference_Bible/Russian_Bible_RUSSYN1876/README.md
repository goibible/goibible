# Russian Synodal Bible (RUSSYN)

This directory preserves the public-domain Russian reference text used for a
future GOI Russian translation pipeline.

- Edition: Russian Synodal Bible (Синодальный перевод), catalog identifier `RUSSYN`
- Language: Russian (`ru`)
- Rights: Public Domain, per eBible.org's Find a Bible record
- Source record: https://ebible.org/find/details.php?id=russyn
- Downloaded source: `source/russyn_vpl.zip` (verse-per-line export)
- SHA-256: `1ac0035cbcbdfcd07a89d50c5e11e87822a74c61b85c18a892278ce4cd4b09a8`

## Versification: this is a mapping project, not a missing-content problem

Russian is a complete 66-book corpus (31,169 verse markers, no duplicates),
but it is **not** drop-in GOI-aligned the way Arabic is. Comparing raw
(book, chapter, verse) addresses against the GOI/KJV spine (31,102
addresses) originally found 784 GOI addresses absent and 851 Russian-only
addresses, 756/821 of them in Psalms. Psalms is now resolved (see below);
the rest is a small residual scattered across Job, Daniel, Song of Songs,
Romans, Samuel, Joshua, Proverbs, and a handful of others (28 absent / 30
Russian-only addresses, per the current `alignment_report.json`).

`atomize_russian_synodal.py` parses the eBible verse-per-line export, maps
its book codes onto this project's KJV spine codes (`1JO`->`1JN`, `EZE`->`EZK`,
`JAM`->`JAS`, `JOE`->`JOL`, `JOH`->`JHN`, `MAR`->`MRK`, `NAH`->`NAM`,
`PHI`->`PHP`, `SOL`->`SNG`, `2JO`->`2JN`, `3JO`->`3JN`), and writes every verse
whose address matches the spine exactly into `One_Directory_RUSSYN1876/`.
**It deliberately excludes PSA entirely** — see below. Everything else is
recorded, per-book and by full address, in `alignment_report.json`; that's
the input for resolving the small remaining non-Psalm gap the same way
Psalms was resolved, not something this script guesses at.

Rerun with:

```
python3 atomize_russian_synodal.py --write
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
all 8 checks matched. Full mapping in `psalm_versification_map.csv`
(status `proposed`: structurally exhaustive and boundary-verified, not yet
verse-by-verse content-checked across all 2,461 addresses).

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
