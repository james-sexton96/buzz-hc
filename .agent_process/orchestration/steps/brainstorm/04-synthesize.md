# Step 04: Synthesize Results

**Model tier:** synthesis
**Tools needed:** Read, Write
**Input:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-product.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-architect.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-critical.md`
**Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md` + `.agent_process/brainstorms/{chosen_name}/brainstorm.md`

---

## Your Task

Read all 3 agent outputs and synthesize into a unified brainstorm document. Where agents disagreed, note the disagreement and explain your reasoning for the chosen direction.

## Synthesis Structure

```markdown
# Brainstorm: {idea}

**Date:** {today}
**Perspectives:** Product, Architecture, Critical

---

## Problem Statement
{Clearest articulation from Product, refined by others}

## Proposed Approach
{Best balance of feasibility, impact, and risk. Note where agents disagreed.}

## Success Criteria
- [ ] {From Product, refined by Architecture and Critical}

## Technical Assessment
- **Complexity:** {From Architecture}
- **Key components:** {From Architecture}
- **Files likely affected:** {From Architecture}

## Risks & Mitigations
{Merged from all three, deduplicated}

## Scope Boundaries (Out of Scope)
{From Product + Critical}

## Open Questions
{Unresolved items needing human input}

## Alternative Approaches Considered
{From Critical — what we chose NOT to do and why}
```

## Save

Write to both:
1. `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md` (for the coordinator)
2. `.agent_process/brainstorms/{chosen_name}/brainstorm.md` (permanent record)

The directory was already created by the coordinator.
