#!/usr/bin/env bash
# Regenerates goi_bible_shell.db from schema.sql + reference_seed.sql.
# Rerun only when the schema or the reference/lookup data changes.
set -euo pipefail
cd "$(dirname "$0")"

rm -f goi_bible_shell.db
sqlite3 goi_bible_shell.db < schema.sql
sqlite3 goi_bible_shell.db < reference_seed.sql

echo "Built goi_bible_shell.db:"
sqlite3 goi_bible_shell.db "SELECT 'editions', count(*) FROM editions UNION ALL SELECT 'books', count(*) FROM books UNION ALL SELECT 'iso_languages', count(*) FROM iso_languages UNION ALL SELECT 'iso_scripts', count(*) FROM iso_scripts UNION ALL SELECT 'iso_regions', count(*) FROM iso_regions UNION ALL SELECT 'verses', count(*) FROM verses;"
