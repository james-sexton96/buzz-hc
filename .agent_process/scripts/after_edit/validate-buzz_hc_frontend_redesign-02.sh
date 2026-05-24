#!/usr/bin/env bash
# Validation script for buzz_hc_frontend_redesign-02
# Scoped checks for the Bloomberg-terminal UI redesign — Part 2 (run screen + persistence)
# bash 3.2 compatible (macOS default) — no associative arrays, no [[ ... =~ ]]
set -euo pipefail

SCOPE="buzz_hc_frontend_redesign-02"
ITERATION="${1:-iteration_01}"
PROJECT_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "=== Validating $SCOPE / $ITERATION ==="

FAILED=0

# 1. TypeScript check (web/pnpm tsc -> "tsc --noEmit" per package.json)
echo "[1] Running TypeScript check (web/pnpm tsc)..."
if (cd web && pnpm tsc) >/tmp/buzz_tsc.log 2>&1; then
  echo "  OK: TypeScript check passed"
else
  echo "  FAIL: TypeScript check failed — see /tmp/buzz_tsc.log"
  tail -20 /tmp/buzz_tsc.log
  FAILED=1
fi

# 2. Jest tests must pass with 4+ tests (3 existing + 1 new useRunSession test)
echo "[2] Running Jest tests (web/pnpm test)..."
if (cd web && pnpm test) >/tmp/buzz_jest.log 2>&1; then
  PASS_COUNT=$(grep -E "Tests:[[:space:]]+[0-9]+ passed" /tmp/buzz_jest.log | grep -oE "[0-9]+ passed" | head -1 | grep -oE "[0-9]+" || echo "0")
  if [ -z "$PASS_COUNT" ]; then
    PASS_COUNT=0
  fi
  if [ "$PASS_COUNT" -ge 4 ]; then
    echo "  OK: $PASS_COUNT Jest tests passed (>=4 required)"
  else
    echo "  FAIL: expected >=4 passing Jest tests, found $PASS_COUNT"
    tail -30 /tmp/buzz_jest.log
    FAILED=1
  fi
else
  echo "  FAIL: Jest run failed — see /tmp/buzz_jest.log"
  tail -30 /tmp/buzz_jest.log
  FAILED=1
fi

# 3. web/app/run/[id]/page.tsx exists
echo "[3] Checking web/app/run/[id]/page.tsx exists..."
if [ -f "web/app/run/[id]/page.tsx" ]; then
  echo "  OK: web/app/run/[id]/page.tsx exists"
else
  echo "  FAIL: web/app/run/[id]/page.tsx is missing"
  FAILED=1
fi

# 4. web/components/buzz/SwarmTopology.tsx exists
echo "[4] Checking web/components/buzz/SwarmTopology.tsx exists..."
if [ -f "web/components/buzz/SwarmTopology.tsx" ]; then
  echo "  OK: web/components/buzz/SwarmTopology.tsx exists"
else
  echo "  FAIL: web/components/buzz/SwarmTopology.tsx is missing"
  FAILED=1
fi

# 5. web/components/buzz/AgentCard.tsx exists
echo "[5] Checking web/components/buzz/AgentCard.tsx exists..."
if [ -f "web/components/buzz/AgentCard.tsx" ]; then
  echo "  OK: web/components/buzz/AgentCard.tsx exists"
else
  echo "  FAIL: web/components/buzz/AgentCard.tsx is missing"
  FAILED=1
fi

# 6. web/hooks/useRunSession.ts must NOT contain "new EventSource"
echo "[6] Checking useRunSession.ts has no 'new EventSource' construction..."
HOOK_FILE="web/hooks/useRunSession.ts"
if [ ! -f "$HOOK_FILE" ]; then
  echo "  FAIL: $HOOK_FILE missing"
  FAILED=1
else
  if grep -q "new EventSource" "$HOOK_FILE"; then
    echo "  FAIL: 'new EventSource' still present in $HOOK_FILE — SSE bookkeeping was not removed"
    grep -n "new EventSource" "$HOOK_FILE"
    FAILED=1
  else
    echo "  OK: no 'new EventSource' construction in $HOOK_FILE"
  fi
fi

# 7. web/app/sessions/[id]/page.tsx must contain "router.replace" (status-aware redirect)
echo "[7] Checking web/app/sessions/[id]/page.tsx uses router.replace..."
SESSIONS_FILE="web/app/sessions/[id]/page.tsx"
if [ ! -f "$SESSIONS_FILE" ]; then
  echo "  FAIL: $SESSIONS_FILE missing"
  FAILED=1
else
  if grep -q "router.replace" "$SESSIONS_FILE"; then
    echo "  OK: router.replace present in $SESSIONS_FILE"
  else
    echo "  FAIL: router.replace not found in $SESSIONS_FILE — back-button-safe redirect not implemented"
    FAILED=1
  fi
fi

# 8. No lucide-react imports in any web/components/buzz/ file or web/app/run/[id]/page.tsx
echo "[8] Checking no lucide-react imports in scoped UI files..."
LUCIDE_HITS=""

# Scan all files under web/components/buzz/ (if directory exists)
if [ -d "web/components/buzz" ]; then
  # bash 3.2 friendly iteration — use find + while read
  while IFS= read -r f; do
    if [ -n "$f" ] && [ -f "$f" ]; then
      HITS=$(grep -n "from ['\"]lucide-react['\"]" "$f" || true)
      if [ -n "$HITS" ]; then
        LUCIDE_HITS="$LUCIDE_HITS
$f:
$HITS"
      fi
    fi
  done < <(find web/components/buzz -type f \( -name '*.tsx' -o -name '*.ts' \))
fi

# Scan /run/[id]/page.tsx
RUN_ID_PAGE="web/app/run/[id]/page.tsx"
if [ -f "$RUN_ID_PAGE" ]; then
  HITS=$(grep -n "from ['\"]lucide-react['\"]" "$RUN_ID_PAGE" || true)
  if [ -n "$HITS" ]; then
    LUCIDE_HITS="$LUCIDE_HITS
$RUN_ID_PAGE:
$HITS"
  fi
fi

if [ -n "$LUCIDE_HITS" ]; then
  echo "  FAIL: lucide-react imports found in scoped UI files:"
  printf "%s\n" "$LUCIDE_HITS"
  FAILED=1
else
  echo "  OK: no lucide-react imports in scoped UI files"
fi

echo ""
if [ "$FAILED" -ne 0 ]; then
  echo "=== Validation FAILED ==="
  exit 1
fi
echo "=== Scoped validation passed ==="
