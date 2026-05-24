# GitHub Issues Handling

> **Purpose:** Single-concern instruction file for sub-agents performing GitHub Issues operations.
> Every orchestration coordinator references this file instead of embedding GH logic inline.

---

## 1. Check If GH Is Enabled

Read `.agent_process/quality-config.json`:

```json
{ "github_issues": { "enabled": true, "repo": "owner/repo" } }
```

- If `github_issues.enabled` is `false`, missing, or the file doesn't exist: **do nothing and return**. No warnings, no errors — GH is simply not part of this project.
- If `enabled` is `true` but `repo` is empty: log a warning and return.

## 2. The Lifecycle Script

**All GH operations go through `github-issues-lifecycle.sh`.** Never run `gh` directly.

```bash
# Query commands (read-only, no side effects)
bash .agent_process/scripts/github-issues-lifecycle.sh get-issue <scope>      # Returns issue number or empty
bash .agent_process/scripts/github-issues-lifecycle.sh search-issue <scope>   # Search GH for matching issues (JSON)
bash .agent_process/scripts/github-issues-lifecycle.sh list-issues            # All open ap:scope issues (JSON)
bash .agent_process/scripts/github-issues-lifecycle.sh audit                  # Compare tracker vs GH, report mismatches
bash .agent_process/scripts/github-issues-lifecycle.sh verify <scope>         # Full verification report for one scope
bash .agent_process/scripts/github-issues-lifecycle.sh resolve-input <input>  # Resolve issue#/scope/path → JSON

# Core actions
bash .agent_process/scripts/github-issues-lifecycle.sh create <scope> [description]  # Creates issue with ap:scope only (no status label)
bash .agent_process/scripts/github-issues-lifecycle.sh start <scope> [description]   # Creates issue + sets status:executing (work begins)
bash .agent_process/scripts/github-issues-lifecycle.sh associate <scope> <issue_number_or_url>
bash .agent_process/scripts/github-issues-lifecycle.sh set-status <scope> <label>
bash .agent_process/scripts/github-issues-lifecycle.sh set-priority <scope> <priority:P0-P4>
bash .agent_process/scripts/github-issues-lifecycle.sh set-iteration <scope> <iteration>
bash .agent_process/scripts/github-issues-lifecycle.sh comment <scope> "message"
bash .agent_process/scripts/github-issues-lifecycle.sh close <scope> <decision>
bash .agent_process/scripts/github-issues-lifecycle.sh retitle <scope> <new_title>

# Scope splitting (when scope fails size gate)
# Format: "scope|description" — description explains what work this child handles
bash .agent_process/scripts/github-issues-lifecycle.sh split <parent_scope> \
  "child1|description" "child2|description" [...]

# Work unit management
bash .agent_process/scripts/github-issues-lifecycle.sh task-create <scope> <wu-id> <description>
bash .agent_process/scripts/github-issues-lifecycle.sh task-update <scope> <wu-id> <status>
```

The script handles `--repo`, retries, label management, and tracker updates internally. You don't need to worry about any of that.

## 2.1. Flexible Input Resolution

The `resolve-input` command accepts any of these formats and returns structured JSON:

**Input formats:**
- GitHub issue number: `#123`, `123`, or full URL
- Scope name: `my_feature_scope`
- Requirement path: `category/my_feature_scope.md`

**Example:**
```bash
bash .agent_process/scripts/github-issues-lifecycle.sh resolve-input 123
```

**Output:**
```json
{
  "scope": "my_feature_scope",
  "requirement_path": ".agent_process/requirements_docs/category/my_feature_scope.md",
  "gh_issue": "123",
  "input_type": "issue",
  "iteration": "iteration_02"
}
```

The `iteration` field contains the current iteration from the tracker (e.g., `iteration_01`, `iteration_02`). This enables `review-iteration` to automatically review the latest iteration without requiring explicit specification.

This enables `plan-scope` and `review-iteration` to accept any input format. The coordinator resolves it to structured values before proceeding.

## 2.2. Rich Issue Bodies

When `start` creates a new issue, it automatically syncs the issue body with content from the requirement document (if found). The body includes:

- **Scope Summary:** Status, priority, complexity, category
- **Objective:** What this scope achieves
- **Background:** Context and motivation
- **Acceptance Criteria:** Success conditions
- **Technical Requirements:** Implementation details
- **Dependencies:** What this scope depends on
- **Out of Scope:** What's explicitly excluded
- **Requirement Source:** Path to the requirement document

To manually sync the body later (e.g., after updating the requirement doc):
```bash
bash .agent_process/scripts/github-issues-lifecycle.sh sync-body <scope>
```

This makes GitHub issues readable by product managers and stakeholders, not just developers.

## 3. Status Label Taxonomy

| Pipeline Step | Label | Notes |
|--------------|-------|-------|
| Brainstorm/Requirements | *(no status label)* | Issue created, not yet planned |
| Plan scope | `status:planning` | Planning coordinator active |
| Execute preflight | `status:executing` | Implementation underway |
| Execute complete | `status:awaiting_review` | Implementation done, awaiting review |
| Review start | `status:reviewing` | Orchestrator review active |
| APPROVE decision | `status:approved` | Issue closed |
| ITERATE decision | `status:iterate` | Needs another pass |
| BLOCK decision | `status:blocked` | Issue closed |
| Scope split | `status:split` | Parent issue closed, child issues created |

Use `set-status` to transition between labels. The script removes old `status:*` labels before applying the new one.

## 3.1. Priority Labels

Priority labels help triage scope urgency. When enabled, `create` (and `start`) applies a default priority and `split` inherits the parent's priority to children.

| Priority | Color | Meaning |
|----------|-------|---------|
| `priority:P0` | Red (#B60205) | Critical — drop everything |
| `priority:P1` | Orange (#D93F0B) | High — this sprint |
| `priority:P2` | Yellow (#FBCA04) | Medium — default priority |
| `priority:P3` | Green (#0E8A16) | Low — when time permits |
| `priority:P4` | Blue (#C5DEF5) | Minimal — nice to have |

**Configuration:**
```json
{
  "priority_labels": {
    "enabled": true,
    "default": "priority:P2"
  }
}
```

**Behavior:**
- **`start`**: Applies default priority (P2 unless configured otherwise)
- **`set-priority`**: Changes priority with mutual exclusivity (removes old, adds new)
- **`split`**: Children inherit parent's priority automatically
- **`create-labels`**: Creates priority labels if enabled

Use `set-priority` to change priority:
```bash
bash .agent_process/scripts/github-issues-lifecycle.sh set-priority my_scope priority:P1
```

## 4. Create / Adopt / Verify Decision Tree

When a pipeline step needs a GH issue for a scope:

```
1. Check tracker for linked issue:
   gh_issue=$(lifecycle.sh get-issue <scope>)
   │
   ├─ gh_issue NOT EMPTY → Run: lifecycle.sh create <scope>
   │     (create will verify the issue, adopt it, regenerate context file)
   │
   └─ gh_issue EMPTY → Search GitHub for matching issue:
      │
      search_results=$(lifecycle.sh search-issue <scope>)
      │
      ├─ search_results HAS MATCHES
      │  │
      │  ├─ Pipeline step should auto-adopt? (plan-scope: yes)
      │  │  └─ Run: lifecycle.sh associate <scope> <first_match>
      │  │
      │  └─ Pipeline step should ask user? (execute-preflight: yes)
      │     └─ Ask: "Found issue #N titled '{title}'. Use this? (yes/no/skip)"
      │        - yes → lifecycle.sh associate <scope> <N>
      │        - no  → fall through to "no matches" path
      │        - skip → continue without GH issue
      │
      └─ search_results EMPTY (no matches)
         │
         ├─ User provided an issue number (#N)?
         │  └─ Run: lifecycle.sh associate <scope> <N>
         │
         ├─ Pipeline step should auto-create? (plan-scope: yes)
         │  └─ Run: lifecycle.sh create <scope>
         │     (creates issue with ap:scope only, no status label yet)
         │
         ├─ Pipeline step should start work? (execute-preflight: yes)
         │  └─ Run: lifecycle.sh start <scope>
         │     (creates issue + sets status:executing)
         │
         └─ Pipeline step should ask user? (other contexts)
            └─ Ask: "No GitHub Issue found for scope '{scope}'.
               Enter issue number/link, say 'create', or 'skip'."
```

**Key rule:** `scope-tracker.jsonl`'s `gh_issue` field is the single source of truth. Whoever sets it first wins. Subsequent steps adopt it.

## 4.1. Split Handling (Scope Size Gate Failure)

When a scope fails the hard size gate during planning (too many criteria, files, or subsystems):

```
1. Scope-check coordinator returns FAIL with recommended breakdown
   │
2. Planning coordinator calls: lifecycle.sh split <parent> "child1|description" "child2|description"
   │
   ├─ Tracker updates:
   │  ├─ Parent scope: status="split", split_into=[child1, child2, ...]
   │  └─ Each child: status="pending", split_from=parent
   │
   └─ GH operations (if enabled):
      ├─ Create child issues with templated body including:
      │  ├─ Description: what work this child handles
      │  ├─ Parent reference: #N (parent_scope)
      │  └─ Requirement doc link (if available)
      ├─ Comment on parent: "Scope split into smaller pieces: #A, #B, #C"
      ├─ Add status:split label to parent
      └─ Close parent issue
```

**Key rules:**
- Child scopes are **independent** — they can be planned/executed in any order
- Parent issue is **closed** — all future work happens on child issues
- Child tracker entries have `split_from` field linking back to parent
- Child issues are regular `ap:scope` issues (no special `ap:child` label needed)

## 4.2. Auditing and Sync

The `audit` command compares local tracker state against GitHub issues and reports mismatches:

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh audit
```

**Mismatch types detected:**

| Type | Description | Suggested Fix |
|------|-------------|---------------|
| `ORPHAN_TRACKER` | Tracker has `gh_issue` that doesn't exist on GH | Remove `gh_issue` from tracker, or recreate the GH issue |
| `TITLE_MISMATCH` | GH issue title ≠ scope name | `lifecycle.sh retitle <scope> <correct_title>` |
| `ORPHAN_GH` | GH issue with `ap:scope` label has no tracker entry | `lifecycle.sh associate <scope> <issue_number>` |
| `UNLINKED` | Tracker scope exists, matching GH issue exists, but not linked | `lifecycle.sh associate <scope> <issue_number>` |

**Output format:** One JSON object per mismatch line, parseable by agents:
```json
{"type":"TITLE_MISMATCH","scope":"foo","gh_issue":"123","gh_title":"old_name","reason":"..."}
```

**When to audit:**
- Before starting a new session on a project
- When preflight reports unexpected state
- After manual GH issue edits
- Periodically as a health check

**Fixing mismatches:** The audit reports suggested fixes but doesn't auto-apply them. Use the appropriate lifecycle commands to resolve each mismatch, with user confirmation for destructive changes.

## 5. Context File

The lifecycle script generates `<project_root>/.agent_process/work/{scope}/.run/gh-issue-context.md` at `start` and `associate` time. This file contains:

- Issue number and repo
- Current status label
- Scope and iteration
- Pre-filled commands for common operations

**Sub-agents receive this file instead of the full issue body.** It's tiny (~15 lines) and contains everything needed to interact with the issue.

## 6. Prohibitions

These rules exist because past violations caused duplicate issues, context bloat, and broken state:

- **Never edit issue body directly** — use the lifecycle script
- **Never load full issue body into agent context** — use the issue number as a pointer, or read `<project_root>/.agent_process/work/{scope}/.run/gh-issue-context.md`
- **Never run `gh` without going through the lifecycle script** — the script handles `--repo`, retries, and tracker sync
- **Never create duplicate issues** — always check `scope-tracker.jsonl` first via `start` (which checks tracker before creating)
- **Never skip the lifecycle script for "simple" operations** — even a comment should go through `lifecycle.sh comment`

## 7. Error Handling

The lifecycle script follows the HALT protocol:

- **Transient errors** (502, 503, timeout, rate limit): retried once automatically
- **Permanent errors** (401, 404, validation): prints `HALT:` message and returns non-zero
- **GH disabled**: all actions return 0 silently (local state still written)

When a HALT occurs:
1. Local state (`scope-tracker.jsonl`, `scope-events.log`) is still written
2. The calling coordinator should stop GH operations but may continue with non-GH work
3. Report the error to the user — don't swallow it

## 8. Sub-Agent Pattern

Parent coordinators spawn a **cheap** sub-agent for GH operations:

```markdown
Spawn a cheap sub-agent:
  - Input: process/github-issues-handling.md + <project_root>/.agent_process/work/{scope}/.run/gh-issue-context.md (if exists)
  - Task: "Verify GH issue for scope {scope}. Update status to {label}."
  - Output: Updated <project_root>/.agent_process/work/{scope}/.run/gh-issue-context.md
```

The parent coordinator does NOT read issues, run `gh`, or process labels. Simple single-command status updates (one bash call already in the orchestration) are acceptable inline — the sub-agent pattern is for anything involving decisions or multiple commands.
