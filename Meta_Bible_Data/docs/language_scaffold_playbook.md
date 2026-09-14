# Language Scaffold Playbook

This is the required intake and audit contract for every new GOI language.
It exists to prevent a useful reference, alignment scaffold, or noun-analysis
asset from being replaced with an empty file, silently regenerated from a
different source, or deleted as "temporary" work.

## Non-negotiable rules

1. The canonical translation is the verse flatfile under `GOI_Bible/`. A
   database, report, export, or application cache is derived and must never be
   treated as its replacement.
2. A source Bible is not accepted merely because it is described as public
   domain. Record the publisher/source URL, retrieval date, exact edition,
   jurisdiction and the licence or public-domain evidence in its source
   manifest. If this cannot be established, label it **licence unresolved**;
   it may be consulted privately but cannot be committed or distributed.
3. Source text, normalized one-verse reference files, scripts, schemas,
   manifests, alignments, exception ledgers, and human-review reports are
   valuable scaffolding. They are tracked in Git. A local SQLite database is
   never the only copy of any of that information.
4. No command may delete, truncate, replace, or bulk-regenerate a scaffold
   until its manifest has been checked, its current hashes recorded, and the
   proposed replacement has passed the same count/hash/size checks. An empty
   file is a failure, never a valid replacement for text or a report.
5. Do not use `rm -rf`, blanket directory replacement, or a forceful Git
   checkout/reset in a language scaffold or reference directory. Removal needs
   a dedicated commit listing every path, the reason, a recoverable Git object
   or backup, and explicit approval.

## Required tracked layout

Use lower-case BCP-47 language subtags and a stable GOI edition ID. Substitute
`<lang>`, `<Language>`, `<ReferenceEdition>`, and `<GOI_ID>` below.

```
GOI_Bible/GOI_Bible_<lang>/
  README.md                                  # status, policy, counts, sources
  <NNN>_<BOOK>_<CCC>_<VVV>_<GOI_ID>.txt     # canonical GOI verses

Reference_Bible/<Language>_Bible_<ReferenceEdition>/
  README.md                                  # provenance and normalisation rules
  SOURCE_MANIFEST.json                       # machine-verified licence evidence, hashes, inventory
  source/                                    # preserved acquisition files; never edited
  One_Directory_<ReferenceEdition>_GOI/      # one normalized reference verse per file
  alignment_exceptions.csv                   # every non-exact coordinate, never implicit

Meta_Bible_Data/Bible_Noun_Extraction/
  <lang>_nt_noun_schema.sql                  # source-controlled schema, if language-specific
  <lang>_ot_noun_schema.sql
  build_<lang>_nt_nouns.py
  build_<lang>_ot_nouns.py
  verify_<lang>_nt_scaffold.py
  verify_<lang>_ot_scaffold.py
  verify_<lang>_noun_coverage.py
  <lang>_noun_renderings.csv                 # reviewable Strong's-to-rendering dictionary

Meta_Bible_Data/staging/reports/<lang>/
  README.md                                  # report index and current release state
  scaffold_readiness.md                      # dated gate results
  alignment_summary.csv
  noun_coverage_summary.csv
  audits/                                    # dated, committed review findings

Meta_Bible_Data/docs/language_scaffolds/
  <lang>.md                                  # completed intake record from the template
```

`source/` preserves the acquired source byte-for-byte. The normalized
`One_Directory_*` directory is an analysis convenience, not a substitute for
the raw acquisition. It must be reproducible from `source/` by a tracked
normalizer or by documented manual steps. Any large source that cannot be
committed must instead have a permanent, versioned archival location, a
cryptographic hash, acquisition instructions, and an explicit reason in
`SOURCE_MANIFEST.md`; do not leave the only copy in an ignored directory.

## Intake sequence

### 1. Choose and record the edition before importing text

Create `Meta_Bible_Data/docs/language_scaffolds/<lang>.md` from
`language_scaffold_intake_template.md`. Give it the target BCP-47 tag,
`GOI_<...>` edition ID, native language name, translator/reviewer ownership,
and a status of `planned`.

Record the reference edition's title, publication/version, source URL,
acquisition date, licence/public-domain evidence, and its intended role:
comparison reference only, word-level noun rendering reference, or permitted
translation input. A reference edition is never copied into GOI output.

### 2. Preserve source and prove its integrity

Commit raw acquisition files below `Reference_Bible/.../source/`, then make a
  `SOURCE_MANIFEST.json` containing for every file: relative path, byte size,
   SHA-256, source URL, retrieval date, and whether it is raw or normalized.
   Check that all text
and report files have a non-zero byte size. Record the normalizer command and
its input/output hashes. The first commit should contain only the reference
source, provenance files, and normalizer; this creates a clean recovery point.

### 3. Establish the GOI/KJV coordinate spine

GOI uses the KJV coordinate system and filename pattern
`<NNN>_<BOOK>_<CCC>_<VVV>_<GOI_ID>.txt`. The expected full-Bible spine is
31,102 verses: 23,145 OT and 7,957 NT.

Normalize the reference edition into one file per reference verse without
changing its text meaning. Produce an alignment table with, at minimum:

```
goi_ordinal,book,chapter,verse,reference_book,reference_chapter,reference_verse,
relation,reason,reviewer,status
```

`relation` is one of `exact`, `split`, `merged`, `missing`, `extra`, or
`fallback`. Every coordinate not `exact` must appear in
`alignment_exceptions.csv` and have a written resolution. Do not conceal a
versification difference by shifting later verses. The readiness report must
show both (a) every GOI coordinate accounted for and (b) no duplicate target
coordinate. A partial OT or NT must declare its expected subtotal and covered
book list instead of claiming full-Bible coverage.

### 4. Build source-language Strong's scaffolding

The noun comparison is anchored in Biblical source languages, not inferred
solely from the target-language reference Bible.

For the NT, retain Greek TR1550 word occurrences with stable verse and word
position, morphology/part of speech, lemma, Strong's number, and proper-name
flag. For the OT, retain WLC/MorphHB Hebrew occurrences with the same fields
and Hebrew Strong's links. Keep source schemas and import/build scripts under
`Meta_Bible_Data/Bible_Noun_Extraction/`; a local `*.sqlite3` is a rebuildable
cache only. Export the language-specific decisions to a tracked CSV:

```
testament,strongs_num,lemma,source_gloss,target_rendering,alternates,
part_of_speech,decision,reviewer,reviewed_on,notes
```

The verifier must report: source noun occurrence count; distinct Strong's
numbers; occurrence count with a target rendering; missing renderings;
duplicate `(book, chapter, verse, word_position)` anchors; and counts per
book. A source noun may map to a multiword target expression, a grammatical
change, or an intentionally implicit rendering, but every such case requires
a ledger entry and human review; it cannot disappear silently.

### 5. Create, translate, and audit GOI flatfiles

Create only the coordinates that passed the relevant readiness gate. Each GOI
file is UTF-8, contains substantive non-whitespace text, and bears the exact
GOI filename/coordinate. Keep an append-only dated change log in
`Meta_Bible_Data/staging/reports/<lang>/audits/` with the coordinate, issue,
old/new text hashes (not necessarily full prose), reason, reviewer, and
source references.

Before a book is marked complete, run and save:

- exact verse-spine count and duplicate/missing-coordinate check;
- reference-alignment and exception-ledger check;
- source noun/Strong's coverage check;
- target-language structural checks (empty, duplicated, malformed, or
  accidentally concatenated verses);
- native-language or qualified human review for semantic and idiomatic
  correctness.

### 6. Release only after the source audit is complete

After the flatfiles and reports are committed, build the SQL version, shell,
downloadable database, manifest, aggregate DB, and reader DB in the order in
`Meta_Bible_Data/docs/inventory.md`. Diff the released database verses against
the canonical flatfiles, verify the manifest count/checksum/status, commit
the generated tracked artifacts, then deploy the reader DB with the documented
remote rollback copy. Preserve the readiness report and release verification
in the same commit or an immediately following, explicitly linked commit.

## Required gates and audit trail

| Gate | Required evidence | Blocks |
|---|---|---|
| Provenance | Source manifest; licence/public-domain evidence; raw hashes | committing/distributing reference text |
| Preservation | Non-zero-size inventory; raw and normalized hashes; normalizer record | replacing or regenerating scaffold files |
| Alignment | 31,102 or declared partial count; no duplicate coordinates; exception ledger | translation and DB build |
| Strong's | Source occurrence table; renderings CSV; missing/duplicate report | "noun coverage" claims |
| Translation | Flatfile count; structural report; semantic review log | language activation |
| Release | Flatfile-to-DB diff; manifest checksum; reader DB query; deployment rollback ID | GitHub/live publication |

Every gate result is dated and committed. Run
`tools/translation_pipeline/verify_scaffold_manifests.py` to validate every
machine-readable source manifest. A pass must name the command,
inputs, counts, commit ID, and output report path. A failure remains recorded;
do not overwrite it with a later pass.

## Safe change protocol

1. Inspect the existing manifest, `git status`, sizes, hashes, and coordinate
   count before editing.
2. Add new material alongside existing material; never repurpose an existing
   source path for a different edition.
3. Validate the candidate output in a new path or temporary ignored workspace.
4. Compare candidate versus current inventory. Reject zero-byte files, an
   unexplained file-count decrease, an unexplained hash change, or a missing
   alignment/Strong's row.
5. Commit source/scaffold changes separately from GOI translation changes and
   separately from derived database releases. The commit message must state
   whether files were added, changed, or intentionally retired.
6. Push only after `git diff --check`, the relevant verifier, and the
   manifest checks pass. Never force-push this repository to repair a
   scaffold mistake; restore the known-good tracked object in a new commit.

## Current examples

- Korean: `GOI_Bible/GOI_Bible_ko/OT_README.md` and the `hebrew_ot_*` tools
  demonstrate a full WLC/MorphHB OT gate.
- Japanese: `GOI_Bible/GOI_Bible_ja/README.md` documents a public-domain
  reference and declared OT coverage gaps.
- Chinese: `Meta_Bible_Data/staging/reports/zh/` retains audit artifacts;
  its canonical output remains the two Chinese GOI flatfile directories.

Existing scaffolds should be migrated to this contract incrementally. Do not
delete or replace them merely to make their layout match the template.
