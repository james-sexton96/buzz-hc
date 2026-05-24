# AI Agent Process

A structured workflow framework for AI-powered development with Claude Code. Provides role separation, iteration management, and decision frameworks that turn ad-hoc AI coding into a repeatable development process.

**Philosophy:** Ship pragmatically, iterate deliberately, pivot when you learn.

---

## This Framework Is Not About AI Doing Everything

Let's be clear: **this is not an autopilot.**

The goal is not to type a prompt and walk away while AI builds your product. That path leads to mediocre software, missed edge cases, and systems nobody understands. AI can write code fast, but speed without direction produces noise.

This framework exists to **elevate your work, not eliminate it.** You're still the architect. You still make the hard calls. You still own the outcome. What changes is *where* you spend your energy:

- **You define what matters** — requirements, acceptance criteria, quality standards
- **You make judgment calls** — when to pivot, what tradeoffs to accept, when "good enough" is good enough
- **You review with intention** — not rubber-stamping AI output, but genuinely evaluating whether it solves the problem
- **You build understanding** — the knowledge base, the patterns, the "why" behind decisions

AI agents handle the mechanical work: writing boilerplate, running validations, organizing artifacts, executing repetitive tasks. They're tireless and consistent. But they don't know what your users need. They don't feel the weight of technical debt. They can't tell when a "working" solution misses the point entirely.

**The human-in-the-middle isn't a bottleneck — it's the whole point.**

Great software comes from humans who care deeply about the problem, supported by tools that handle the grunt work. This framework structures that collaboration: AI does the coding and scope organization, you do the thinking and deciding. The result isn't "AI-generated code" — it's *your* work, built faster and more consistently.

If you want to ship something you're proud of, something that solves real problems well, you have to stay engaged. This framework helps you do that at a higher level — focused on design, quality, and outcomes rather than syntax and boilerplate.

**Do great work. AI is here to help, not to replace you.**

---

## Quick Start

```bash
# 1. Install the framework into your project
/path/to/ai_agent_process/install.sh /path/to/your/project

# 2. Open Claude Code in your project and initialize
/ap_project init

# 3. Create your first requirement
/ap_brainstorm "improve the login experience"
# or: /ap_requirements add "user_authentication"

# 4. Plan the iteration (read orchestration prompt, work with Claude)
#    Open: .agent_process/orchestration/plan-scope.md
#    This creates: iteration_plan.md with frozen acceptance criteria

# 5. Execute the work
/ap_exec user_auth iteration_01

# 6. Review results (orchestrator decides: APPROVE/ITERATE/BLOCK/PIVOT)
#    Open: .agent_process/orchestration/review-iteration.md

# 7. Ship it (after APPROVE)
/ap_release pr
```

**Key distinction:** Steps 3, 5, 7 are slash commands. Steps 4 and 6 are orchestration prompts you read with Claude — they guide multi-step planning and review workflows.

Read on for the full picture.

---

## Dependencies

### Required

| Dependency | Purpose | Install |
|------------|---------|---------|
| **Claude Code** | AI orchestration engine (slash commands, agents, hooks) | [claude.ai/code](https://claude.ai/code) |
| **Git** | Version control, branching, history tracking | Pre-installed on most systems |
| **Bash 4+** | Install script, validation hooks, utility scripts | Pre-installed on Linux/macOS |
| **GitHub CLI (`gh`)** | PR creation, issue management, CI status checks | `brew install gh` / [cli.github.com](https://cli.github.com) |

### Optional

| Dependency | Purpose | When You Need It | Install |
|------------|---------|------------------|---------|
| **Metaswarm** (Claude Code plugin) | Multi-agent brainstorming, design review gates, PR shepherd, self-reflection | Enhanced ideation and review quality | [marketplace plugin](https://github.com/dsifry/metaswarm) — enable via `quality-config.json` |
| **Docker** | Containerized dev environment with bypass permissions | Safe experimentation, CI parity | See `.docker-dev/README.md` |
| **Python 3** | Knowledge migration, quality config management | Only during `install.sh` | Pre-installed on most systems |

---

## Table of Contents

1. [This Framework Is Not About AI Doing Everything](#this-framework-is-not-about-ai-doing-everything)
2. [Quick Start](#quick-start)
3. [Dependencies](#dependencies)
4. [Overview](#overview)
5. [The Workflow](#the-workflow)
6. [Roles & Responsibilities](#roles--responsibilities)
7. [Key Concepts](#key-concepts)
8. [Slash Commands Reference](#slash-commands-reference)
9. [Quality Configuration](#quality-configuration)
10. [Directory Structure](#directory-structure)
11. [Getting Started Guide](#getting-started-guide)
12. [Success Metrics](#success-metrics)
13. [Customization](#customization)
14. [Documentation Reference](#documentation-reference)

---

## Overview

The AI Agent Process solves a common problem: AI-assisted development often becomes a chaotic loop of "try something, see if it works, try again." This framework introduces structure through:

- **Role separation** — Human defines scope, orchestrator plans/reviews, implementation executes
- **Frozen criteria** — No moving goalposts during implementation
- **Iteration budgets** — Maximum 3 attempts before escalation prevents infinite loops
- **Decision framework** — Every review ends with a clear decision (APPROVE/ITERATE/BLOCK/PIVOT)
- **Scoped validation** — Only test what you changed, not the entire codebase
- **Knowledge base** — Patterns, gotchas, and decisions compound across iterations
- **Adversarial review** — Fresh agent verifies criteria without implementation bias

### What This Provides

| Component | Purpose |
|-----------|---------|
| **Slash Commands** | Executable workflows for planning, execution, review, and release |
| **Orchestration Prompts** | Decomposed coordinator + step file architecture for planning and review |
| **Iteration Templates** | Standardized artifacts for tracking work |
| **Validation Tools** | Scoped testing scripts with automatic hook-based execution |
| **Project Management** | Roadmap, backlog, and requirements tracking via `/ap_project` |
| **Knowledge Base** | JSONL-based patterns, gotchas, decisions accumulated across iterations |
| **Adversarial Review** | Fresh-instance code review for unbiased criterion verification |
| **Work Unit Decomposition** | DAG-based parallel execution for multi-domain scopes |
| **PR Shepherd** | Post-PR agent monitoring CI, reviews, and merge-readiness |
| **Design Review Gate** | Multi-reviewer plan assessment for complex scopes (opt-in) |
| **Quality Configuration** | Centralized feature control via `quality-config.json` |
| **GitHub Issues Integration** | Issue-first workflow with optional scope and work unit tracking via GitHub Issues |
| **Metaswarm Integration** | Optional multi-agent brainstorming, design review, PR automation (opt-in) |

---

## The Workflow

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        THE AGENT PROCESS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. PLAN          2. EXECUTE        3. REVIEW        4. SHIP   │
│   ─────────        ─────────         ─────────        ──────    │
│   Human defines   /ap_exec          Orchestrator    /ap_release │
│   scope + criteria implements        reviews         creates PR │
│                                                                 │
│   ┌─────────┐     ┌─────────┐       ┌─────────┐     ┌────────┐ │
│   │ Define  │────▶│ Execute │──────▶│ Review  │────▶│ Ship   │ │
│   │ Scope   │     │ Work    │       │ Results │     │ It!    │ │
│   └─────────┘     └─────────┘       └────┬────┘     └────────┘ │
│                                          │                      │
│                        ┌─────────────────┼─────────────────┐    │
│                        ▼                 ▼                 ▼    │
│                   ┌────────┐       ┌──────────┐      ┌───────┐ │
│                   │ITERATE │       │  PIVOT   │      │ BLOCK │ │
│                   │(a/b/c) │       │(new iter)│      │(human)│ │
│                   └────────┘       └──────────┘      └───────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Steps

#### Step 0: Create Requirement (Slash Commands)
```bash
/ap_brainstorm "idea"           # Multi-agent ideation → requirement
/ap_requirements add "name"     # Direct creation
/ap_requirements add #42        # From GitHub Issue
```
Produces a formal requirement file in `.agent_process/requirements_docs/`.

#### Step 1: Plan (Orchestration Prompt)
```
Read: .agent_process/orchestration/plan-scope.md
```
1. Orchestrator sizes the scope (fits 1-2 weeks? split if too large)
2. Queries knowledge base for relevant patterns and gotchas
3. Creates `iteration_plan.md` with **LOCKED** acceptance criteria
4. Sets up scoped validation script
5. **Critical:** Criteria CANNOT change once iteration starts

#### Step 2: Execute (Slash Command)
```bash
/ap_exec <scope> <iteration>
```
- Reads the iteration plan
- For multi-domain scopes (3+ files across 2+ layers), decomposes into work units — a DAG of independently-executable tasks with per-unit agents and validation
- Implements changes within scope boundaries (parallel where possible)
- Runs scoped validation (hook fires automatically)
- Spawns adversarial reviewer (fresh agent, zero context)
- Creates `results.md` (with Work Unit Summary if decomposed) and `test-output.txt`

#### Step 3: Review (Orchestration Prompt)
```
Read: .agent_process/orchestration/review-iteration.md
```
- Evaluates results against **frozen criteria for this major iteration** (after PIVOT, uses revised criteria)
- Verifies actual code, not just claims in results.md
- Reads adversarial review verdict
- Chooses exactly one decision: **APPROVE / ITERATE / BLOCK / PIVOT**

#### Step 4: Ship or Continue
- **APPROVE** → `/ap_release pr` to create PR (slash command)
- **ITERATE** → Creates sub-iteration (a/b/c), max 3 attempts, return to Step 2
- **PIVOT** → New major iteration with revised criteria (requires human approval), return to Step 1
- **BLOCK** → Escalate to human, do not proceed

### End-to-End Process Flow

The complete lifecycle from idea to acceptance, with all optional features enabled:

```
┌───────────────────────────────────────────────────────────────────────┐
│                  IDEA → ACCEPTANCE: FULL LIFECYCLE                    │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─── IDEATION ─────────────────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  GH Issue?              Vague idea?            Clear req?        │ │
│  │  ──────────             ────────────           ──────────        │ │
│  │  /ap_brainstorm #42     /ap_brainstorm "idea"  /ap_requirements  │ │
│  │  /ap_requirements       │                        add "title"     │ │
│  │    add #42              ├─ Product agent              │          │ │
│  │    │                    ├─ Architecture agent         │          │ │
│  │    │                    ├─ Critical agent             │          │ │
│  │    │                    ▼                             │          │ │
│  │    │                  Brainstorm synthesis            │          │ │
│  │    │                    │                             │          │ │
│  │    │                    ├─ Optional: design review    │          │ │
│  │    ▼                    ▼                             ▼          │ │
│  │  ┌───────────────────────────────────────────────────────────┐   │ │
│  │  │ Formal AP Requirement (.agent_process/requirements_docs/) │   │ │
│  │  │ • YAML frontmatter (id, type, category, status, priority) │   │ │
│  │  │ • Objective, Technical Requirements, Success Criteria      │  │ │
│  │  │ • Auto-associated with GH issue if #N was provided        │   │ │
│  │  └───────────────────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────┘│
│                                  │                                    │
│                                  ▼                                    │
│  ┌─── PLANNING (Orchestrator) ──────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  Human copies requirement → orchestration/plan-scope.md          │ │
│  │                                                                  │ │
│  │  Orchestrator:                                                   │ │
│  │    0.5. GH issue check — adopt existing, create, or skip        │ │
│  │    1. Size check — fits 1-2 weeks? Split if too large            │ │
│  │    2. Query knowledge base — patterns, gotchas, decisions        │ │
│  │    3. Create iteration_plan.md with LOCKED acceptance criteria   │ │
│  │    4. Set up scoped validation script                            │ │
│  │    5. If complexity: complex → design review gate (2-4 agents)   │ │
│  │    6. Create work/ directory and iteration_01/ folder            │ │
│  │                                                                  │ │
│  │  Output: .agent_process/work/{scope}/iteration_plan.md           │ │
│  │          .agent_process/scripts/after_edit/validate-{scope}.sh   │ │
│  └───────────────────────────────────────────────────────────────────┘│
│                                  │                                    │
│                                  ▼                                    │
│  ┌─── EXECUTION (/ap_exec) ─────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  Step 0.4:  GitHub Issues health check (if enabled)              │ │
│  │  Step 0.5:  Scope tracking init (adopt or create issue + events) │ │
│  │  Step 0.7:  Pre-flight checks                                    │ │
│  │    • Session recovery — detect interrupted work                  │ │
│  │    • Working tree check — uncommitted changes in scope?          │ │
│  │    • Branch check — auto-checkout scope/{scope}                  │ │
│  │    • Git context — recent commits for files in scope             │ │
│  │  Step 1:    Load context (plan, criteria, prior results)         │ │
│  │  Step 1.25: Decomposition (3+ files, 2+ layers → work units)     │ │
│  │  Step 2:    Implement (specialized agent or parallel units)      │ │
│  │  Step 3:    Scoped validation (hook fires automatically)         │ │
│  │  Step 4:    Full validation + test-output.txt                    │ │
│  │  Step 4.5:  Adversarial review (fresh agent, zero context)       │ │
│  │  Step 5:    Document results → results.md                        │ │
│  │                                                                  │ │
│  │  Output: results.md, test-output.txt, adversarial-review.md      │ │
│  └───────────────────────────────────────────────────────────────────┘│
│                                  │                                    │
│                                  ▼                                    │
│  ┌─── REVIEW (Orchestrator) ────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  Step 1:   Load context (plan, results, test output)             │ │
│  │  Step 1.5: Scope event verification (check tracking state)        │ │
│  │  Step 2:   Evaluate against frozen criteria (version-aware)      │ │
│  │  Step 3:   Code verification (read actual files, not claims)     │ │
│  │  Step 3.5: Documentation verification gate                       │ │
│  │  Step 3.6: Integration verification gate                         │ │
│  │  Step 3.7: Read adversarial review verdict                       │ │
│  │  Step 4:   CHOOSE ONE DECISION:                                  │ │
│  │                                                                  │ │
│  │    APPROVE  → Close epic, deposit knowledge, suggest release     │ │
│  │    ITERATE  → 1-3 specific fixes, create sub-iteration (a/b/c)  │ │
│  │    BLOCK    → Close epic, escalate to human immediately          │ │
│  │    PIVOT    → Requires human approval, revised criteria          │ │
│  │                                                                  │ │
│  │  Step 10: Suggest artifact evaluation                            │ │
│  └───────────────────────────────────────────────────────────────────┘│
│                                  │                                    │
│                           (on APPROVE)                                │
│                                  ▼                                    │
│  ┌─── RELEASE (/ap_release) ────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  1. Gather scope context and changes                             │ │
│  │  2. Update CHANGELOG.md (Added/Changed/Fixed/Removed/Security)   │ │
│  │  3. Create build tag (build/N)                                   │ │
│  │  4. Commit, push, create PR via gh                               │ │
│  │  5. Optional: PR shepherd monitors CI + reviews                  │ │
│  │                                                                  │ │
│  │  Modes: pr | beta | release patch|minor|major                    │ │
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Slash Commands vs Orchestration Prompts

The framework uses two types of interactions:

| Type | How to Invoke | Purpose | Examples |
|------|---------------|---------|----------|
| **Slash Commands** | `/ap_<command>` | Single-step operations | `/ap_brainstorm`, `/ap_exec`, `/ap_release` |
| **Orchestration Prompts** | `Read: .agent_process/orchestration/<file>.md` | Multi-step workflows with sub-agents | `plan-scope.md`, `review-iteration.md` |

**Slash commands** are self-contained: you invoke them, they run, they're done.

**Orchestration prompts** are collaborative: you read the prompt file with Claude, and it guides a multi-step workflow — spawning sub-agents, gathering your input, and producing structured artifacts. These are the "thinking" phases where plans are created and decisions are made.

```
Typical workflow:
  /ap_brainstorm "idea"              ← Slash command creates requirement
  Read: plan-scope.md                ← Orchestration prompt creates iteration plan
  /ap_exec scope iteration_01        ← Slash command implements
  Read: review-iteration.md          ← Orchestration prompt reviews and decides
  /ap_release pr                     ← Slash command ships
```

---

## Roles & Responsibilities

### Product Owner (Human)
- Supplies scope briefs, priorities, and go/no-go decisions
- Defines acceptance criteria (immutable once iteration starts)
- Makes final decisions when iteration budget exhausted
- Approves PIVOTs and unblocks BLOCKed work

### Orchestrator (AI Planning Role)
- Plans iterations with frozen criteria
- Reviews results using 4-choice framework
- Enforces iteration budget (cannot create `iteration_01_d`)
- Escalates blockers immediately (no silent failures)

### Implementation (AI Execution Role)
- Implements changes via `/ap_exec <scope> <iteration>`
- Records validation artifacts using scoped validation
- Respects scope boundaries and frozen criteria
- Does NOT modify acceptance criteria

---

## Key Concepts

### Two-Level Iteration Model

```
Major iterations (criteria changes via PIVOT):
  iteration_01  → Initial criteria (v1)
  iteration_02  → Revised criteria (v2) after PIVOT
  iteration_03  → Further revision (v3) if needed

Sub-iterations (fixes within same criteria via ITERATE):
  iteration_01_a/b/c  → Fix attempts for v1 criteria
  iteration_02_a/b/c  → Fix attempts for v2 criteria

Example progression:
  01 → 01_a → 01_b → PIVOT → 02 → 02_a → APPROVE
```

| Decision | What it means | Creates |
|----------|---------------|---------|
| **PIVOT** | Wrong approach, need revised criteria | New major iteration (02, 03...) |
| **ITERATE** | Minor fixes needed, same criteria | Sub-iteration (_a, _b, _c) |
| **APPROVE** | All criteria met | Scope complete |
| **BLOCK** | External blocker, need human help | Nothing (escalate) |

### Iteration Budget

```
iteration_01     ← First attempt
iteration_01_a   ← First fix (if needed)
iteration_01_b   ← Second fix (if needed)
iteration_01_c   ← Final attempt (if needed)

After iteration_01_c:
 → Can APPROVE if criteria met
 → MUST BLOCK if criteria not met (no iteration_01_d)
```

This prevents infinite refinement loops. After 3 sub-iterations, the human must decide: ship as-is, pivot, or abort.

### Frozen Criteria

Acceptance criteria are **LOCKED** at iteration start:

```markdown
## Acceptance Criteria (LOCKED - DO NOT MODIFY)
- [ ] Feature X implemented
- [ ] Tests pass
- [ ] Documentation updated

During iteration, discovered: Performance issue
→ Do NOT add "[ ] Fix performance" to this iteration
→ Add to backlog for future scope
```

**Why?** Prevents scope creep and moving goalposts. New discoveries become backlog items.

### Knowledge Base

The project accumulates wisdom across iterations in `.agent_process/knowledge/`:

```
knowledge/
├── patterns.jsonl       # Recommended approaches that worked
├── gotchas.jsonl        # Non-obvious pitfalls that bit us
├── decisions.jsonl      # Architectural choices with rationale
└── anti-patterns.jsonl  # Approaches that failed
```

- **Planning phase** queries the knowledge base for entries matching the scope
- **APPROVE decisions** deposit 0-3 code learnings (patterns, gotchas, decisions)
- **BLOCK/PIVOT decisions** deposit 0-2 process observations (agent behavior, scope structure issues)
- Starts empty, grows organically — no manual population needed
- Entries are JSONL (one JSON object per line) for easy grep/search
- Knowledge always lives in `.agent_process/knowledge/` as the canonical store

See `process/knowledge-base.md` for full documentation.

### Adversarial Review

A **fresh reviewer agent** with zero implementation context independently verifies each frozen criterion against the actual code. The reviewer:

- Receives only the frozen criteria and the changed files (NOT results.md)
- Produces a binary **PASS/FAIL** per criterion with **file:line evidence**
- Cannot be influenced by watching the implementation (no anchoring bias)
- Is **advisory input** to the orchestrator's 4-choice decision, not a replacement

**Platform-adaptive execution:** The primary review runs during implementation (Step 4.5 of `/ap_exec`) using a fresh Task agent. The orchestrator reads the pre-existing verdict. If no verdict exists, the orchestrator falls back to a rubric-based self-review using the same structured criteria.

### Work Unit Decomposition

When a scope touches 3+ files across 2+ system layers (backend + frontend, schema + API + tests, etc.), `/ap_exec` automatically decomposes the scope into independently-executable work units:

```
WU-001: Schema + ORM model  ──┐
                                ├──→ WU-003: API endpoint ──→ WU-004: Integration tests
WU-002: Frontend component  ──┘
```

Each unit has its own files, agent selection, and validation. Independent units run in parallel; dependent units wait for prerequisites.

- **Trigger:** 3+ files AND 2+ system layers AND first iteration (not sub-iteration)
- **Soft cap:** 3-6 units per scope
- **Session recovery:** `current_work_unit.conf` tracks progress across interruptions
- **Results:** `## Work Unit Summary` section in results.md

See `process/work-unit-execution.md` for the full how-to guide.

### PR Shepherd

An optional post-PR agent activated with `--shepherd` that monitors the PR lifecycle:

- **CI monitoring** — Checks pipeline status, auto-fixes lint/type failures
- **Review response** — Drafts replies to reviewer comments, implements change requests within scope
- **Merge-readiness** — Reports when all checks pass and threads are resolved

The shepherd only modifies files already in the PR, never force-pushes, and never merges. It's a CI babysitter with commenting privileges — the human always clicks merge.

See `process/pr-shepherd.md` for the full how-to guide.

### Design Review Gate

An opt-in quality checkpoint for architecturally significant scopes. When a requirement has `complexity: complex` in its frontmatter and `design_review.enabled` is `true` in `quality-config.json`, 2-4 specialist reviewers assess the iteration plan before execution begins:

- **Architect Reviewer** — Always included for complex scopes
- **Security Reviewer** — When scope touches auth, tokens, encryption, user data
- **Product/UX Reviewer** — When scope touches user-facing workflows

All reviewers must APPROVE. REQUEST_CHANGES triggers plan revision (max 2 cycles, then human escalation). Disabled by default — zero overhead for normal scopes.

See `process/design-review-gate.md` for the full how-to guide.

### GitHub Issues Integration

Optional scope and work unit tracking via GitHub Issues with an **issue-first workflow** — issues can exist before any AP command runs:

- **Issue-first flow** — Create a GitHub Issue, then pass it to `/ap_brainstorm #42` or `/ap_requirements add #42` to seed the workflow from the issue's content
- **Associate existing issues** — Link any issue to a scope via the `associate` action, or the pipeline auto-creates when missing
- **Adopt or create** — If a scope already has a linked issue, the pipeline reuses it (no duplicates); if not, it creates one or asks the user
- **Pipeline-wide status labels** — Each stage updates the issue: `status:planning` → `status:executing` → `status:reviewing` → `status:approved`
- **Sub-issues per work unit** — Individual work unit tracking as sub-issues
- **Sub-agent delegation** — All GH operations are isolated in cheap sub-agents via `process/github-issues-handling.md`, keeping parent coordinators focused and context-lean
- **Session recovery** — `scope-tracker.jsonl` + `scope-events.log` provide authoritative local state regardless of GH availability

Configured during `install.sh` (prompts for opt-in). File-based tracking always works even with GitHub Issues disabled.

See `process/github-issues-integration.md` for setup and `process/github-issues-handling.md` for the sub-agent delegation pattern.

### Scoped Validation

Only validate files you changed:

```bash
# Good: Scoped validation
npx eslint "path/to/changed-file.tsx"
npm test -- --testPathPattern="ScopeTests"

# Bad: Full codebase validation
npm run typecheck  # Fails on 89 unrelated errors
npm test           # Fails on 10 unrelated tests
```

Pre-existing issues are documented once in the iteration plan, not re-litigated each iteration.

---

## Slash Commands Reference

### `/ap_brainstorm` — Ideation → Requirement

```bash
/ap_brainstorm "Improve the login experience"     # Multi-agent brainstorm → formal requirement
/ap_brainstorm "We need better error handling"     # Works with or without metaswarm
/ap_brainstorm #42                                 # Seed brainstorm from GitHub Issue #42
```

Spawns 3 parallel agents (Product, Architecture, Critical) to explore the idea from different angles, synthesizes their output, optionally runs design review, and creates a formal AP requirement. When given a `#N` issue argument, reads the issue content as the brainstorm seed and associates the resulting requirement with that issue.

### `/ap_requirements` — Requirements Management

```bash
/ap_requirements add "feature name"          # Create requirement (offers brainstorm option)
/ap_requirements add #42                     # Create requirement from GitHub Issue #42
/ap_requirements import "path/to/file.md"    # Import existing file as requirement
/ap_requirements list                        # Show all requirements by category
/ap_requirements list "infrastructure"       # Filter by category
```

When given a `#N` argument, reads the issue title and body to pre-populate the requirement and automatically associates the scope with that issue in `scope-tracker.jsonl`.

### `/ap_project` — Project Management

```bash
/ap_project init                    # Initialize roadmap infrastructure
/ap_project discover                # Scan project and build roadmap
/ap_project status                  # Check current project status

/ap_project add-todo "description"  # Add item to backlog
/ap_project set-status "req_id complete reason"  # Set requirement status
/ap_project archive "req_id type reason"         # Archive requirement
/ap_project archive-completed       # Bulk archive approved work

/ap_project sync                    # Reconcile roadmap with work/
/ap_project report                  # Generate stakeholder report
/ap_project help                    # Show all commands
```

### `/ap_exec` — Execute Iterations

```bash
/ap_exec <scope> <iteration>
# Example: /ap_exec user_auth iteration_01
# Example: /ap_exec user_auth iteration_01_a
```

**What it does:**
1. Pre-flight checks (session recovery, working tree, branch, git context)
2. Reads iteration plan and frozen criteria
3. Decomposes into work units if multi-domain scope
4. Implements changes within scope
5. Runs scoped validation (automatic via hook)
6. Adversarial review (fresh agent, zero context)
7. Creates results artifacts

### `/ap_release` — Release Workflow

```bash
/ap_release pr                     # PR only (no version tag)
/ap_release pr --shepherd          # PR + shepherd monitoring
/ap_release beta                   # Beta tag + PR
/ap_release release patch          # Patch release (1.0.0 → 1.0.1)
/ap_release release minor          # Minor release (1.0.0 → 1.1.0)
/ap_release release major          # Major release (1.0.0 → 2.0.0)

# No-scope mode (analyze git diff instead of work/)
/ap_release noscope pr
/ap_release noscope release patch
```

**`--shepherd` flag:** After PR creation, launches a shepherd agent that monitors CI status, responds to review comments, auto-fixes lint/type issues, and reports merge-readiness. The shepherd never merges — the human always clicks merge.

### `/ap_iteration_results` — Document Results

```bash
/ap_iteration_results <scope> <iteration>
```

Creates structured `results.md` from validation output.

### `/ap_changelog_init` — Initialize Changelog

```bash
/ap_changelog_init
```

Initializes CHANGELOG.md from git history for projects not yet tracking releases.

---

## Quality Configuration

`quality-config.json` provides centralized control over all quality gates. Every feature checks its section before activating:

```json
{
  "pre_flight":              { "enabled": true, "session_recovery": true, "working_tree_check": true, "branch_check": true, "git_context": true },
  "knowledge_base":          { "enabled": true, "query_during_planning": true, "deposit_on_approve": true },
  "adversarial_review":      { "enabled": true, "skip_for_trivial": true, "trivial_threshold_files": 2 },
  "work_unit_decomposition": { "enabled": true, "trigger_threshold_files": 3, "trigger_threshold_layers": 2 },
  "design_review":           { "enabled": false, "trigger": "complexity:complex", "max_revision_cycles": 2 },
  "github_issues":           { "enabled": false, "repo": "owner/name" },
  "pr_shepherd":             { "enabled": true },
  "metaswarm":               { "enabled": false, "features": { "brainstorm": true, "design_review": true, "prime": true, "pr_shepherd": true, "self_reflect": true } }
}
```

If the file doesn't exist, all features use built-in defaults. See `process/quality-configuration.md` for the full schema reference.

---

## Directory Structure

After installation, your project will have:

```
your-project/
├── .claude/
│   └── commands/           # Slash commands (Claude Code looks here)
│       ├── ap_brainstorm.md
│       ├── ap_requirements.md
│       ├── ap_exec.md
│       ├── ap_project.md
│       ├── ap_release.md
│       ├── ap_iteration_results.md
│       └── ap_changelog_init.md
│
├── quality-config.json     # Feature control for all quality gates
│
└── .agent_process/
    ├── orchestration/      # Planning and review prompts
    │   ├── plan-scope.md                  # Planning prompt (entry point)
    │   ├── review-iteration.md            # Review prompt (entry point)
    │   ├── scope-sizing-rules.md          # Configurable scope thresholds
    │   ├── context/
    │   │   └── base-context.md            # Orchestrator onboarding
    │   ├── coordinators/                  # Decomposed prompt entry points
    │   │   ├── plan-scope.md
    │   │   ├── execute-preflight.md
    │   │   ├── execute-main.md
    │   │   ├── review-iteration.md
    │   │   ├── release.md
    │   │   └── brainstorm.md
    │   └── steps/                         # Modular step files (43 total)
    │       ├── planning/                  # 12 focused planning steps
    │       ├── execution/                 # 7 focused execution steps
    │       ├── review/                    # 9 focused review steps
    │       ├── release/                   # 9 focused release steps
    │       └── brainstorm/                # 6 focused brainstorm steps
    │
    ├── knowledge/          # Accumulated project wisdom (JSONL)
    │   ├── patterns.jsonl
    │   ├── gotchas.jsonl
    │   ├── decisions.jsonl
    │   └── anti-patterns.jsonl
    │
    ├── process/            # Process documentation
    │   ├── validation-playbook.md
    │   ├── naming_conventions.md
    │   ├── knowledge-base.md
    │   ├── work-unit-execution.md
    │   ├── pr-shepherd.md
    │   ├── design-review-gate.md
    │   ├── quality-configuration.md
    │   ├── github-issues-integration.md
    │   ├── github-issues-handling.md
    │   ├── metaswarm-integration.md
    │   ├── local_environment_instructions.md
    │   └── ...
    │
    ├── requirements_docs/  # Project requirements
    │   └── _TEMPLATE_requirements.md
    │
    ├── roadmap/            # Project tracking (after /ap_project init)
    │   ├── master_roadmap.md
    │   ├── backlog.md
    │   └── .roadmap_config.json
    │
    ├── scripts/
    │   ├── after_edit/     # Scoped validation scripts (auto-generated)
    │   ├── github-issues-lifecycle.sh
    │   ├── lib/
    │   │   └── tracker-utils.sh
    │   ├── evaluate-scope.sh
    │   └── hook_after_edit.sh
    │
    ├── templates/          # Iteration templates
    │   ├── iteration-plan.md
    │   ├── iteration-feedback.md
    │   ├── results.md
    │   ├── adversarial-review-prompt.md
    │   ├── work-unit-decomposition.md
    │   └── design-review-prompt.md
    │
    └── work/               # Active iteration work
        └── <scope_name>/
            ├── iteration_plan.md
            └── iteration_01/
                ├── results.md
                └── test-output.txt
```

---

## Getting Started Guide

### 1. Install the Framework

```bash
# From within your project directory
/path/to/ai_agent_process/install.sh

# Or specify target directory
./install.sh /path/to/your/project
```

The installer copies slash commands to `.claude/commands/` and sets up the `.agent_process/` directory. It prompts about optional GitHub Issues integration.

### 2. Initialize Project Management

```bash
/ap_project init      # Create roadmap infrastructure
/ap_project discover  # Scan existing project (optional)
```

### 3. Define Your First Requirement

Choose your entry point based on what you have:

| Starting Point | Command | What Happens |
|----------------|---------|--------------|
| Vague idea | `/ap_brainstorm "improve login"` | Multi-agent ideation → formal requirement |
| Clear feature | `/ap_requirements add "user_auth"` | Direct requirement creation |
| Existing spec | `/ap_requirements import "spec.md"` | Import with AP frontmatter |
| GitHub Issue | `/ap_brainstorm #42` or `/ap_requirements add #42` | Seed from issue content |

All paths produce a formal requirement file in `.agent_process/requirements_docs/`.

### 4. Plan the First Iteration

**This is NOT a slash command.** Read the orchestration prompt with Claude:

```
Read: .agent_process/orchestration/plan-scope.md
```

Work with the orchestrator to:
1. **Size check** — Verify scope fits 1-2 weeks; break down if too large
2. **Query knowledge base** — Pull relevant patterns and gotchas
3. **Create iteration_plan.md** — With **LOCKED** acceptance criteria
4. **Set up scoped validation** — Script that runs automatically via hook

**Output:** `.agent_process/work/{scope}/iteration_plan.md`

The orchestrator spawns sub-agents for each step. You approve the final plan.

### 5. Execute the Work

```bash
/ap_exec user_auth iteration_01
```

This slash command:
1. Runs pre-flight checks (branch, working tree, session recovery)
2. Loads the frozen criteria from iteration_plan.md
3. Decomposes into work units if multi-domain (3+ files, 2+ layers)
4. Implements changes within scope
5. Runs validation (hook fires automatically)
6. Spawns adversarial reviewer (fresh agent, zero implementation context)
7. Creates `results.md` and `test-output.txt`

### 6. Review and Decide

**This is NOT a slash command.** Read the review prompt with Claude:

```
Read: .agent_process/orchestration/review-iteration.md
```

The orchestrator:
1. Loads results, test output, and adversarial review verdict
2. Evaluates against **frozen criteria** (not claims in results.md — actual code)
3. Verifies documentation and integration
4. **Chooses exactly one decision:**

| Decision | Meaning | What Happens Next |
|----------|---------|-------------------|
| **APPROVE** | All criteria met | Proceed to release |
| **ITERATE** | Minor fixes needed (same criteria) | Create sub-iteration (_a, _b, _c) |
| **PIVOT** | Wrong approach (need revised criteria) | New major iteration (02, 03) — requires human approval |
| **BLOCK** | External blocker | Escalate to human immediately |

### 7. Ship It

```bash
/ap_release pr              # Creates PR with changelog updates
/ap_release pr --shepherd   # Creates PR + monitors CI and reviews
```

The PR shepherd (optional) monitors CI status, responds to review comments, and reports merge-readiness. It never merges — the human always clicks merge.

---

## Success Metrics

### Healthy Process

| Metric | Target | Why |
|--------|--------|-----|
| Major iterations per scope | 1-3 | PIVOTs indicate learning, not failure |
| Sub-iterations per major | 0-2 | More suggests criteria problems |
| Scope completion rate | >80% | Achievable scopes properly sized |
| Time to completion | 1-2 weeks | Reasonable cadence |

### Warning Signs

| Sign | Problem | Solution |
|------|---------|----------|
| >3 sub-iterations on same criteria | Criteria too vague or ambitious | PIVOT or BLOCK |
| PIVOTs without clear criteria changes | Misusing the mechanism | Review planning process |
| <20% scope completion rate | Scopes too large | Split into smaller scopes |
| Indefinite completion time | Scope creep or blockers | Enforce frozen criteria |

---

## Customization

### Local Environment Instructions

For projects with unique requirements, customize workflows in:

**File:** `.agent_process/process/local_environment_instructions.md`

Every coordinator reads this file before starting its workflow. Instructions are **additive** — they augment default steps, never skip them.

**Keep it short.** Agents read this on every workflow run. Only include what's different about your project.

| Section | What goes here | Example |
|---------|---------------|---------|
| **Pre-Execution Setup** | Commands to run before implementation | `source .env && verify-auth` |
| **Multi-Repository Configuration** | Polyrepo branch checking, repo mapping | Branch verification across sub-repos |
| **Release Modifications** | Custom args, multi-project ordering | Topological sort, dependency-ordered releases |
| **Validation Extensions** | Extra validation beyond scoped hooks | Cross-repo integration tests |
| **Notes** | Other project-specific context | Architecture notes affecting agent work |

**Installation behavior:** Template installed on first setup, **preserved on re-installation** (never overwritten).

### Central Sync (Multi-Project)

For teams using this framework across multiple projects, you can configure central sync to keep all projects updated from a single source. See `install.sh` for configuration options.

---

## Documentation Reference

### Core Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Base Context | `orchestration/context/base-context.md` | Quick onboarding for orchestration |
| Plan Scope | `orchestration/coordinators/plan-scope.md` + `steps/planning/` | How to plan new scopes |
| Execute Iteration | `orchestration/coordinators/execute-*.md` + `steps/execution/` | How to execute iterations |
| Review Iteration | `orchestration/coordinators/review-iteration.md` + `steps/review/` | How to review and decide |
| Validation Playbook | `process/validation-playbook.md` | Testing patterns |
| Naming Conventions | `process/naming_conventions.md` | IDs, files, categories |

### Process Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Knowledge Base | `process/knowledge-base.md` | Query, deposit, curate project knowledge |
| Work Unit Execution | `process/work-unit-execution.md` | Multi-domain scope decomposition and DAG execution |
| PR Shepherd | `process/pr-shepherd.md` | Post-PR CI monitoring and review response |
| Design Review Gate | `process/design-review-gate.md` | Multi-reviewer plan assessment for complex scopes |
| Quality Configuration | `process/quality-configuration.md` | `quality-config.json` schema reference |
| GitHub Issues Integration | `process/github-issues-integration.md` | Optional issue tracking setup and usage |
| GitHub Issues Handling | `process/github-issues-handling.md` | Sub-agent delegation pattern for GH operations |
| Metaswarm Integration | `process/metaswarm-integration.md` | Multi-agent brainstorming and review gates |
| Local Environment | `process/local_environment_instructions.md` | Project-specific customization |
| Roadmap Schema | `process/roadmap_schema.md` | Roadmap file format |

### Templates

| Template | Location | Purpose |
|----------|----------|---------|
| Requirements | `requirements_docs/_TEMPLATE_requirements.md` | New requirements |
| Iteration Plan | `templates/iteration-plan.md` | Planning iterations |
| Results | `templates/results.md` | Documenting outcomes |
| Feedback | `templates/iteration-feedback.md` | Review feedback |
| Adversarial Review | `templates/adversarial-review-prompt.md` | Fresh reviewer prompt |
| Work Unit Decomposition | `templates/work-unit-decomposition.md` | Architect Agent decomposition prompt |
| Design Review | `templates/design-review-prompt.md` | Specialist reviewer prompt |

---

## Installation

```bash
# From within your project directory
/path/to/ai_agent_process/install.sh

# Or specify target directory
/path/to/ai_agent_process/install.sh /path/to/your/project
```

**Re-running install.sh preserves:**
- Your work in `.agent_process/work/`
- Your knowledge base in `.agent_process/knowledge/`
- Your local environment instructions
- Your central sync configuration
- Your existing requirements documents

---

## Testing

The framework includes its own test suite:

```bash
bash test/run-tests.sh
```

This runs contract tests and unit tests validating AP's own artifacts and scripts — it's not your project's test suite.

---

## Contributing

This is a personal workflow template. Fork and customize for your needs.

---

**Philosophy:** Ship pragmatically, iterate deliberately, pivot when you learn.
