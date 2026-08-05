#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker run --rm -v "$ROOT:/src" -w /src tobix/pywine:3.11 bash -lc '
set -euo pipefail

wine python -m pip install --force-reinstall -r requirements-windows.txt
rm -rf dist/GOIBible-win build/GOIBible-win build/GOIBible.spec dist/goibible_install.exe

wine python -m PyInstaller \
  --noconfirm \
  --windowed \
  --name GOIBible \
  --distpath dist/GOIBible-win \
  --workpath build/GOIBible-win \
  --specpath build \
  --noupx \
  --icon "Z:/src/goibible/resources/goibible-icon.ico" \
  --add-data "Z:/src/goibible/resources;goibible/resources" \
  run.py

PYSIDE="/opt/wineprefix/drive_c/Python/Lib/site-packages/PySide6"
if [ ! -d "$PYSIDE" ]; then
  PYSIDE="$(find / -path "*/Python/Lib/site-packages/PySide6" -type d 2>/dev/null | head -1)"
fi
if [ -z "$PYSIDE" ] || [ ! -d "$PYSIDE" ]; then
  echo "Could not locate Windows PySide6 install inside container" >&2
  exit 1
fi

mkdir -p dist/GOIBible-win/GOIBible/_internal/PySide6
cp -n "$PYSIDE"/*.dll dist/GOIBible-win/GOIBible/_internal/PySide6/ || true
mkdir -p dist/GOIBible-win/GOIBible/_internal/PySide6/plugins
cp -a "$PYSIDE"/plugins/platforms dist/GOIBible-win/GOIBible/_internal/PySide6/plugins/ || true
cp -a "$PYSIDE"/plugins/styles dist/GOIBible-win/GOIBible/_internal/PySide6/plugins/ || true

wine dist/GOIBible-win/GOIBible/GOIBible.exe &
pid=$!
sleep 5
if kill -0 "$pid" 2>/dev/null; then
  wineserver -k || true
else
  wait "$pid" || { cat /tmp/goibible-wine.log; exit 1; }
fi

apt-get update >/dev/null
apt-get install -y nsis >/dev/null
makensis installer/goibible.nsi
'

echo "Installer: $ROOT/dist/goibible_install.exe"
