# Step 02: Gather Project Context + Code Review

**Model tier:** capable
**Tools needed:** Read, Grep, Glob, Bash
**Input:** idea (from user)
**Output:** `<project_root>/.agent_process/brainstorms/{name}/.run/02-context.md`

---

## Your Task

Collect context that grounds the brainstorm in this specific project. This includes **actual code review** — not just surface-level scanning — so the brainstorm agents produce technically feasible requirements.

## Part 1: Project Context

1. **Read project README** (if exists) — understand what this project does
2. **Scan existing requirements:**
   ```bash
   ls .agent_process/requirements_docs/ 2>/dev/null
   ```
3. **Check backlog** for related items:
   ```bash
   grep -i "relevant_keywords" .agent_process/roadmap/backlog.md 2>/dev/null
   ```
4. **Query knowledge base** for related patterns/gotchas:
   ```bash
   KB_DIR=".agent_process/knowledge"
   grep -i "relevant_keywords" "$KB_DIR"/*.jsonl 2>/dev/null
   ```

Extract keywords from the idea to search with.

## Part 2: Code Exploration (CRITICAL)

This part is what prevents brainstorm from producing idealistic requirements that get rejected by plan-scope.

1. **Search for relevant code:**
   - Use Grep to find files related to the idea's keywords
   - Look for existing implementations of similar features
   - Find the main entry points and patterns

2. **Read CLAUDE.md files:**
   - Root: `.claude/CLAUDE.md` or `CLAUDE.md`
   - Check for development patterns, testing requirements, architectural constraints

3. **Read 3-5 key files** most relevant to the idea:
   - Understand current architecture
   - Identify patterns and conventions
   - Note dependencies and integration points

4. **Assess technical landscape:**
   - What framework/stack is used?
   - What patterns exist for similar features?
   - Are there obvious constraints or blockers?

## Output Format

```markdown
# Project Context

**Project:** {name from README or directory}
**Idea:** {user's idea}

## Project Overview
- {what this project does}
- {tech stack and frameworks}

## Relevant Context
- {bullet points grounding the idea in this project}

## Existing Related Work
- {any related requirements, backlog items, or knowledge entries}

## Code Exploration

### Patterns & Conventions
{Key patterns from CLAUDE.md and code review}

### Relevant Files
{List 3-5 files most relevant to this idea, with 1-line summary of each}

### Technical Landscape
- **Framework:** {what's used}
- **Similar Features:** {existing implementations that could inform this}
- **Integration Points:** {where this idea would connect}
- **Constraints:** {any obvious blockers or limitations}

### Feasibility Notes
{Brief assessment of what's possible given current codebase}
```
