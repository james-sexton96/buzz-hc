# Brainstorm Coordinator

You are orchestrating a multi-agent brainstorm. Take a vague idea and turn it into a well-structured AP requirement through diverse perspectives, synthesis, and mandatory feasibility review.

## Inputs

- **Idea:** provided by the user (freeform text from `{{ idea }}`)

## Brainstorm Directory

Before starting, propose 2-3 short directory names derived from the idea and ask the user to pick one (or suggest their own). Use snake_case, max ~40 chars.

Example for "Improve the login experience for returning users":
> 1. `improve_login_returning_users`
> 2. `returning_user_login_ux`
> 3. `login_experience_improvement`

Once confirmed, create the directory:
```bash
mkdir -p .agent_process/brainstorms/{chosen_name}/.run
```

All step outputs go to `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/`.
The final synthesis saves to `.agent_process/brainstorms/{chosen_name}/brainstorm.md`.

## Model Tiers

| Tier | Use For | Claude Code | Codex |
|------|---------|-------------|-------|
| **cheap** | Config check | haiku | gpt-5.4-mini |
| **capable** | Context + code review, brainstorm agents, requirement writing | sonnet | gpt-5.4 |
| **synthesis** | Aggregating 3 perspectives, feasibility gatekeeper | opus | gpt-5.4 |

## Data Flow

Step outputs go to `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/`.

---

## Local Environment Instructions

Read `.agent_process/process/local_environment_instructions.md` before starting steps. If any section is not `<none>`, pass relevant content to sub-agents that need it. These instructions are ADDITIVE — they augment but never skip default steps.

---

## Step Sequence

### Step 01: Config Check (sequential)

Spawn a **cheap** sub-agent with `orchestration/steps/brainstorm/01-config-check.md`.
- **Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/01-config.md`

### Step 02: Gather Context + Code Review (sequential)

Spawn a **capable** sub-agent with `orchestration/steps/brainstorm/02-gather-context.md`.
- Pass: idea
- **Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/02-context.md`

This step now does actual code exploration — not just README scanning — so brainstorm agents have grounded technical context.

### Step 03: Brainstorm Agents (3 in parallel)

Spawn THREE **capable** sub-agents **simultaneously** with `orchestration/steps/brainstorm/03-spawn-agents.md`.
- Pass: idea, context output
- **Outputs:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-product.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-architect.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-critical.md`

Wait for all three.

### Step 04: Synthesize (sequential)

Spawn a **synthesis** sub-agent with `orchestration/steps/brainstorm/04-synthesize.md`.
- Pass: all 3 agent outputs
- **Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md`
- Also saves to `.agent_process/brainstorms/{chosen_name}/brainstorm.md`

### Step 05: Feasibility Review (MANDATORY)

Spawn a **synthesis** sub-agent with `orchestration/steps/brainstorm/05-feasibility-review.md`.
- Pass: synthesis output, idea
- **Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md`

This step runs the same checks plan-scope uses — knowledge base query, CLAUDE.md review, actual code review. It ensures the requirement is grounded in codebase reality before writing.

**Gate behavior:**
- If `CLARIFICATION_NEEDED: false` → Proceed to Step 05b
- If `CLARIFICATION_NEEDED: true` → Present questions to user, resolve, then proceed

**Do NOT skip this step.** It prevents idealistic requirements that get rejected later.

### Step 05b: Scope Size Check + Breakdown Offer

Run scope-sizing check per `process/scope-sizing-check.md` with thresholds from `orchestration/scope-sizing-rules.md`.

**Purpose:** Catch oversized requirements NOW while you have full brainstorm context.

**Process:**
1. Using the synthesis output, count: criteria, files expected to change, subsystems
2. Run 5-second check
3. Compare against thresholds

**If VERDICT: PASS or WARN:**
- Output: `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05b-scope-check.md`
- Proceed to Step 06
- If WARN, include risk note for the requirement

**If VERDICT: FAIL:**
- Output: `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05b-scope-check.md` with failure details
- Ask the user:

> "The brainstormed requirement exceeds size thresholds:
> - Criteria: {N} (threshold: >10)
> - Files: {N} (threshold: >15)  
> - Subsystems: {N} (threshold: >4)
>
> Would you like me to break it down into smaller requirements?
> 1. **Yes, break it down** (recommended — you have full brainstorm context)
> 2. **No, write as single requirement** (plan-scope will require breakdown later)"

**If user chooses breakdown:**
1. Follow breakdown process in `process/scope-breakdown.md`
2. Use brainstorm context to inform split decisions
3. Create child requirements with sequential naming
4. Validate each child against thresholds
5. Output: `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05b-breakdown.md` + child requirement files
6. Proceed to Step 06 with children

**If user declines:**
- Note in synthesis: "User chose to defer breakdown to plan-scope"
- Proceed to Step 06 with single requirement

### Steps 06-08: Transform + Confirm + Write (sequential)

Spawn a **capable** sub-agent with `orchestration/steps/brainstorm/06-08-transform-write.md`.
- Pass: synthesis output, feasibility review output, scope check output, idea
- **Output:** The requirement `.md` file(s) in `requirements_docs/{category}/`
- Also: confirm with user (title, category, priority, complexity), update roadmap

If breakdown occurred in Step 05b:
- Transform and write EACH child requirement
- Create parent breakdown file
- Update roadmap with all children

The feasibility review findings inform:
- Technical Requirements (from knowledge patterns)
- Known Risks (from knowledge gotchas + code review)
- Out of Scope (from knowledge anti-patterns)
- Implementation guidance

---

## Verification Checklist

- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/01-config.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/02-context.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-product.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-architect.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-critical.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/04-synthesis.md`
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05-feasibility-review.md`
- [ ] `CLARIFICATION_NEEDED: false` in feasibility review
- [ ] `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/05b-scope-check.md`
- [ ] `VERDICT: PASS` or `WARN` (or breakdown completed)
- [ ] Requirement file(s) in `requirements_docs/`

---

## After Brainstorm Completes

**Next step:** Plan the scope using `orchestration/plan-scope.md` (in Codex), then run `/ap_exec {requirement_id}`.

Do NOT suggest:
- `/metaswarm:start` or any metaswarm commands
- Any workflow outside the AP system

AP workflow: `/ap_brainstorm` → `plan-scope.md` (Codex) → `/ap_exec` → `/ap_release`
