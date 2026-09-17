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
addresses):

- 784 GOI addresses are absent from the Russian source
- 851 Russian addresses don't exist on the GOI spine
- 756 of the 784 absent / 821 of the 851 Russian-only are in Psalms
  (the Synodal tradition follows a different Psalm division/numbering in
  places); the rest is scattered across Job, Daniel, Song of Songs, Romans,
  Samuel, Joshua, Proverbs, and a handful of others.

`atomize_russian_synodal.py` parses the eBible verse-per-line export, maps
its book codes onto this project's KJV spine codes (`1JO`->`1JN`, `EZE`->`EZK`,
`JAM`->`JAS`, `JOE`->`JOL`, `JOH`->`JHN`, `MAR`->`MRK`, `NAH`->`NAM`,
`PHI`->`PHP`, `SOL`->`SNG`, `2JO`->`2JN`, `3JO`->`3JN`), and writes only the
30,318 verses whose address matches the spine exactly into
`One_Directory_RUSSYN1876/`. Everything else is recorded, per-book and by
full address, in `alignment_report.json` — that report is the input to a
future hand-built Russian->GOI versification map (chiefly a Psalm
renumbering table); this script does not guess at one.

Rerun with:

```
python3 atomize_russian_synodal.py --write
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
