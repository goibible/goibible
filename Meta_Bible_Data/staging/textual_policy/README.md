# NT Textual Policy

This directory records language-neutral textual decisions for GOI Bible translation.
It applies to every language edition unless a later project decision explicitly
changes a row.

Bracket convention:

- `[]` = conflicted ancient reading; early evidence exists on both sides.
- `{}` = supplemental traditional material; preserved in the TR/church tradition
  but not the earliest-mainline text.
- No brackets = translate the preferred source reading as normal.

TR1550 remains the verse spine and the default Greek witness. When older reliable
manuscript evidence is clearly stronger and the meaning changes, the row in
`nt_textual_policy.csv` governs translation and display.

Current rule examples:

- `ROM 12:11` uses "serving the Lord" with no brackets.
- `MRK 16:9-20` is retained with `{}`.
- `LUK 22:43-44` is retained with `[]`.
- `1JN 5:7-8` follows the shorter early text in the main translation.
- `GAL 3:1` follows the shorter critical text without the TR/KJV phrase about
  obeying the truth.
- `REV 1:11` follows the shorter critical text without the TR/KJV Alpha and
  Omega phrase in this verse.

## Closed Source-Name Suppressions

These rows are intentionally excluded from source-name audit debt. They are not
translation misses.

| Audit ref | Strong's | Closure type | Decision |
|---|---|---|---|
| `ACT 4:6` | `G2419` Jerusalem | Verse-boundary closure | Jerusalem is present in `ACT 4:5`; do not add it to `ACT 4:6`. |
| `ACT 9:29` | `G2424` Jesus | Verse-boundary closure | Lord Jesus is present in `ACT 9:28`; do not duplicate it in `ACT 9:29`. |
| `ACT 9:29` | `G2962` Lord | Verse-boundary closure | Lord Jesus is present in `ACT 9:28`; do not duplicate it in `ACT 9:29`. |
| `ACT 13:33` | `G2316` God | Verse-boundary closure | God/Jesus clause is present in `ACT 13:32`; do not duplicate it in `ACT 13:33`. |
| `ACT 13:33` | `G2424` Jesus | Verse-boundary closure | God/Jesus clause is present in `ACT 13:32`; do not duplicate it in `ACT 13:33`. |
| `1TI 3:16` | `G2316` God | Textual-policy closure | Use the older critical reading, "He who was revealed in flesh," not TR "God was revealed." |
| `1JN 5:7` | `G4151` Spirit | Textual-policy closure | Use the shorter early text; Spirit is translated in `1JN 5:8`. |
