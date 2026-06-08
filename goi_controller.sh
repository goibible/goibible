#!/bin/bash
# GOI Bible Translation Controller - Harness/Python Hybrid
# Enforces security policy while enabling --resume capability

set -euo pipefail

BOOK="$1"
PHASE="${2:-phase1_triage}"
RESUME_POINT="${3:-}"

# Security hardening (per policy)
export SECURE_MODE=1
export NETWORK_ACCESS=BLOCKED
ulimit -n 256  # Limit file descriptors

# Create harness task list
tasks new-list "GOI Translation: $BOOK ($PHASE)" --description "Automated translation pipeline with resume capability"
TASK_ID=$(tasks list | grep "GOI Translation" | awk '{print $1}' | tail -n1)

tasks add "Run $PHASE for $BOOK" --id $TASK_ID

tasks toggle $TASK_ID  # Mark as in-progress

# Execute with resume capability
if [ -n "$RESUME_POINT" ]; then
  echo "Resuming $PHASE from $RESUME_POINT..."
  python3 $PHASE.py --book="$BOOK" --resume="$RESUME_POINT"
else
  echo "Starting fresh $PHASE for $BOOK..."
  python3 $PHASE.py --book="$BOOK"
fi

# Quality gate enforcement
if [ $? -eq 0 ]; then
  tasks toggle $TASK_ID  # Mark as done
  echo "\n✅ Phase completed successfully!"
  echo "Next: Run 'tasks add "Advance to next phase"'"
else
  ERROR_LOG=$(mktemp)
  echo "❌ Translation failed - capturing error report"
  python3 qa_validator.py --last-error > "$ERROR_LOG"
  
  # Auto-trigger harness security report
  show_security_report \
    --title="GOI Translation Error" \
    --summary="Semantic integrity failure in $BOOK" \
    --findings_markdown="$(cat $ERROR_LOG)" \
    
  echo "\n🚨 Critical error! Review with: show_security_report"
  echo "Auto-recovery: ./goi_controller.sh $BOOK $PHASE $(tail -n1 $ERROR_LOG | grep -oP 'resume=\\K\\S+')"
  exit 1
fi