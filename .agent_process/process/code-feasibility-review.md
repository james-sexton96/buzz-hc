# Code Feasibility Review

**Type:** Reference (Diátaxis)
**Purpose:** Shared instructions for reviewing requirements against actual code

---

## Overview

This document defines the standard feasibility review process used by:
- Plan-scope (Step 03)
- Brainstorm (Step 05)
- `/ap_requirements add` and `/ap_requirements import`

The goal is to catch issues early — before committing to implementation — by grounding requirements in codebase reality.

---

## Review Process

### 1. Query Knowledge Base

Search `.agent_process/knowledge/` for relevant entries before reviewing code.

```bash
KB_DIR=".agent_process/knowledge"

# Extract keywords from the requirement
# - Category name (e.g., auth, frontend, api)
# - File names mentioned
# - Technical concepts (e.g., middleware, caching, validation)

# Search by keywords
grep -i "<keyword1>\|<keyword2>\|<keyword3>" "$KB_DIR"/*.jsonl 2>/dev/null

# Search by affected files
grep -i "<filename_pattern>" "$KB_DIR"/*.jsonl 2>/dev/null
```

**What to extract:**
- **Patterns** → Inform implementation approach
- **Gotchas** → Add to Known Risks
- **Decisions** → Respect existing architectural choices
- **Anti-patterns** → Explicitly avoid in requirements

If the knowledge base doesn't exist or returns nothing, note it and proceed.

### 2. Read CLAUDE.md Files

Check for development patterns and conventions:

```bash
# Root level
cat .claude/CLAUDE.md 2>/dev/null || cat CLAUDE.md 2>/dev/null

# For each directory that will be modified
cat {directory}/CLAUDE.md 2>/dev/null
```

**Focus on:**
- Code patterns and conventions
- Testing requirements
- Architectural constraints
- Naming conventions
- What NOT to do

### 3. Review Actual Code

Open and read files the requirement says will be modified or created.

**For files to modify:**
- Understand current implementation
- Identify patterns and architecture
- Note dependencies (imports, exports, API contracts)
- Check for tests that will need updates

**For files to create:**
- Find similar existing files as templates
- Identify where they should live (directory structure)
- Check for naming conventions

**Search for related code:**
```bash
# Find files related to the requirement's keywords
grep -r "<keyword>" --include="*.ts" --include="*.py" -l .

# Find similar implementations
grep -r "<pattern>" --include="*.ts" --include="*.py" -l .
```

### 4. Assess Technical Feasibility

Answer these questions:

1. **Is this achievable with the current codebase structure?**
   - Does the architecture support this?
   - Are there framework limitations?

2. **What's the recommended implementation approach?**
   - Based on existing patterns
   - Informed by knowledge base
   - Following CLAUDE.md conventions

3. **What's the complexity?**
   - `simple` — Single file, clear path, <1 day
   - `moderate` — Multiple files, some unknowns, 1-3 days
   - `complex` — Cross-cutting, significant unknowns, 3+ days

### 5. Identify Risks

Combine findings from code review and knowledge base:

| Risk Source | What to Look For |
|-------------|------------------|
| Knowledge gotchas | Things that bit previous scopes |
| Knowledge anti-patterns | Approaches that failed |
| Code review | Fragile files, tight coupling, missing tests |
| Dependencies | External APIs, shared modules, breaking changes |
| Performance | Hot paths, large data, user-facing latency |

**Rate each risk:** low / medium / high

### 6. Check Clarification Needs

Identify questions that block planning:

**Resolvable from code/docs** → Answer them now using what you found:
- "How does X currently work?" → Read the code, answer it
- "What pattern does Y use?" → Check CLAUDE.md or similar files
- "Has this been tried before?" → Check knowledge base

**Requires human judgment** → These MUST be flagged:
- "Should this support mobile?"
- "What's the priority vs feature X?"
- "Is breaking change acceptable?"

**Set the gate:**
- `CLARIFICATION_NEEDED: false` — Proceed with planning/writing
- `CLARIFICATION_NEEDED: true` — Stop and ask the human

---

## Output Template

Use this structure for all feasibility review outputs:

```markdown
# Code Feasibility Review

**Requirement:** {id or title}
**Reviewed:** {date}

## Knowledge Base Findings

**Keywords searched:** {keywords}
**Entries found:** {count}

{If entries found:}
- **[pattern]** {fact} — {recommendation}
- **[gotcha]** {fact} — {recommendation}
- **[anti-pattern]** {fact} — {recommendation}

{If no entries:}
*No relevant knowledge base entries.*

## CLAUDE.md Patterns

{Key patterns and conventions relevant to this scope}

## Current State

{What exists today in the files this scope will touch}

## Technical Assessment

- **Feasible:** YES / NO / CONDITIONAL
- **Approach:** {recommended implementation strategy}
- **Complexity:** simple / moderate / complex

## Dependencies

{Files, modules, APIs this scope depends on}

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| {risk} | low/medium/high | {how to address} |

## Implementation Guidance

{Specific patterns to follow, pitfalls to avoid, conventions to maintain — informed by knowledge base and code review}

## Clarification Status

CLARIFICATION_NEEDED: true / false

{If true, list questions requiring human judgment:}
1. {question}
2. {question}

{If false:}
All questions resolved from code and documentation.
```

---

## Integration Notes

### For Plan-Scope

- Runs as Step 03
- Output: `<project_root>/.agent_process/work/{scope}/.run/planning/03-code-review.md`
- Blocks planning if `CLARIFICATION_NEEDED: true`

### For Brainstorm

- Runs as Step 05 (mandatory)
- Output: `<project_root>/.agent_process/work/{scope}/.run/brainstorm/05-feasibility-review.md`
- Must resolve or escalate all questions before writing requirement
- Findings inform: Technical Requirements, Known Risks, Success Criteria

### For /ap_requirements add

- Runs after template is filled, before writing
- Inline output (no separate file)
- Iterates with user if `CLARIFICATION_NEEDED: true`

### For /ap_requirements import

- Offered with reasoning (recommended for new/draft imports)
- Inline output
- Flags issues for user to address in the imported requirement
