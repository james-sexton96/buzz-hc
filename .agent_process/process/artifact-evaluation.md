# Artifact Evaluation

> **Type:** How-To Guide (Diataxis)
> **Audience:** AP users validating scope artifacts

## Overview

`evaluate-scope.sh` validates that artifacts produced during scope execution conform to the expected schema. It catches formatting issues, missing sections, invalid statuses, and qualified verdicts that agents sometimes produce.

## When to Run

- **After orchestrator review** — Step 10 of the review process suggests running it
- **Before creating a PR** — catch artifact issues before they land in the repo
- **When debugging** — if the orchestrator is confused by results, validation often reveals why
- **Periodic audit** — scan all work folders to find artifacts that drifted from the schema

## Usage

```bash
# Validate a single scope's artifacts
bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/<scope>

# Strict mode (rejects legacy format variations)
bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/<scope> --strict

# Scan ALL scopes (using the test runner)
bash test/run-tests.sh scan .agent_process/work
```

## What It Validates

| Artifact | Validator | Checks |
|----------|-----------|--------|
| `iteration_plan.md` | `validate-iteration-plan.sh` | Required sections, frozen criteria markers, checkboxes, technical assessment, knowledge integration |
| `results.md` | `validate-results.sh` | Status field (must be COMPLETE/NEEDS REVISION/BLOCKED), required sections, acceptance criteria checkboxes, date field |
| `adversarial-review.md` | `validate-adversarial-review.sh` | Binary verdicts only (PASS/FAIL), no qualified passes, file:line evidence, summary with X/Y count |
| `scope-events.log` | `validate-scope-events.sh` | Valid event format, lifecycle events (SCOPE_START, TASK_CREATE, etc.) |
| `knowledge/*.jsonl` | `validate-knowledge-entry.sh` | Valid JSON, required fields (fact, recommendation for metaswarm schema; scope, content for legacy), type matches filename |

## Reading the Output

```
Validating: .agent_process/work/my_scope/iteration_01/results.md

  PASS: Status is valid (current format)
  PASS: Section 'Summary' found
  PASS: Section 'Changed Files' found
  WARN: Section 'Changed Files' found with variant name
  PASS: Section 'Acceptance Criteria' found
  PASS: Adversarial Review section present
  PASS: Date field present
  PASS: Title follows expected format
  PASS: Found 5 acceptance criteria (4 checked, 1 unchecked)

Results: 0 violations, 1 warnings
VERDICT: PASS (with warnings)
```

- **PASS** — artifact conforms to the schema
- **WARN** — minor deviation that's acceptable (e.g., variant section name, legacy format)
- **FAIL** — violation that should be fixed (e.g., invalid status, missing required section)

## Strict Mode

By default, validators accept legacy format variations (pre-v2.5 artifacts). Use `--strict` to enforce current format only:

```bash
bash .agent_process/scripts/evaluate-scope.sh .agent_process/work/<scope> --strict
```

Strict mode rejects:
- Status without emoji prefix (e.g., `COMPLETE` instead of `✅ COMPLETE`)
- Missing Adversarial Review section
- Other legacy format variations

## Installation

The validators are installed automatically by `install.sh` into `.agent_process/scripts/`. They're copied from `test/contract/validate-*.sh` in the framework source.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Cannot find validator scripts" | Scripts not installed | Re-run `install.sh` |
| Older artifacts failing | Format evolved since they were created | Use non-strict mode (default) |
| "No artifacts found" | Wrong path or empty scope folder | Check the path points to a scope work directory |
