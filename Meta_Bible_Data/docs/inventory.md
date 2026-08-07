# GOI Bible: Flatfile & Database Inventory

Last verified: 2026-08-06, during the Vietnamese OT launch. Every location and
build command below was checked hands-on this session (not assumed from
memory) — see "How this was verified" at the bottom for what that means in
practice, and re-verify anything before trusting it if a lot of time has
passed since the date above.

**The rule this whole document exists to enforce:** flatfiles are the one
canonical source of truth. Every database below is a *derived, rebuildable
artifact*. If a translation fix only touches a flatfile and nothing rebuilds
downstream from it, that fix is invisible everywhere except a raw `grep` of
the repo. This session found three separate places where exactly that had
happened (stale download DBs, a stale/incomplete live reader DB, one verse
where a fix was reported as done but never actually applied) — so treat "did
I rebuild everything downstream" as a real step, not a formality.

---

## 1. Flatfiles (canonical source — edit these, nothing else)

All under repo root `/home/albert/projects/bible`, one `.txt` file per verse,
named `<NNN>_<BOK>_<CCC>_<VVV>_<suffix>.txt`.

### Translations (`GOI_Bible/`)
| Directory | Language | Suffix | Verses |
|---|---|---|---|
| `GOI_Bible/GOI_Bible_English` | English | `_GOI_En.txt` | 31,102 (OT+NT) |
| `GOI_Bible/GOI_Bible_vi` | Vietnamese | `_GOI_vi.txt` | 31,102 (OT+NT) |
| `GOI_Bible/GOI_Bible_Chinese_Hant` | Chinese (Traditional) | `_GOI_Zh_Hant.txt` | 31,102 (OT+NT) |
| `GOI_Bible/GOI_Bible_Chinese_Hans` | Chinese (Simplified) | `_GOI_Zh_Hans.txt` | 31,102 (OT+NT) |

**Every fix to Hant must be mirrored to Hans by hand** (and vice versa) —
there is no automated conversion step in the live pipeline; Hans was
originally generated from Hant via OpenCC t2s once, then diverges via manual
edits on both sides.

### Reference sources (`Reference_Bible/`) — not edited, used for verification
| Directory | Content |
|---|---|
| `Reference_Bible/Greek_Bible_TR1550/One_Directory_TR1550` | Textus Receptus 1550 (NT source text) |
| `Reference_Bible/Hebrew_Bible_WLC/One_Directory_WLC_KJV` | Westminster Leningrad Codex (OT source text) |
| `Reference_Bible/English_Bible_KJV/One_Directory_KJV` | KJV — this project's primary reference translation |
| `Reference_Bible/English_Bible_WEBUS/One_Directory_WEBUS` | World English Bible (US) |
| `Reference_Bible/Chinese_Bible_CUV/One_Directory_CUV` | Chinese Union Version — secondary reference for Chinese idiom/convention |
| `Reference_Bible/Vietnamese_Bible_VIE1934/One_Directory_VIE1934` | 1934 Vietnamese Bible — secondary reference for Vietnamese idiom/convention |

### Supporting data
- `Meta_Bible_Data/Bible_Noun_Extraction/greek_noun.sqlite3` — Strong's-number-tagged NT word data (drives systemic word-pattern sweeps like the πνεῦμα/ἔθνος/ἀρχή/θεραπεία checks). No equivalent exists for the Hebrew OT yet.
- `Meta_Bible_Data/full_bible/` — single-file-per-edition exports (`.md`), used as download bundles on the site. **No Vietnamese `.md` exists yet** — flagged during this session, not generated.

---

## 2. Databases (derived — rebuild, don't hand-edit)

### 2a. The build chain (in order)

```
flatfiles (GOI_Bible/*)
    │
    ▼  tools/translation_pipeline/goi_language_pipeline.py stage <edition_id>
    │     ├─ check_flatfiles / normalize / readiness / coverage
    │     ├─ build_sql  → Meta_Bible_Data/sqlite/build_buffet.py <edition_id>
    │     │     reads flatfiles + Meta_Bible_Data/local_backups/GOI_bible.sqlite3
    │     │     writes Meta_Bible_Data/sqlite/versions/<edition_id>.sql
    │     └─ build_download
    │           ├─ Meta_Bible_Data/sqlite/build_shell.sh
    │           │     rebuilds Meta_Bible_Data/sqlite/goi_bible_shell.db (schema + reference seed only)
    │           └─ Meta_Bible_Data/goi_db_download/build_downloads.py <edition_id>
    │                 combines shell.db + sqlite/versions/*.sql
    │                 writes Meta_Bible_Data/goi_db_download/<edition_id>.db  ← the canonical distributable
    │                 writes Meta_Bible_Data/goi_db_download/manifest.json
    ▼
Meta_Bible_Data/goi_db_download/*.db   (git-tracked; apps + reader pull from here)
    │
    ▼  tools/build_reader_db.py   (added this session — no dependency, run manually after any goi_db_download change)
    ▼
/var/www/goibible.org/read/data/bible.sqlite3   ← powers read.goibible.org (needs manual rsync to dsvx after rebuild)
```

**Command to run after any flatfile edit**, from repo root:
```bash
python3 tools/translation_pipeline/goi_language_pipeline.py stage <EDITION_ID>
# e.g. stage GOI_vi, stage GOI_Zh_Hant, stage GOI_Zh_Hans, stage GOI_En
python3 tools/build_reader_db.py
```
Then commit + push (§4) and rsync the reader DB to dsvx (§3).

### 2b. Every database location found on this machine

| Path | What it is | Tracked in git? | Status as of this session |
|---|---|---|---|
| `Meta_Bible_Data/local_backups/GOI_bible.sqlite3` | The "main" registry DB `build_buffet.py` reads as a template/reference | No (`.gitignore`) | Rebuilt correctly this session (was the source of the stale-GOI_vi bug — see §5) |
| `Meta_Bible_Data/sqlite/versions/<edition>.sql` | Per-edition SQL dump, intermediate | **Yes** | Current |
| `Meta_Bible_Data/sqlite/goi_bible_shell.db` | Empty schema + reference seed, no verse rows | **Yes** (explicit `.gitignore` exception) | Current |
| `Meta_Bible_Data/goi_db_download/*.db` (8 editions: `GOI_En`, `GOI_vi`, `GOI_Zh_Hant`, `GOI_Zh_Hans`, `KJV`, `WEBUS`, `TR1550`, `WLC`) | **The canonical distributable** — apps and the reader both ultimately source from these | **Yes** (explicit `.gitignore` exception) | Rebuilt and current as of this session |
| `Meta_Bible_Data/goi_db_download/manifest.json` | Lists each edition's status (`active`/`pending`), checksum, size — Android/desktop apps fetch this **live from GitHub** to discover what's downloadable | **Yes** | Current; `GOI_vi` now `active` |
| `Meta_Bible_Data/sqlite/editions/*.db` | **Stale/orphaned.** Written by `build_buffet.py`/`split_editions.sh`, but `build_downloads.py` does NOT read from here — this directory is not part of the live `stage` pipeline at all. Found `GOI_vi.db` here still at 7,957 (NT-only) rows. | No | **Dead weight — safe to delete, not part of any live path. Do not treat this directory as a source of truth for anything.** |
| `/var/www/goibible.org/read/data/bible.sqlite3` | Powers **read.goibible.org**, the live public web reader (separate from the download/app path) | No (lives outside this repo, on the local machine + mirrored to dsvx) | Was stale for every edition and **completely missing Vietnamese** until this session; now rebuilt via `tools/build_reader_db.py` and synced to dsvx |
| `/var/www/goibible.org/www/data/site_content.sqlite3` | Small CMS DB — homepage/nav copy per language, read by `index.php` | No | Vietnamese content upserted via `/var/www/goibible.org/tools/upsert_vietnamese_home.php`; synced to dsvx |
| `Apps/GOIBible_android/app/src/main/assets/GOI_En.db`, `GOI_Zh_Hant.db` | Bundled-at-install editions for the Android app | **Yes**, but `Apps/` itself is currently **untracked** in this repo (see §4 note) | Only English + Traditional Chinese are pre-bundled; **the app fetches any other edition (Vietnamese, Simplified Chinese) on demand from the GitHub manifest** — confirmed by reading `BibleRepo.kt`/`SettingsScreen.kt`, no code change needed |
| `Apps/GOIBible_desktop/goibible/resources/GOI_En.db`, `GOI_Zh_Hant.db` | Same pattern for the desktop app | Same as above | Same dynamic-fetch design, confirmed via `app.py` |
| `Apps/GOIBible_desktop/data/bible.db`, `Apps/GOIBible_desktop/dist/**/data/bible.db` | **User-local runtime cache** — the merged working DB the desktop app builds for itself at runtime after downloading editions | No | Not a source, ignore for update purposes |
| `Meta_Bible_Data/archive/atomic_bible.sqlite3`, `Meta_Bible_Data/local_backups/goi_bible_downloads/*.db` | Old pre-migration snapshots | No | Historical only, not live |
| `Apps/bible_verse_randomizer/**/randomizer.sqlite3` | Belongs to an unrelated sub-project (verse randomizer, not the main Bible reader/apps) | No | Out of scope for Bible-text updates |

### 2c. Things that do *not* need a separate update
- **Android APK / desktop installer binaries** — confirmed this session that neither app bundles more than English + Traditional Chinese at install time; every other edition (including Vietnamese) is fetched dynamically from the GitHub-hosted `manifest.json` + `.db` files. **No app rebuild is needed when flatfiles/download-DBs change.**
- `/var/www/goibible.org/www/download/index.html` — lists the three platform installers only, has no per-language logic, nothing to update there for a translation change.

---

## 3. The `dsvx` production server

SSH alias `dsvx` → `129.212.185.75`. Live site tree lives at
`/var/www/goibible.org/` on both this machine and dsvx as **parallel
copies** — there is no automated deploy; every sync is a manual `rsync`.

Rollback pattern already established on dsvx (found in use, not introduced
this session): before overwriting any live file under `/var/www/goibible.org`,
snapshot it into a timestamped folder under `/var/www/goibible.org/.rollback/`
with the same relative path, then rsync the new file over. Example used this
session:
```bash
TS=$(date +%Y%m%d-%H%M%S)
ssh dsvx "mkdir -p /var/www/goibible.org/.rollback/${TS}/read/data && \
          cp /var/www/goibible.org/read/data/bible.sqlite3 \
             /var/www/goibible.org/.rollback/${TS}/read/data/bible.sqlite3"
rsync -av --checksum /var/www/goibible.org/read/data/bible.sqlite3 \
      dsvx:/var/www/goibible.org/read/data/bible.sqlite3
```

Files on dsvx that need re-syncing whenever their local counterpart changes:
| Local path | Remote path | When to sync |
|---|---|---|
| `/var/www/goibible.org/read/data/bible.sqlite3` | same path on dsvx | After `tools/build_reader_db.py` |
| `/var/www/goibible.org/www/data/site_content.sqlite3` | same path on dsvx | After running `/var/www/goibible.org/tools/upsert_vietnamese_home.php` or any other homepage-content edit |
| `/var/www/goibible.org/www/download/*` | same path on dsvx | Only if an app is actually rebuilt (rare — see §2c) |

**Open item, not resolved this session:** `/var/www/goibible.org/github` is a
*separate* local git checkout of the same `goibible/goibible` remote,
apparently used historically to push a curated "public-safe" subset (via
`tools/copy_github_repo.sh`, excluding internal staging/audit files) rather
than the full working tree. It's now stale (sitting behind `origin/main`) and
arguably moot, since this session's direct pushes from the main working
directory already put the *entire* internal tree — including
`Meta_Bible_Data/staging/**`, audit JSON dumps, etc. — onto `goibible/goibible`.
Whether the public repo is supposed to be the full tree or a curated subset
is a policy call for the repo owner, not something to silently resolve.

---

## 4. Git

- Remote: `git@github.com:goibible/goibible.git`, branch `main`.
- `Apps/` (both `GOIBible_android` and `bible_verse_randomizer`) is
  **currently untracked** in this repo — `bible_verse_randomizer` has its own
  nested `.git`, and both directories carry large build caches
  (`.gradle`, `node_modules`, `dist/`) that should never be committed as-is.
  `GOIBible_desktop` was moved into `Apps/` this session and **is** tracked.
  If Android ever needs to be tracked properly, it needs its own `.gitignore`
  for `build/`, `.gradle/`, `.idea/`, `.kotlin/` first.
- `.gitignore` excludes `*.db`/`*.sqlite3`/`*.sqlite` globally, with explicit
  carve-outs for `Meta_Bible_Data/sqlite/goi_bible_shell.db` and everything
  under `Meta_Bible_Data/goi_db_download/`. Any new database that needs to
  ship in the repo has to be added as an explicit exception the same way.

---

## 5. Failure modes actually hit this session (so the next person doesn't repeat them)

1. **Stale registry rows silently truncate a rebuild.** `build_buffet.py`
   only falls back to the full template edition when an existing edition has
   *zero* rows in `local_backups/GOI_bible.sqlite3`. `GOI_vi` had a leftover
   partial registration (7,957 NT-only rows) from before the OT was
   translated, so every rebuild silently kept using the truncated data
   instead of pulling the full 31,102-verse flatfile set. Fix: if verse
   counts look wrong after a rebuild, check for stale rows in that registry
   DB before assuming the flatfiles are the problem.
2. **Rebuilding before finishing edits ships stale data.** The `goi_db_download/*.db`
   files were rebuilt to fix (1), then ~250 more translation bugs were found
   and fixed in the flatfiles *afterward* by a separate audit pass — but the
   databases were never rebuilt a second time until this inventory check
   caught it by diffing a known-fixed verse against what was actually in the
   shipped `.db`. **Always rebuild last, after all edits for the session are
   done — or rebuild again at the very end as a final step.**
3. **"Already fixed" needs a receipt, not a memory.** One verse (RUT 4:17)
   was confirmed as a bug during a live smoketest, described as fixed in
   a later instruction to a scrubbing subagent ("skip it, already fixed"),
   but the actual `Edit` call had never been made. The subagent trusted the
   claim and skipped it, so it silently stayed broken. Treat "I looked at
   this and confirmed it's wrong" and "I applied the fix" as two different,
   independently-verifiable facts — check the file, don't check the memory.
4. **A production database can exist with no build script at all.** The
   reader DB at `/var/www/goibible.org/read/data/bible.sqlite3` had
   apparently been hand-assembled once and never touched by any script in
   the repo — it just drifted. `tools/build_reader_db.py` now exists so this
   can't happen silently again, but it's worth periodically checking whether
   *other* undiscovered hand-built artifacts exist elsewhere on this machine
   or on dsvx.

---

## How this was verified

Every path in this document was checked directly this session: `find`/`du`
against the actual filesystem, `sqlite3`/Python queries against the actual
database contents (not just file existence), reading the actual pipeline
scripts (`goi_language_pipeline.py`, `build_buffet.py`, `build_downloads.py`)
rather than assuming their behavior, and SSH'ing into `dsvx` to check the
live server directly rather than assuming the local and remote copies match.
Nothing here is inferred from commit messages or prior session summaries
alone. If you're reading this much later, re-run the `find`/`du`/query
commands above rather than trusting the tables blindly — treat this as a
map that was accurate on the date at the top, not a live status page.
