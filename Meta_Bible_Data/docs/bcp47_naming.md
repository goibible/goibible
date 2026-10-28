# BCP 47 naming for GOI editions

The catalog (`Meta_Bible_Data/sqlite/editions.json`) says every GOI edition is
identified by a BCP 47 tag. These rules keep that claim literally true.

## The rule

For every GOI edition with `bcp47_tag` = `<tag>`:

| Thing | Must be | Example (`zh-Hant`) |
|---|---|---|
| Flatfile directory | `GOI_Bible/GOI_Bible_<tag>` (exact case) | `GOI_Bible/GOI_Bible_zh-Hant` |
| `edition_id` | `GOI_<tag>` (case-insensitive) | `GOI_zh-Hant` |
| `filename_suffix` | `GOI_<tag>` (case-insensitive) | `001_GEN_001_001_GOI_zh-Hant.txt` |
| Download DB / SQL / epub | `<edition_id>.db` / `.sql` / `.epub` | `GOI_zh-Hant.db` |

Subtags are joined with a hyphen, never an underscore (`zh-Hant`, not `zh_Hant`).
BCP 47 tags are case-insensitive, so the existing `GOI_En`, `GOI_Es` and so on
are valid. Write new editions in canonical case (`GOI_en`, `GOI_pt-BR`).

The same applies to internal edition keys in `Bible_Noun_Extraction`
(`verify_editions.EDITIONS`, `apply_edition_fixes.py`, `edition_fixes_log.csv`):
`en`, `zh-Hant`, `zh-Hans`, … — not `zh_hant`.

**Enforced by** `tools/translation_pipeline/verify_release_integrity.py`. It runs
in CI and fails any active GOI edition whose directory, `edition_id` or
`filename_suffix` breaks the rule.

## Renames done on 2026-10-28

| Old | New |
|---|---|
| `GOI_Bible/GOI_Bible_English` | `GOI_Bible/GOI_Bible_en` |
| `GOI_Bible/GOI_Bible_Chinese_Hans` | `GOI_Bible/GOI_Bible_zh-Hans` |
| `GOI_Bible/GOI_Bible_Chinese_Hant` | `GOI_Bible/GOI_Bible_zh-Hant` |
| edition / suffix `GOI_Zh_Hans` | `GOI_zh-Hans` |
| edition / suffix `GOI_Zh_Hant` | `GOI_zh-Hant` |
| internal key `zh_hans` / `zh_hant` | `zh-Hans` / `zh-Hant` |

What changed:

- **Files:** 93,306 verse files were moved with `git mv`, and their contents are unchanged. 62,204 of them also took the new suffix.
- **Artifacts:** the download DBs, `sqlite/versions/*.sql`, the epubs and `iphone_package/data/*.db` were renamed. Their `edition_id`, `version` and notes values were rewritten in place, and each epub's `urn:goi-bible:` identifier was updated.
- **Manifest:** `manifest.json` has new sha256 values for the rewritten DBs.
- **References:** all code and living docs were updated, in the main repo and the `Bible_Noun_Extraction` submodule.

**Left on purpose** as historical record: `logs/`, `staging/`, `plans/`,
`reports_archive/`, `sweep_history/`, dated docs, and
`docs/greek_to_chinese_gameplan.md`. Read old names there as the names that
were in use when those files were written.

**Legacy aliases** keep saved state from older builds working:

- `Apps/GOIBible_desktop/goibible/state.py` and
  `Apps/GOIBible_android/.../AppState.kt` (`LEGACY_EDITION_IDS`)
- `Meta_Bible_Data/full_bible/generate_markdown_bible.py` (accepts `goi_zh_hant` and similar)
- the goibible.org reader on dsvx, once it is deployed (old `?edition=GOI_Zh_Hant` links)

## Trapping names that grep cannot see

A plain grep only finds names written out in full. These cases slip past it:

- **Assembled names:** `'GOI_Zh_' + ed`, `f"GOI_Bible_{lang.capitalize()}"`, `"GOI_%s_%s" % (lang, script)`, `tag.replace('-', '_')`.
- **Decomposed names:** `suffix != ['GOI', 'Zh', ed]` after `split('_')`, or a part-count check.
- **Probes that skip what they don't find:** `exists()` on a guessed path. A glob of a missing directory returns 0 files, and the script still passes.

Two traps cover these.

1. **Static: `tools/bcp47_composite_scan.py`** (runs in CI and blocks). It parses each Python file and folds every string-building expression into a template, with unknown parts shown as `{}` and case/replace transforms recorded. It then flags old-name shapes, case transforms on tags, two-part `_` joins after `GOI_`, decomposed suffix lists, part-count checks, and comparisons against old fragments. Shell, PHP, Kotlin, Swift and JS get a token scan. Its self-test cases are in the docstring examples. Reviewed exceptions go in `ALLOW` and `REVIEWED`.
2. **Runtime: `tools/bcp47_tripwire.py`.** It hooks `open`, `listdir`, `scandir`, `glob`, pathlib globs and `stat` (which covers `exists()` and `is_file()`). It sees the final path however it was built, and reports each call site once on stderr and in `~/.cache/goi_bcp47_tripwire.log`. Use it on any script with `tools/py-tripwire script.py [args]`. Set `GOI_BCP47_TRIPWIRE=raise` to turn hits into errors.
   - `tools/install_bcp47_tripwire.sh` can make it always-on for an interpreter (one `.pth` line; `--remove` undoes it). That is the owner's call, so it is not installed by default.

What the traps found on 2026-10-28:

- `gender_ngram.py` and `plurality_ngram.py` guessed `GOI_{lang.capitalize()}`. That matched 0 Vietnamese files (the suffix is `GOI_vi`). They now ask `goi_catalog.py`, which reads `editions.json`.
- `zh/verify_current_artifacts.py` decomposed the suffix as `['GOI','Zh',ed]`, so it would have rejected all 62,204 Chinese verses.
- `verify_coverage.py --filename-suffix GOI_Zh_Hant` reports `coverage: 0.0%` without failing. The tripwire now names the probe at line 117.

**Rule:** never assemble a GOI directory or suffix from a language code. Use `goi_catalog.flatfile_dir(tag)` and `goi_catalog.suffix(tag)` in `Bible_Noun_Extraction`, or read `editions.json`.

## Adding a new edition

1. Pick the BCP 47 tag first, e.g. `pt-BR`.
2. Create `GOI_Bible/GOI_Bible_pt-BR/` with files `NNN_BOOK_CCC_VVV_GOI_pt-BR.txt`.
3. Set `edition_id` and `filename_suffix` to `GOI_pt-BR` in `editions.json`.
4. Run `python3 tools/translation_pipeline/verify_release_integrity.py --edition GOI_pt-BR`.
