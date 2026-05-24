# Plan New Scope

## Your Role
You are the orchestrator planning a new development scope. You will follow a coordinator that breaks planning into focused sub-agent steps.

## ⚠️ SESSION BOUNDARIES

This is designed for a separate orchestration session. Key points:

1. **Fresh Session**: Assume no prior context - load all files explicitly using Read tool
2. **Read-Only Review**: Do not modify application code (only create process artifacts)
3. **No Commits**: Do NOT commit or push — the user decides when to commit planning artifacts
4. **Handoff Required**: Stop and provide summary for human approval before execution
5. **Implementation Separate**: A different session will execute the work

**You are NOT the implementation agent.**
Your role: Plan → Review Code → Decide → Handoff to implementation

---

## Preflight: Load Context (READ THESE FILES FIRST)

Before proceeding, use the Read tool to load these files:

**Core context:**
1. `.agent_process/orchestration/context/base-context.md` - Quick onboarding to process rules
2. `.agent_process/README.md` - Process philosophy and principles
3. `.agent_process/orchestration/context/personality/default-profile.md` - Agent personality baseline
4. `.agent_process/orchestration/context/personality/user-profile.md` - User adaptation (if exists; create from `adaptation-schema.json` defaults if absent)

**Coordinator (your step-by-step orchestration guide):**
3. `.agent_process/orchestration/coordinators/plan-scope.md` - **Follow this file.** It tells you which sub-agents to spawn, in what order, and how data flows between steps.

**Templates (sub-agents will use these):**
4. `.agent_process/templates/iteration-plan.md` - Template for iteration plan
5. `.agent_process/requirements_docs/_TEMPLATE_requirements.md` - Requirements format

**Validation reference:**
6. `.agent_process/process/validation-playbook.md` - Validation patterns

Once you've loaded context, follow the coordinator from its first step.

---

## Scope Reference (Flexible Input)

**Reference:** `{{SCOPE_NAME, GITHUB_ISSUE, or REQUIREMENT_PATH}}`

Specify which scope to plan using any of these formats:

- **Requirement path:** `category/my_feature_scope.md` — direct path to the requirement doc
- **Scope name:** `my_feature_scope` — matches the `id:` field in a requirement doc's frontmatter
- **GitHub issue number:** `#123`, `123`, or full URL — the issue title must match a scope name

If using a GitHub issue number, a requirement document must exist with a matching scope name. The requirement doc is the source of truth for acceptance criteria and scope boundaries.

The coordinator's Step 0 resolves whichever form you pass into the concrete `scope` / `requirement_path` / `gh_issue` triple — you don't need to do this yourself.

---

## Your Task

**Follow the coordinator at `orchestration/coordinators/plan-scope.md`.** It is the authoritative flow; this wrapper only sets context and hands off.

The coordinator is the **lean 4-step** variant. Each step is executed by a focused sub-agent that receives only its own instructions.

Steps the coordinator will guide you through:
- **Step 0:** Resolve input → `scope`, `requirement_path`, `gh_issue`
- **Step 1:** Scope Setup — **HARD GATE** (cheap agent; scope-size check, folder creation)
- **Step 2:** Technical Assessment (capable agent; KB query + code feasibility + design decisions)
- **Step 3:** Define Scope (capable agent; files, frozen criteria, doc impact)
- **Step 4:** Create Plan (synthesis / best model; aggregates into `iteration_plan.md`)
- **Then:** optional `human-prereqs.md`, GitHub issue start, completion summary

Each step writes its output to `.agent_process/work/{scope}/.run/planning/` so subsequent steps can read it.

If you find anything in this wrapper that contradicts the coordinator, the coordinator wins.

---

## Tools Available

Use these tools throughout:

- **Read**: Load requirements, review code files, load context
- **Write**: Create new files (iteration_plan.md, validation scripts, etc.)
- **Edit**: Modify existing files if needed
- **Bash**: Create directories, make scripts executable (chmod +x)
- **Glob/Grep**: Search for code patterns when assessing feasibility
- **Agent/Task**: Spawn focused sub-agents for each step (Claude Code)

---

## Human Notes (Optional)
[Any additional context not in requirements doc]

---

**Remember:**
- Load context files first (Preflight)
- Follow the coordinator — it handles sequencing and parallelism
- Each sub-agent sees only its step file (~40-80 lines), keeping focus sharp
- Stop and provide handoff summary for approval
