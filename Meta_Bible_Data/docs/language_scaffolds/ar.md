# Language scaffold intake: `ar` / `GOI_Ar`

## Identity and ownership

| Field | Value |
|---|---|
| Status | scaffolded; Gospel machine draft failed noun-coverage gate |
| GOI edition ID | `GOI_Ar` |
| BCP-47 tag | `ar` |
| Language name (native / English) | العربية / Arabic |
| Scope | full Bible (reference scaffold only) |
| Scaffold owner | Codex |
| Language reviewer | unresolved |
| Started | 2026-09-16 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | Arabic Van Dyck Bible / Syrian Mission / 1865 |
| Source URL | `https://eBible.org/Scriptures/arb-vd_usfm.zip` |
| Retrieved | 2026-09-16 |
| Licence evidence | `https://ftp.ebible.org/details.php?id=arb-vd` |
| Jurisdiction and conclusion | eBible explicitly identifies this edition as public domain; preserved for comparison reference only. |
| Rights status | verified public domain |
| GOI use | comparison and noun-rendering reference only |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/Arabic_Bible_VanDyck1865/source/` | 1 | preserved byte-for-byte |
| Normalized reference | `Reference_Bible/Arabic_Bible_VanDyck1865/One_Directory_VanDyck1865_GOI/` | 31,102 | GOI/KJV-coordinate aligned |
| Alignment ledger | `Reference_Bible/Arabic_Bible_VanDyck1865/alignment_exceptions.csv` | 4 rows | verified |
| Source noun anchors | `Meta_Bible_Data/Bible_Noun_Extraction/ar/source_anchor_occurrences/` | 173,844 occurrences | source-language anchors complete |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/ar_noun_renderings.csv` | header only | canonical review ledger not started |
| Rejected Gospel draft | `GOI_Bible/GOI_Bible_ar/` | 3,779 uncommitted files | structural draft only; blocked from release |
| Audit reports | `Meta_Bible_Data/staging/reports/ar/` | 4 | scaffold-only |

## GOI coordinate alignment

| Measure | Expected | Observed |
|---|---:|---:|
| Full GOI spine | 31,102 | 31,102 |
| OT spine | 23,145 | 23,145 |
| NT spine | 7,957 | 7,957 |
| Exact reference alignments | 31,100 | 31,100 |
| Declared exceptions | 4 source rows | 4 |
| Duplicate GOI coordinates | 0 | 0 |
| Missing GOI coordinates | 0 | 0 |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-16 | Source/alignment | `normalize_vandyck1865.py` | pass | source manifest, alignment ledger, readiness report | pending | Codex |
| 2026-09-16 | Strong's source anchors | `build_ar_source_noun_anchors.py` and `verify_ar_noun_scaffold.py` | pass (renderings pending) | `Meta_Bible_Data/Bible_Noun_Extraction/ar/source_anchor_occurrences/` | pending | Codex |
| 2026-09-18 | Gospel structural draft | sequential DeepSeek/Flex rendering, MAT/MRK/LUK/JHN | pass: 3,779/3,779 coordinates; no blank/duplicate/foreign-script files | uncommitted `GOI_Bible/GOI_Bible_ar/` | none | Codex |
| 2026-09-18 | Gospel noun/Strong's coverage | `verify_coverage.py --lang ar --book MAT --book MRK --book LUK --book JHN` | **fail: 4,131/12,021 (34.4%)** | rejected draft; recovery plan | none | Codex |
| 2026-09-18 | Automated noun repair | strict dictionary-form Arabic matcher | **stopped**: rejected valid inflected forms such as `أخ` → `إخوته`; no release claim | system journal + `/tmp/goi-arabic-gospels-noun-repair.log` | none | Codex |

## Release record

Not applicable: Arabic has no approved GOI translation, database, or deployed
edition. The 2026-09-18 Gospel files are an uncommitted failed draft and must
not be promoted, packaged, or used as an active edition.
