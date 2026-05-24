# Step 01: Gather Context

**Model tier:** cheap
**Tools needed:** Read, Bash
**Input:** context mode (scope/noscope), scope name, iteration name
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/01-context.md`

---

## Your Task

Gather the information needed for changelog and release. Two modes:

### Scope Mode (default)

```bash
cat .agent_process/work/current_iteration.conf
```

**Step 1: Read artifacts for context**
- `.agent_process/work/{scope}/{iteration}/results.md` — what was implemented
- `.agent_process/work/{scope}/iteration_plan.md` — scope context  
- `<project_root>/.agent_process/work/{scope}/.run/gh-issue-context.md` — tracked GitHub issue context, if present

Extract: summary, change type (feature/fix/breaking), user-facing changes, and GitHub issue number if available.

**Step 2: Discover ACTUAL changed files via git**

The plan/results may not list all files. Always check git for the real diff:

```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff --name-only ${DEFAULT_BRANCH}...HEAD
git status --short
```

**Step 3: Multi-repo discovery (if local_environment_instructions specifies repos)**

Check `.agent_process/process/local_environment_instructions.md` for repo mappings. For each sub-repo directory that exists:

```bash
for repo in ai-lab stratum stratum-clin stratum-cv stratum-alz nap-gcp-platform; do
  if [ -d "$repo/.git" ]; then
    echo "=== $repo ==="
    cd "$repo"
    git diff --name-only origin/main...HEAD 2>/dev/null || git diff --name-only HEAD~10..HEAD
    git status --short
    cd ..
  fi
done
```

**Merge all sources:** Combine files from artifacts + git diff. The git diff is authoritative — include ALL changed files, even if not in the plan.

### No-Scope Mode (noscope arg)

```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff --stat ${DEFAULT_BRANCH}...HEAD
git status --short
```

Read key changed files to understand the work. Summarize findings.

### Build Number (both modes)

```bash
LAST_BUILD=$(git tag -l "build/*" | sed 's|build/||' | sort -n | tail -1)
BUILD_NUM=$(( ${LAST_BUILD:-0} + 1 ))
echo "Build number: ${BUILD_NUM}"
```

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/01-context.md`:

```markdown
# Release Context

**Mode:** scope / noscope
**Scope:** {name or "none"}
**Iteration:** {name or "none"}
**Build number:** {N}
**GitHub issue:** #{N} / none

## Changes Summary
- {bullet points describing what changed}

**Change type:** feature / fix / refactor / docs / chore
**User-facing:** YES / NO

## Changed Files (from git)

### {repo-name or "root"}
- path/to/file1.py
- path/to/file2.md

### {another-repo}
- path/to/file3.tf

## Files from Plan (for reference)
- {files listed in iteration_plan.md, if different from git}

**Note:** The git diff is authoritative. Files changed but not in the plan should still be included in the release.
```
