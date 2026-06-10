# OT KJV Versification Audit — 2026-06-08

## Summary
- WLC OT flatfiles: `23213`
- KJV OT flatfiles: `23145`
- Net address delta: `68`
- `WLC_ONLY` addresses: `180`
- `KJV_ONLY` addresses: `112`

## WLC_ONLY Breakdown
- `FILE_NAMING_ANOMALY`: `1`
- `KNOWN_SHIFT_REMAP`: `113`
- `PSALM_SUPERSCRIPTION_OR_OFFSET`: `66`

## KJV_ONLY Breakdown
- `KJV_ONLY_SHIFT_HOLE`: `112`

## Interpretation
- The current `+68` is not evidence of 68 extra content verses.
- The largest bucket is Psalm versification drift, where WLC counts superscriptions/titles into the chapter verse numbering and KJV does not.
- The non-Psalm mismatches are mostly known chapter/verse shift cases, not new content.
- `1KI 23:1` stands out as a flatfile naming anomaly and should be treated separately from ordinary versification drift.

## WLC_ONLY By Book
- `1CH`: `16`
- `1KI`: `15`
- `1SA`: `2`
- `2CH`: `2`
- `2KI`: `1`
- `2SA`: `1`
- `DAN`: `4`
- `DEU`: `3`
- `ECC`: `1`
- `EXO`: `5`
- `EZK`: `5`
- `GEN`: `1`
- `HOS`: `4`
- `ISA`: `1`
- `JER`: `1`
- `JOB`: `8`
- `JOL`: `5`
- `JON`: `1`
- `LEV`: `7`
- `MIC`: `1`
- `NAM`: `1`
- `NEH`: `7`
- `NUM`: `17`
- `PSA`: `66`
- `SNG`: `1`
- `ZEC`: `4`

## KJV_ONLY By Book
- `1CH`: `15`
- `1KI`: `14`
- `1SA`: `1`
- `2CH`: `2`
- `2KI`: `1`
- `2SA`: `1`
- `DAN`: `4`
- `DEU`: `3`
- `ECC`: `1`
- `EXO`: `5`
- `EZK`: `5`
- `GEN`: `1`
- `HOS`: `4`
- `ISA`: `2`
- `JER`: `1`
- `JOB`: `8`
- `JOL`: `5`
- `JON`: `1`
- `LEV`: `7`
- `MIC`: `1`
- `NAM`: `1`
- `NEH`: `8`
- `NUM`: `16`
- `SNG`: `1`
- `ZEC`: `4`

## Next Step
- Use the CSV as the canonical worklist before any physical renaming of `GOI_Bible_English` OT files.
- Resolve Psalm superscriptions as a mapping policy, not as literal extra-content deletions.
- Fix or account for `1KI 23:1` before attempting an automated KJV renumber pass.
