# Step 03: Multi-Agent Brainstorm (3 agents in parallel)

**Model tier:** capable (x3 parallel agents)
**Tools needed:** Agent/Task
**Input:** idea, context output (`<project_root>/.agent_process/brainstorms/{chosen_name}/.run/02-context.md`)
**Output:** `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-product.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-architect.md`, `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/03-critical.md`

---

## Your Task

Spawn 3 brainstorm agents **in parallel** (single message, 3 Agent calls). Each gets the same idea and context but a different perspective.

## Agent 1: Product Strategist

Explore from product perspective:
1. **Problem Statement** — Who is affected, how?
2. **Proposed Approach** — 2-3 solutions, simplest to most ambitious, with trade-offs
3. **Success Criteria** — 3-5 measurable outcomes (not implementation tasks)
4. **Risks & Open Questions** — What could go wrong? What don't we know?
5. **Scope Boundaries** — What is explicitly NOT part of this?

## Agent 2: Software Architect

Explore from technical perspective:
1. **Technical Feasibility** — Can this be done with the current stack?
2. **Implementation Approach** — High-level design, systems involved, data flow
3. **Files & Components Likely Affected** — Based on project structure
4. **Integration Points** — Where does this connect to existing systems?
5. **Technical Risks** — Performance, scalability, migration, compatibility
6. **Complexity Assessment** — Simple / Moderate / Complex

## Agent 3: Devil's Advocate

Stress-test the idea:
1. **Assumption Check** — What assumptions might be wrong?
2. **Alternative Approaches** — Simpler ways to achieve the same outcome?
3. **Failure Modes** — What are the worst-case scenarios?
4. **Dependencies & Blockers** — External factors that could block this?
5. **Honest Assessment** — Should we do this at all? What's the opportunity cost?

## Rules

- All 3 agents must be concrete and specific to this project
- Launch all 3 in a single response (parallel)
- Each writes its output to its own `<project_root>/.agent_process/brainstorms/{chosen_name}/.run/` file
