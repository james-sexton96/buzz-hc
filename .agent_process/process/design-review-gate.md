# Design Review Gate

> **Diátaxis type:** How-To Guide (task-oriented)

## Overview

The design review gate is an optional quality checkpoint between planning and execution. When triggered, 2-4 specialist reviewers independently assess the iteration plan for design-level issues that would be expensive to fix post-implementation.

**Activation:** Set `complexity: complex` in the requirement frontmatter AND enable `design_review.enabled: true` in `quality-config.json`.

**Where it runs:** Step 8.5 of `orchestration/coordinators/plan-scope.md (coordinator) + orchestration/steps/planning/ (step files)`, after the iteration plan is complete but before execution begins.

**Default:** Disabled. This is an opt-in gate for architecturally significant scopes.

---

## When to Use

| Scope Characteristic | Use Design Review? |
|---------------------|-------------------|
| Touches auth, tokens, encryption, user data | Yes — tag `complexity: complex` |
| Crosses 3+ system layers (DB + API + frontend + tests) | Yes |
| Introduces a new architectural pattern | Yes |
| Modifies a critical shared module | Yes |
| Single-layer focused work (just frontend, just tests) | No |
| Bug fix with clear root cause | No |
| Documentation-only scope | No |

---

## How It Works

### 1. Tag the Requirement

Add `complexity: complex` to the requirement's frontmatter:

```yaml
---
id: auth_oauth2_integration
type: requirement
category: authentication
status: not_started
priority: high
complexity: complex
---
```

### 2. Enable the Gate (if not already)

In `.agent_process/quality-config.json`:

```json
{
  "design_review": {
    "enabled": true
  }
}
```

### 3. Planning Triggers the Gate

When the orchestrator reaches Step 8.5 during planning, it:

1. Checks both conditions (config enabled + frontmatter complexity)
2. Selects 2-4 specialist reviewers based on scope characteristics
3. Spawns reviewers (parallel Task agents in Claude Code, sequential rubric in Codex)
4. Collects verdicts

### 4. Reviewers Assess the Plan

Each reviewer receives the iteration plan and relevant knowledge base entries. They produce:
- **APPROVE** — plan is sound from their specialist perspective
- **REQUEST_CHANGES** — specific, actionable revisions needed

### 5. Gate Resolution

- **All APPROVE** → Execution proceeds normally
- **Any REQUEST_CHANGES** → Orchestrator revises the plan and re-submits (max 2 cycles)
- **After 2 failed cycles** → Human escalation with compiled feedback

---

## Reviewer Selection

| Scope Touches | Reviewer |
|--------------|----------|
| Any complex scope | **Architect Reviewer** (always included) |
| Auth, tokens, encryption, user data | **Security Reviewer** |
| UI, UX, user-facing workflows | **Product/UX Reviewer** |
| 3+ system layers | Additional domain specialist |

Minimum 2 reviewers, maximum 4. Configured in `quality-config.json` under `design_review.min_reviewers` and `design_review.max_reviewers`.

---

## Platform-Adaptive Execution

The design review runs during planning, which may happen in either Claude Code or Codex:

| Platform | Execution Method |
|----------|-----------------|
| Claude Code | Parallel Task agents — true isolation between reviewers |
| Codex | Sequential rubric walk-through — orchestrator assumes each reviewer lens in turn |

The same prompt template (`templates/design-review-prompt.md`) is used in both cases. Quality gates remain mandatory regardless of platform.

---

## Troubleshooting

**Gate keeps blocking on the same feedback:**
- After 2 revision cycles, the gate escalates to the human. Don't force it through — the reviewer is catching something real.
- Review the REQUEST_CHANGES feedback. Is the plan genuinely addressing it, or is the revision superficial?

**Reviewers producing boilerplate approvals:**
- The prompts need sharpening. The reviewer should be finding specific, actionable issues — not rubber-stamping.
- Consider adding domain-specific context to the reviewer prompt (e.g., "this project uses Firebase Auth, not custom JWT").

**Gate slowing down simple scopes:**
- Don't tag simple scopes as `complexity: complex`. The gate only fires when explicitly triggered.
- If in doubt, leave `complexity` out of the frontmatter — the default is no gate.

**Codex reviews feel weaker than Claude Code reviews:**
- They are — sequential self-review has anchoring bias. This is the same trade-off as adversarial review on Codex. The rubric structure mitigates it but doesn't eliminate it.
- For truly critical scopes, consider running the planning phase in Claude Code instead.

---

## Integration Points

| Component | Interaction |
|-----------|-------------|
| `orchestration/coordinators/plan-scope.md (coordinator) + orchestration/steps/planning/ (step files)` Step 8.5 | Runs the gate between plan creation and execution handoff |
| `templates/design-review-prompt.md` | Specialist reviewer prompt template |
| `templates/iteration-plan.md` | `## Design Review` section records the outcome |
| `quality-config.json` | `design_review` section controls enabled state and settings |
| Requirement frontmatter | `complexity: complex` triggers the gate |
| Knowledge base | Relevant entries are passed to reviewers as context |

---

## Relationship to Other Gates

```
Plan → [Design Review Gate] → Execute → [Adversarial Review] → Review → Decision
        ↑ catches design flaws      ↑ catches implementation gaps
        before code exists           after code exists
```

The design review gate and adversarial review are complementary:
- **Design review** catches "this approach won't work" before writing code
- **Adversarial review** catches "this code doesn't meet the criteria" after writing code

Both are optional. Both are platform-adaptive. Neither replaces the orchestrator's judgment.
