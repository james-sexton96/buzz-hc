#!/usr/bin/env bash
# Validation script for buzz_hc_frontend_redesign-03
# Scoped checks for the Bloomberg-terminal UI redesign — Part 3 (report dossier + KPI panels)
# bash 3.2 compatible (macOS default) — no associative arrays, no mapfile, no ${var^^}, no &>>
set -euo pipefail

SCOPE="buzz_hc_frontend_redesign-03"
ITERATION="${1:-iteration_01}"
PROJECT_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "=== Validating $SCOPE / $ITERATION ==="

FAILED=0

# 1. TypeScript check — zero errors (web/pnpm tsc -> "tsc --noEmit" per package.json)
echo "[1] Running TypeScript check (cd web && pnpm tsc)..."
if (cd web && pnpm tsc) >/tmp/buzz03_tsc.log 2>&1; then
  echo "  OK: TypeScript check passed"
else
  echo "  FAIL: TypeScript check failed — see /tmp/buzz03_tsc.log"
  tail -20 /tmp/buzz03_tsc.log
  FAILED=1
fi

# 2. Next.js production build must succeed (covers lint + build path)
echo "[2] Running Next.js build (cd web && pnpm build)..."
if (cd web && pnpm build) >/tmp/buzz03_build.log 2>&1; then
  echo "  OK: pnpm build succeeded"
else
  echo "  FAIL: pnpm build failed — see /tmp/buzz03_build.log"
  tail -40 /tmp/buzz03_build.log
  FAILED=1
fi

# 3. web/app/report/[id]/page.tsx exists
echo "[3] Checking web/app/report/[id]/page.tsx exists..."
if [ -f "web/app/report/[id]/page.tsx" ]; then
  echo "  OK: web/app/report/[id]/page.tsx exists"
else
  echo "  FAIL: web/app/report/[id]/page.tsx is missing"
  FAILED=1
fi

# 4. web/components/buzz/PanelCard.tsx exists
echo "[4] Checking web/components/buzz/PanelCard.tsx exists..."
if [ -f "web/components/buzz/PanelCard.tsx" ]; then
  echo "  OK: web/components/buzz/PanelCard.tsx exists"
else
  echo "  FAIL: web/components/buzz/PanelCard.tsx is missing"
  FAILED=1
fi

# 5. web/components/buzz/FootnoteDrawer.tsx exists
echo "[5] Checking web/components/buzz/FootnoteDrawer.tsx exists..."
if [ -f "web/components/buzz/FootnoteDrawer.tsx" ]; then
  echo "  OK: web/components/buzz/FootnoteDrawer.tsx exists"
else
  echo "  FAIL: web/components/buzz/FootnoteDrawer.tsx is missing"
  FAILED=1
fi

# 6. web/components/buzz/DonutChart.tsx exists
echo "[6] Checking web/components/buzz/DonutChart.tsx exists..."
if [ -f "web/components/buzz/DonutChart.tsx" ]; then
  echo "  OK: web/components/buzz/DonutChart.tsx exists"
else
  echo "  FAIL: web/components/buzz/DonutChart.tsx is missing"
  FAILED=1
fi

# 7. web/components/buzz/SparkLine.tsx exists
echo "[7] Checking web/components/buzz/SparkLine.tsx exists..."
if [ -f "web/components/buzz/SparkLine.tsx" ]; then
  echo "  OK: web/components/buzz/SparkLine.tsx exists"
else
  echo "  FAIL: web/components/buzz/SparkLine.tsx is missing"
  FAILED=1
fi

# 8. No lucide-react imports in the five scoped UI files
echo "[8] Checking no lucide-react imports in scoped UI files..."
LUCIDE_HITS=""

# Parallel arrays (bash 3.2 safe — no associative arrays)
SCOPED_FILES_1="web/app/report/[id]/page.tsx"
SCOPED_FILES_2="web/components/buzz/PanelCard.tsx"
SCOPED_FILES_3="web/components/buzz/FootnoteDrawer.tsx"
SCOPED_FILES_4="web/components/buzz/DonutChart.tsx"
SCOPED_FILES_5="web/components/buzz/SparkLine.tsx"

for f in "$SCOPED_FILES_1" "$SCOPED_FILES_2" "$SCOPED_FILES_3" "$SCOPED_FILES_4" "$SCOPED_FILES_5"; do
  if [ -f "$f" ]; then
    HITS=$(grep -n "from ['\"]lucide-react['\"]" "$f" || true)
    if [ -n "$HITS" ]; then
      LUCIDE_HITS="$LUCIDE_HITS
$f:
$HITS"
    fi
  fi
done

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
