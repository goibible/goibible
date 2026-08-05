#!/usr/bin/env bash
set -euo pipefail

SRC="/home/albert/projects/bible"
DST="/var/www/goibible.org/github"

echo "Source: $SRC"
echo "Destination: $DST"

mkdir -pv "$DST"

echo "Copying top-level files..."
rsync -av --delete "$SRC/README.md" "$DST/"
rsync -av --delete "$SRC/Meta_Bible_Data/docs/README_GOI.md" "$DST/README_GOI.md"
rsync -av --delete "$SRC/.gitignore" "$DST/"
rsync -av --delete \
  --exclude 'editions/' \
  --exclude '*.sqlite3' \
  --exclude '*.db' \
  --exclude '*.bak*' \
  "$SRC/Meta_Bible_Data/sqlite/" "$DST/Meta_Bible_Data/sqlite/"
rsync -av "$SRC/Meta_Bible_Data/sqlite/goi_bible_shell.db" "$DST/Meta_Bible_Data/sqlite/goi_bible_shell.db"

for dir in GOI_Bible Meta_Bible_Data/full_bible; do
  echo "Copying directory: $dir"
  mkdir -pv "$DST/$dir"
  rsync -av --delete --exclude '__pycache__/' --exclude '*.pyc' "$SRC/$dir/" "$DST/$dir/"
done

echo "Copied GOI public staging tree to $DST"
