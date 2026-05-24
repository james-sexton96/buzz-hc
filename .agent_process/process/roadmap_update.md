# Roadmap Update Process

**Purpose:** Define when and how the roadmap is maintained during project execution.

**See also:** `naming_conventions.md` for requirement ID formats and file naming rules.

---

## Update Triggers

### 1. Iteration Completion (Automatic)

**When:** After writing `results.md` with completion status (✅ APPROVED, ✅ COMPLETE, 🚫 BLOCKED, etc.)

**What gets updated:**
- Requirement status and work scope counts in `master_roadmap.md`
- Category completion percentages in `master_roadmap.md`
- Active Work and Blocked Items sections in `master_roadmap.md`
- Last Updated timestamp

**Who triggers:** Orchestration prompts (Claude following instructions, not commands)

### 2. New Requirement Added (Manual)

**When:** User creates new requirement file or uses `/ap_project add-requirement` or `/ap_project import-requirement`

**What gets updated:**
- Add new row to `master_roadmap.md` in appropriate category section
- Update category counts and status summary in `master_roadmap.md`
- If using `import-requirement`: Adds frontmatter, standardizes filename (see `naming_conventions.md`)
- If creating manually: Re-run discovery to detect structure changes

### 3. Backlog Management (Manual)

**When:** User adds/resolves todo items or uses `/ap_project add-todo`

**What gets updated:**
- Add/remove items from `backlog.md`
- Move items to formal requirements if they become scope-sized

### 4. Project Structure Changes (On-Demand)

**When:** User runs `/ap_project sync` or significant directory restructuring

**What gets updated:**
- Full re-discovery of requirements and work directories
- Regenerate `master_roadmap.md` with fresh matching statistics
- Reconcile orphaned work or requirements

---

## Update Procedures

### Orchestration-Triggered Updates

**Context:** These are instructions for Claude during `/ap_exec` or iteration review, not commands.

#### Step 1: Detect Completion

```markdown
# Instructions for Claude (in review coordinator)

After writing results.md, check if status changed to ✅ APPROVED, ✅ COMPLETE, 🚫 BLOCKED, etc.

If status changed:
1. Read current `.agent_process/roadmap/master_roadmap.md`
2. Find the requirement in the appropriate category section
3. Update the work scope count and status icon
4. Move requirement between Active Work / Blocked Items sections as needed
5. Recalculate category completion percentages
```

#### Step 2: Update Master Roadmap

All updates are made to `master_roadmap.md`. The file contains consolidated sections:

```markdown
# Example updates in master_roadmap.md

## Status Summary (recalculate)
| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Approved | [N] | [%] | ← Recalculate totals
| 🔍 Completed (Review Pending) | [N] | [%] | ← Recalculate totals

## Category Breakdown (recalculate)
| Category | Complete | In Progress | Blocked | Completion |
|----------|----------|-------------|---------|------------|
| {Category} | [N] | [N] | [N] | [%] | ← Recalculate based on work scope updates

## Active Work / Blocked Items (move requirements as needed)
| Requirement | Category | Work Scopes |
|-------------|----------|-------------|
| {requirement_id} | {category} | [N] | ← Add/remove based on status change

## Requirements by Category (update status icon)
| Status | Priority | Requirement | Work Scopes |
|--------|----------|-------------|-------------|
| [icon] | [PRIORITY] | {Display Name} | [N] | ← Update status icon and work scope count
```

**Iteration format:** Count major iterations + progression. Examples:
- `1 (01)` - Single iteration, no PIVOT
- `2 (01→02)` - Two major iterations (one PIVOT)
- `1+2 (01_b)` - One major + 2 sub-iterations

---

## Detailed Post-Iteration Instructions

**For orchestration to reference:** These step-by-step instructions should be included in iteration review prompts.

### When to Execute

Execute these steps **after** you have:
1. Completed an iteration
2. Written `results.md` with status (✅ APPROVED, ✅ COMPLETE, 🚫 BLOCKED, etc.)
3. Validated all acceptance criteria

**Skip if:**
- Iteration is still in progress
- Results.md shows IN_PROGRESS status
- Roadmap directory doesn't exist (project not using roadmap yet)

### Step-by-Step Procedure

#### 1. Check if Roadmap Exists

```bash
ls .agent_process/roadmap/
```

If no roadmap directory exists, skip remaining steps.

#### 2. Identify Current Work

Determine identifiers from work directory name:
- **Work scope:** Directory name (e.g., `feature_scope_15_description`)
- **Requirement ID:** Extract by removing `_scope_XX_` pattern

**Examples:**
```
Work: feature_name_scope_01_first_component
→ Requirement: feature_name

Work: category_feature_scope_02_second_component
→ Requirement: category_feature
```

#### 3. Update Master Roadmap

Read `.agent_process/roadmap/master_roadmap.md` and update all relevant sections:

**Status mapping:**
- "✅ APPROVED" in results.md → ✅ icon (Approved)
- "✅ COMPLETE" in results.md → 🔍 icon (Completed — Review Pending)
- "🚫 BLOCKED" → ❌ icon
- "🚧 IN PROGRESS" → 🚧 icon

**Update these sections:**

1. **Status Summary table** - Recalculate counts and percentages
2. **Category Breakdown table** - Update category completion percentage
3. **Active Work section** - Add/remove requirement based on status
4. **Blocked Items section** - Add/remove requirement if blocked/unblocked
5. **Requirements by Category section** - Update status icon and work scope count
6. **Last Updated timestamp** in header

**Aggregate status logic:**
- All scopes approved → ✅ Approved
- All scopes completed but not all approved → 🔍 Completed (Review Pending)
- Any scope blocked → ❌ Blocked
- Mix of complete/incomplete → 🚧 In Progress

**Completion calculation:**
```
% Complete = (Complete Requirements / Total Requirements) × 100
```

#### 4. Update Status Banners

When a requirement's status changes in the roadmap, update banners in all related files:

**Files to update:**
1. Requirement file: `requirements_docs/{category}/{requirement}.md`
2. Current iteration results: `.agent_process/work/{scope}/{iteration}/results.md`
3. Any related sub-requirements or breakdown files

**Banner rules:**
- Status changed to 🔧 SCOPED → Add/update with `[!NOTE]` scoped banner
- Status changed to 🚧 IN PROGRESS → Add/update with `[!NOTE]` in-progress banner
- Status changed to 🔍 COMPLETED → Add/update with `[!NOTE]` completed (review pending) banner
- Status changed to ✅ APPROVED → Add/update with `[!TIP]` approved banner
- Status changed to ❌ BLOCKED → Add/update with `[!WARNING]` blocked banner
- Status changed to 🗄️ ARCHIVED → Add/update with `[!CAUTION]` archived banner

See **Status Change Banners** section below for detailed banner formats and examples.

#### 5. Capture Follow-up Items

If results.md contains "Follow-up" or "Known Issues" sections:
- Add HIGH priority items to `.agent_process/roadmap/backlog.md`
- Note if items need their own scope

### Error Handling

If roadmap files are missing or malformed:
1. Note the issue in results.md
2. Continue with iteration completion normally
3. User can run `/ap_project sync` to rebuild

---

## Status Change Banners

**Principle:** When a requirement's status changes in the roadmap, **mark all related source files** with status banners to maintain consistency between documentation and implementation.

This ensures developers can see at a glance whether a requirement file is active, complete, blocked, or archived without checking the roadmap.

### When to Add/Update Banners

Add or update status banners when:
- A requirement changes status (📋 → 🔧 → 🚧 → ✅ or ❌)
- An iteration completes and updates the requirement's aggregate status
- A requirement is archived via `/ap_project archive`
- A requirement is unblocked and returns to active work

### Banner Format

Add the banner immediately after the frontmatter (or at the very top if no frontmatter).

**Template:**
```markdown
> [!{TYPE}]
> **{ICON} {STATUS}** — *{Context}*
>
> {Additional information}
> {Reference to roadmap or related documentation}
```

### Status-Specific Banners

| Status | Alert Type | Icon | When to Use |
|--------|-----------|------|-------------|
| Scoped | `NOTE` | 🔧 | Work scope created, awaiting execution |
| In Progress | `NOTE` | 🚧 | Active work on this requirement |
| Completed | `NOTE` | 🔍 | Implementation done, awaiting orchestrator review |
| Approved | `TIP` | ✅ | Reviewed and accepted by orchestrator |
| Blocked | `WARNING` | ❌ | Cannot proceed due to blockers |
| Archived | `CAUTION` | 🗄️ | Superseded, abandoned, or out of scope |

### Banner Examples

#### Scoped Banner

```markdown
> [!NOTE]
> **🔧 SCOPED** — *Work scope created, awaiting execution*
>
> Planning complete. Iteration plan ready at `.agent_process/work/{scope}/iteration_plan.md`.
> Run `/ap_exec {scope} iteration_01` to begin implementation.
```

#### In Progress Banner

```markdown
> [!NOTE]
> **🚧 IN PROGRESS** — *Active development*
>
> This requirement is currently being implemented.
> See: `.agent_process/roadmap/master_roadmap.md` for current status.
```

#### Completed Banner (Review Pending)

```markdown
> [!NOTE]
> **🔍 COMPLETED** — *Implementation done, awaiting review*
>
> All acceptance criteria addressed. Ready for orchestrator review.
> See: `.agent_process/work/{scope}/{iteration}/results.md` for details.
```

#### Approved Banner

```markdown
> [!TIP]
> **✅ APPROVED** — *Reviewed and accepted*
>
> All acceptance criteria met. Work approved in 2 iterations.
> See: `.agent_process/work/{scope}/iteration_02/results.md` for details.
```

#### Blocked Banner

```markdown
> [!WARNING]
> **❌ BLOCKED** — *Waiting on: {blocker description}*
>
> Cannot proceed until {specific blocker} is resolved.
> See: `.agent_process/roadmap/master_roadmap.md` → Blocked Items section.
```

#### Archived Banners (Type-Specific)

**Superseded:**
```markdown
> [!CAUTION]
> **🗄️ ARCHIVED** — *Superseded by {replacement}*
>
> This requirement has been replaced by a newer implementation.
> See: `.agent_process/roadmap/archived_roadmap.md` for details.
```

**Abandoned:**
```markdown
> [!CAUTION]
> **🗄️ ARCHIVED** — *Abandoned: {reason}*
>
> This requirement is no longer being pursued.
> See: `.agent_process/roadmap/archived_roadmap.md` for details.
```

**Completed:**
```markdown
> [!CAUTION]
> **🗄️ ARCHIVED** — *Completed and archived*
>
> This requirement was successfully completed and has been archived.
> See: `.agent_process/roadmap/archived_roadmap.md` for details.
```

**Out of Scope:**
```markdown
> [!CAUTION]
> **🗄️ ARCHIVED** — *Out of scope: {reason}*
>
> This requirement falls outside the project's current scope.
> See: `.agent_process/roadmap/archived_roadmap.md` for details.
```

### Files to Update

When a status changes, update banners in **all** of these locations:

1. **Requirement file** (`requirements_docs/{category}/{requirement}.md`)
2. **Related work scope results** (`.agent_process/work/{scope}/iteration_*/results.md`)
3. **Breakdown files** (if this is a parent requirement with sub-requirements)
4. **All sub-requirement files** (if this requirement has a breakdown)

### Banner Management Strategy

**Adding banners:**
- First status change: Add banner at the top (after frontmatter)
- Subsequent changes: Replace existing banner with new status

**Removing banners:**
- When returning to "Not Started" (📋): Remove banner entirely
- When unblocking: Replace blocked banner with in-progress banner

**Multiple status transitions:**
- Only keep the **current** status banner
- Historical status is tracked in `results.md` files and roadmap, not in requirement files

### Example: Full Status Lifecycle

**Initial state (no banner):**
```markdown
---
id: user-authentication
title: User Authentication System
---

# User Authentication System

[Requirement content...]
```

**After first iteration starts:**
```markdown
---
id: user-authentication
title: User Authentication System
---

> [!NOTE]
> **🚧 IN PROGRESS** — *Active development*
>
> This requirement is currently being implemented.
> See: `.agent_process/roadmap/master_roadmap.md` for current status.

# User Authentication System

[Requirement content...]
```

**After hitting a blocker:**
```markdown
> [!WARNING]
> **❌ BLOCKED** — *Waiting on: OAuth provider approval*
>
> Cannot proceed until OAuth provider credentials are obtained.
> See: `.agent_process/roadmap/master_roadmap.md` → Blocked Items section.
```

**After completing implementation (awaiting review):**
```markdown
> [!NOTE]
> **🔍 COMPLETED** — *Implementation done, awaiting review*
>
> All acceptance criteria addressed. Ready for orchestrator review.
> See: `.agent_process/work/user_authentication_scope_03/iteration_01/results.md` for details.
```

**After orchestrator approval:**
```markdown
> [!TIP]
> **✅ APPROVED** — *Reviewed and accepted*
>
> All acceptance criteria met. Work approved in 3 iterations.
> See: `.agent_process/work/user_authentication_scope_03/iteration_01/results.md` for details.
```

**After archiving (superseded):**
```markdown
> [!CAUTION]
> **🗄️ ARCHIVED** — *Superseded by unified-auth-system requirement*
>
> This requirement has been replaced by a newer, more comprehensive auth approach.
> See: `.agent_process/roadmap/archived_roadmap.md` for details.
```

### Automation Guidelines

**During orchestration:**
- After writing `results.md`, check if requirement status changed
- If changed, update banners in requirement file and all related work files
- Use Edit tool to replace existing banner or add new one

**During `/ap_project` commands:**
- Commands like `archive`, `set-status` should update banners automatically
- `sync` command should verify banner consistency and offer to fix mismatches
- Status override in `.roadmap_config.json` should trigger banner updates

### Consistency Checks

Banners should always match the roadmap status. To verify:
1. Read requirement's status from `master_roadmap.md`
2. Read banner from requirement file (if present)
3. If mismatch: Update banner to match roadmap
4. If no banner but status ≠ 📋: Add appropriate banner

---

### Command-Triggered Updates

**Context:** User invokes `/ap_project` commands for manual management.

#### Discovery/Sync Process

1. **Full scan** of `requirements_docs/` and `work/`
2. **Fuzzy matching** work directories to requirements
3. **Status aggregation** from latest results.md files
4. **Regenerate `master_roadmap.md`** from discovered state
5. **Preserve configuration** in `.roadmap_config.json` (project_mappings, status_overrides)

#### Incremental Updates

For small changes (add todo, update priority):
1. **Read current `master_roadmap.md`**
2. **Apply specific change** (add row, update field)
3. **Update Last Updated timestamp**
4. **Validate consistency** (percentages still add up)

---

## Update Safeguards

### Data Preservation

- **Backup current roadmap** before major updates (`.roadmap_backup_TIMESTAMP/`)
- **Preserve manual edits** like category overrides, priority adjustments
- **Warn before destructive operations** (full regeneration)

### Consistency Checks

After any update, validate:
- **Completion percentages** add up to 100%
- **Work scope counts** match actual directories
- **Status logic** (can't be Complete with In Progress work scopes)
- **Timestamp ordering** (last activity ≤ current time)

### Error Handling

- **Graceful degradation** - partial updates on file access errors
- **Clear error messages** - which files failed, what to fix
- **Rollback capability** - restore from backup if update fails

---

## Performance Considerations

### Incremental Discovery

- **Track Last Updated** in `master_roadmap.md` header
- **Only re-scan changed files/directories** when possible
- **Skip full fuzzy matching** if structure unchanged

### Large Project Handling

- **Limit discovery** to 1000 files, warn if exceeded
- **Paginate large tables** in roadmap files
- **Summarize instead of listing** if >100 work scopes per requirement

---

## Integration Points

### With Orchestration

The orchestration system should include instructions for Claude to follow after iteration completion. These instructions should be embedded in the iteration review prompts (e.g., `orchestration/review-iteration.md` or similar) and reference this process document.

**Key points for orchestration integration:**
- After writing results.md, Claude should check if roadmap exists
- If roadmap exists, follow the "Orchestration-Triggered Updates" section above
- Reference this document for detailed procedures
- No dependency on slash commands - use Read/Write/Edit tools directly

### With Commands

**File:** `.claude/commands/ap_project.md`

Provides user interface for:
- Manual roadmap updates
- Adding requirements/todos
- Syncing with current state
- Generating status reports

### With Existing Workflows

- **Compatible with current orchestration** - doesn't change `/ap_exec` behavior
- **Supplements todo_requirements.md** - migrates items to backlog.md
- **Works with any requirement format** - doesn't require schema changes

---

## Migration from Existing Projects

### Bootstrap Process

For projects with existing requirements but no roadmap:

1. **Run discovery** on current state
2. **Create initial roadmap files** from discovered data
3. **Migrate todo_requirements.md** to backlog.md
4. **Add coordinators** for future maintenance

### Backwards Compatibility

- **Keep existing todo_requirements.md** until fully migrated
- **Don't require roadmap** for orchestration to work
- **Optional adoption** - teams can use roadmap or not

This process ensures roadmap stays synchronized with project reality while being flexible enough for any team's workflow.