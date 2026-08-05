# O LORD / O God vocative review — GOI English

**Date:** 2026-07-09
**Scope:** All KJV OT verses containing "O LORD"/"O God"/"O Lord GOD"/"Oh Lord"/"Oh God"
where the corresponding GOI_En verse does not already contain an equivalent
vocative marker (`O Lord`, `O God`, `O the Lord`, `O Jehovah`, `O my Lord`,
`O my God`). SQL query and full row-by-row trail: `o_lord.csv` (repo root).

**Authority used:**
- WLC (Hebrew) — authority for correctness (is this actually a vocative address in the source?).
- KJV — authority for English idiom only (how English conventionally renders it), not for meaning.

## Result

144 candidate verses reviewed, 20 at a time, decision + reason + final edited
text recorded per verse in `o_lord.csv`.

- **101 no_edit** — mostly SQL false positives (substring matches like "to God" inside
  "pertaining to God", "do God" inside oath formulas "thus may God do...", "no gods"),
  3rd-person narrative/oath-formula uses of "God"/"the LORD" that were never vocative,
  and verses where GOI already renders the address validly (bare name, "my Lord",
  or a pronoun-immediately-adjacent-to-title apposition) without the literal word "O".
- **43 edit** — applied to `GOI_Bible_English/*.txt`, `sqlite/versions/GOI_En.sql`,
  and `GOI_bible.sqlite3` (`GOI_En` edition). Categories:
  - Flat "the LORD"/"the God" reading as a 3rd-person description where WLC/KJV
    intend direct 2nd-person address, with no adjacent pronoun to rescue it.
  - A recurring literal `(my)` / `(gods)` / bracketed placeholder artifact left
    unresolved in the GOI text (a data-corruption bug independent of style) —
    appeared ~10 times across the dataset (e.g. Deut 3:24, Amos 7:5, Jer 32:25,
    Isa 38:16, Psa 51:15, 79:12, 86:3, 109:21, 140:7).
  - Genuine person/mood mismatches: GOI shifts between 3rd- and 2nd-person for
    the same referent mid-verse, or turns a 2nd-person imperative/petition into
    a 3rd-person declarative (e.g. Psa 108:5, 125:4, 139:19, 119:57/64/89/108).

### Verses edited (43)

1CH 17:19, 1CH 29:16, 1SA 23:11, 2CH 20:6, 2SA 7:28, AMO 7:5, DAN 9:15, DAN 9:19,
DEU 3:24, ISA 38:16, ISA 63:17, JER 11:5, JER 11:20, JER 15:16, JER 16:19,
JER 20:12, JER 32:25, JER 51:62, NEH 1:5, PSA 5:3, PSA 25:4, PSA 25:7, PSA 26:6,
PSA 30:3, PSA 51:15, PSA 55:9, PSA 58:6, PSA 70:1, PSA 71:17, PSA 77:13,
PSA 79:12, PSA 84:12, PSA 86:3, PSA 89:15, PSA 108:5, PSA 109:21, PSA 119:57,
PSA 119:64, PSA 119:89, PSA 119:108, PSA 125:4, PSA 139:19, PSA 140:7

## Where the fix landed

Applied identically, verified row-for-row before writing, to all three copies
of the GOI English edition:
1. `GOI_Bible_English/<NNN>_<BOOK>_<CCC>_<VVV>_GOI_En.txt` (43 flatfiles)
2. `sqlite/versions/GOI_En.sql` (the git-trackable import file)
3. `GOI_bible.sqlite3` (`verses` table, `edition_id='GOI_En'`)

Backups taken before writing (local, gitignored, not committed):
`GOI_bible.sqlite3.bak-o_lord_edit_20260709_220011`,
`sqlite/versions/GOI_En.sql.bak-o_lord_edit_20260709_220011`,
`GOI_Bible_English.bak-o_lord_edit_20260709_220011.tar.gz`.

## Related: sqlite binary-to-text migration finished

Same session: verified `sqlite/assemble.sh` reproduces `GOI_bible.sqlite3`
row-for-row (all tables) from `sqlite/schema.sql` + `reference_seed.sql` +
`versions/*.sql`, then stopped tracking the compiled `GOI_bible.sqlite3`,
`sqlite/shell.sqlite3`, and a stale pre-WLC-removal `.sqlite3` backup in git
(added to `.gitignore`; rebuild locally instead of committing binaries).
Unrelated binaries elsewhere in the repo (`archive/`, `backup/`,
`greek_noun.sqlite3`) were left untouched — out of scope, no matching
buffet/rebuild system verified for them.

Committed as: "Restore O LORD/O God vocatives dropped in GOI English; stop
tracking compiled sqlite3 binaries".
