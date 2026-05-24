# Work Unit Execution

**Type:** How-To Guide (Diátaxis)
**Purpose:** Decompose multi-domain scopes into structured work units and execute them as a DAG

---

## Overview

Work unit decomposition is an optional preflight step in `/ap_exec` (Step 1.25, defined in `orchestration/steps/execution/0125-decomposition.md`) that breaks large, multi-domain scopes into independently-executable units. Each unit has its own files, agent, and validation. Units form a DAG — independent units run in parallel, dependent units wait for prerequisites.

**When it triggers:** 3+ files across 2+ system layers (backend + frontend, schema + API + tests, etc.)

**When it doesn't trigger:** Simple scopes (single domain, <3 files) execute exactly as before — single-pass, no decomposition overhead.

---

## When to Use Decomposition

| Scope Shape | Decompose? | Why |
|-------------|-----------|-----|
| 2 backend files + 1 test | No | Single domain, 3 files but all backend |
| 3 backend files + 2 frontend files | Yes | 2 layers, 5 files |
| 1 migration + 2 API files + 1 frontend + 2 tests | Yes | 3+ layers, 6 files |
| Sub-iteration (_a/_b/_c) | Never | Sub-iterations address specific fixes, not full decomposition |

---

## The Decomposition Process

### Step 1: Identify Layers

Read the "Files in Scope" from `iteration_plan.md` and categorize:

| Pattern | Layer |
|---------|-------|
| `migrations/`, `.sql`, schema files | Database |
| Backend API files, routes, services | Backend |
| Frontend components, hooks, `.tsx` | Frontend |
| Test files (`__tests__/`, `.test.`, `.spec.`) | Tests |
| Config, Docker, CI/CD | Infrastructure |
| Documentation (`docs/`, `*.md`) | Docs |

### Step 2: Group Files into Units

Each unit should:
- Touch files in 1-2 closely-related layers
- Address specific acceptance criteria
- Be independently validatable (codebase compiles after unit completes)
- Minimize file overlap with other units

### Step 3: Define Dependencies

Ask: "Can this unit execute without the results of another unit?"
- If yes → no dependency (can run in parallel)
- If no → add dependency on the prerequisite unit

Common patterns:
- Tests that mock modified modules → depend on the code unit
- Frontend consuming a changed API → depends on backend unit
- Integration tests → depend on all code units

### Step 4: Select Agents

Use the same agent selection logic from `/ap_exec` Step 1.5, but scoped to each unit's files instead of the full scope.

### Step 5: Execute the DAG

For each parallel group (units with no unmet dependencies):
1. Launch all units' agents simultaneously (single response with multiple Task calls)
2. Wait for all to complete
3. Validate each unit's files
4. Update `current_work_unit.conf`
5. Move to the next group

---

## Session Recovery

If a session is interrupted mid-execution, the next session reads `current_work_unit.conf`:

```
SCOPE=user_profile_images
ITERATION=iteration_01
CURRENT_UNIT=WU-003
TOTAL_UNITS=4
COMPLETED_UNITS=WU-001,WU-002
```

Resume from WU-003 — don't re-execute WU-001 and WU-002.

---

## Results Documentation

When decomposition is used, the results.md `## Work Unit Summary` section tracks per-unit status:

```markdown
## Work Unit Summary

| Unit | Description | Status | Files Changed | Validation |
|------|-------------|--------|---------------|------------|
| WU-001 | Schema + ORM model | ✅ Complete | `migration.sql`, `user.py` | PASS |
| WU-002 | Frontend component | ✅ Complete | `ProfileImage.tsx` | PASS |
| WU-003 | API endpoint | ✅ Complete | `profile.py`, `upload.py` | PASS |
| WU-004 | Integration tests | ✅ Complete | `test_integration.py` | PASS |

**Decomposition trigger:** 7 files across 3 layers (Database, Backend, Frontend)
**Parallel groups executed:** 3
**Session recovery:** Not needed
```

---

## Constraints

- **Frozen criteria** — decomposition cannot introduce new acceptance criteria. If you find missing criteria, note them for the backlog
- **Soft cap: 3-6 units** — more than 6 means the scope should have been split at the requirements level
- **Sub-iterations skip decomposition** — `_a/_b/_c` iterations address specific fixes from orchestrator review, not full re-decomposition
- **The orchestrator reviews the full scope** — work units are a tactical implementation detail. The orchestrator's 4-choice decision evaluates all criteria together, not per-unit

---

## Troubleshooting

**Q: A unit can't be validated independently — it breaks compilation.**
A: The unit's files are too tightly coupled to split. Merge it with the unit it depends on. Not every file boundary is a good unit boundary.

**Q: More than 6 units needed.**
A: The scope is too large. Recommend splitting at the requirements level (separate requirements docs for each major subsystem).

**Q: Session interrupted, but `current_work_unit.conf` is missing.**
A: Fall back to reading `results.md` — check the Work Unit Summary for which units show as complete. Resume from the first incomplete unit.

**Q: One unit failed validation but others passed.**
A: Fix the failing unit. Don't re-execute completed units unless the fix requires changes to their files (which would indicate the dependency graph was wrong).

---

## Integration Points

| Component | How it interacts with work units |
|-----------|------|
| Agent selection (Step 1.5) | Runs per-unit instead of per-scope |
| Task invocation (Step 2) | One Task per unit, parallel where possible |
| Validation (Step 3) | Scoped to unit's files |
| Results (Step 5) | Work Unit Summary section added |
| Knowledge base (planning) | Entries may inform decomposition decisions |
| Adversarial review | Reviews full scope, not per-unit |
