# Language scaffold intake: `fr` / `GOI_Fr`

## Identity and ownership

| Field | Value |
|---|---|
| Status | planned |
| GOI edition ID | `GOI_Fr` |
| BCP-47 tag | `fr` |
| Language name (native / English) | français / French |
| Scope | full Bible |
| Scaffold owner | Claude |
| Language reviewer | unresolved |
| Started | 2026-09-23 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | Louis Segond 1910 (Bible Segond), eBible.org `fraLSG` verse-per-line distribution |
| Source URL | `https://eBible.org/Scriptures/fraLSG_vpl.zip` |
| Retrieved | 2026-09-23 |
| Licence evidence | `https://ebible.org/find/details.php?id=fraLSG` -- "Cette Bible est dans le domaine public. Il n'est pas protégé par copyright. This Bible is in the Public Domain. It is not copyrighted." (page snapshot preserved in `source/`) |
| Jurisdiction and conclusion | Translator Louis Segond died 1885; first edition 1910; eBible explicitly identifies the edition as public domain. |
| Rights status | verified public domain |
| GOI use | comparison, versification and noun-rendering reference only; never copied into GOI output |

## Tracked inventory

| Role | Path | File count | Status |
|---|---|---:|---|
| Raw acquisition | `Reference_Bible/French_Bible_LSG1910/source/` + `SOURCE_MANIFEST.json` | | pending |
| Normalized reference | `Reference_Bible/French_Bible_LSG1910/One_Directory_LSG1910_GOI/` | | pending |
| Alignment ledger | `Reference_Bible/French_Bible_LSG1910/alignment_exceptions.csv` | | pending |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/fr_noun_renderings.csv` | | pending |
| Audit reports | `Meta_Bible_Data/staging/reports/fr/` | | pending |

## GOI coordinate alignment

| Measure | Expected | Observed | Report / commit |
|---|---:|---:|---|
| Full GOI spine | 31,102 | | |
| OT spine | 23,145 | | |
| NT spine | 7,957 | | |
| Declared exceptions | ledger count | | |
| Duplicate GOI coordinates | 0 | | |
| Missing GOI coordinates | 0 | | |

## Source-language noun anchors

| Testament | Source | Occurrences | Distinct Strong's | Rendering coverage | Missing | Duplicate anchors | Report / commit |
|---|---|---:|---:|---:|---:|---:|---|
| NT | Greek TR1550 (`greek_noun.sqlite3`, shared) | | | | | 0 | |
| OT | WLC + MorphHB (`fr/hebrew_ot_fr.sqlite3`) | | | | | 0 | |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-09-23 | Intake | this record created before acquisition | planned | this file | | Claude |

## Release record (complete only when active)

Not applicable: no GOI French translation exists yet.
