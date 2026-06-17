# Not Copied To `/var/www/goibible.org/github`

This is the inventory of paths that are intentionally left out of the public staging tree.

## VCS And Local Tool State

- `.git/`
- `.claude/`
- `.obsidian/`
- `.pi/`
- `opencode-quota/`
- `opencode.json`
- `tui.json`

## Generated Logs And Scratch

- `logs/`
- `backup/`
- `archive/`
- `GOI_Bible_English_prefix-backups/`

## Private Or Reproducible Source Trees

- `Bible_Noun_Extraction/`
- `sources/`
- `Hebrew_Bible_WLC/`
- `English_Bible_KJV/`
- `English_Bible_WEBUS/`
- `Chinese_Bible_CUV/`

## Local Working Databases

- `GOI_bible_legacy.sqlite3` if present
- any `*.sqlite3.bak*`
- any `*.db`

## Helper Files Not Published

- `copy_github_repo.sh`
- `no_copy_github_repo.md`
- any other repo-local helper script or note created only for staging or cleanup

## Public Tree That *Is* Copied

The staging script copies only:

- `README.md`
- `README_GOI.md`
- `.gitignore`
- `GOI_bible.sqlite3`
- `GOI_Bible_English/`
- `GOI_Bible_Chinese_Hant/`
- `GOI_Bible_Chinese_Hans/`

## Website Tree

The `/var/www/goibible.org/www/` tree is reserved for website-only content and is not part of the GitHub repo staging area.
