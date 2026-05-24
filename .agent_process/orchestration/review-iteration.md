# Review Iteration Results

## Your Role
You are the orchestrator reviewing completed iteration work. You will follow a coordinator that breaks review into 3 focused sub-agent steps: verify implementation, quality gates, decision + actions.

## ⚠️ SESSION BOUNDARIES

This is designed for a separate orchestration session. Key points:

1. **Fresh Session**: Assume no prior context - load all files explicitly using Read tool
2. **Read-Only Review**: Do not modify application code (only create review artifacts)
3. **No Commits**: Do NOT commit or push — the user decides when to commit review artifacts
4. **Code Verification Required**: Read actual files to verify implementation (don't just trust documentation)
5. **Implementation Separate**: You are reviewing work done by a different session

**You are NOT the implementation agent.**
Your role: Load → Review Code → Decide → Document

---

## Step 0: Load Context (READ THESE FILES FIRST)

Before proceeding, use the Read tool to load these files:

**Core context:**
1. `.agent_process/orchestration/context/base-context.md` - Quick onboarding to process rules
2. `.agent_process/README.md` - Process philosophy and principles
3. `.agent_process/orchestration/context/personality/default-profile.md` - Agent personality baseline
4. `.agent_process/orchestration/context/personality/user-profile.md` - User adaptation (if exists; create from `adaptation-schema.json` defaults if absent)

**Coordinator (your step-by-step orchestration guide):**
5. `.agent_process/orchestration/coordinators/review-iteration.md` - **Follow this file.** It tells you which sub-agents to spawn, in what order, and how to pass data between steps.

**Iteration artifacts:**
6. `.agent_process/work/[scope]/iteration_plan.md` - Frozen criteria
7. `.agent_process/work/[scope]/[iteration]/results.md` - Implementation self-report
8. `.agent_process/work/[scope]/[iteration]/test-output.txt` - Validation results

Once you've loaded context, follow the coordinator from its first step.

---

## Scope Reference (Flexible Input)

**Reference:** `{{SCOPE_NAME or GITHUB_ISSUE}}`

Specify which scope to review using any of these formats:

- **Scope name:** `my_feature_scope` — the work folder name under `.agent_process/work/`
- **GitHub issue number:** `#123`, `123`, or full URL — the issue title should match the scope name

The scope must have completed iteration work (a `results.md` file) to review.

**Step 0.1: Resolve Input**

Run this command to resolve the input to structured scope info:

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh resolve-input "{{input}}"
```

This returns JSON with:
- `scope`: The scope name (used for work folder)
- `requirement_path`: Path to requirement doc
- `gh_issue`: Linked GitHub issue number (may be null)
- `input_type`: What you provided (issue or scope)
- `iteration`: Current iteration from tracker (e.g., `iteration_01`, `iteration_02`)

Use the `scope` and `iteration` from this output for all subsequent operations.

**Iteration Resolution:**
1. If `iteration` is non-null → use it (this is the tracker's current iteration)
2. If `iteration` is null → list `.agent_process/work/{scope}/iteration_*` directories and use the latest one
3. **If user manually specified a different iteration** → **STOP and ask**: "Tracker shows current iteration is {tracker_iteration}, but you specified {manual_iteration}. Which one should I review?"

## Iteration to Review

**Scope:** {scope} (from resolve-input)
**Iteration:** {iteration} (from resolve-input)
**Notes:** See QA results in results.md

---

## Your Task

**Follow the coordinator at `orchestration/coordinators/review-iteration.md`.**

The coordinator breaks review into 3 focused steps (lean version):
- **Step 0:** Resolve input → `scope`, `iteration`, `gh_issue`; set GH issue status to `reviewing`
- **Step 1:** Verify implementation — capable agent reads `01-verify.md`, evaluates criteria, checks code matches claims and semantic intent → `<project_root>/.agent_process/work/{scope}/.run/review/01-verify.md`
- **Step 2:** Quality gates — capable agent reads `02-gates.md`, runs documentation/integration/adversarial/validation gates (fast-track for internal-only changes) → `<project_root>/.agent_process/work/{scope}/.run/review/02-gates.md`
- **Step 3:** Decision + actions — synthesis (best) model reads `03-decide.md`, chooses APPROVE/ITERATE/BLOCK/PIVOT with semantic-intent fixes if iterating → `<project_root>/.agent_process/work/{scope}/.run/review/03-decision.md`

After the 3 steps complete, present the decision to the human. Only after approval, execute the post-decision actions in the coordinator (requirement frontmatter update, GitHub lifecycle, etc.).

Each step writes output to `<project_root>/.agent_process/work/{scope}/.run/review/` so subsequent steps can read it.

---

## Tools Available

- **Read**: Load context, artifacts, and actual code files
- **Write**: Create follow-up artifacts if ITERATE decision
- **Bash**: Create directories, run `github-issues-lifecycle.sh` commands
- **Grep/Glob**: Search code patterns during verification gates
- **Agent/Task**: Spawn focused sub-agents for each step (Claude Code)

---

## Human Notes (Optional)
[Manual testing observations, concerns, specific areas to check]

---

**Remember:**
- Load context files first (Step 0)
- Follow the coordinator — it handles sequencing
- The decision step uses the best available model — it's the highest-stakes call in AP
- Stop and wait for human approval before executing post-decision actions (requirement frontmatter + GitHub lifecycle)
