# Steps 06-08: Transform, Confirm, Write

**Model tier:** capable
**Tools needed:** Read, Write, Bash
**Input:** synthesis (`<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md`), feasibility review (`<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md`), scope check (`<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05b-scope-check.md`), idea
**Output:** Requirement file(s) in `requirements_docs/{category}/`

---

## Your Task

Transform the brainstorm synthesis into a formal AP requirement file, confirm with the user, and write it.

## Step 6: Transform to Requirement

Map synthesis fields to requirement template:

```markdown
---
id: {requirement_id}
type: requirement
category: {category}
status: not_started
priority: {priority}
complexity: {simple | moderate | complex}
source: ap-brainstorm
---

# Requirements: {derived_title}

## Objective
{From Problem Statement — one clear sentence}

## Background
{From Problem Statement — expanded context}

## Technical Requirements
{From Proposed Approach — numbered list}

## Success Criteria
{From Success Criteria — checkboxes}

## Files Expected to Change
{From Technical Assessment}

## Out of Scope
{From Scope Boundaries}

## Known Risks
{From Risks & Mitigations}

## Notes

### Brainstorm Source
- **Brainstorm doc:** `.agent_process/brainstorms/{name}.md`
- **Date:** {today}
- **Perspectives:** Product, Architecture, Critical

### Feasibility Review
{Summary from `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md` — key findings that shaped this requirement}

### Open Questions
{Items needing human input}
```

## Step 7: Confirm with User

Present key fields for review:
- **Title:** {derived}
- **Category:** {suggest, ask if not obvious}
- **Priority:** {suggest from urgency signals}
- **Complexity:** {from Architecture agent}

Wait for user confirmation or adjustments.

## Step 8: Write and Register

**Single requirement (no breakdown):**
1. Determine location: `requirements_docs/{category}/`
2. Generate ID (find existing IDs, suggest next)
3. Write the requirement file
4. Update master roadmap with NOT_STARTED status

**If breakdown occurred in Step 05b:**
1. Transform and write EACH child requirement
2. Each child uses `-01`, `-02` suffix per the parent ID
3. Create parent breakdown file (`{id}-breakdown.md`) with coverage map
4. Update roadmap with all children (parent marked as `split`)

If the scope check returned WARN (not FAIL), include the risk note in Known Risks.

## Report

```
✓ Brainstorm complete: {id}
  Requirement: requirements_docs/{category}/{id}.md
  Brainstorm:  .agent_process/brainstorms/{name}.md
  Criteria:    {count} acceptance criteria

Next step: Plan the scope using orchestration/plan-scope.md (in Codex), then /ap_exec {id}
```

**Important:** The next step uses AP's `orchestration/plan-scope.md` — NOT metaswarm. Never suggest `/metaswarm:start` or other metaswarm commands as alternatives to AP workflow.
