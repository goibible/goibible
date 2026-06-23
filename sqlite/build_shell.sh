#!/usr/bin/env bash
# Regenerates shell.sqlite3 from schema.sql + reference_seed.sql.
# Rerun only when the schema or the reference/lookup data changes.
set -euo pipefail
cd "$(dirname "$0")"

rm -f shell.sqlite3
sqlite3 shell.sqlite3 < schema.sql
sqlite3 shell.sqlite3 < reference_seed.sql

echo "Built shell.sqlite3:"
sqlite3 shell.sqlite3 "SELECT 'editions', count(*) FROM editions UNION ALL SELECT 'books', count(*) FROM books UNION ALL SELECT 'iso_languages', count(*) FROM iso_languages UNION ALL SELECT 'iso_scripts', count(*) FROM iso_scripts UNION ALL SELECT 'iso_regions', count(*) FROM iso_regions UNION ALL SELECT 'verses', count(*) FROM verses;"
