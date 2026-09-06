# Spanish (GOI_Es) verses changed 2026-09-03 through 2026-09-05

Complete list of every verse whose **text content changed** during this
session, for cross-referencing against any existing audio recording. Verses
generated fresh for the first time (the original Stage 5 OT run) are NOT
included here — only verses that existed, then had their text edited or
regenerated afterward.

## 1. Resumed after exhausting all retries during initial generation (6)

These verses had no content at all until this session; if audio was
recorded from a corpus snapshot taken before 2026-09-04, these were
silent/missing and now have text for the first time.

- 2 Chronicles 1:13
- Song of Songs 2:7
- Isaiah 9:1
- Ezekiel 5:7
- Ezekiel 29:7
- Ezekiel 47:8

## 2. Noun/name-consistency fixes (13)

- Proverbs 16:5 — encoding bug (literal `\u00XX` escapes fixed to real characters); wording unchanged
- 1 Chronicles 14:17 — was a citation-header leak ("1 Crónicas 14:17"), regenerated with real content
- 1 Chronicles 19:6 — "Aram-naharaim" → "Aram-Naharaim"
- 1 Chronicles 27:28 — "Baal-hanan" → "Baal-hanán"
- Judges 3:8 — "Aram-naharaim" → "Aram-Naharaim"
- Nehemiah 7:59 — "Poqueret-hazebaim" → "Poqueret-hasebaim"
- Numbers 33:33 — "Hor-haggidgad" → "Hor-hagidgad"
- 1 Kings 22:48 — "Ezeón-geber" → "Ezión-geber"
- Deuteronomy 2:8 — "Etsión-geber" → "Ezión-geber"
- Numbers 33:35 — "Esion-geber" → "Ezión-geber"
- Numbers 33:36 — "Esion-geber" → "Ezión-geber"
- 2 Chronicles 8:17 — "Esion-geber" → "Ezión-geber"
- 2 Chronicles 20:36 — "Esion-geber" → "Ezión-geber"

## 3. Clause-completeness fixes — real translation errors (3)

- Genesis 15:19 — wrong nation-name list entirely (was duplicating v21's
  list); now correctly translates its own Kenite/Kenizzite/Kadmonite list
- Exodus 2:21 — "Moisés accedió a **morir**" corrected to "**habitar**"
  (was a full meaning reversal: "agreed to die" → "agreed to dwell")
- Ezekiel 16:43 — verb corrected from "considerado" to "cometido"

## 4. Duplicate-word stutter fix (1)

- Proverbs 4:23 — "Sobre toda guarda guarda tu corazón" → "Sobre toda cosa
  guardada, guarda tu corazón"

## 5. Register fix: ustedes → vosotros, full regeneration (72)

Every verse below had its whole text regenerated (not just a word swap) to
fix a "ustedes" (Latin American formal) register drift back to the
corpus's established "vosotros" register. Treat these as fully re-written,
not minor edits — safest to re-record entirely rather than patch.

- Exodus 12:16, 12:26, 16:4, 24:8, 24:14
- Leviticus 11:4, 11:10, 14:34, 25:20
- Numbers 1:5, 11:20, 15:14, 18:3, 18:4, 22:13, 27:14, 32:30, 33:52, 34:9
- Deuteronomy 1:33, 4:8, 9:16, 11:5, 14:8
- Joshua 3:3, 9:8, 9:22, 10:25, 22:28
- Judges 8:18, 9:19, 14:12, 14:13, 15:7
- 1 Samuel 17:8, 21:15, 25:19
- 2 Samuel 2:5, 19:22
- 2 Chronicles 19:11, 30:7, 32:13
- Ezra 1:3, 4:2, 9:11
- Nehemiah 1:9, 2:19, 5:8, 5:9, 6:3, 13:17
- Esther 8:8
- Job 32:12
- Psalm 127:2, 129:8
- Isaiah 29:11
- Jeremiah 17:24, 23:38, 26:13, 27:9, 30:22, 44:4, 44:10
- Ezekiel 6:7, 11:11, 12:22, 13:14, 20:30, 20:35, 37:14
- Malachi 1:5, 3:1

---

**Total: 95 verses** with changed text (6 + 13 + 3 + 1 + 72, no overlaps
between categories). Full technical detail on why each category changed is
in `PLANS_ES.md` §5.
