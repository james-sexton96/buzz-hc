#!/usr/bin/env bash
# validate-scope-events.sh — Contract validator for scope-events.log files
#
# Validates that a scope event log has:
#   - Valid timestamp, event type, and scope field on every line
#   - Coherent lifecycle (started before closed, iterations sequential)
#
# Usage:
#   bash test/contract/validate-scope-events.sh path/to/scope-events.log
#
# Exit 0 = PASS, Exit 1 = FAIL

set -uo pipefail

FILE="${1:-}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: validate-scope-events.sh <path/to/scope-events.log>"
  exit 1
fi

VIOLATIONS=0
WARNINGS=0

violation() {
  echo "  FAIL: $1"
  VIOLATIONS=$((VIOLATIONS + 1))
}

warning() {
  echo "  WARN: $1"
  WARNINGS=$((WARNINGS + 1))
}

echo "Validating: $FILE"
echo ""

# Valid event types — the contract
VALID_TYPES="SCOPE_START|ITERATION_START|ITERATION_CLOSE|WU_CREATE|WU_UPDATE|SCOPE_CLOSE|COMMENT|ERROR"

# ISO-8601 timestamp pattern (good enough — not a full ISO parser, but catches garbage)
TS_PATTERN='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z'

LINE_NUM=0
HAS_SCOPE_START=false
HAS_SCOPE_CLOSE=false
SCOPE_CLOSED_AT=0
OPEN_ITERATIONS=""
SCOPE_NAME=""

while IFS= read -r line; do
  LINE_NUM=$((LINE_NUM + 1))
  [[ -z "$line" ]] && continue

  # --- Field 1: Timestamp ---
  local_ts=$(echo "$line" | cut -d' ' -f1)
  if ! echo "$local_ts" | grep -qE "$TS_PATTERN"; then
    violation "Line ${LINE_NUM}: Invalid timestamp '${local_ts}'"
    continue
  fi

  # --- Field 2: Event type ---
  local_type=$(echo "$line" | cut -d' ' -f2)
  if ! echo "$local_type" | grep -qE "^(${VALID_TYPES})$"; then
    violation "Line ${LINE_NUM}: Invalid event type '${local_type}'"
    continue
  fi

  # --- Field 3+: Must contain scope=something ---
  if ! echo "$line" | grep -qE 'scope=[^ ]+'; then
    violation "Line ${LINE_NUM}: Missing scope= field"
    continue
  fi

  # Extract scope name from this line
  local_scope=$(echo "$line" | sed -n 's/.*scope=\([^ ]*\).*/\1/p')

  # Track scope name consistency
  if [[ -z "$SCOPE_NAME" ]]; then
    SCOPE_NAME="$local_scope"
  elif [[ "$local_scope" != "$SCOPE_NAME" ]]; then
    warning "Line ${LINE_NUM}: Scope mismatch '${local_scope}' vs '${SCOPE_NAME}' (multi-scope log?)"
  fi

  # --- Lifecycle coherence ---
  case "$local_type" in
    SCOPE_START)
      if [[ "$HAS_SCOPE_START" == true ]]; then
        warning "Line ${LINE_NUM}: Duplicate SCOPE_START"
      fi
      HAS_SCOPE_START=true
      ;;
    SCOPE_CLOSE)
      if [[ "$HAS_SCOPE_CLOSE" == true ]]; then
        violation "Line ${LINE_NUM}: Scope closed twice"
      fi
      if [[ "$HAS_SCOPE_START" != true ]]; then
        violation "Line ${LINE_NUM}: SCOPE_CLOSE without SCOPE_START"
      fi
      HAS_SCOPE_CLOSE=true
      SCOPE_CLOSED_AT=$LINE_NUM
      ;;
    ITERATION_START)
      if [[ "$HAS_SCOPE_START" != true ]]; then
        violation "Line ${LINE_NUM}: ITERATION_START before SCOPE_START"
      fi
      if [[ "$HAS_SCOPE_CLOSE" == true ]]; then
        violation "Line ${LINE_NUM}: ITERATION_START after SCOPE_CLOSE"
      fi
      # Track open iteration
      local_iter=$(echo "$line" | sed -n 's/.*iteration=\([^ ]*\).*/\1/p')
      if [[ -n "$local_iter" ]]; then
        OPEN_ITERATIONS="${OPEN_ITERATIONS} ${local_iter}"
      fi
      ;;
    ITERATION_CLOSE)
      if [[ "$HAS_SCOPE_START" != true ]]; then
        violation "Line ${LINE_NUM}: ITERATION_CLOSE before SCOPE_START"
      fi
      ;;
    WU_CREATE|WU_UPDATE)
      if [[ "$HAS_SCOPE_START" != true ]]; then
        violation "Line ${LINE_NUM}: ${local_type} before SCOPE_START"
      fi
      if [[ "$HAS_SCOPE_CLOSE" == true ]]; then
        violation "Line ${LINE_NUM}: ${local_type} after SCOPE_CLOSE"
      fi
      ;;
    COMMENT|ERROR)
      # These can appear anywhere — no lifecycle constraints
      ;;
  esac

  # Events after scope close (except ERROR/COMMENT) are suspicious
  if [[ "$HAS_SCOPE_CLOSE" == true && "$SCOPE_CLOSED_AT" -ne "$LINE_NUM" ]]; then
    if [[ "$local_type" != "COMMENT" && "$local_type" != "ERROR" ]]; then
      violation "Line ${LINE_NUM}: Event '${local_type}' after SCOPE_CLOSE at line ${SCOPE_CLOSED_AT}"
    fi
  fi

done < "$FILE"

# --- Summary checks ---

if [[ "$LINE_NUM" -eq 0 ]]; then
  violation "Empty scope-events.log file"
else
  echo "  INFO: ${LINE_NUM} events"
fi

if [[ "$HAS_SCOPE_START" == true ]]; then
  echo "  PASS: Scope lifecycle started"
else
  warning "No SCOPE_START event found"
fi

if [[ "$HAS_SCOPE_CLOSE" == true ]]; then
  echo "  INFO: Scope was closed"
fi

# Check for ERROR events
ERROR_COUNT=$(grep -c ' ERROR ' "$FILE" 2>/dev/null || true)
ERROR_COUNT="${ERROR_COUNT:-0}"
if [[ "$ERROR_COUNT" -gt 0 ]]; then
  warning "${ERROR_COUNT} ERROR events found"
fi

# --- Report ---
echo ""
echo "Results: ${VIOLATIONS} violations, ${WARNINGS} warnings"

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo "VERDICT: FAIL"
  exit 1
else
  if [[ "$WARNINGS" -gt 0 ]]; then
    echo "VERDICT: PASS (with warnings)"
  else
    echo "VERDICT: PASS"
  fi
  exit 0
fi
