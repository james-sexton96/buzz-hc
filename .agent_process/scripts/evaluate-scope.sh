#!/usr/bin/env bash
# evaluate-scope.sh — Validate all artifacts in a scope's work folder
#
# Runs contract validators against results.md, adversarial-review.md,
# iteration_plan.md, scope-events.log, and knowledge JSONL files.
#
# Usage:
#   bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/<scope>
#   bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/<scope> --strict
#
# Installed to .agent_process/scripts/ by install.sh

set -uo pipefail

SCOPE_PATH="${1:-}"
STRICT="${2:-}"

if [[ -z "$SCOPE_PATH" || ! -d "$SCOPE_PATH" ]]; then
  echo "Usage: evaluate-scope.sh <path/to/scope/work/folder> [--strict]"
  echo "Example: bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/my_scope"
  exit 1
fi

# Find the scripts directory (could be in .agent_process/scripts/ or test/contract/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Look for validators relative to this script
if [[ -f "$SCRIPT_DIR/validate-results.sh" ]]; then
  VALIDATOR_DIR="$SCRIPT_DIR"
elif [[ -f "$SCRIPT_DIR/../test/contract/validate-results.sh" ]]; then
  VALIDATOR_DIR="$SCRIPT_DIR/../test/contract"
else
  # Try project root
  PROJECT_ROOT="$SCRIPT_DIR"
  while [[ "$PROJECT_ROOT" != "/" ]]; do
    if [[ -d "$PROJECT_ROOT/.agent_process" ]]; then break; fi
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
  done
  if [[ -f "$PROJECT_ROOT/.agent_process/scripts/validate-results.sh" ]]; then
    VALIDATOR_DIR="$PROJECT_ROOT/.agent_process/scripts"
  else
    echo "Error: Cannot find validator scripts"
    exit 1
  fi
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_WARN=0

run_validator() {
  local validator="$1" file="$2" label="$3"
  local extra_args="${4:-}"

  if [[ ! -f "$file" ]]; then
    return
  fi

  local rel_path="${file#$SCOPE_PATH/}"
  echo -e "${BLUE}  $label: $rel_path${NC}"

  local output
  output=$(bash "$VALIDATOR_DIR/$validator" "$file" $extra_args 2>&1)
  local exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    if echo "$output" | grep -q "WARN"; then
      echo -e "    ${YELLOW}PASS (with warnings)${NC}"
      ((TOTAL_WARN++))
    else
      echo -e "    ${GREEN}PASS${NC}"
    fi
    ((TOTAL_PASS++))
  else
    echo -e "    ${RED}FAIL${NC}"
    echo "$output" | grep "FAIL:" | sed 's/^/      /'
    ((TOTAL_FAIL++))
  fi
}

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Scope Artifact Evaluation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo "Target: $SCOPE_PATH"
echo ""

# --- Iteration Plan ---
if [[ -f "$SCOPE_PATH/iteration_plan.md" ]]; then
  run_validator "validate-iteration-plan.sh" "$SCOPE_PATH/iteration_plan.md" "Plan"
fi

# --- Results files (in each iteration folder) ---
while IFS= read -r file; do
  run_validator "validate-results.sh" "$file" "Results" "$STRICT"
done < <(find "$SCOPE_PATH" -name "results.md" -not -path "*/templates/*" 2>/dev/null | sort)

# --- Adversarial review files ---
while IFS= read -r file; do
  run_validator "validate-adversarial-review.sh" "$file" "Review"
done < <(find "$SCOPE_PATH" -name "adversarial-review.md" 2>/dev/null | sort)

# --- Scope event logs ---
while IFS= read -r file; do
  run_validator "validate-scope-events.sh" "$file" "ScopeEvents"
done < <(find "$SCOPE_PATH" -name "scope-events.log" 2>/dev/null | sort)

# --- Knowledge files (at project level, not scope level) ---
KNOWLEDGE_DIR=""
# Walk up to find .agent_process/knowledge/
CHECK_DIR="$SCOPE_PATH"
while [[ "$CHECK_DIR" != "/" ]]; do
  if [[ -d "$CHECK_DIR/knowledge" ]]; then
    KNOWLEDGE_DIR="$CHECK_DIR/knowledge"
    break
  fi
  CHECK_DIR="$(dirname "$CHECK_DIR")"
done

if [[ -n "$KNOWLEDGE_DIR" ]]; then
  while IFS= read -r file; do
    # Skip schema-only files (1 line = just the header)
    line_count=$(wc -l < "$file" | tr -d ' ')
    if [[ "$line_count" -gt 1 ]]; then
      run_validator "validate-knowledge-entry.sh" "$file" "Knowledge"
    fi
  done < <(find "$KNOWLEDGE_DIR" -name "*.jsonl" 2>/dev/null | sort)
fi

# --- Summary ---
echo ""
echo -e "${BLUE}───────────────────────────────────────────────${NC}"
local total=$((TOTAL_PASS + TOTAL_FAIL))
echo "  Artifacts validated: ${total}"
echo -e "  ${GREEN}Pass: ${TOTAL_PASS}${NC} (${TOTAL_WARN} with warnings)"
echo -e "  ${RED}Fail: ${TOTAL_FAIL}${NC}"

if [[ $TOTAL_FAIL -gt 0 ]]; then
  echo ""
  echo -e "  ${RED}OVERALL: FAIL${NC}"
  exit 1
elif [[ $total -eq 0 ]]; then
  echo ""
  echo -e "  ${YELLOW}No artifacts found to validate${NC}"
  exit 0
else
  echo ""
  echo -e "  ${GREEN}OVERALL: PASS${NC}"
  exit 0
fi
