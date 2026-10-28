#!/usr/bin/env bash
# Install (or with --remove, uninstall) the BCP 47 path tripwire for each given Python interpreter.
# It adds one .pth line to the interpreter's user site-packages; nothing else is touched.
# usage: tools/install_bcp47_tripwire.sh [--remove] [python ...]   (default: python3 /usr/bin/python3)
set -euo pipefail
hook="$(cd "$(dirname "$0")" && pwd)/bcp47_tripwire.py"
remove=0; [[ "${1:-}" == "--remove" ]] && { remove=1; shift; }
for py in "${@:-python3 /usr/bin/python3}"; do
  for p in $py; do
    site=$("$p" -c 'import site; print(site.getusersitepackages())')
    pth="$site/goi_bcp47_tripwire.pth"
    if (( remove )); then rm -f "$pth"; echo "removed $pth"; continue; fi
    mkdir -p "$site"
    echo "import os; p='$hook'; os.path.isfile(p) and exec(compile(open(p).read(), p, 'exec'))" > "$pth"
    echo "installed $pth ($("$p" -c 'import sys; print(sys.version.split()[0])'))"
  done
done
