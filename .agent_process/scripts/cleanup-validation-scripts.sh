#!/usr/bin/env bash
set -euo pipefail

# Remove orphaned validation scripts (scripts with no matching work directory)
#
# Safe to run: only removes scripts that have no corresponding work directory,
# meaning they're from old/renamed scopes that no longer exist.
#
# Usage:
#   ./cleanup-validation-scripts.sh           # Actually remove orphans
#   ./cleanup-validation-scripts.sh --dry-run # Preview what would be removed

SCRIPT_DIR=".agent_process/scripts/after_edit"
WORK_DIR=".agent_process/work"
DRY_RUN=${1:-}

# Verify we're in a project with .agent_process
if [[ ! -d "$SCRIPT_DIR" ]]; then
  echo "Error: No .agent_process/scripts/after_edit/ directory found"
  echo "Run this from a project root with ai_agent_process installed"
  exit 1
fi

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "🔍 DRY RUN MODE - no changes will be made"
  echo ""
fi

REMOVED=0
ERRORS=0

echo "═══════════════════════════════════════════════════════"
echo "    Validation Script Cleanup"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "🗑️  Removing orphan scripts (no matching work directory)..."
for script in "$SCRIPT_DIR"/validate-*.sh; do
  [[ -f "$script" ]] || continue
  # Extract scope name - escape the dot in .sh to avoid matching 'ash' in 'dashboard'
  scope=$(basename "$script" | sed 's/validate-//;s/\.sh$//')

  # Skip if work directory exists
  if [[ -d "$WORK_DIR/$scope" ]]; then
    continue
  fi

  if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "  Would remove: validate-$scope.sh"
    REMOVED=$((REMOVED + 1))
  else
    if rm "$script" 2>/dev/null; then
      echo "  ✅ Removed: validate-$scope.sh"
      REMOVED=$((REMOVED + 1))
    else
      echo "  ❌ Failed to remove: validate-$scope.sh"
      ERRORS=$((ERRORS + 1))
    fi
  fi
done
echo ""

echo "═══════════════════════════════════════════════════════"
echo "    Cleanup Summary"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "DRY RUN - no changes made"
  echo "Would remove: $REMOVED orphan scripts"
  echo ""
  echo "Run without --dry-run to apply changes"
else
  echo "✅ Removed orphans: $REMOVED"
  if [[ $ERRORS -gt 0 ]]; then
    echo "❌ Errors:          $ERRORS"
  fi
fi

echo ""

# Show remaining state
REMAINING=$(ls "$SCRIPT_DIR"/validate-*.sh 2>/dev/null | wc -l | tr -d ' ')
WORK_DIRS=$(ls -d "$WORK_DIR"/*/ 2>/dev/null | grep -v '_breakdowns\|_noscope' | wc -l | tr -d ' ')

echo "Post-cleanup state:"
echo "  Validation scripts: $REMAINING"
echo "  Work directories:   $WORK_DIRS"
