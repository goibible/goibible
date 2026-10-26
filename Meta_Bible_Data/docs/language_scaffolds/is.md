# Language scaffold intake: `is` / `GOI_Is`

## Identity and ownership

| Field | Value |
|---|---|
| Status | NT 7,957/7,957 drafted (Claude, no native review); OT lexicon + 463 batches ready, pilot ot_001 only; 1912 OCR aligned to the spine as reference |
| GOI edition ID | `GOI_Is` (registered, status pending) |
| BCP-47 tag | `is` |
| Language name (native / English) | íslenska / Icelandic |
| Scope | full Bible |
| Scaffold owner | Claude (owner ruling 2026-10-11) |
| Language reviewer | unresolved |
| Started | 2026-10-09 |

## Reference edition and rights

| Field | Value |
|---|---|
| Edition / publisher / publication year | *Biblía, það er Heilög Ritning: ný þýðing úr frummálunum*, British and Foreign Bible Society, 1912 revision |
| Source URL or permanent archive ID | `https://baekur.is/bok/2216a541-26e3-4616-a87b-0255066ca04c/Biblia` |
| Retrieved | 2026-10-09 |
| Licence or public-domain evidence URL | `https://krans.is/app/um/` identifies Biblían 1912 as public domain |
| Jurisdiction and conclusion | Historical 1912 translation, publicly identified as public domain; title page in the acquired archive reads 1912. |
| Rights status | public domain |
| GOI use | historical comparison only; WLC and TR1550 remain definitive |

This is the **1912** printing, not the 1908 printing or the 1914 revision. The acquired digital copy is page OCR, not a verified verse transcription. Do not use a later edition's verse text to fill OCR gaps.

## Tracked inventory

| Role | Path | File count | Bytes | SHA-256 manifest | Status |
|---|---|---:|---:|---|---|
| Raw acquisition | `Reference_Bible/Icelandic_Bible_B20A1912/source/` | 2 | see manifest | `Reference_Bible/Icelandic_Bible_B20A1912/SOURCE_MANIFEST.json` | catalog HTML and 1,318-page OCR ZIP preserved |
| OCR archive audit | `Reference_Bible/Icelandic_Bible_B20A1912/ocr_archive_audit.json` | 1 | see file | source hashes checked | page sequence complete; verse completeness unverified |
| Normalized reference | `Reference_Bible/Icelandic_Bible_B20A1912/OCR_to_txt/parsed_ot/` | 1 | see file | none | OT only, 22,961 of 23,145 matched by banded LCS; machine candidates, reference only |
| Alignment ledger | unresolved | 0 | 0 | none | not started |
| Target rendering ledger | unresolved | 0 | 0 | none | not started |
| Audit reports | unresolved | 0 | 0 | none | not started |

## GOI coordinate alignment

| Measure | Expected | Observed | Report / commit |
|---|---:|---:|---|
| Full GOI spine | 31,102 | not measured | OCR has no trustworthy verse boundaries |
| OT spine | 23,145 | not measured | |
| NT spine | 7,957 | not measured | |
| Exact reference alignments | unresolved | not measured | |
| Declared exceptions | 0 or ledger count | not measured | |
| Duplicate GOI coordinates | 0 | not measured | |
| Missing GOI coordinates | 0 or declared partial scope | not measured | |

## Source-language noun anchors

| Testament | Source | Occurrences | Distinct Strong's | Rendering coverage | Missing | Duplicate anchors | Report / commit |
|---|---|---:|---:|---:|---:|---:|---|
| NT | Greek TR1550 | 28,889 | see verify_language | 100% (824 hand-reviewed synonyms/compounds, 2 text fixes) | 0 | 0 | `python3 -I verify_language.py --lang is` |
| OT | WLC + MorphHB | 144,955 | 6,333 | renderings for all lemmas (machine draft, needs_review); no OT text yet | n/a | 0 | `is/hebrew_ot_is.sqlite3` |

## Gate history (append only)

| Date | Gate | Command / method | Result | Evidence path | Commit | Reviewer |
|---|---|---|---|---|---|---|
| 2026-10-09 | Reference discovery | Find a Bible record and Icelandic Bible Society history | 1908 public-domain candidate identified; acquisition pending | links above | | |
| 2026-10-09 | Text availability | Internet Archive item `ISLCE_DBS_HS` metadata and OCR sample | Full-book `Icelandic-(1908)-Bible_djvu.txt` exists (4,755,047 bytes); title page confirms 1908; OCR has verse-number and line-break errors, so it is not a clean verse dataset | `https://archive.org/download/ISLCE_DBS_HS/Icelandic-%281908%29-Bible_djvu.txt` | | |
| 2026-10-09 | Edition change | owner: skip 1908 and obtain the 1912 revision | 1912 selected | this record | | owner |
| 2026-10-09 | Acquisition | Bækur.is full-book text ZIP | 1,318 sequential page OCR files; 1912 on title page | `Reference_Bible/Icelandic_Bible_B20A1912/SOURCE_MANIFEST.json` | | |
| 2026-10-09 | Page continuity | `python3 Reference_Bible/Icelandic_Bible_B20A1912/audit_ocr_archive.py` | pass for 1,318-page sequence; OCR verse completeness not established | `Reference_Bible/Icelandic_Bible_B20A1912/ocr_archive_audit.json` | | |
| 2026-10-24 | NT draft | translated from TR1550, spine OK 7,957 | 0 hard validator problems | `is/translation/` | ab5a8499d4 | |
| 2026-10-24 | Plural/sense review | 397 plural candidates, 97 senses | 8 fixes, rest closed | `is/translation/text_fixes.tsv` | | |
| 2026-10-26 | Scaffold completion | OT table, grammar OT import, plural verdicts, NT coverage verdicts, matcher compound head | see verify_language | `is/README.md` | | |

## Release record (complete only when active)

| Item | Value |
|---|---|
| GOI flatfile verifier result | not started |
| Flatfile-to-download-DB diff | not started |
| Manifest checksum and verse count | not started |
| Reader DB query and hash | not started |
| Remote rollback ID | not started |
| Git release commit | not started |
