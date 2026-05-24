#!/usr/bin/env bash
set -euo pipefail

# Analyze validation script health and orphan status
#
# Reports:
# - Scripts with matching work directories (healthy)
# - Orphan scripts (no matching work directory)
# - Work directories missing validators
#
# Usage: ./analyze-validation-scripts.sh [--cleanup-preview]

SCRIPT_DIR=".agent_process/scripts/after_edit"
WORK_DIR=".agent_process/work"
CLEANUP_PREVIEW=${1:-}

# Verify we're in a project with .agent_process
if [[ ! -d "$SCRIPT_DIR" ]]; then
  echo "Error: No .agent_process/scripts/after_edit/ directory found"
  echo "Run this from a project root with ai_agent_process installed"
  exit 1
fi

echo "═══════════════════════════════════════════════════════"
echo "         Validation Script Health Analysis"
echo "═══════════════════════════════════════════════════════"
echo ""

# Count totals
TOTAL_SCRIPTS=$(ls "$SCRIPT_DIR"/validate-*.sh 2>/dev/null | wc -l | tr -d ' ')
TOTAL_WORK_DIRS=$(ls -d "$WORK_DIR"/*/ 2>/dev/null | grep -v '_breakdowns\|_noscope' | wc -l | tr -d ' ')

echo "📊 Overview"
echo "   Total validation scripts: $TOTAL_SCRIPTS"
echo "   Total work directories:   $TOTAL_WORK_DIRS"
echo ""

# Categorize scripts
MATCHED=()
ORPHANS=()

for script in "$SCRIPT_DIR"/validate-*.sh; do
  [[ -f "$script" ]] || continue
  # Extract scope name - escape the dot in .sh to avoid matching 'ash' in 'dashboard'
  scope=$(basename "$script" | sed 's/validate-//;s/\.sh$//')

  if [[ -d "$WORK_DIR/$scope" ]]; then
    MATCHED+=("$scope")
  else
    ORPHANS+=("$scope")
  fi
done

echo "✅ Matched (script + work dir): ${#MATCHED[@]}"
echo "❌ Orphans (script, no work):   ${#ORPHANS[@]}"
echo ""

# Show orphan patterns
echo "═══════════════════════════════════════════════════════"
echo "         Orphan Analysis by Prefix"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "Orphan prefixes (sorted by count):"
if [[ ${#ORPHANS[@]} -gt 0 ]]; then
  for scope in "${ORPHANS[@]}"; do
    # Extract prefix (first segment before numeric suffix or phase/scope marker)
    echo "$scope" | sed -E 's/(_[0-9]+[a-z]*_.*|_scope_.*|_phase_.*)//'
  done | sort | uniq -c | sort -rn | head -20
else
  echo "  (none - all scripts have matching work directories)"
fi

echo ""

# Show work dirs without validators
echo "═══════════════════════════════════════════════════════"
echo "    Work Directories Without Validators"
echo "═══════════════════════════════════════════════════════"
echo ""

MISSING_VALIDATORS=0
for dir in "$WORK_DIR"/*/; do
  [[ -d "$dir" ]] || continue
  scope=$(basename "$dir")
  # Skip internal directories
  [[ "$scope" == "_breakdowns" || "$scope" == "_noscope" ]] && continue

  if [[ ! -f "$SCRIPT_DIR/validate-$scope.sh" ]]; then
    echo "  📁 $scope"
    MISSING_VALIDATORS=$((MISSING_VALIDATORS + 1))
  fi
done

if [[ $MISSING_VALIDATORS -eq 0 ]]; then
  echo "  (none - all work directories have validators)"
fi

echo ""
echo "   Total without validators: $MISSING_VALIDATORS"
echo ""

# Cleanup preview
if [[ "$CLEANUP_PREVIEW" == "--cleanup-preview" ]]; then
  echo "═══════════════════════════════════════════════════════"
  echo "    Cleanup Preview (commands to remove orphans)"
  echo "═══════════════════════════════════════════════════════"
  echo ""
  if [[ ${#ORPHANS[@]} -gt 0 ]]; then
    for scope in "${ORPHANS[@]}"; do
      echo "rm '$SCRIPT_DIR/validate-$scope.sh'"
    done
  else
    echo "# No orphans to remove"
  fi
  echo ""
fi

echo "═══════════════════════════════════════════════════════"
echo "              Summary & Recommendations"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "1. ORPHAN CLEANUP: ${#ORPHANS[@]} scripts can be safely removed"
echo "   (they reference scopes with no work directories)"
echo ""
echo "2. VALIDATOR GAP: $MISSING_VALIDATORS work directories lack validators"
echo "   (this is normal - not all scopes need custom validators)"
echo ""

if [[ ${#ORPHANS[@]} -gt 0 ]]; then
  echo "Run with --cleanup-preview to see removal commands"
  echo "Run cleanup-validation-scripts.sh to remove orphans"
fi
