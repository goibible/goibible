# Korean Old Testament Scaffold

The Korean OT will be translated directly from the Hebrew WLC source, using
the KJV coordinate spine. The Korean 1911 edition is a verification reference;
the Chinese CUV is reserved for the 111 Korean-reference gap coordinates.

Translation is intentionally gated per book until `hebrew_ot.sqlite3` contains
the WLC verses, MorphHB Hebrew noun occurrences, and Korean Strong's renderings.

Completed Torah stage:

- Genesis: 1,533 verses
- Exodus: 1,213 verses
- Leviticus: 859 verses
- Numbers: 1,288 verses
- Deuteronomy: 959 verses
- Total: 5,852 verses

Full OT scaffold:

- 39 canonical KJV/WLC book codes
- 23,145 Hebrew source verses
- MorphHB noun positions linked to Hebrew Strong's numbers
- Korean 1911 reference with Chinese CUV fallback exceptions
- Per-book readiness gates, resumable translation, noun verification, and QA

Run
`verify_ko_ot_scaffold.py` before translation and `qa_ko_ot.py` only after all
39 books have output. The 74 exact-spine coordinates absent from Korean 1911
are recorded in `ot_alignment_exceptions`; all have Chinese CUV fallback files.

Output files use the existing format, for example:
`001_GEN_001_001_GOI_Ko.txt`.
