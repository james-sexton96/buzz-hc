# Release Coordinator

You are orchestrating the release workflow. This runs AFTER orchestrator approval — it's the final step before code is merged and optionally released.

## Inputs

- **Context mode:** `scope` (default) or `noscope` (first arg is literally `noscope`)
- **Mode:** `pr` | `beta` | `release` (required)
- **Version type:** `patch` | `minor` | `major` (required for `release` mode)
- **Flags:** `--shepherd` / `--no-shepherd` (optional, anywhere in args)

**Default is scope mode.** Only use noscope if the user explicitly passes `noscope` as the first argument. If `/ap_release pr` is called without `noscope`, it's scope mode — read from `current_iteration.conf`.

## Model Tiers

| Tier | Use For | Claude Code | Codex |
|------|---------|-------------|-------|
| **cheap** | File reads, version parsing, structure detection | haiku | gpt-5.4-mini |
| **capable** | Change classification, changelog writing, commit/tag/push/PR | sonnet | gpt-5.4 |

## Data Flow — Run Directory

The run directory depends on context mode:

**Scope mode (default):**
```bash
# Read the current scope
SCOPE=$(grep "^SCOPE=" .agent_process/work/current_iteration.conf | cut -d= -f2)
mkdir -p <project_root>/.agent_process/work/${SCOPE}/.run/release
```
All step outputs go to `<project_root>/.agent_process/work/{scope}/.run/release/`.

**Noscope mode (explicit `noscope` arg only):**
```bash
mkdir -p <project_root>/.agent_process/work/_noscope/.run/release
```
All step outputs go to `<project_root>/.agent_process/work/_noscope/.run/release/`.

**Never write `<project_root>/.agent_process/work/{scope_or_noscope}/.run/` to the project root.** It always goes under `.agent_process/work/`.

---

## Local Environment Instructions

Read `.agent_process/process/local_environment_instructions.md` before starting steps. If any section is not `<none>`:
- **Release Modifications:** Apply custom arguments, multi-project ordering, or additional steps. Pass to the sub-agents that handle context gathering (Step 01) and commit/push (Steps 07-09)
- **Multi-Repository Configuration:** Pass to Step 01 for context gathering across repos, and Steps 07-09 for per-repo commit/tag/push

These instructions are ADDITIVE — they augment but never skip default steps.

---

## Step Sequence

### Parallel: Context Gathering (steps 01 + 02)

Spawn TWO **cheap** sub-agents **simultaneously**:

1. `orchestration/steps/release/01-gather-context.md`
   - Pass: context mode (scope/noscope), scope name, iteration name
   - **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/01-context.md`

2. `orchestration/steps/release/02-detect-structure.md`
   - **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/02-structure.md`

Wait for both before proceeding.

### Step 03: Get Current Version (sequential)

Spawn a **cheap** sub-agent with `orchestration/steps/release/03-get-version.md`.
- Pass: structure output, mode, version type
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/03-version.md`

### Step 04: Determine Change Type (sequential)

Spawn a **capable** sub-agent with `orchestration/steps/release/04-change-type.md`.
- Pass: context output, mode
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/04-change-type.md` (includes drafted changelog entry)

### Step 05: Update Changelog (sequential)

Spawn a **capable** sub-agent with `orchestration/steps/release/05-update-changelog.md`.
- Pass: mode, version info, change type output
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/05-changelog.md`
- **Action:** Writes to `CHANGELOG.md` (and `USER_CHANGELOG.md` for beta/release)

### Step 06: Update Version Files (CONDITIONAL — release mode only)

**If mode is NOT `release`:** Skip, write "N/A — not release mode" to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/06-version-update.md`.

**If mode IS `release`:** Spawn a **cheap** sub-agent with `orchestration/steps/release/06-update-version.md`.
- Pass: structure output, new version
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/06-version-update.md`

### Steps 07-09: Commit, Tag, Push, PR (MUST BE SEQUENTIAL)

Spawn a **capable** sub-agent with `orchestration/steps/release/07-09-commit-tag-push.md`.

**These git operations MUST run as a single sequential step.** Do NOT attempt to parallelize commit, tag, push, or PR creation.

- Pass: mode, version info, build number, context mode, scope, changelog entry
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/07-09-git-ops.md`

### Step 095: PR Shepherd (CONDITIONAL)

**Check whether shepherd should run:**
1. Read `quality-config.json` → `pr_shepherd.enabled`
2. If `true` AND no `--no-shepherd` flag → run automatically
3. If `false` AND `--shepherd` flag present → run
4. Otherwise → skip

**If running:** Spawn a **capable** sub-agent with `orchestration/steps/release/095-pr-shepherd.md`.
- Pass: PR URL from step 07-09 output
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/095-shepherd.md`

**If skipping:** Write "Skipped — {reason}" to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/095-shepherd.md`.

### Step 10: Report (sequential)

Spawn a **cheap** sub-agent with `orchestration/steps/release/10-report.md`.
- Pass: ALL `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/*` files
- **Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/10-report.md`
- Present the report to the user

---

## Verification Checklist

Before presenting the report, verify:

- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/01-context.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/02-structure.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/03-version.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/04-change-type.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/05-changelog.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/06-version-update.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/07-09-git-ops.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/095-shepherd.md`
- [ ] `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/10-report.md`
