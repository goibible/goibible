# GOI Bible Desktop

Portable Python/Qt version of the Android GOI Bible reader.

## Run From Source

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

If your shell has a system Qt path in `LD_LIBRARY_PATH`, use `./scripts/run.sh`; it clears that variable before launching so PySide6 uses its bundled Qt libraries.

The app creates `data/bible.db` and `data/settings.json` beside the source tree. In a packaged build, the same `data/` folder is created beside the executable, so the app remains portable.
The build script preserves `dist/GOIBible/data/` across rebuilds, so imported editions are not deleted when regenerating the portable folder.
On Linux, the window uses the bundled GOI icon at runtime. The portable build also writes `dist/GOIBible/GOIBible.desktop` so file managers and launchers can show the app icon.

## Features

- Bundled `GOI_En` SQLite edition from the Android app.
- Book/chapter navigation with transport controls.
- Split reader panes with optional sync lock.
- Verse search in the active edition.
- Dark/light display, font selection, and font size.
- Import additional compatible `.db` edition files from disk or URL.
- Remove installed editions while keeping at least one.

## Build Portable Folder

```bash
source .venv/bin/activate
./scripts/build_portable.sh
```

The portable folder is written to `dist/GOIBible/`.

## Build Windows Installer

On Windows with Python 3 and NSIS installed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_installer.ps1
```

The installer is written to `dist\goibible_install.exe`.

From this Linux workspace, Docker can build the Windows installer through Wine:

```bash
./scripts/build_windows_installer_docker.sh
```
