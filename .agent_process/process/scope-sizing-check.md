# Scope Sizing Check

**Type:** Reference (Diátaxis)
**Purpose:** Shared instructions for checking if a requirement is appropriately sized

---

## Overview

This document defines the standard scope-sizing check used by:
- Plan-scope (Step 01)
- `/ap_requirements add` (before writing)
- `/ap_brainstorm` (before writing)

The goal is to catch oversized requirements early — before committing to implementation.

---

## Thresholds

Read `orchestration/scope-sizing-rules.md` for the current threshold values. That file is the single source of truth for:
- 5-second check criteria
- Size thresholds (target/warning/fail)
- Duration targets
- Override mechanism

---

## Check Process

### 1. Read the Requirement

Extract from the requirement:
- **Objective** — Can it be explained in one sentence?
- **Success Criteria / Acceptance Criteria** — Count them
- **Files Expected to Change** — Count them
- **Subsystems touched** — Identify distinct areas (e.g., API, frontend, database, auth)

### 2. Run the 5-Second Check

All must be YES to pass:

| Check | Question |
|-------|----------|
| One sentence? | Can the objective be explained in one sentence? |
| Done definition? | Do I know what "done" looks like (specific, testable)? |
| Timeframe? | Can this be done in 1-2 weeks? |
| Specific name? | Is the name specific (not vague like "cleanup" or "improve")? |

### 3. Check Size Thresholds

Compare metrics against `orchestration/scope-sizing-rules.md`:

| Metric | How to Count |
|--------|--------------|
| Criteria count | Number of items in Success Criteria / Acceptance Criteria |
| Files to change | Number of files in "Files Expected to Change" |
| Subsystems | Distinct architectural areas (API, frontend, database, workers, etc.) |

### 4. Check for Override

If the requirement has `scope_override: true` in frontmatter:
- Still run all checks (informational)
- Shift Fail thresholds to Warning only
- Note the override reason in output

### 5. Check Red Flags

These always fail regardless of override:
- Objective needs multiple paragraphs
- Uses vague verbs without specifics: "cleanup", "improve", "refactor"
- Has dependencies on other in-progress work
- Touches files owned by multiple active scopes

---

## Output Format

```markdown
# Scope Size Check

**Requirement:** {id or title}

## 5-Second Check
1. One sentence: YES/NO — "{the sentence or why it fails}"
2. Done definition: YES/NO — "{summary or concern}"
3. Timeframe: YES/NO — "{estimate or concern}"
4. Specific name: YES/NO — "{assessment}"

## Size Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Criteria count | {N} | 3-7 (warn 8-10, fail >10) | PASS/WARN/FAIL |
| Files to change | {N} | 4-10 (warn 11-15, fail >15) | PASS/WARN/FAIL |
| Subsystems | {N} | 1-3 (warn 4, fail >4) | PASS/WARN/FAIL |

## Override Status
{scope_override: true/false}
{If true: reason from frontmatter}

## Red Flags
{List any red flags found, or "None"}

## VERDICT: PASS / WARN / FAIL

{If FAIL, include breakdown suggestion:}
This requirement exceeds size thresholds. Recommend splitting into:
1. {area-1}: {which criteria}
2. {area-2}: {which criteria}
3. {area-3}: {which criteria}
```

---

## Integration Notes

### For Plan-Scope (Step 01)

- Output: `<project_root>/.agent_process/work/{scope}/.run/planning/01-scope-check.md`
- If FAIL → Coordinator offers to run breakdown (Step 01b)
- If PASS/WARN → Continue to Step 02

### For /ap_requirements add

- Runs after feasibility review (Step 5.5), before writing
- If FAIL → Offer to break down inline
- If PASS/WARN → Write requirement

### For /ap_brainstorm

- Runs after feasibility review (Step 05), before Step 06
- If FAIL → Offer to break down inline
- If PASS/WARN → Proceed to transform and write

### Breakdown Process

If the check returns FAIL and the user wants to break down the requirement, follow the process in `process/scope-breakdown.md`.
