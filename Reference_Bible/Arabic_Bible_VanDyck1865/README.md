# Arabic Van Dyck Bible (1865) reference scaffold

This directory preserves the public-domain Arabic Van Dyck Bible as a
comparison and noun-rendering reference for planned `GOI_Ar`. It is never a
GOI translation input or a replacement for the canonical GOI flatfiles.

## Preserved source and reproduction

- Raw source: `source/arb-vd_usfm.zip`, downloaded from eBible on 2026-09-16.
- Provenance and SHA-256: `SOURCE_MANIFEST.json`.
- Normalizer: `normalize_vandyck1865.py`.
- Normalized output: `One_Directory_VanDyck1865_GOI/`.

Run from the repository root:

```bash
python3 Reference_Bible/Arabic_Bible_VanDyck1865/normalize_vandyck1865.py
python3 Reference_Bible/Arabic_Bible_VanDyck1865/normalize_vandyck1865.py --check
```

The source has 66 books and 31,104 verse markers. The normalizer produces the
31,102-coordinate GOI/KJV spine by merging only `1TI 6:21–22` and `3JN
1:14–15`, as recorded in `alignment_exceptions.csv`. The raw archive remains
unchanged.

No GOI Arabic verse files, noun claims, database, or publication artifacts are
created by this scaffold.
