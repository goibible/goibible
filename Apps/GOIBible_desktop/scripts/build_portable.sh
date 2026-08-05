#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

unset LD_LIBRARY_PATH

PYINSTALLER="${PYINSTALLER:-$ROOT/.venv/bin/pyinstaller}"
DATA_BACKUP=""

if [ -d "$ROOT/dist/GOIBible/data" ]; then
  DATA_BACKUP="$(mktemp -d)"
  cp -a "$ROOT/dist/GOIBible/data" "$DATA_BACKUP/data"
fi

"$PYINSTALLER" \
  --noconfirm \
  --windowed \
  --name GOIBible \
  --icon "goibible/resources/goibible-icon.png" \
  --add-data "goibible/resources:goibible/resources" \
  run.py

if [ -n "$DATA_BACKUP" ]; then
  rm -rf "$ROOT/dist/GOIBible/data"
  cp -a "$DATA_BACKUP/data" "$ROOT/dist/GOIBible/data"
  rm -rf "$DATA_BACKUP"
fi

cp goibible/resources/goibible-icon.png "$ROOT/dist/GOIBible/goibible-icon.png"
cat > "$ROOT/dist/GOIBible/GOIBible.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=GOI Bible
Comment=Portable GOI Bible reader
Exec=$ROOT/dist/GOIBible/GOIBible
Icon=$ROOT/dist/GOIBible/goibible-icon.png
Terminal=false
Categories=Education;Literature;
EOF
chmod +x "$ROOT/dist/GOIBible/GOIBible.desktop"

echo "Portable build: $ROOT/dist/GOIBible"
