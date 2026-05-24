#!/usr/bin/env bash
# Validation script for agent_pipeline_tdd_error_handling
# Runs scoped checks for iteration_01 (Phase A)
set -euo pipefail

SCOPE="agent_pipeline_tdd_error_handling"
ITERATION="${2:-iteration_01}"
PROJECT_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "=== Validating $SCOPE / $ITERATION ==="

# 1. Verify agent_limit in Literal
echo "[1] Checking agent_limit in WorkflowEvent Literal..."
python3 -c "
from app.schema import WorkflowEvent
e = WorkflowEvent(event_type='agent_limit', source='test', message='test')
assert e.event_type == 'agent_limit', 'agent_limit not in Literal'
print('  OK: agent_limit is valid event_type')
"

# 2. Verify add_event is async
echo "[2] Checking ResearchContext.add_event is async..."
python3 -c "
import inspect
from app.context import ResearchContext
assert inspect.iscoroutinefunction(ResearchContext.add_event), 'add_event is not async'
print('  OK: ResearchContext.add_event is async')
"

# 3. Verify no unawaiited add_event calls in agent files
echo "[3] Checking for unawaited add_event calls..."
UNAWAITED=$(grep -rn "ctx\.deps\.add_event\|ctx\.add_event" \
  app/agents/lead.py app/agents/researcher.py app/agents/analyst.py app/agents/reporter.py \
  2>/dev/null | grep -v "await " || true)
if [ -n "$UNAWAITED" ]; then
  echo "  FAIL: Found unawaited add_event calls:"
  echo "$UNAWAITED"
  exit 1
fi
echo "  OK: All add_event calls have await"

# 4. Verify run_reporter has try/except
echo "[4] Checking run_reporter has try/except..."
python3 -c "
import ast, sys
with open('app/agents/lead.py') as f:
    tree = ast.parse(f.read())

found = False
for node in ast.walk(tree):
    if isinstance(node, ast.AsyncFunctionDef) and node.name == 'run_reporter':
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                found = True
                break

if not found:
    print('  FAIL: run_reporter has no try/except')
    sys.exit(1)
print('  OK: run_reporter has try/except')
"

# 5. Verify asyncio.wait_for used in lead.py
echo "[5] Checking asyncio.wait_for in lead.py..."
COUNT=$(grep -c "asyncio.wait_for" app/agents/lead.py 2>/dev/null || echo "0")
if [ "$COUNT" -lt 3 ]; then
  echo "  FAIL: Expected at least 3 asyncio.wait_for calls in lead.py, found $COUNT"
  exit 1
fi
echo "  OK: Found $COUNT asyncio.wait_for calls"

# 6. Verify failed_stage column migration
echo "[6] Checking failed_stage migration in database.py..."
python3 -c "
with open('api/database.py') as f:
    content = f.read()
assert 'failed_stage' in content, 'failed_stage migration not found in database.py'
print('  OK: failed_stage migration present')
"

# 7. Verify mark_error accepts failed_stage
echo "[7] Checking mark_error signature..."
python3 -c "
import inspect
from api.db_sessions import mark_error
sig = inspect.signature(mark_error)
assert 'failed_stage' in sig.parameters, 'failed_stage not in mark_error signature'
print('  OK: mark_error accepts failed_stage')
"

# 8. Run tests
echo "[8] Running test suite..."
uv run pytest tests/ -v --tb=short 2>&1 | tail -30
echo ""
echo "=== Validation complete ==="
