# GOIBible — iOS port spec

Source of truth: the native Android app at `Apps/GOIBible_android/` in the original repo
(Kotlin + Jetpack Compose). This doc ports its exact behavior for a SwiftUI rebuild — it is not
a redesign. If anything here seems ambiguous, prefer literal parity with what's described over
inventing new behavior.

## 1. App identity

- Name: **GOIBible**
- Offline, multilingual Bible reader. No network calls, no accounts, no backend — everything
  runs against a local SQLite database.
- Ships with 4 bundled editions (see `data/`): English (`GOI_En`), Vietnamese (`GOI_vi`),
  Chinese Simplified (`GOI_Zh_Hans`), Chinese Traditional (`GOI_Zh_Hant`).
- Not in scope: no audio/TTS/read-along video features. (There's a separate, unrelated
  narrated-video pipeline elsewhere in the source repo — ignore it, it's a different product.)

## 2. Data layer

Table/column details are in `schema.md` — read that alongside this section.

**Bootstrap (first launch):**
1. Copy `GOI_En.db` from the app bundle into the app's writable documents directory as the
   working database (e.g. `bible.db`).
2. Open it, then `CREATE TABLE IF NOT EXISTS` the `book_names` and `bookmarks` tables (in case
   the bundled base DB predates them).
3. For each of the other three bundled edition `.db` files, run the merge routine below against
   the working DB.

**Merge routine** (also reused later for "add edition" in Settings):
1. `ATTACH DATABASE '<path-to-edition-db>' AS src`
2. Sanity check: `SELECT count(*) FROM src.sqlite_master WHERE type='table' AND name IN
   ('editions','verses')` must be `2`, else fail with an error (not a valid edition db).
3. In a transaction:
   - `INSERT OR IGNORE INTO books SELECT * FROM src.books`
   - `INSERT OR REPLACE INTO editions SELECT * FROM src.editions`
   - if `src` has a `book_names` table: `INSERT OR REPLACE INTO book_names SELECT * FROM
     src.book_names`
   - `INSERT OR REPLACE INTO verses SELECT * FROM src.verses`
4. `DETACH DATABASE src`

**Remove edition** (Settings → remove a downloaded edition): inside a transaction, delete from
`bookmarks`, `verses`, `book_names`, `editions` where `edition_id = ?`, in that order.

**Queries needed** (exact SQL in `schema.md` under Search; the rest are straightforward
`SELECT`s filtered by `edition_id`/`conical`/`chapter` — see `BibleRepo.kt` in the original repo
if you have access to it, otherwise these named operations are self-explanatory):
- list editions
- list books that have verses in a given edition (LEFT JOIN `book_names` for localized titles)
- chapter count for a book in an edition (`MAX(chapter)`)
- verses for edition+book+chapter, ordered by verse
- search (LIKE, see `schema.md`)
- random verse in an edition
- bookmark CRUD + "bookmarks near current position" (see §4 Bookmarks screen for sort order)

## 3. Navigation / state model — "movie transport" pattern

This is the core interaction model; get this right before worrying about visual polish.

- The app tracks **one or two "panes"**, each holding: `editionId`, `conical` (book number),
  `chapter`, and a transient `pendingVerse` (set when jumping from search/bookmarks/randomizer,
  cleared once the reader scrolls to it).
- **Split mode**: off by default. When on, both panes render side by side (or stacked — match
  whatever reads best on iPhone portrait; Android used side-by-side but iPhone width may call
  for stacked — use judgment, note the deviation if you make one).
- **Sync lock**: when split AND sync-locked, chapter-navigation actions (first/prev/next/last/
  seek-to-chapter, and jump-to-verse from search/bookmarks/randomizer) apply to **both** panes
  at once. Each pane keeps its own `editionId` (language) independent of the other — only the
  book/chapter position is shared. When sync lock is turned ON, immediately snap the *other*
  pane's book+chapter to match the *active* pane's (don't wait for the next navigation).
- When split is turned OFF, reset "active pane" to pane 0.
- **Active pane**: whichever pane the user is currently interacting with (tap to select, or
  simplest: whichever pane's transport controls were last used) — book/chapter edits when NOT
  synced apply only to the active pane.
- **Book navigation**: stepping to prev/next book skips to the next book in that edition's own
  book list (each edition may have a different available book list — e.g. Hebrew-only editions
  lack the NT). Landing on a new book resets chapter to 1.
- **Chapter navigation edge behavior**: next-chapter past the last chapter of a book rolls into
  chapter 1 of the next available book; prev-chapter before chapter 1 rolls into the last
  chapter of the previous book. Don't wrap past the first/last book.
- **Changing edition on a pane**: if the new edition doesn't contain the current book, fall back
  to that edition's first available book, chapter 1. Otherwise clamp the current chapter to the
  new edition's chapter count for that book.
- **Persistence**: split flag, sync-lock flag, dark mode, font choice, font size, and each
  pane's edition/book/chapter should persist across app launches (Android used
  SharedPreferences — use `UserDefaults` on iOS with equivalent keys/shape).

## 4. Screens

- **Reader** — the main view. Shows one pane (or two, per split mode) of verse text for the
  active book/chapter/edition. Tapping/long-pressing a verse toggles its bookmark (exact
  Android gesture doesn't need to be copied verbatim — pick an iOS-idiomatic equivalent, e.g.
  tap for select, long-press or swipe for bookmark — just keep the capability). Respects
  font family, font size, and dark/light theme from Settings.
- **Transport bar** — persistent bar (Android: bottom bar) with: first chapter, previous
  chapter, next chapter, last chapter, split-mode toggle, sync-lock toggle, and buttons to open
  Search, Bookmarks, Randomizer, Settings, About.
- **Search** — text field; runs the LIKE query (schema.md) against the *active pane's* edition;
  results list book/chapter/verse + snippet; tapping a result calls "jump to verse" (which
  respects sync-lock, i.e. applies to both panes if locked).
- **Bookmarks** — lists all bookmarks across editions, sorted by proximity to the current
  reading position: same-edition-as-current first, then same-book, then same-chapter, then by
  absolute distance in book number, then chapter number, then verse number (closest to verse 1
  first), then newest-created-first as final tiebreak. Tapping a bookmark jumps the active pane
  there. Supports deleting a bookmark.
- **Randomizer** — a dialog/sheet that picks one random verse from the active edition and lets
  the user jump to it.
- **Settings** — font family picker (bundled font is `literata.ttf`, in `branding/`), font size
  slider/stepper (range 10–28), dark/light mode toggle (default: dark), and edition management:
  list currently-loaded editions, "add edition" (import a `.db` file into the working DB via the
  merge routine), "remove edition" (delete routine above) — don't allow removing the last
  remaining edition.
- **About** — static app info screen (name, purpose, credits/license as appropriate — keep it
  simple, this isn't a Kotlin-source detail worth over-porting).

## 5. Theming

- Dark mode default ON.
- Custom font: `branding/literata.ttf` — this must ship as the primary reading typeface, not
  just an option buried in settings (it's the app's default look).
- Font size range 10–28 (Android default was 12).
- Otherwise: standard iOS look and feel (native SwiftUI components, no attempt to pixel-clone
  Android Material3 widgets) — behavioral parity matters far more than pixel parity here.

## 6. Build target

- iOS 16+, native Swift + SwiftUI.
- SQLite access via GRDB.swift (recommended, add as a Swift Package Manager dependency) or the
  raw `sqlite3` C API if avoiding third-party deps is preferred.
- No network entitlements needed — everything is local.
