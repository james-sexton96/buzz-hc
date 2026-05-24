# Scope Breakdown

**Type:** Reference (Diátaxis)
**Purpose:** Shared instructions for breaking down oversized requirements into smaller, executable scopes

---

## Overview

This document defines the standard breakdown process used by:
- Plan-scope (Step 01b)
- `/ap_requirements add` (when scope check fails)
- `/ap_brainstorm` (when scope check fails)

The goal is to split large requirements into independently-shippable children while preserving traceability and managing dependencies.

---

## When to Use

Run this process when:
- Scope-sizing check returns `VERDICT: FAIL`
- User agrees to break down the requirement

Do NOT break down if:
- User declines (they take responsibility for the large scope)
- Requirement has `scope_override: true` with valid reason

---

## Naming Convention (CRITICAL)

**Child requirements MUST follow this pattern:**

```
{parent_id}-01.md
{parent_id}-02.md
{parent_id}-03.md
```

**Example:**
- Parent: `user_auth_overhaul.md`
- Children:
  - `user_auth_overhaul-01.md` (NOT `user_auth_login.md`)
  - `user_auth_overhaul-02.md` (NOT `user_auth_sessions.md`)

**Rationale:** Descriptive names break traceability. Sequential suffixes:
1. Make parent-child relationships obvious
2. Preserve git history continuity
3. Prevent naming bikeshedding

**The parent file becomes:** `{parent_id}-breakdown.md`

---

## Breakdown Phases

```
┌──────────────────────────────────────────────────────┐
│  Phase 1: ARCHITECTURAL REVIEW                       │
│  - Review entire requirement for soundness           │
│  - Identify internal dependencies                    │
│  - Document decisions that apply to all children     │
├──────────────────────────────────────────────────────┤
│  Phase 2: DEPENDENCY MAPPING                         │
│  - Map criteria to subsystems                        │
│  - Identify cross-cutting concerns                   │
│  - Determine split boundaries                        │
│  - Define execution order                            │
├──────────────────────────────────────────────────────┤
│  Phase 3: CREATE CHILD REQUIREMENTS                  │
│  - Generate {id}-01.md, {id}-02.md, etc.             │
│  - Each child is standalone and executable           │
│  - Include split_from: and depends_on: frontmatter   │
├──────────────────────────────────────────────────────┤
│  Phase 4: VALIDATE CHILDREN                          │
│  - Run scope-sizing check on EACH child              │
│  - If any fail → adjust and re-validate              │
│  - Max 2 adjustment cycles before escalation         │
├──────────────────────────────────────────────────────┤
│  Phase 5: FINALIZE                                   │
│  - Rename parent to {id}-breakdown.md                │
│  - Add coverage map and execution order              │
│  - Update roadmap with children                      │
└──────────────────────────────────────────────────────┘
```

---

## Phase 1: Architectural Review

Before splitting, analyze the WHOLE requirement:

### Questions to Answer

1. **Is this requirement sound?** Any contradictions or undefined terms?
2. **What are the internal dependencies?** Which criteria must come before others?
3. **Are there cross-cutting concerns?** Things that affect ALL children?
4. **What's the natural split boundary?** Data layer vs API vs UI? Phase 1 vs Phase 2?
5. **What should be deferred?** Items to explicitly exclude from ALL children?

### Output: Architectural Decisions

```markdown
## Architectural Decisions

1. **{Decision}** — {rationale}
2. **{Decision}** — {rationale}

## Cross-Cutting Concerns

- {Concern}: handled in {child-N}
- {Concern}: deferred to future scope

## Execution Order

1. {child-01}: {why it's first}
2. {child-02}: {depends on child-01 because...}
```

---

## Phase 2: Dependency Mapping

Create a mapping of criteria to children:

```markdown
## Criteria to Child Mapping

| Criterion | Child | Depends On | Notes |
|-----------|-------|------------|-------|
| Schema setup | -01 | — | Foundation |
| API endpoints | -01 | — | Same child |
| Entity extraction | -02 | -01 | Needs schema |
| Review UI | -03 | -02 | Needs entities |
```

### Splitting Rules

- Keep tightly coupled criteria together (schema + CRUD = same child)
- Backend before frontend (if they touch same data)
- Foundation first, features second
- Each child must be independently shippable

---

## Phase 3: Create Child Requirements

For each child, create a file with this structure:

```markdown
---
id: {parent_id}-{NN}
type: requirement
category: {same as parent}
status: not_started
priority: {same as parent}
split_from: {parent_id}
depends_on: [{list of dependencies, if any}]
---

# {Parent Title} — Part {N}: {Brief Subtitle}

**Split from:** `{parent_id}` (see `{parent_id}-breakdown.md` for context)

{If dependencies:}
**Prerequisites:** {what must be done first}

## Objective
{Focused objective for THIS child only}

## Technical Requirements
{Only criteria assigned to this child}

## Success Criteria
{Only criteria assigned to this child}

## Files Expected to Change
{Scoped to this child}

## Architectural Context
{Relevant decisions from Phase 1}

---
*Part {N} of {total} from `{parent_id}`. See breakdown file for complete context.*
```

---

## Phase 4: Validate Children

**Run scope-sizing check on EVERY child before finalizing.**

### Process

1. Check each child against `process/scope-sizing-check.md`
2. If ANY child fails:
   - Identify why (too many criteria? subsystems?)
   - Adjust: split further or rebalance criteria
   - Re-validate ALL children
3. Max 2 adjustment cycles — escalate to human if still failing

### Adjustment Strategies

**Too many criteria (>7):**
- Split by layer (schema vs API vs UI)
- Create "foundation" child for shared infrastructure

**Too many subsystems (>3):**
- Child is doing too many things
- Each child should focus on one cohesive area

**Too many files (>12):**
- Often symptom of too many subsystems
- Check if some files belong to a different child

---

## Phase 5: Finalize

### Rename Parent to Breakdown File

```markdown
---
id: {original_id}
type: breakdown
status: split
children: [{id}-01, {id}-02, {id}-03]
---

# {Original Title} — BREAKDOWN

**Status:** Split into smaller requirements.

## Child Requirements

1. `{id}-01.md` — {description}
2. `{id}-02.md` — {description}

## Execution Order

{From Phase 1/2}

## Coverage Map

| Original Criterion | Assigned To |
|--------------------|-------------|
| {criterion 1} | -01 |
| {criterion 2} | -02 |

## Original Content

{Preserve original requirement below for reference}

---
{original content}
```

### Update Roadmap

- Add all children to roadmap with `not_started` status
- Mark parent as `split` (not a working scope)

### GitHub Issues (if enabled)

```bash
# Format: "scope|description" for each child
bash .agent_process/scripts/github-issues-lifecycle.sh split \
  {parent_scope} \
  "{child-01}|Handles the first part: brief description of what this child covers" \
  "{child-02}|Handles the second part: brief description of what this child covers" \
  "{child-03}|Handles the third part: brief description of what this child covers"
```

The description should explain what work this child scope handles and how it relates to the parent scope.

---

## Failure Modes

**Stop and escalate if:**
- Architectural review finds fundamental issues
- Dependencies form a cycle
- Child validation fails after 2 adjustments
- Breakdown creates more than 6 children (original was too large)

---

## Integration Notes

### For Plan-Scope (Step 01b)

- Runs after Step 01 returns FAIL
- Full orchestration with parallel sub-agents for review
- Output: `<project_root>/.agent_process/work/{scope}/.run/planning/01b-breakdown.md` + child files

### For /ap_requirements add

- Runs inline when scope check fails
- Same process, but outputs directly (no `<project_root>/.agent_process/work/{scope}/.run/` files)
- Creates children in `requirements_docs/{category}/`

### For /ap_brainstorm

- Runs inline after feasibility review if scope check fails
- Brainstorm context informs the split decisions
- Creates children in `requirements_docs/{category}/`
