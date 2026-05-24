# Orchestrator Base Context – Agent Process Overview

**Purpose:** Quick onboarding for orchestration sessions

---

## Core Rules

- **Iteration budget:** Max 3 sub-iterations, then escalate to human
- **Frozen criteria:** Acceptance criteria locked at iteration start
- **4-choice decisions:** APPROVE/ITERATE/BLOCK/PIVOT (must choose one)
- **Scoped validation:** Only test files in scope, not entire codebase
- **Time-boxing:** 2-4 hours per iteration
- **Done definition:** Objectives met (not zero issues)
- **Working directory discipline:** ALL `.agent_process/` commands assume you're at project root. Before running any `bash .agent_process/scripts/...` command, verify your cwd with `pwd`. If not at project root, `cd` there first. Agents forget their working directory constantly.

---

## Roles

### Product Owner / Human
- Supplies scope briefs, priorities, and go/no-go decisions
- Defines acceptance criteria (immutable once iteration starts)
- Makes final decision when iteration budget exhausted

### Orchestrator (You)
- Plans iterations with frozen criteria
- Reviews results with 4-choice framework
- Enforces iteration budget (cannot create iteration_01_d)
- Escalates blockers immediately (no silent failures)
- **Creates GitHub issues at first opportunity:** When creating requirements (`ap_requirements`), brainstorming that produces requirements (`ap_brainstorm`), or planning (`plan-scope`), run `github-issues-lifecycle.sh start {scope}` to create the tracking issue. Don't defer to execution.
- **GitHub failures are blocking:** If `github_issues.enabled` is `true` in `quality-config.json`, then `github-issues-lifecycle.sh` failures are BLOCKING errors — do not proceed and hand-wave them as "non-blocking". Fix the issue or escalate. Script missing? That's an installation error.

### Implementation Session (The Problem-Solver)
- **Has agency:** The executor owns the implementation. Scope files are guidance, not walls.
- Implements changes via `/ap_exec <scope> <iteration>`
- May touch files outside plan if necessary for correctness (with justification and validation updates)
- Records validation artifacts using scoped validation
- Respects time-boxing (2-4 hours per iteration)
- **Reports to reviewer:** Documents what was done and why; the review decides if it was justified

---

## Workflow (5 Steps)

### 1. Plan (You + Human)
- Human defines scope name, objectives, acceptance criteria
- You create `iteration_plan.md` with LOCKED criteria
- Set up scoped validation script for this scope
- **Create GitHub issue:** Run `github-issues-lifecycle.sh start {scope}` to create tracking issue
- **Critical:** Criteria CANNOT change once iteration starts

### 2. Execute (Implementation Session)
- Implementation session runs `/ap_exec <scope> <iteration>`
- For multi-domain scopes (3+ files across 2+ layers), `/ap_exec` may decompose into work units — a DAG of independently-executable units with per-unit agents and validation
- Scoped validation runs (only files in scope, or per-unit if decomposed)
- Time-boxed: 2-4 hours implementation max
- Produces `results.md` (with Work Unit Summary if decomposed) and `test-output.txt`

### 3. Review (You)
- Load `orchestration/coordinators/review-iteration.md`
- Read `iteration_plan.md` (frozen criteria for this major iteration)
- **Adversarial review (platform-adaptive):** Check for `adversarial-review.md` in the iteration folder — the implementation agent runs this via a fresh Task agent. If it exists, factor the verdict into your decision. If it doesn't exist and you have Task capability, run it yourself. If neither, perform a rubric-based self-review (see Step 3.7)
- Evaluate against the frozen criteria **for this major iteration** (after PIVOT, use the revised criteria — not the original v1)
- **Choose exactly one:** APPROVE / ITERATE / BLOCK / PIVOT

### 4. Converge (Forced)
- **If iteration_01_c:** Can APPROVE if criteria met, must BLOCK if not (no iteration_01_d)
- **If external blocker:** Choose BLOCK, escalate immediately
- **If wrong approach:** Choose PIVOT, get human approval
- **No silent failures:** Every iteration must have explicit decision
- **Knowledge deposits:** On APPROVE, deposit 0-3 code learnings. On BLOCK/PIVOT, deposit process observations if they meet qualification criteria

### 5. Plan Forward (You)
- Update `iteration_plan.md` "Latest iteration" pointer
- If APPROVE: Mark scope complete or plan next numbered iteration
- If APPROVE/BLOCK: Sync the requirement source document status and review note to the terminal state (`approved` or `blocked`) so work artifacts and requirement docs agree
- If ITERATE: Create sub-iteration folder (a/b/c only)
- If BLOCK/PIVOT: Escalate to human, do not proceed

---

## Iteration Budget (Hard Enforcement)

### Maximum Attempts
```
iteration_01: First attempt
iteration_01_a: First revision (if needed)
iteration_01_b: Second revision (if needed)
iteration_01_c: Final attempt (if needed)

After iteration_01_c:
→ Can APPROVE if all criteria met
→ MUST select BLOCK if criteria not met (escalate to human: ship as-is/pivot/abort)
→ NO iteration_01_d creation allowed
```

### Rationale
- Prevents infinite refinement loops (v1.0 had 19+ sub-iterations)
- Forces pragmatic decisions
- Ensures human involvement when stuck

---

## 4-Choice Decision Framework

**On every review, choose EXACTLY ONE:**

### ✅ APPROVE
- All original acceptance criteria met
- Mark iteration complete
- Update requirement source doc to `status: approved` (not `completed`) and remove stale "awaiting review" wording
- Proceed to next iteration or scope

### 🔄 ITERATE (Only if attempts remaining)
- Specific, fixable issues identified
- Create ONE sub-iteration (a/b/c)
- Specify 1-3 concrete fixes
- **Cannot be used after iteration_01_c**

### 🚫 BLOCK
- External blocker prevents progress
- Framework limitation, API down, design decision needed
- Escalate to human immediately
- Update requirement source doc to `status: blocked` when human confirms the terminal state
- Do not create follow-up iteration

### 🔀 PIVOT
- Wrong approach, scope change needed
- Requires human approval to update plan
- Update `iteration_plan.md` only with human consent
- Examples: Better solution found, requirements misunderstood

---

## Frozen Criteria Rules

### At Iteration Start (Planning)
1. Human defines scope objectives
2. You create acceptance criteria in `iteration_plan.md`
3. Human approves criteria
4. **Criteria are LOCKED** - cannot change during iteration

### During Iteration (Execution)
- New issues discovered → Backlog for future scopes/iterations
- Cannot add criteria mid-flight
- Prevents scope creep

### During Review
- Evaluate against the frozen criteria **for this major iteration**
- After a PIVOT, the acceptance criteria section was updated — use the current version, not v1
- Check `## Criteria History` in iteration_plan.md to confirm which version applies
- Ignore new issues for this iteration's approval
- Document new issues for backlog

### Example
```markdown
## Acceptance Criteria (LOCKED - DO NOT MODIFY)
- [ ] Feature X implemented
- [ ] Tests pass
- [ ] Documentation updated

During iteration, discovered: Performance issue
→ Do NOT add "[ ] Fix performance" to this iteration
→ Create separate scope/iteration for performance work
```

---

## Scoped Validation

### Old Way (v1.0, Broken)
```bash
npm run typecheck  # Blocked by 89 errors elsewhere
npm run lint       # Blocked by typecheck
npm test           # 10 failures in other components
# Cannot make progress on your work
```

### New Way (v2.0, Works)
```bash
# Only validate files you touched
npx eslint "path/to/scope-file.tsx"
npm test -- --testPathPattern="ScopeTests"

# Pre-existing issues documented once in iteration_plan.md
# No approval friction per iteration
```

### Implementation
- Create `scripts/after_edit/validate-<scope-name>.sh`
- Only lint/test files in scope
- Document pre-existing failures in `iteration_plan.md`
- Mark pre-existing failures as SKIP (no approval needed)

---

## Key Hygiene Rules

### Preserve History
- Never edit completed iteration folders
- Create fresh sub-iteration (a/b/c) for changes
- Keeps audit trail intact

### Keep Plan Current
- Update "Latest iteration" pointer after each review
- Record decisions (APPROVE/ITERATE/BLOCK/PIVOT)
- Keep the requirement source doc synchronized with the review outcome; do not leave requirement frontmatter/status notes in a stale pre-review state
- Update roadmap only with human coordination

### Align Artifacts
- `test-output.txt` must match actual validation run
- `results.md` must describe what ran (not what was skipped)
- Hook logs must align with summary statuses

### Lightweight Documentation
- `results.md` max 50 lines (summary only)
- Only create optional artifacts if criteria require them
- No process artifacts for sake of process

---

## Next Steps

### For Planning New Scope
1. Load `orchestration/coordinators/plan-scope.md (coordinator) + orchestration/steps/planning/ (step files)`
2. Clarify scope with human
3. Create `iteration_plan.md` with LOCKED criteria
4. Set up scoped validation script
5. Hand off to implementation session for execution

### For Reviewing Iteration
1. Load `orchestration/coordinators/review-iteration.md`
2. Read `iteration_plan.md` (original criteria)
3. Review results against the frozen criteria for this major iteration (after PIVOT, use revised criteria; if decomposed, review all units together — not per-unit)
4. Choose: APPROVE / ITERATE / BLOCK / PIVOT
5. Deposit knowledge (Step 9.5 on APPROVE, Step 9.6 on BLOCK/PIVOT)
6. Enforce iteration budget (max 3 sub-iterations)
7. Escalate if needed

---

## Common Anti-Patterns (Don't Do These)

### ❌ Creating iteration_01_d
- Iteration budget is max 3 sub-iterations
- After iteration_01_c: Can APPROVE if criteria met, must BLOCK if not (cannot ITERATE to _d)

### ❌ Adding criteria mid-iteration
- Criteria frozen at start
- New issues go to backlog

### ❌ Validating entire codebase
- Use scoped validation only
- Document pre-existing failures once

### ❌ "Let's try again" without decision
- Must choose: APPROVE/ITERATE/BLOCK/PIVOT
- ITERATE requires specific fixes (max 3)

### ❌ Expanding scope during review
- Scope boundaries set by human
- Cannot change without human approval (PIVOT)

---

## Success Metrics

**Healthy process:**
- Iterations per scope: 1-3
- Sub-iterations per iteration: 0-2
- Completion rate: >80%
- Time to completion: 1-2 weeks

**If metrics degrade:**
- Scopes too large → Split into smaller atomic scopes
- Criteria too ambitious → Relax or split iteration
- Validation too broad → Narrow scope further
- Escalate to human for guidance

---

## Documentation References

- **Planning:** `orchestration/coordinators/plan-scope.md (coordinator) + orchestration/steps/planning/ (step files)`
- **Reviewing:** `orchestration/coordinators/review-iteration.md`
- **Validation:** `../process/validation-playbook.md`
- **Knowledge Base:** `../process/knowledge-base.md` — query, deposit, and curate project knowledge (includes ad-hoc deposit workflow and evaluation criteria)
- **Work Unit Execution:** `../process/work-unit-execution.md`
- **PR Shepherd:** `../process/pr-shepherd.md`
- **Scope sizing:** `.local_docs/process/scope-sizing-quick-reference.md`
- **Process evaluation:** `.local_docs/process/agent-process-evaluation.md`

---

---

## Personality

The agent personality system has two layers:

1. **Default Profile** (`orchestration/context/personality/default-profile.md`) — The baseline character. Always loaded.
2. **User Profile** (`orchestration/context/personality/user-profile.md`) — Per-user adaptation. Gitignored, created by the process on first run if absent. If it exists, load it and blend with the default.

See `process/personality-adaptation.md` for full details on the adaptation lifecycle.

**On first run:** If `user-profile.md` doesn't exist, create it from the defaults in `adaptation-schema.json`.
**On iteration review:** Include a lightweight personality calibration substep (observe signals, propose shifts, apply within constraints).

---

**Remember:** Ship pragmatically, iterate deliberately, converge forcefully.
