# Step 02: Technical Assessment

**Input:** Requirement file, scope name
**Output:** `<project_root>/.agent_process/work/{scope}/.run/planning/02-assess.md`

---

## Guiding Principle

Capture not just WHAT to build, but WHY certain approaches were chosen. The executor needs to understand design rationale to avoid mechanical changes that miss the intent.

---

## 1. Knowledge Base Query

Search `.agent_process/knowledge/` for relevant patterns:

```bash
grep -i "keyword1\|keyword2" .agent_process/knowledge/*.jsonl 2>/dev/null
```

For each relevant entry, note:
- The pattern/decision
- **When it applies** (and when it doesn't)
- Source reference

---

## 2. Code Feasibility Review

Read the codebase to assess:

**Existing Patterns:**
- How does similar functionality work today?
- What conventions does the codebase follow?
- What would need to change?

**Implementation Approach:**
- What's the recommended approach?
- **Why this approach** over alternatives? (Document the reasoning!)
- What are the key assumptions?

**Known Risks:**
- What could go wrong?
- What edge cases exist?
- What dependencies are involved?

---

## 3. Design Decisions (IMPORTANT)

Document key decisions with rationale:

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| {decision point} | {chosen approach} | {alternatives considered} | {reasoning} |

This table transfers to the iteration plan so the executor understands the design intent.

---

## Output

```markdown
# Technical Assessment

**Scope:** {scope}

## Knowledge Base
{N} relevant entries:
- {pattern}: {when to use / when not to use}

## Code Review Findings
- {finding 1 with file references}
- {finding 2}

## Implementation Approach
{Recommended approach with WHY}

**Key Assumptions:**
- {assumption 1 — if false, approach needs revision}
- {assumption 2}

## Design Decisions
| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| {decision} | {choice} | {alternatives} | {rationale} |

## Risks
- {risk 1}: {mitigation}
- {risk 2}: {mitigation}

## Clarification Needed
{Questions requiring human input, or "None"}
```
