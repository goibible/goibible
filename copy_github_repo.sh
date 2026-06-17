#!/usr/bin/env bash
set -euo pipefail

SRC="/home/albert/projects/bible"
DST="/var/www/goibible.org/github"

mkdir -p "$DST"

rsync -a --delete "$SRC/README.md" "$DST/"
rsync -a --delete "$SRC/docs/README_GOI.md" "$DST/README_GOI.md"
rsync -a --delete "$SRC/.gitignore" "$DST/"
rsync -a --delete "$SRC/GOI_bible.sqlite3" "$DST/"

for dir in GOI_Bible_English GOI_Bible_Chinese_Hant GOI_Bible_Chinese_Hans; do
  mkdir -p "$DST/$dir"
  rsync -a --delete "$SRC/$dir/" "$DST/$dir/"
done

echo "Copied GOI public staging tree to $DST"
