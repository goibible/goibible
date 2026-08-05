# Biblical Source Name Database

This database is the canonical source-name layer. It is built from source-language texts only:

- OT: WLC/MorphHB Hebrew, keyed by Hebrew Strong's numbers.
- NT: TR1550 parsed Greek by default, keyed by Greek Strong's numbers.

Translation references such as VIE1934 are not used to create canonical entities. They should map language forms onto these source entities later.

Documented critical-reading overrides are allowed when the earlier/stronger manuscript evidence is clearly preferable to the local TR1550 reading. Current override:

- `ROM 12:11`: use `κυρίῳ` / `G2962` / Lord instead of TR1550 `καιρῷ` / time.

## Database

- `biblical_source_names.sqlite3`

Main tables:

- `source_name_entities`: one canonical source entity per testament/source Strong's key.
- `source_name_occurrences`: one row per contextual verse occurrence, including source form, morphology, Strong's number, book/chapter/verse, and source file.
- `source_verse_references`: one row per raw source verse reference, including MorphHB `KJV:` notes when present so GOI/KJV-aligned editions can map source occurrences to the correct display verse.
- `source_name_links`: dictionary links, especially Greek NT names that point back to Hebrew Strong's entries.

## Current Baseline

Fresh build:

- OT Hebrew entities: 2,414
- OT Hebrew occurrences: 36,972
- OT MorphHB raw verse references: 23,213
- OT MorphHB refs with explicit `KJV:` mapped note: 2,026
- NT Greek entities: 266
- NT Greek occurrences: 5,350
- Greek-to-Hebrew dictionary links: 266

Breakdown:

- OT names of God: 8 entities, 10,179 occurrences.
- OT proper names: 2,406 entities, 26,793 occurrences.
- NT names of God: 5 entities, 3,590 occurrences.
- NT proper names: 261 entities, 1,760 occurrences.

## Build

```bash
python3 scripts/build_source_name_db.py --rebuild
```

This is stronger than noun count because it preserves lexical identity, source morphology, Strong's context, verse references, and cross-testament dictionary links.

For OT work, use `source_verse_references` before judging verse-level misses. Raw MorphHB/WLC verse IDs are not always the same as the GOI/KJV verse spine; Psalms superscriptions and several chapter-boundary notes are explicit examples. The source-name audit consumes these mapped notes so every language inherits the same source-reference cleanup.

## Current GOI English Audit Buckets

After the closed NT textual-policy and verse-boundary suppressions, the active source-name audit queue is clean:

- Active audit rows: 0
- Unique `ref + Strong's` targets: 0
- Closed NT textual/boundary suppressions: 7

Detailed bucket counts are tracked in `staging/source_names/goi_en_bucket_counts.md`.
The closed suppression decisions are documented in `staging/textual_policy/README.md`.
