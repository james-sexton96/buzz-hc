# Work Unit Decomposition Template

**Purpose:** Architect Agent prompt for decomposing multi-domain scopes into executable work units.

---

## Instructions for Decomposition

You are breaking a multi-domain scope into independently-executable work units. The scope has frozen acceptance criteria — your job is tactical decomposition, not scope expansion.

---

## Inputs You Receive

1. **Frozen acceptance criteria** (from iteration_plan.md)
2. **Files in scope** (the full list of files to create/modify)
3. **Technical assessment** (orchestrator's implementation guidance)
4. **Knowledge base entries** (if any matched during planning)

---

## Your Task

Analyze the files and criteria, then produce a DAG of work units.

### Output Format

```markdown
## Work Unit Decomposition

**Scope:** {{scope_name}}
**Total units:** N
**Estimated parallel groups:** M

### WU-001: [Short description]
- **Files:** [list of files this unit touches]
- **Layer:** [Database | Backend | Frontend | Tests | Infrastructure | Docs]
- **Dependencies:** [None | list of WU-IDs that must complete first]
- **Criteria addressed:** [AC1, AC2, etc. — reference by number from iteration_plan.md]
- **Agent:** [recommended agent type from ap_exec.md Step 1.5]
- **Validation:** [what to check after this unit — compile, specific tests, grep]

### WU-002: [Short description]
...

### Execution Order

[ASCII DAG showing parallel and sequential relationships]

WU-001 ──┐
          ├──→ WU-003 ──→ WU-004
WU-002 ──┘

### Parallel Groups
- **Group 1 (parallel):** WU-001, WU-002
- **Group 2 (sequential after Group 1):** WU-003
- **Group 3 (sequential after Group 2):** WU-004
```

---

## Rules

1. **Frozen criteria are sacred** — if you identify something missing, note it under `### Backlog Items Discovered` but do NOT create a work unit for it

2. **3-6 units max** — more suggests the scope needs splitting at the requirements level. If you genuinely need more, explain why

3. **Each unit must be independently validatable** — after completing WU-001, the codebase should compile and pass the unit's targeted validation. Don't create units that leave the codebase broken mid-execution

4. **Minimize cross-unit file overlap** — ideally each file appears in exactly one unit. If a file must be touched by multiple units, document the dependency explicitly and ensure the later unit depends on the earlier one

5. **Tests go with the code they test** unless they span multiple units (integration tests) — in which case they get their own unit that depends on all the code units

6. **Don't over-decompose** — if two files are tightly coupled and will be edited together, keep them in one unit. The goal is useful boundaries, not maximum granularity

---

## Dependency Guidelines

| Situation | Dependency? |
|-----------|------------|
| Frontend reads from API that's being changed | Frontend depends on Backend |
| Tests mock modules being modified | Tests depend on the code unit |
| Schema migration + API using new schema | API depends on Schema |
| Two independent frontend components | No dependency — parallel |
| Docs describing changed API | Docs depends on API unit |

---

## Example

**Scope:** Add user profile images (7 files, 3 layers)

```markdown
## Work Unit Decomposition

**Scope:** user_profile_images
**Total units:** 4
**Estimated parallel groups:** 3

### WU-001: Database schema + ORM model
- **Files:** `migrations/add_profile_image.sql`, `backend/models/user.py`
- **Layer:** Database
- **Dependencies:** None
- **Criteria addressed:** AC1 (schema exists), AC2 (model updated)
- **Agent:** backend-security:backend-expert
- **Validation:** `python manage.py migrate --check`, type check

### WU-002: Frontend profile image component
- **Files:** `frontend/src/components/ProfileImage.tsx`, `frontend/src/hooks/useProfileImage.ts`
- **Layer:** Frontend
- **Dependencies:** None (uses existing API contract)
- **Criteria addressed:** AC5 (UI displays image)
- **Agent:** frontend-excellence:react-specialist
- **Validation:** `npx tsc --noEmit`, component renders

### WU-003: API endpoint + S3 upload
- **Files:** `backend/api/profile.py`, `backend/services/image_upload.py`
- **Layer:** Backend
- **Dependencies:** WU-001 (needs schema)
- **Criteria addressed:** AC3 (upload endpoint), AC4 (S3 storage)
- **Agent:** backend-security:backend-expert
- **Validation:** `pytest tests/test_profile_api.py`

### WU-004: Integration tests
- **Files:** `tests/test_profile_integration.py`
- **Layer:** Tests
- **Dependencies:** WU-001, WU-002, WU-003
- **Criteria addressed:** AC6 (integration tests pass)
- **Agent:** dev-accelerator:test-automator
- **Validation:** `pytest tests/test_profile_integration.py`

### Execution Order
WU-001 ──┐
          ├──→ WU-003 ──→ WU-004
WU-002 ──────────────────┘

### Parallel Groups
- **Group 1 (parallel):** WU-001, WU-002
- **Group 2 (after WU-001):** WU-003
- **Group 3 (after all):** WU-004
```
