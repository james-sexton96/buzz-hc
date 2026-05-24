#!/usr/bin/env bash
# Validation script for buzz_hc_frontend_redesign-01
# Scoped checks for the Bloomberg-terminal UI redesign — Part 1 (foundation + static screens)
# bash 3.2 compatible (macOS default)
set -euo pipefail

SCOPE="buzz_hc_frontend_redesign-01"
ITERATION="${1:-iteration_01}"
PROJECT_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "=== Validating $SCOPE / $ITERATION ==="

FAILED=0

# 1. TypeScript validation (use `tsc` script — package.json defines `tsc: tsc --noEmit`)
echo "[1] Running TypeScript check (web/pnpm tsc)..."
if (cd web && pnpm tsc) >/tmp/buzz_tsc.log 2>&1; then
  echo "  OK: TypeScript check passed"
else
  echo "  FAIL: TypeScript check failed — see /tmp/buzz_tsc.log"
  tail -20 /tmp/buzz_tsc.log
  FAILED=1
fi

# 2. Jest tests must pass 3/3
echo "[2] Running Jest tests (web/pnpm test)..."
if (cd web && pnpm test) >/tmp/buzz_jest.log 2>&1; then
  PASS_COUNT=$(grep -E "Tests:[[:space:]]+[0-9]+ passed" /tmp/buzz_jest.log | grep -oE "[0-9]+ passed" | head -1 | grep -oE "[0-9]+" || echo "0")
  if [ "$PASS_COUNT" = "3" ]; then
    echo "  OK: 3/3 Jest tests passed"
  else
    echo "  FAIL: Expected 3 passing Jest tests, found $PASS_COUNT"
    tail -20 /tmp/buzz_jest.log
    FAILED=1
  fi
else
  echo "  FAIL: Jest tests failed — see /tmp/buzz_jest.log"
  tail -20 /tmp/buzz_jest.log
  FAILED=1
fi

# 3. Check that <html in web/app/layout.tsx contains className="dark"
echo "[3] Checking <html className=\"dark\"> in layout.tsx..."
LAYOUT_FILE="web/app/layout.tsx"
if [ ! -f "$LAYOUT_FILE" ]; then
  echo "  FAIL: $LAYOUT_FILE does not exist"
  FAILED=1
else
  HTML_LINE=$(grep -n "<html" "$LAYOUT_FILE" | head -1 || true)
  if [ -z "$HTML_LINE" ]; then
    echo "  FAIL: no <html tag found in $LAYOUT_FILE"
    FAILED=1
  elif echo "$HTML_LINE" | grep -q 'className="dark"'; then
    echo "  OK: <html className=\"dark\"> set in layout.tsx"
  else
    echo "  FAIL: <html tag in $LAYOUT_FILE is missing className=\"dark\""
    echo "    Found: $HTML_LINE"
    FAILED=1
  fi
fi

# 4. Check that web/app/globals.css contains oklch (token migration happened)
echo "[4] Checking OKLCH tokens in globals.css..."
GLOBALS_FILE="web/app/globals.css"
if [ ! -f "$GLOBALS_FILE" ]; then
  echo "  FAIL: $GLOBALS_FILE does not exist"
  FAILED=1
elif grep -q "oklch" "$GLOBALS_FILE"; then
  echo "  OK: oklch present in globals.css"
else
  echo "  FAIL: no oklch tokens found in $GLOBALS_FILE"
  FAILED=1
fi

# 5. Check that web/app/query/page.tsx exists
echo "[5] Checking web/app/query/page.tsx exists..."
if [ -f "web/app/query/page.tsx" ]; then
  echo "  OK: web/app/query/page.tsx exists"
else
  echo "  FAIL: web/app/query/page.tsx is missing"
  FAILED=1
fi

# 6. Check that web/components/buzz/TopNav.tsx exists
echo "[6] Checking web/components/buzz/TopNav.tsx exists..."
if [ -f "web/components/buzz/TopNav.tsx" ]; then
  echo "  OK: web/components/buzz/TopNav.tsx exists"
else
  echo "  FAIL: web/components/buzz/TopNav.tsx is missing"
  FAILED=1
fi

# 7. Check that web/components/buzz/SwarmGraph.tsx exists
echo "[7] Checking web/components/buzz/SwarmGraph.tsx exists..."
if [ -f "web/components/buzz/SwarmGraph.tsx" ]; then
  echo "  OK: web/components/buzz/SwarmGraph.tsx exists"
else
  echo "  FAIL: web/components/buzz/SwarmGraph.tsx is missing"
  FAILED=1
fi

# 8. Check that in-scope app files do NOT import from lucide-react
echo "[8] Checking no lucide-react imports in scoped app files..."
LUCIDE_FILES="web/app/page.tsx web/app/sessions/page.tsx web/app/query/page.tsx"
LUCIDE_HITS=""
for f in $LUCIDE_FILES; do
  if [ -f "$f" ]; then
    HITS=$(grep -n "from ['\"]lucide-react['\"]" "$f" || true)
    if [ -n "$HITS" ]; then
      LUCIDE_HITS="$LUCIDE_HITS\n$f:\n$HITS"
    fi
  fi
done
if [ -n "$LUCIDE_HITS" ]; then
  echo "  FAIL: lucide-react imports found in scoped app files:"
  printf "$LUCIDE_HITS\n"
  FAILED=1
else
  echo "  OK: no lucide-react imports in scoped app files"
fi

echo ""
if [ "$FAILED" -ne 0 ]; then
  echo "=== Validation FAILED ==="
  exit 1
fi
echo "=== Validation complete ==="
