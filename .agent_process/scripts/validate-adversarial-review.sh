#!/usr/bin/env bash
# validate-adversarial-review.sh — Contract validator for adversarial-review.md
#
# Ensures adversarial review artifacts follow the template rules:
# - Binary verdicts only (PASS or FAIL, no qualifiers)
# - File:line evidence for each verdict
# - Summary with X/Y count
#
# Usage:
#   bash test/contract/validate-adversarial-review.sh path/to/adversarial-review.md

set -uo pipefail

FILE="${1:-}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: validate-adversarial-review.sh <path/to/adversarial-review.md>"
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

# --- 1. Extract all verdict lines ---
# Multiple formats seen in the wild:
#   **Verdict:** PASS
#   | AC1 | **PASS** | ...
#   **PASS** — standalone
#   AC1: BLOCKED  (this is wrong — should be PASS or FAIL)

# Check for **Verdict:** style
VERDICT_LINES=$(grep -iE "\*\*Verdict:\*\*" "$FILE" || true)
# Check for table-style verdicts (bold or plain)
TABLE_VERDICTS=$(grep -iE "^\|.*((\*\*(PASS|FAIL|BLOCKED)\*\*)|\b(PASS|FAIL|BLOCKED)\b)" "$FILE" | grep -viE "^\|.*Verdict" || true)
# Check for inline header-style: **PASS**, **FAIL**
HEADER_VERDICTS=$(grep -E "^##.*\b(AC|Criterion)" "$FILE" || true)

VERDICT_COUNT=0
QUALIFIED_PASSES=0
INVALID_VERDICTS=0

# Process **Verdict:** lines
if [[ -n "$VERDICT_LINES" ]]; then
  while IFS= read -r line; do
    ((VERDICT_COUNT++))
    verdict=$(echo "$line" | sed 's/.*\*\*Verdict:\*\*\s*//' | xargs)

    # Check for qualified passes: "PASS (something)" or "PASS — something"
    if echo "$verdict" | grep -qiE "^PASS\s*[\(—–-]"; then
      violation "Qualified pass detected (line): $line"
      ((QUALIFIED_PASSES++))
    elif echo "$verdict" | grep -qiE "^(PASS|FAIL)$"; then
      : # Clean verdict, good
    elif echo "$verdict" | grep -qiE "^BLOCKED"; then
      violation "BLOCKED is not a valid adversarial review verdict (must be PASS or FAIL): $line"
      ((INVALID_VERDICTS++))
    else
      violation "Unrecognized verdict: '$verdict' from line: $line"
      ((INVALID_VERDICTS++))
    fi
  done <<< "$VERDICT_LINES"
fi

# Process table-style verdicts
if [[ -n "$TABLE_VERDICTS" ]]; then
  while IFS= read -r line; do
    ((VERDICT_COUNT++))

    if echo "$line" | grep -qiE "\|\s*\*{0,2}BLOCKED\*{0,2}\s*\|"; then
      violation "BLOCKED used in table verdict (must be PASS or FAIL): $line"
      ((INVALID_VERDICTS++))
    elif echo "$line" | grep -qiE "PASS\s*[\(]"; then
      violation "Qualified pass in table: $line"
      ((QUALIFIED_PASSES++))
    fi
  done <<< "$TABLE_VERDICTS"
fi

if [[ "$VERDICT_COUNT" -eq 0 ]]; then
  violation "No verdicts found in file"
else
  echo "  INFO: Found ${VERDICT_COUNT} verdict(s)"
fi

if [[ "$QUALIFIED_PASSES" -eq 0 && "$INVALID_VERDICTS" -eq 0 && "$VERDICT_COUNT" -gt 0 ]]; then
  echo "  PASS: All verdicts are binary (PASS or FAIL)"
fi

# --- 2. Check for file:line evidence ---
# Look for patterns like: `path/to/file.ts`, lines 42-58
# or: File: `path/to/file.ts`, line 34
# or: `file.ts` line 42
EVIDENCE_LINES=$(grep -cE '`[^`]+\.(ts|js|py|sh|md|json|yaml|yml)`' "$FILE" 2>/dev/null || true)
EVIDENCE_LINES="${EVIDENCE_LINES:-0}"

if [[ "$EVIDENCE_LINES" -gt 0 ]]; then
  echo "  PASS: File references found (${EVIDENCE_LINES} citations)"
else
  # Some reviews cite evidence differently (grep commands, etc.)
  ALT_EVIDENCE=$(grep -cE "(rg |grep |lines? [0-9]|line [0-9])" "$FILE" 2>/dev/null || true)
  ALT_EVIDENCE="${ALT_EVIDENCE:-0}"
  if [[ "$ALT_EVIDENCE" -gt 0 ]]; then
    warning "Evidence uses alternative format (grep/line refs) instead of file:line citations"
  else
    violation "No file evidence found — verdicts must cite file:line"
  fi
fi

# --- 3. Summary section ---
if grep -qiE "(summary|overall|result)" "$FILE"; then
  echo "  PASS: Summary/Overall section present"

  # Check for X/Y count
  if grep -qE "[0-9]+/[0-9]+" "$FILE"; then
    echo "  PASS: X/Y criteria count found"
  else
    warning "No X/Y criteria count in summary"
  fi
else
  violation "No Summary or Overall section found"
fi

# --- 4. Reviewer attribution ---
if grep -qiE "(reviewer|fresh|independent|zero.*context)" "$FILE"; then
  echo "  PASS: Reviewer attribution present"
else
  warning "No reviewer attribution (expected 'Fresh instance' or similar)"
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
