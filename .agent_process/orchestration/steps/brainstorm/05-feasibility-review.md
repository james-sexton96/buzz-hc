# Step 05: Feasibility Review (MANDATORY)

**Model tier:** synthesis
**Tools needed:** Read, Grep, Glob
**Input:** Synthesis (`<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md`), idea
**Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md`

---

## Instructions

Follow the standard feasibility review process in **`process/code-feasibility-review.md`**.

This step ensures the brainstorm output is grounded in codebase reality before becoming a formal requirement.

## Context for This Step

- **You are:** The feasibility gatekeeper for brainstormed requirements
- **Your goal:** Ensure this requirement will pass plan-scope's checks
- **Blocking gate:** If `CLARIFICATION_NEEDED: true`, you must resolve or escalate

## Why This Step is Mandatory

Previously, brainstorm was producing idealistic requirements that got rejected by plan-scope's code review. This step catches those issues early by running the same checks plan-scope uses.

## Input: What You're Reviewing

Read `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md` and extract:
- **Success Criteria** — Are these measurable and testable?
- **Technical Assessment** — Are the files/components real?
- **Proposed Approach** — Is this feasible with current architecture?
- **Open Questions** — Can these be resolved from code/docs?

## Your Task

1. **Run the full feasibility review** per `process/code-feasibility-review.md`
2. **Cross-check synthesis claims** against actual code
3. **Resolve what you can** — answer questions from code/docs
4. **Flag what you can't** — questions requiring human judgment

## Handling Clarification Needs

**If questions are resolvable from code/docs:**
- Answer them in your review
- Update findings to reflect the answers
- Set `CLARIFICATION_NEEDED: false`

**If questions require human judgment:**
- List them clearly with context
- Set `CLARIFICATION_NEEDED: true`
- The coordinator will present these to the user before proceeding

## How Findings Inform the Requirement

Your review directly shapes the final requirement:

| Your Finding | Becomes |
|--------------|---------|
| Knowledge patterns | Implementation guidance in Technical Requirements |
| Knowledge gotchas | Items in Known Risks |
| Knowledge anti-patterns | Items in Out of Scope |
| Feasibility concerns | Refined Success Criteria |
| Risk assessment | Known Risks with mitigations |

## Output Location

Write your review to: `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md`

Use the output template from `process/code-feasibility-review.md`.

## What Happens Next

- If `CLARIFICATION_NEEDED: false` → Proceed to Step 05b (Scope Size Check)
- If `CLARIFICATION_NEEDED: true` → Coordinator asks user, then re-runs this step or proceeds
