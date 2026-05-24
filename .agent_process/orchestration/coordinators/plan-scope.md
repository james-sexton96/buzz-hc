# Plan Scope Coordinator (Lean)

Plan a scope in 4 steps instead of 13.

## Model Tiers

| Tier | Use For | Claude Code | Codex |
|------|---------|-------------|-------|
| **cheap** | Scope setup, size check | haiku | gpt-5.4-mini |
| **capable** | Technical assessment | sonnet | gpt-5.4 |
| **synthesis** | Defining frozen criteria, creating final plan | opus | gpt-5.4 |

## Prohibitions

- Do NOT commit, push, or modify application code during planning
- Planning artifacts go to `<project_root>/.agent_process/work/{scope}/.run/planning/` only

---

## Step 0: Resolve Input

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh resolve-input "{{input}}"
```

Returns: `scope`, `requirement_path`, `gh_issue`. 

If `requirement_path` is null, ask user for the requirement path.

Read the requirement file.

---

## Step 1: Scope Setup (HARD GATE)

Spawn **cheap** agent:

```
Agent({
  description: "Setup scope {scope}",
  prompt: "Read orchestration/steps/planning/01-setup.md and execute.
    Requirement: {requirement_path}
    
    Check scope size, derive names, create work folder.
    If FAIL: offer breakdown or override.
    Output: <project_root>/.agent_process/work/{scope}/.run/planning/01-setup.md"
})
```

**Gate:** If `VERDICT: FAIL`, stop and offer breakdown. Do not proceed until PASS/WARN.

---

## Step 2: Technical Assessment

Spawn **capable** agent:

```
Agent({
  description: "Assess {scope}",
  prompt: "Read orchestration/steps/planning/02-assess.md and execute.
    Requirement: {requirement_path}
    Scope: {scope}
    
    Query knowledge base, review code feasibility, document design decisions.
    Capture WHY decisions were made, not just WHAT.
    Output: <project_root>/.agent_process/work/{scope}/.run/planning/02-assess.md"
})
```

---

## Step 3: Define Scope

Spawn **synthesis** agent — frozen criteria cascade through the entire pipeline:

```
Agent({
  model: "{synthesis}",  // Claude Code: "opus" | Codex: use best available
  description: "Define {scope}",
  prompt: "Read orchestration/steps/planning/03-define.md and execute.
    Requirement: {requirement_path}
    Scope: {scope}
    Input: <project_root>/.agent_process/work/{scope}/.run/planning/02-assess.md
    
    Define files, create frozen criteria, assess doc impact.
    Output: <project_root>/.agent_process/work/{scope}/.run/planning/03-define.md"
})
```

---

## Step 4: Create Plan

Spawn **synthesis** (best model) agent:

```
Agent({
  model: "{synthesis}",  // Claude Code: "opus" | Codex: use best available
  description: "Create plan for {scope}",
  prompt: "Read orchestration/steps/planning/04-plan.md and execute.
    Requirement: {requirement_path}
    Scope: {scope}
    Inputs: All <project_root>/.agent_process/work/{scope}/.run/planning/*.md files
    
    Document pre-existing issues, create validation script, write iteration plan.
    Include Design Decisions table from assessment.
    Output: .agent_process/work/{scope}/iteration_plan.md"
})
```

---

## Human Prerequisites (if needed)

A `human-prereqs.md` file pauses execution and asks the human a question. **The default answer to "should this be a human prereq?" is NO.** The orchestrator already has full planning context — most "uncertain" planning decisions are the orchestrator's call to make, recorded in the iteration plan's **Design Decisions** table, not surfaced to the human.

### Filter: should this be a human prereq?

For every candidate prereq item, the planner MUST answer YES to all three questions. If any answer is NO, the item is NOT a human prereq — fold it into the iteration plan's **Design Decisions** table with the orchestrator's call and reasoning.

1. **Can the orchestrator structurally NOT make this decision?**
   YES examples: external system credentials needed; deploy / production sign-off; an upstream team must agree to a contract change; the answer commits real budget or timeline beyond this scope; the original requirement explicitly named a feature the planner wants to defer.
   NO examples: "should we exclude feature X because the existing storage contract doesn't support it?" (planner has full context to decide); "which of two equally-supported library APIs should we use?" (planner picks based on existing patterns); "is this implementation approach correct?" (that's a planner judgment, documented in Design Decisions).
2. **Could a developer who doesn't know the codebase's internal vocabulary answer this in 30 seconds?**
   The question must be answerable without referencing internal table names, internal step numbers, internal contract identifiers, or planning artifacts (`Step 3 locked criteria`, `the Phase 2 evidence path`, `the X service's internal table`). If a human would need a glossary to even understand what's being asked, the question itself is wrong-shaped — either rewrite it in user-outcome terms, or remove it.
3. **What concrete user-visible (or operator-visible) behavior changes based on this answer?**
   The planner must articulate the consequence in one sentence, in user terms. "The feature X type won't appear in the new view" passes. "We won't widen the contract surface for type X" does not — that's an implementation framing of the same fact, but a human can't act on it.

If all three answers are YES, write the item to `human-prereqs.md` using the structured template below. Otherwise, document the decision in the iteration plan's **Design Decisions** table and proceed.

### Template (when a human prereq is genuinely needed)

```
.agent_process/work/{scope}/human-prereqs.md
```

```markdown
# Human Prerequisites — {scope}

## Pre-execution (ask before work starts)

- [ ] {Plain-language question — one sentence, no codebase jargon, written for a developer who didn't sit in the planning session.}
  - **What this means:** {1–2 sentences in user-outcome terms. Describe the visible change, not the implementation. NEVER reference internal step numbers, internal table or contract names, or planning artifacts.}
  - **Recommended answer:** {YES or NO + one-line reason. The orchestrator's recommendation should be obvious; the human is sanity-checking, not making the call cold.}
  - **If you say YES:** {what happens, in user-outcome terms}
  - **If you say NO:** {what happens, in user-outcome terms — usually "scope re-opens" or "extra cycle of work"}
  - **Override required because:** {one of: external credential / external commitment / scope-shape change / requirement-named feature being deferred / production-impact decision. If you can't fill this in concretely, the item should not be on this list — fold it into Design Decisions instead.}

## Mid-execution (pause before live / external / destructive steps)

- [ ] {action and trigger — e.g. "before deploying to staging," "before running the migration"}
  - **What this means:** {user/operator-visible context}
  - **Recommended answer:** {go / hold + reason}

## Post-execution (ask after work completes)

- [ ] {follow-up, cutover, notification, prod parity confirmation}
  - **What this means:** {what the human will see and need to do after the iteration ships}

## Allowed Responses
- **proceed** — prerequisites satisfied, continue execution
- **blocked** — cannot proceed, stop and report
- **local-only** — skip live/external validation, note limitation in results
```

### Worked example: a question that should NOT go to the human

Planning surfaces the question "the original requirement listed feature X as a target type, but the existing storage contract doesn't support it for this surface — keep X out of this scope, or re-scope to widen the contract?"

Filter:
- Q1: Can the orchestrator decide this? YES it can — the storage contract is observable; widening it is a separate scope; deferring is the obvious call. **FAIL filter Q1.**
- Action: do NOT write a human prereq. Add to the iteration plan's **Design Decisions** table:

  | Decision | Chosen | Rejected | Why |
  |----------|--------|----------|-----|
  | Feature X coverage in this scope | Defer X (file follow-up scope) | Widen storage contract now | Existing storage doesn't support X for this surface; widening is a separate concern that re-opens the contract review. User impact: the new view shows the supported types only; X support comes in a follow-up. |

  The user will see this at review time and can override if they disagree. Default flow does not pause.

### Worked example: a question that SHOULD go to the human

Original requirement explicitly listed feature X as a primary deliverable, and the planner discovered mid-planning that supporting X needs ~1 week of contract widening that isn't budgeted.

Filter:
- Q1: Can the orchestrator decide this alone? NO — the original requirement promised X; deferring it changes what the user agreed to. **PASS Q1** (requirement-named feature being deferred).
- Q2: Can a developer answer in 30 seconds without internal vocabulary? Yes if framed as "X support won't ship with this scope; OK to defer?" rather than "exclude entity_type=X due to contract limitation." **PASS Q2.**
- Q3: Concrete user-visible consequence? Yes — "X won't appear in the new view." **PASS Q3.**
- Action: write the item with the full structure. Recommended answer: YES (defer). The human can override if X is critical.

```markdown
- [ ] **Feature X support won't ship with this scope. OK to defer X to a follow-up?**
  - **What this means:** Users will see the new view with the four originally-planned types, but feature X (also originally planned) won't appear yet. X stays accessible everywhere it was before; just no entry in the new view.
  - **Recommended answer:** YES — defer X. Reason: supporting X here adds ~1 week of foundational work; deferring keeps this scope on schedule and X ships in the next iteration.
  - **If you say YES:** This scope ships in current shape (~3 days); X follow-up scope opens after.
  - **If you say NO:** This scope grows by ~1 week; the foundational widening goes in first; AC review re-opens.
  - **Override required because:** The original requirement explicitly listed X as a target type; deferring it is a scope-shape change the orchestrator shouldn't make unilaterally.
```

This file is optional — only create it if at least one item passes all three filter questions. When it exists, the execution coordinator is required to present its contents to the human at Step 0.5 (before work) and Step 6 (after work) of `execute.md`; it will never silently skip.

**Looser legacy formats are still accepted on the executor side.** If an older `human-prereqs.md` is missing the structured fields, the executor will surface what's there as best it can — but the planning step should produce the structured form for any new file.

---

## GitHub Issues (if enabled)

After plan created:

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh start {scope}
```

This creates/adopts the issue and sets `status:planning`.

---

## Completion

Verify outputs:
- `<project_root>/.agent_process/work/{scope}/.run/planning/01-setup.md`
- `<project_root>/.agent_process/work/{scope}/.run/planning/02-assess.md`
- `<project_root>/.agent_process/work/{scope}/.run/planning/03-define.md`
- `.agent_process/work/{scope}/iteration_plan.md`

Report to user:

```markdown
## Planning Complete

**Scope:** {scope}
**Plan:** `.agent_process/work/{scope}/iteration_plan.md`

- Files: {N}
- Criteria: {N}
- Pre-existing issues: {N} (will SKIP)

**Next:** `/ap_exec {scope} iteration_01`
```
