# GOIBible: iPhone, iPad and Mac

One SwiftUI codebase (`Sources/GOIBible`), a 1:1 port of `Apps/GOIBible_android`. No third-party deps (system SQLite3).

| Build | Where | How |
|---|---|---|
| iPhone/iPad on device | Linux | `./sync-resources.sh && xtool dev` (free Apple ID, re-sign every 7 days) |
| iOS .ipa + macOS .app | GitHub Actions (`.github/workflows/apple.yml`) | push changes under `iphone/` → download the `goibible-apple` artifact |
| Any target, Simulator | a Mac | `./sync-resources.sh && xcodegen generate && open GOIBible.xcodeproj` |

`sync-resources.sh` copies the 4 bundled editions from `Meta_Bible_Data/goi_db_download` and Literata from the Android app,
so all apps ship the same data. Generated resources are gitignored.
