# Installing Claude Code Hooks

## Overview

The `.agent_process` uses a simplified hook system:
- **after_edit hook**: Provides scoped validation feedback after implementation
- **No enforcement hooks**: Orchestrator review is the quality gate

---

## Installation

### Step 1: Ensure .claude Directory Exists

```bash
mkdir -p .claude
```

### Step 2: Configure Hooks in settings.json

Edit `.claude/settings.json` (or `.claude/settings.local.json` for local-only config):

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /absolute/path/to/project/.agent_process/scripts/hook_after_edit.sh"
          }
        ]
      }
    ]
  }
}
```

**Important notes:**
- Use **absolute paths** for reliability (relative paths may not resolve correctly)
- The hook goes in `.claude/settings.json`, NOT `.claude/hooks.json`
- The format requires nested `hooks` arrays (see structure above)
- The SubagentStop hook runs automatically when Task agents complete

**Example for this project:**
```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/samwachtel/PycharmProjects/your-project/.agent_process/scripts/hook_after_edit.sh"
          }
        ]
      }
    ]
  }
}
```

### Step 3: Make Hook Script Executable

```bash
chmod +x .agent_process/scripts/hook_after_edit.sh
```

### Step 4: Restart Claude Code

After modifying settings.json, restart Claude Code for changes to take effect.

---

## How It Works

### after_edit Hook (Scoped Validation)

**Trigger:** Automatically runs after Task agent completes (SubagentStop event)

**Purpose:** Provides immediate feedback on scoped validation

**Data Flow:**
1. Hook checks for execution lock file (`.agent_process/work/.execution_active`)
2. If lock not present, silently exits (prevents noise from non-exec edits)
3. Hook script reads current scope from `.agent_process/work/current_iteration.conf`
4. Finds the matching validator: `.agent_process/scripts/after_edit/validate-{scope}.sh`
5. Runs scope-specific validation (ESLint + Jest tests)
6. Reports results (PASS/FAIL)
7. **No blocking** - just feedback, Claude can proceed

**Example Output:**
```bash
[hook_after_edit] Running scoped validation for my_scope/iteration_01_a
[hook_after_edit] Running validator for scope: my_scope
[my_scope-validation] Linting scope sources...
[my_scope-validation] Running scope unit tests...
✓ 47/47 tests passing
[hook_after_edit] Complete
```

---

## Creating Scope-Specific Validation Scripts

### Template Structure

Create `validate-{scope-name}.sh` in `.agent_process/scripts/after_edit/`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCOPE=${1:-unknown}
ITERATION=${2:-unknown}

printf "[%s-validation] scope=%s iteration=%s\n" "$SCOPE" "$SCOPE" "$ITERATION"

# List files in this scope
FILES_TO_LINT=(
  "frontend/src/path/to/file1.tsx"
  "frontend/src/path/to/file2.ts"
)

pushd frontend >/dev/null

printf "[%s-validation] Linting scope sources...\n" "$SCOPE"
npx eslint "${FILES_TO_LINT[@]}" --max-warnings 0

printf "[%s-validation] Running scope tests...\n" "$SCOPE"
npm test -- --testPathPatterns=YourTestPattern --watchAll=false --passWithNoTests=false

popd >/dev/null

printf "[%s-validation] Complete.\n" "$SCOPE"
```

### Make Executable

```bash
chmod +x .agent_process/scripts/after_edit/validate-{scope-name}.sh
```

---

## Philosophy

### Fast Feedback, Not Enforcement

**Old approach (removed):**
- ❌ Stop hook blocked completion if artifacts missing
- ❌ Required `expected_artifacts.json` rigid enforcement
- ❌ Checked artifact alignment, file existence
- ❌ Created compliance work instead of quality work

**New approach (simplified):**
- ✅ after_edit provides immediate scoped validation feedback
- ✅ No blocking - just helpful feedback
- ✅ Orchestrator review is the real quality gate
- ✅ Focus on implementation, not process compliance

### Why This Works

**Convergence mechanisms prevent the real problems:**
- Iteration budget (max 3 sub-iterations) → Prevents infinite loops
- Frozen criteria → Prevents scope creep
- Scoped validation → Prevents false blockers
- 4-choice decisions → Forces explicit choices

**Hooks provide value without overhead:**
- Fast feedback on files you changed
- Runs automatically (no manual steps)
- Exit code reflects validation (but doesn't block)
- Helps Claude fix issues quickly

**Orchestrator review catches quality issues:**
- Reviews against original acceptance criteria
- Catches incomplete work
- Makes go/no-go decisions
- Better than automated checking

---

## Troubleshooting

### Hook Doesn't Run

**Check:**
1. Is hook configured in `.claude/settings.json` (NOT `.claude/hooks.json`)?
2. Is the JSON format correct (nested `hooks` arrays)?
3. Is `hook_after_edit.sh` executable? (`chmod +x`)
4. Did you restart Claude Code after changing settings?

**Debug:**
```bash
# Test manually with stdin
echo "" | bash .agent_process/scripts/hook_after_edit.sh

# Check if hook is triggering (add debug logging)
echo "[hook_after_edit] TRIGGERED at $(date)" >> /tmp/claude-hook-debug.log
# Add this line to the top of hook_after_edit.sh
```

**Known Issue:**
The `/hooks` UI may show incorrect information or display bugs. If `/hooks` shows the hook isn't registered but manual testing works, the hook is likely firing correctly - the UI just has a display bug.

### Validation Script Not Found

**Check:**
1. Does script exist in `.agent_process/scripts/after_edit/`?
2. Does script name match pattern `validate-{scope}.sh`?
3. Is script executable?
4. Does `.agent_process/work/current_iteration.conf` have the correct SCOPE value?

**Debug:**
```bash
# List available validators
ls -la .agent_process/scripts/after_edit/validate-*.sh

# Check current scope
cat .agent_process/work/current_iteration.conf
```

### Validation Fails

**This is expected behavior!** Hook provides feedback, not enforcement.

**What Claude should do:**
1. Read failure output
2. Fix issues
3. Re-run (hook runs automatically on next attempt)
4. Document in results.md if persistent failures

**What Claude should NOT do:**
- ❌ Try to work around validation failures
- ❌ Skip validation requirements
- ✅ Fix the actual issues

---

## Key Differences from Old Documentation

**File location:**
- ❌ Old: `.claude/hooks.json`
- ✅ New: `.claude/settings.json`

**Configuration format:**
- ❌ Old: `{"SubagentStop": {"command": "..."}}`
- ✅ New: `{"hooks": {"SubagentStop": [{"hooks": [{"type": "command", "command": "..."}]}]}}`

**Scope/iteration passing:**
- ❌ Old: Environment variables `${SCOPE:-}` and `${ITERATION:-}`
- ✅ New: Hook script reads from `.agent_process/work/current_iteration.conf`

**Path handling:**
- ❌ Old: Relative paths `bash .agent_process/scripts/...`
- ✅ New: Absolute paths `/full/path/to/.agent_process/scripts/...`

---

## Summary

**Single hook:** `after_edit` (scoped validation feedback)
**Location:** `.claude/settings.json` (NOT hooks.json)
**Format:** Nested structure with `hooks` arrays
**Purpose:** Fast feedback, not enforcement
**Philosophy:** Help Claude fix issues quickly, orchestrator review for quality

---

**See also:**
- `.agent_process/scripts/hook_after_edit.sh` - Main hook script
- `.agent_process/scripts/after_edit/validate-*.sh` - Scope-specific validators
- `.agent_process/work/current_iteration.conf` - Scope/iteration tracking
