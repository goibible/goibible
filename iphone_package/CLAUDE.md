# iOS port of GOIBible — instructions for Claude Code

You're building a native iOS app that ports an existing Android app ("GOIBible" — an offline,
multilingual Bible reader) so it looks and behaves the same on iPhone. You do not have access to
the original Android/Kotlin source — everything you need has been pre-extracted into this
folder. Read `SPEC.md` and `schema.md` in full before writing any code; they are the source of
truth, ported directly from the original app's source, not paraphrased from memory.

## What's in this folder

- `SPEC.md` — full feature and behavior spec: data bootstrap/merge logic, navigation model
  ("movie transport" pattern with split-screen + sync-lock), every screen, theming.
- `schema.md` — exact SQLite table/column shapes for the bundled databases, plus the exact
  search query (LIKE-based, with escaping) to replicate.
- `data/GOI_En.db`, `GOI_vi.db`, `GOI_Zh_Hans.db`, `GOI_Zh_Hant.db` — the four bundled Bible
  editions (English, Vietnamese, Chinese Simplified, Chinese Traditional). Bundle all four as
  app resources.
- `branding/literata.ttf` — the app's primary reading font. Use it as the default typeface, not
  a buried option.
- `branding/ic_launcher_source.png` — app icon source, but it's only 192×192 (the largest size
  available from the Android build). iOS wants a 1024×1024 source for the Xcode asset catalog —
  **upscale or regenerate at 1024×1024 before finalizing the icon**; don't ship it blurry.
- `reference/mockup.svg` — original design mockup, for visual reference only (not authoritative
  over `SPEC.md` for behavior).

## Build approach

- Native Swift + SwiftUI, iOS 16+ target.
- SQLite via GRDB.swift (add as an SPM dependency) or the raw `sqlite3` C API — GRDB recommended.
- This is a **port**, not a redesign: match `SPEC.md`'s screens and interaction model exactly.
  Where iPhone screen constraints genuinely require a different layout choice than Android
  (e.g. split-pane side-by-side vs. stacked), make the call and note the deviation, but don't
  drift from the spec otherwise.
- No network calls — everything is local/offline.
- Signing: a free Apple ID is enough to build and run on your own device via Xcode. No paid
  Apple Developer Program membership needed unless you later want TestFlight distribution or a
  build that survives longer than the free provisioning profile's ~7-day expiry.

## Verification before calling it done

- Build and run on a real device (or simulator first, then device) — confirm the app launches,
  merges all four editions on first run, and you can read/search/bookmark/randomize across all
  four languages.
- Test split mode + sync lock together: turning on sync lock while split should snap both panes
  to the same book/chapter immediately; chapter navigation should then move both panes; editions
  per pane should stay independent.
- Test edition add/remove in Settings against the merge/remove routines in `SPEC.md` §2 — don't
  allow removing the last remaining edition.
