# Step 01: Preflight Checks

**Output:** `<project_root>/.agent_process/work/{scope}/.run/execution/01-preflight.md`

---

Run these checks before implementation. All can run in parallel EXCEPT branch check runs first (it may change branches).

## 1. Branch Check (FIRST)

```bash
CURRENT=$(git branch --show-current)
EXPECTED="scope/{scope}"
```

**Decision tree:**

1. **On expected branch already?** → Proceed
2. **Expected branch doesn't exist?** → Create it and switch: `git checkout -b "$EXPECTED"`
   - This is the normal case after plan-scope — just create and go
3. **Expected branch exists but you're on a different branch?** → Flag for human
   - May have uncommitted work on the expected branch
   - Present options: switch to it, continue on current, or stash and switch

**Key principle:** Don't block execution for a branch that doesn't exist yet. Just create it.
The only blocking case is when the expected branch has prior work that needs attention.

## 2. Session Recovery

Check for uncommitted work from interrupted sessions:

```bash
git status --porcelain | head -5
```

If changes exist in scope files, present options:
- Stash and continue
- Commit and continue  
- Abort and let user handle

## 3. Working Tree Check

Verify clean working state:

```bash
git diff --stat HEAD 2>/dev/null | head -10
```

Flag if significant uncommitted changes exist outside `.agent_process/`.

## 4. Git Context

Get recent changes to scope files for context:

```bash
git log --oneline -5 -- {scope_files}
```

This helps the executor understand recent work.

## 5. Tracker Sync

Ensure the tracker reflects the iteration being executed:

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh set-iteration {scope} {iteration}
bash .agent_process/scripts/github-issues-lifecycle.sh set-status {scope} executing
```

This prevents tracker drift when review post-decision is skipped or a new iteration is started manually. The tracker should always match execution reality. Setting status to `executing` transitions from `planning` (set by `start`) to active work.

**If GitHub integration is enabled, failures here are BLOCKING:**
- Check `quality-config.json` for `github_issues.enabled`
- If `true` and these commands fail: **STOP and report the error**
- Do NOT proceed with "non-blocking" hand-waving
- Script not found? That's an installation error — fix it or reinstall
- The script itself gracefully no-ops when `github_issues.enabled` is `false`

---

## Output

```markdown
# Preflight Results

**Scope:** {scope}
**Iteration:** {iteration}

## Branch
- Current: {branch}
- Expected: scope/{scope}
- Status: OK / CREATED / NEEDS_DECISION
- Action taken: {none / created branch / awaiting user}

## Working State
- Uncommitted changes: {none / N files — listed}
- Recovery needed: YES / NO

## Git Context
- Recent commits touching scope: {count}
- Last change: {date} — {message}

## Gate
PREFLIGHT: PASS / BLOCKED

**PASS conditions:**
- Already on expected branch, OR
- Expected branch didn't exist and was created, OR
- Working tree is clean (only .agent_process/ changes are OK)

**BLOCK only if:**
- Expected branch exists with uncommitted work that needs attention
- Significant uncommitted changes outside .agent_process/
- Recovery from interrupted session requires user decision

{If blocked: reason and recommended action}
```
