# Language scaffold intake: `<lang>` / `GOI_<ID>`

Copy this file to `Meta_Bible_Data/docs/language_scaffolds/<lang>.md` before
acquiring or transforming text. Replace every bracketed value; do not remove
a section that is not yet known—mark it `unresolved` and record who owns it.

## Identity and ownership

| Field | Value |
|---|---|
| Status | planned / scaffolded / translating / audit / active |
| GOI edition ID | `GOI_<ID>` |
| BCP-47 tag | `<lang>` |
| Language name (native / English) | `<native>` / `<English>` |
| Scope | OT / NT / full Bible |
| Scaffold owner | `<name>` |
| Language reviewer | `<name>` |
| Started | `YYYY-MM-DD` |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | `<value>` |
| Source URL or permanent archive ID | `<url>` |
| Retrieved | `YYYY-MM-DD` |
| Licence or public-domain evidence URL | `<url>` |
| Jurisdiction and conclusion | `<value>` |
| Rights status | verified public domain / licensed / unresolved |
| GOI use | comparison only / permitted translation input |

Do not import or publish source text while rights status is unresolved.

## Tracked inventory

| Role | Path | File count | Bytes | SHA-256 manifest | Status |
|---|---|---:|---:|---|---|
| Raw acquisition | `Reference_Bible/.../source/` + `SOURCE_MANIFEST.json` | | | | |
| Normalized reference | `Reference_Bible/.../One_Directory_..._GOI/` | | | | |
| Alignment ledger | `Reference_Bible/.../alignment_exceptions.csv` | | | | |
| Target rendering ledger | `Meta_Bible_Data/Bible_Noun_Extraction/<lang>_noun_renderings.csv` | | | | |
| Audit reports | `Meta_Bible_Data/staging/reports/<lang>/` | | | | |

## GOI coordinate alignment

| Measure | Expected | Observed | Report / commit |
|---|---:|---:|---|
| Full GOI spine | 31,102 | | |
| OT spine | 23,145 | | |
| NT spine | 7,957 | | |
| Exact reference alignments | | | |
| Declared exceptions | 0 or ledger count | | |
| Duplicate GOI coordinates | 0 | | |
| Missing GOI coordinates | 0 or declared partial scope | | |

## Source-language noun anchors

| Testament | Source | Occurrences | Distinct Strong's | Rendering coverage | Missing | Duplicate anchors | Report / commit |
|---|---|---:|---:|---:|---:|---:|---|
| NT | Greek TR1550 | | | | | 0 | |
| OT | WLC + MorphHB | | | | | 0 | |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| | | | | | | |

## Release record (complete only when active)

| Item | Value |
|---|---|
| GOI flatfile verifier result | |
| Flatfile-to-download-DB diff | |
| Manifest checksum and verse count | |
| Reader DB query and hash | |
| Remote rollback ID | |
| Git release commit | |
