#!/usr/bin/env bash
# validate-results.sh — Contract validator for results.md artifacts
#
# Checks that results.md files conform to the expected schema.
# Older artifacts may legitimately fail (format evolved over time).
# Exit 0 = valid, Exit 1 = violations found.
#
# Usage:
#   bash test/contract/validate-results.sh path/to/results.md
#   bash test/contract/validate-results.sh path/to/results.md --strict
#
# --strict mode rejects legacy format variations (pre-v2.5 artifacts)

set -uo pipefail

FILE="${1:-}"
STRICT="${2:-}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: validate-results.sh <path/to/results.md> [--strict]"
  exit 1
fi

VIOLATIONS=0
WARNINGS=0

violation() {
  echo "  FAIL: $1"
  ((VIOLATIONS++))
}

warning() {
  echo "  WARN: $1"
  ((WARNINGS++))
}

echo "Validating: $FILE"
echo ""

# --- 1. Status field exists and is valid ---
STATUS_LINE=$(grep -m1 "^\*\*Status:\*\*" "$FILE" || true)

if [[ -z "$STATUS_LINE" ]]; then
  violation "No **Status:** field found"
else
  # Extract the status value (everything after **Status:** )
  STATUS_VALUE=$(echo "$STATUS_LINE" | sed 's/\*\*Status:\*\*\s*//')

  # Check for known INVALID statuses first (before partial matching)
  # These are real mistakes agents have made
  BAD_STATUSES=("INCOMPLETE" "IN PROGRESS" "IN_PROGRESS" "PARTIAL" "PENDING" "DONE" "PASSED" "FAILED")
  STATUS_INVALID=false
  for bad in "${BAD_STATUSES[@]}"; do
    if echo "$STATUS_VALUE" | grep -qi "\b${bad}\b"; then
      violation "Invalid status value: $STATUS_VALUE"
      STATUS_INVALID=true
      break
    fi
  done

  if [[ "$STATUS_INVALID" == "false" ]]; then
    # Valid statuses (current format with emoji)
    if echo "$STATUS_VALUE" | grep -qE "(✅ COMPLETE|⚠️ NEEDS REVISION|🚫 BLOCKED)"; then
      echo "  PASS: Status is valid (current format)"
    elif echo "$STATUS_VALUE" | grep -qiE "^\s*(COMPLETE|NEEDS REVISION|BLOCKED)"; then
      # Legacy format without emoji — anchored to start to avoid "INCOMPLETE" matching
      if [[ "$STRICT" == "--strict" ]]; then
        violation "Status uses legacy format (no emoji): $STATUS_VALUE"
      else
        warning "Status uses legacy format (acceptable pre-v2.5): $STATUS_VALUE"
      fi
    else
      violation "Status is invalid: $STATUS_VALUE"
    fi
  fi
fi

# --- 2. Required sections exist ---
REQUIRED_SECTIONS=("Summary" "Changed Files" "Validation" "Acceptance Criteria")

for section in "${REQUIRED_SECTIONS[@]}"; do
  if grep -qE "^##\s+.*${section}" "$FILE"; then
    echo "  PASS: Section '${section}' found"
  else
    # Try looser match (some agents use ## Changes Made, ## Files Changed, etc.)
    case "$section" in
      "Changed Files")
        if grep -qiE "^##\s+(Changed Files|Changes Made|Files Changed|Changes)" "$FILE"; then
          warning "Section '${section}' found with variant name"
        else
          violation "Missing required section: ${section}"
        fi
        ;;
      "Acceptance Criteria")
        if grep -qiE "^##\s+(Acceptance Criteria|Criteria)" "$FILE"; then
          echo "  PASS: Section '${section}' found"
        elif grep -qiE "\*\*Acceptance Criteria" "$FILE"; then
          warning "Acceptance Criteria found as bold text, not section header"
        else
          violation "Missing required section: ${section}"
        fi
        ;;
      *)
        violation "Missing required section: ${section}"
        ;;
    esac
  fi
done

# --- 3. Adversarial Review section (post-v2.5 only) ---
if grep -qiE "^##\s+Adversarial Review" "$FILE"; then
  echo "  PASS: Adversarial Review section present"
elif [[ "$STRICT" == "--strict" ]]; then
  violation "Missing Adversarial Review section (required in strict mode)"
else
  warning "No Adversarial Review section (expected in v2.5+ artifacts)"
fi

# --- 4. Date field exists ---
if grep -qE "^\*\*Date:\*\*" "$FILE"; then
  echo "  PASS: Date field present"
else
  violation "No **Date:** field found"
fi

# --- 5. Title matches expected format ---
TITLE=$(head -1 "$FILE")
if echo "$TITLE" | grep -qE "^#\s+Iteration Results"; then
  echo "  PASS: Title follows expected format"
else
  warning "Title doesn't match expected format: $TITLE"
fi

# --- 6. Acceptance criteria have checkboxes ---
AC_CHECKED=$(grep -cE "^\s*-\s+\[x\]" "$FILE" 2>/dev/null || true)
AC_UNCHECKED=$(grep -cE "^\s*-\s+\[ \]" "$FILE" 2>/dev/null || true)
# grep -c returns empty on no match in some shells; default to 0
AC_CHECKED="${AC_CHECKED:-0}"
AC_UNCHECKED="${AC_UNCHECKED:-0}"
AC_TOTAL=$((AC_CHECKED + AC_UNCHECKED))

if [[ "$AC_TOTAL" -gt 0 ]]; then
  echo "  PASS: Found ${AC_TOTAL} acceptance criteria (${AC_CHECKED} checked, ${AC_UNCHECKED} unchecked)"
else
  warning "No checkbox-style acceptance criteria found"
fi

# --- 7. File length sanity check (max ~200 lines for results.md) ---
LINE_COUNT=$(wc -l < "$FILE" | tr -d ' ')
if [[ "$LINE_COUNT" -gt 300 ]]; then
  warning "results.md is ${LINE_COUNT} lines (recommended max ~200)"
fi

# --- 8. Bad status check moved to section 1 (check-before-match) ---

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
