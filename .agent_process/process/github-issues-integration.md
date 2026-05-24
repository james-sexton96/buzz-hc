# GitHub Issues Integration

> **Diátaxis type:** How-To Guide (task-oriented)
> **Audience:** AP users who want scope/work-unit tracking via GitHub Issues

## Overview

When GitHub Issues integration is enabled, AP automatically creates and manages issues for each scope and work unit. Issues provide team visibility, cross-session state tracking, and a natural link between AP work and your project's issue tracker.

**File-based tracking always works.** `scope-tracker.jsonl` and `scope-events.log` are written regardless of the GitHub Issues setting. Issues are an optional layer on top.

---

## Prerequisites

1. **GitHub CLI (`gh`)** version 2.20.0+
   ```bash
   gh --version
   ```
2. **Authenticated session**
   ```bash
   gh auth status
   ```
   If not authenticated: `gh auth login`
3. **Repository access** — you need write access to create issues and labels

---

## Setup

### During Installation

`install.sh` asks whether you want GitHub Issues tracking:

```
Would you like to track AP scopes as GitHub Issues? [y/N]
```

If you say yes, the installer:
1. Verifies `gh` is installed and authenticated
2. Detects the repo from your git remote (or asks for `owner/repo`)
3. Creates AP labels on the repo (`ap:scope`, `status:planning`, etc.)
4. Writes the config to `quality-config.json`

### Manual Configuration

Edit `.agent_process/quality-config.json`:

```json
{
  "github_issues": {
    "enabled": true,
    "repo": "myorg/myproject",
    "_user_configured": true
  }
}
```

Then create labels:
```bash
bash .agent_process/scripts/github-issues-lifecycle.sh create-labels
```

---

## How It Works

### Scope Lifecycle

| Pipeline Step | What Happens |
|--------------|-------------|
| `/ap_brainstorm #43` | Reads issue for context, brainstorms, creates requirement, associates scope |
| `/ap_requirements add #43` | Reads issue for context, creates requirement, associates scope |
| `plan-scope` (Step 0.5) | Creates issue if none exists yet, sets `status:planning` |
| `plan-scope` scope-check FAIL | Calls `split` — closes parent with `status:split`, creates child issues |
| `/ap_exec` preflight (Step 0.4) | Health check — verifies `gh` works and repo is accessible |
| `/ap_exec` preflight (Step 0.5) | Verifies issue exists; if not, **asks user** for number, 'create', or 'skip' |
| During execution | Work unit sub-issues created, `status:executing` label |
| Orchestrator review | Label transitions to `status:reviewing` |
| APPROVE decision | `status:approved`, issue closed |
| ITERATE decision | `status:iterate` label, comment with reason |
| BLOCK decision | `status:blocked`, issue closed |

### Labels

| Label | Purpose |
|-------|---------|
| `ap:scope` | Identifies AP-managed scope issues |
| `status:planning` | Scope is being planned |
| `status:executing` | Implementation in progress |
| `status:reviewing` | Orchestrator review underway |
| `status:approved` | Scope approved (issue closed) |
| `status:iterate` | Needs another iteration |
| `status:blocked` | Scope blocked (issue closed) |
| `status:split` | Scope was too large, split into children (issue closed) |

### File-Based State (Always Active)

| File | Purpose |
|------|---------|
| `.agent_process/work/scope-tracker.jsonl` | One JSON line per scope: name, iteration, status, gh_issue number |
| `.agent_process/work/scope-events.log` | Append-only event log: timestamps, scope, action, details |

These files are the authoritative state source. GitHub Issues are a mirror with extra features (comments, team visibility, cross-linking).

---

## Polyrepo Support

For projects where the AP framework lives in a different repo than the code:

```json
{
  "github_issues": {
    "enabled": true,
    "repo": "myorg/my-app"
  }
}
```

The `repo` field is passed as `--repo` to every `gh` command, so issues are created in the correct repository regardless of which repo you're working in.

### Nested Repos (Monorepo with Sub-repos)

If your project has nested git repositories (e.g., a root repo containing multiple sub-repos), the lifecycle script automatically handles this:

1. **AP Root Detection** — If you run commands from a sub-repo, the script traverses up to find `.agent_process/` and operates from there.

2. **Git Remote Info** — If the current git remote differs from the configured `github_issues.repo`, the script logs an informational message but continues. This is expected in polyrepo setups where issues are tracked in a central repo.

**Example structure:**
```
stratum-root/           ← AP installed here, issues tracked in stratum-root repo
├── .agent_process/
├── stratum/            ← nested git repo (different remote)
├── stratum-clin/       ← nested git repo (different remote)
└── ai-lab/             ← nested git repo (different remote)
```

Running `lifecycle.sh` from `stratum-root/stratum/` will:
1. Detect no `.agent_process/` in cwd
2. Find AP root at `stratum-root/`
3. Change to that directory
4. Log: "Not at AP root. Changing to: /path/to/stratum-root"
5. Continue with the command

---

## The Lifecycle Script

All GitHub Issues operations go through `github-issues-lifecycle.sh`. Agents and coordinators never run raw `gh` commands. For detailed sub-agent instructions, see `process/github-issues-handling.md`.

```bash
# Health check
bash .agent_process/scripts/github-issues-lifecycle.sh health-check

# Create/adopt scope issue — applies ap:scope label only, no status label
bash .agent_process/scripts/github-issues-lifecycle.sh create <scope> [description]

# Start work — creates issue + sets status:executing (use when execution begins)
bash .agent_process/scripts/github-issues-lifecycle.sh start <scope> [description]

# Associate existing issue with scope
bash .agent_process/scripts/github-issues-lifecycle.sh associate <scope> <issue_number_or_url>

# Update status label (removes old status:* labels first)
bash .agent_process/scripts/github-issues-lifecycle.sh set-status <scope> <label>

# Close scope
bash .agent_process/scripts/github-issues-lifecycle.sh close <scope> [decision]

# Advance iteration
bash .agent_process/scripts/github-issues-lifecycle.sh set-iteration <scope> <iteration>

# Verify scope state
bash .agent_process/scripts/github-issues-lifecycle.sh verify <scope>

# Add comment
bash .agent_process/scripts/github-issues-lifecycle.sh comment <scope> <message>

# Split scope into children (when scope-check fails)
# Format: "scope|description" — description explains what this child handles
bash .agent_process/scripts/github-issues-lifecycle.sh split <parent_scope> \
  "child1|description of child1 work" "child2|description of child2 work" [...]

# Create work unit sub-issue
bash .agent_process/scripts/github-issues-lifecycle.sh task-create <scope> <wu_id> <description>

# Update work unit status
bash .agent_process/scripts/github-issues-lifecycle.sh task-update <scope> <wu_id> <status>
```

---

## Ad-Hoc Knowledge

When GitHub Issues is enabled, the knowledge base still lives in `.agent_process/knowledge/` as JSONL files. Issues can reference knowledge entries in comments, but knowledge is not stored in issues.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "GitHub Issues health check failed" | `gh` not authenticated or repo inaccessible | Run `gh auth login` or check `github_issues.repo` in config |
| "Scope tracking failed to initialize" | Labels missing or API error | Run `github-issues-lifecycle.sh create-labels` |
| Duplicate issues created | Scope tracker out of sync | Check `scope-tracker.jsonl` for existing `gh_issue` entry |
| HALT during execution | GitHub API is down or rate-limited | Fix the issue, then re-run `/ap_exec` — session recovery picks up where you left off |

### Health Check

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh health
```

This verifies:
- `gh` CLI is on PATH
- `gh auth status` succeeds
- The configured repo is accessible
- Required labels exist

---

## When GitHub Issues Adds Value

- **Team visibility** — Stakeholders can see scope progress without reading `.agent_process/` files
- **Multi-session work** — Issues persist across Claude Code sessions; `scope-tracker.jsonl` provides recovery state
- **Cross-linking** — `#N` in commit messages auto-links to issues; PRs can reference scope issues
- **Notifications** — Team members get notified of scope status changes

## When to Skip It

- **Solo projects** — File-based tracking is sufficient
- **Air-gapped environments** — No GitHub access
- **Rapid prototyping** — Overhead isn't worth it for throwaway work

---

## Disabling

Set `github_issues.enabled` to `false` in `quality-config.json`:

```json
{
  "github_issues": {
    "enabled": false,
    "_user_configured": true
  }
}
```

File-based tracking (`scope-tracker.jsonl`, `scope-events.log`) continues to work. Existing GitHub Issues are not modified or closed.
