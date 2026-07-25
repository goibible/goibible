#!/usr/bin/env bash
set -euo pipefail

SRC="/home/albert/projects/bible"
DST="/var/www/goibible.org/github"

echo "Source: $SRC"
echo "Destination: $DST"

mkdir -pv "$DST"

echo "Copying top-level files..."
rsync -av --delete "$SRC/README.md" "$DST/"
rsync -av --delete "$SRC/docs/README_GOI.md" "$DST/README_GOI.md"
rsync -av --delete "$SRC/.gitignore" "$DST/"
rsync -av --delete --exclude 'editions/' --exclude '*.sqlite3' --exclude '*.db' "$SRC/sqlite/" "$DST/sqlite/"
rsync -av "$SRC/sqlite/goi_bible_shell.db" "$DST/sqlite/goi_bible_shell.db"

for dir in GOI_Bible_English GOI_Bible_Chinese_Hant GOI_Bible_Chinese_Hans full_bible; do
  echo "Copying directory: $dir"
  mkdir -pv "$DST/$dir"
  rsync -av --delete "$SRC/$dir/" "$DST/$dir/"
done

echo "Copied GOI public staging tree to $DST"
