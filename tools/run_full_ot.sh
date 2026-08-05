#!/bin/bash
# Drives OT_to_English.py across all 39 OT books / ~929 chapters / ~23,213 verses.
# Resume-safe: OT_to_English.py skips verses whose output file already exists,
# so killing and re-running this picks up where it left off.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DB="$REPO_ROOT/Meta_Bible_Data/Bible_Noun_Extraction/bible_noun.sqlite3"
LOG="$REPO_ROOT/Meta_Bible_Data/logs/full_ot_translation_run.log"
mkdir -p "$(dirname "$LOG")"

BOOKS="GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL"

echo "=== Full OT translation run started $(date) ===" | tee -a "$LOG"

for book in $BOOKS; do
  chapters=$(sqlite3 "$DB" "SELECT DISTINCT chapter_number FROM verses v JOIN books b ON b.book_id=v.book_id WHERE b.book_code='$book' ORDER BY 1")
  for ch in $chapters; do
    echo "--- $book chapter $ch : $(date) ---" | tee -a "$LOG"
    python3 "$SCRIPT_DIR/OT_to_English.py" --book "$book" --chapter "$ch" 2>&1 | tee -a "$LOG"
  done
done

echo "=== Full OT translation run finished $(date) ===" | tee -a "$LOG"
