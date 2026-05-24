#!/usr/bin/env bash
# validate-iteration-plan.sh — Contract validator for iteration_plan.md
#
# Checks that iteration plans conform to the expected schema:
# - Required sections exist (Acceptance Criteria, Files in Scope, etc.)
# - Criteria are actually frozen (checkboxes present)
# - Technical assessment populated
# - Brainstorm source documented (if applicable)
#
# Usage:
#   bash test/contract/validate-iteration-plan.sh path/to/iteration_plan.md

set -uo pipefail

FILE="${1:-}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: validate-iteration-plan.sh <path/to/iteration_plan.md>"
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

# --- 1. Required sections ---
REQUIRED_SECTIONS=(
  "Acceptance Criteria"
  "Files in Scope"
  "Validation"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if grep -qiE "^##\s+.*${section}" "$FILE"; then
    echo "  PASS: Section '${section}' found"
  else
    violation "Missing required section: ${section}"
  fi
done

# --- 2. Acceptance criteria have checkboxes (frozen = actionable) ---
AC_CHECKED=$(grep -cE "^\s*-\s+\[x\]" "$FILE" 2>/dev/null || true)
AC_UNCHECKED=$(grep -cE "^\s*-\s+\[ \]" "$FILE" 2>/dev/null || true)
AC_CHECKED="${AC_CHECKED:-0}"
AC_UNCHECKED="${AC_UNCHECKED:-0}"
AC_TOTAL=$((AC_CHECKED + AC_UNCHECKED))

if [[ "$AC_TOTAL" -gt 0 ]]; then
  echo "  PASS: Found ${AC_TOTAL} acceptance criteria checkboxes"
else
  # Could be numbered list instead
  AC_NUMBERED=$(grep -cE "^[0-9]+\.\s" "$FILE" 2>/dev/null || true)
  AC_NUMBERED="${AC_NUMBERED:-0}"
  if [[ "$AC_NUMBERED" -gt 2 ]]; then
    warning "Acceptance criteria use numbered list (checkboxes preferred for tracking)"
  else
    violation "No acceptance criteria found (need checkboxes or numbered list)"
  fi
fi

# --- 3. LOCKED marker present ---
if grep -qiE "LOCKED|DO NOT MODIFY|frozen" "$FILE"; then
  echo "  PASS: Criteria locked/frozen marker present"
else
  warning "No LOCKED/frozen marker found (criteria should be explicitly frozen)"
fi

# --- 4. Technical assessment section ---
if grep -qiE "^##\s+.*Technical Assessment" "$FILE"; then
  echo "  PASS: Technical Assessment section found"
elif grep -qiE "^##\s+.*Implementation" "$FILE"; then
  warning "No 'Technical Assessment' section, but 'Implementation' section found (variant name)"
else
  warning "No Technical Assessment section"
fi

# --- 5. Out of Scope section ---
if grep -qiE "^##\s+.*Out of Scope" "$FILE"; then
  echo "  PASS: Out of Scope section found"
else
  warning "No Out of Scope section (helps prevent scope creep)"
fi

# --- 6. Known Patterns & Constraints (knowledge base integration) ---
if grep -qiE "^##\s+.*Known Patterns|^##\s+.*Knowledge" "$FILE"; then
  echo "  PASS: Known Patterns / Knowledge section found"
else
  warning "No Known Patterns section (knowledge base may not have been queried)"
fi

# --- 7. Brainstorm source (if applicable) ---
if grep -qiE "brainstorm|ap-brainstorm|ap_brainstorm" "$FILE"; then
  echo "  INFO: Brainstorm-sourced requirement detected"
  if grep -qiE "source.*brainstorm|brainstorm.*doc" "$FILE"; then
    echo "  PASS: Brainstorm source reference present"
  else
    warning "Mentions brainstorm but no source reference"
  fi
fi

# --- 8. Iteration budget ---
if grep -qiE "iteration.*budget|max.*iteration|attempts" "$FILE"; then
  echo "  PASS: Iteration budget documented"
else
  warning "No iteration budget mentioned"
fi

# --- 9. Requirements source ---
if grep -qiE "requirements.*source|source.*requirement" "$FILE"; then
  echo "  PASS: Requirements source documented"
else
  warning "No requirements source path (needed for status updates)"
fi

# --- 10. Scope name in title ---
TITLE=$(head -1 "$FILE")
if echo "$TITLE" | grep -qE "^#\s+"; then
  echo "  PASS: Title present"
else
  warning "No title found on first line"
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
