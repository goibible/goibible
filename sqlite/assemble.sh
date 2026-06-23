#!/usr/bin/env bash
# Builds a full, working .sqlite3 from shell.sqlite3 + the version buffet.
# Usage: assemble.sh <target.sqlite3> [edition_id ...]
# With no edition_id args, loads every edition in versions/.
set -euo pipefail
cd "$(dirname "$0")"

TARGET="${1:-GOI_bible_assembled.sqlite3}"
shift || true

rm -f "$TARGET"
cp shell.sqlite3 "$TARGET"

if [ "$#" -gt 0 ]; then
    EDITIONS=("$@")
else
    EDITIONS=()
    for f in versions/*.sql; do
        EDITIONS+=("$(basename "$f" .sql)")
    done
fi

for ed in "${EDITIONS[@]}"; do
    echo "Loading $ed..."
    sqlite3 "$TARGET" < "versions/$ed.sql"
done

echo "Built $TARGET:"
sqlite3 "$TARGET" "SELECT edition_id, count(*) FROM verses GROUP BY edition_id;"
