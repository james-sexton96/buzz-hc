#!/usr/bin/env bash
# validate-knowledge-entry.sh — Contract validator for knowledge JSONL files
#
# Checks that each line in a .jsonl knowledge file has required fields
# and valid values.
#
# Usage:
#   bash test/contract/validate-knowledge-entry.sh path/to/patterns.jsonl

set -uo pipefail

FILE="${1:-}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: validate-knowledge-entry.sh <path/to/file.jsonl>"
  exit 1
fi

VIOLATIONS=0
WARNINGS=0
LINE_NUM=0
VALID=0

violation() {
  echo "  FAIL [line $LINE_NUM]: $1"
  ((VIOLATIONS++))
}

warning() {
  echo "  WARN [line $LINE_NUM]: $1"
  ((WARNINGS++))
}

echo "Validating: $FILE"
echo ""

# Determine expected type from filename
BASENAME=$(basename "$FILE" .jsonl)
VALID_TYPES=""
case "$BASENAME" in
  patterns)      VALID_TYPES="pattern" ;;
  gotchas)       VALID_TYPES="gotcha" ;;
  decisions)     VALID_TYPES="decision" ;;
  anti-patterns) VALID_TYPES="anti-pattern" ;;
  *)             VALID_TYPES="pattern|gotcha|decision|anti-pattern" ;;
esac

while IFS= read -r line; do
  ((LINE_NUM++))

  # Skip empty lines
  [[ -z "$line" ]] && continue

  # Validate JSON
  if ! echo "$line" | python3 -c "import json,sys; json.loads(sys.stdin.read())" 2>/dev/null; then
    violation "Invalid JSON"
    continue
  fi

  # Check required fields
  RESULT=$(echo "$line" | python3 -c "
import json, sys
entry = json.loads(sys.stdin.read())
errors = []
warnings = []

# Detect schema: metaswarm (fact/recommendation) vs legacy AP (scope/content)
is_metaswarm = 'fact' in entry
is_legacy = 'content' in entry or 'scope' in entry

if is_metaswarm:
    # Metaswarm schema: fact + recommendation required
    for field in ['fact', 'recommendation']:
        if field not in entry:
            errors.append(f'missing required field: {field}')
        elif not entry[field].strip():
            errors.append(f'{field} is empty')
    if 'confidence' not in entry:
        warnings.append('missing confidence field')
elif is_legacy:
    # Legacy AP schema: scope + content required
    for field in ['scope', 'content']:
        if field not in entry:
            errors.append(f'missing required field: {field}')
        elif not str(entry[field]).strip():
            errors.append(f'{field} is empty')
    if 'date' not in entry and 'added' not in entry:
        warnings.append('no date/added field')
else:
    errors.append('unrecognized schema — needs fact+recommendation or scope+content')

# Type field (recommended for both schemas)
if 'type' not in entry:
    warnings.append('missing type field')
else:
    valid = '${VALID_TYPES}'.split('|')
    # Also accept metaswarm types
    valid.extend(['api_behavior', 'code_quirk', 'dependency', 'performance', 'security'])
    if entry['type'] not in valid:
        errors.append(f'invalid type \"{entry[\"type\"]}\" (expected: {valid})')

print('ERRORS:' + '|'.join(errors))
print('WARNINGS:' + '|'.join(warnings))
" 2>/dev/null)

  ERRORS=$(echo "$RESULT" | grep "^ERRORS:" | sed 's/^ERRORS://')
  WARNS=$(echo "$RESULT" | grep "^WARNINGS:" | sed 's/^WARNINGS://')

  if [[ -n "$ERRORS" ]]; then
    IFS='|' read -ra ERR_ARR <<< "$ERRORS"
    for err in "${ERR_ARR[@]}"; do
      [[ -n "$err" ]] && violation "$err"
    done
  fi

  if [[ -n "$WARNS" ]]; then
    IFS='|' read -ra WARN_ARR <<< "$WARNS"
    for w in "${WARN_ARR[@]}"; do
      [[ -n "$w" ]] && warning "$w"
    done
  fi

  ((VALID++))
done < "$FILE"

echo ""
echo "  Entries: ${LINE_NUM} total, ${VALID} valid JSON"
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
