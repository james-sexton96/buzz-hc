# Iteration Plan – buzz_hc_frontend_redesign-02

## Scope Overview
- **Scope Name:** buzz_hc_frontend_redesign-02
- **Date:** 2026-05-24
- **Summary:** Implement the live run observation screen at `/run/[id]` using `useLiveSession` (refresh-safe), refactor `useRunSession` to a start-only hook, and convert `/sessions/[id]` + bare `/run` into status-aware redirects.

## Requirements Source
- **Path:** `.agent_process/requirements_docs/ui_redesign/buzz_hc_frontend_redesign-02.md`
- **Document:** `buzz_hc_frontend_redesign-02.md`

*Part 2 of 4 split from `buzz_hc_frontend_redesign`. Depends on Part 1 (design tokens, atoms, `components/buzz/` directory).*

## Current Status
- Latest iteration: **iteration_01 (not started)**
- Decision: N/A
- Next: Run `/ap_exec buzz_hc_frontend_redesign-02 iteration_01`

## Acceptance Criteria (LOCKED - DO NOT MODIFY)

Copied verbatim from `.run/planning/03-define.md`. **FROZEN — 10 criteria.**

- [ ] Navigating to `/run/<id>` for a session with `status=complete` renders the full historical session (header bar, pipeline strip showing all stages complete, agent cards, event log) without `EventSource` being opened — verified via DOM snapshot + EventSource spy in component test or manual devtools check.
- [ ] Navigating to `/run/<id>` for a session with `status=running`, then refreshing the page, results in (a) historical events from DB rendered immediately, (b) a single `EventSource` connection to `/run/<id>/stream`, and (c) new events appended to the existing list — no duplicate connections, no lost historical events.
- [ ] `/sessions/<id>` calls `router.replace('/run/<id>')` when fetched status ∈ {running, queued, paused, error} and `router.replace('/report/<id>')` when status = complete. Browser back button after redirect returns to the prior page (not the `/sessions/<id>` URL).
- [ ] `/run` (no id) calls `router.replace('/query')` on mount; no query form rendered on `/run`.
- [ ] Jest test `web/__tests__/useRunSession.test.ts` passes and asserts `global.EventSource` constructor is never invoked across a full `run()` call; also asserts `router.push` is called exactly once with `/run/<returned_session_id>`.
- [ ] `PipelineStrip` rendered against a real completed session's `events` array shows all 5 stages with `state=complete` (green border + ✓ glyph). Against a running session with `agent_start` for Researcher but no `agent_end`, the Researcher stage shows `state=running` (cyan + ↻); later stages show `state=queued` (border + ·).
- [ ] Error banner is rendered when `session.status === "error"` containing `session.error_msg`, derived failed-agent label (from last `agent_start` without matching `agent_end`), and a "↻ Retry stage" button. Clicking the button invokes `retrySession(id)` and navigates to `/run/<new_session_id>`.
- [ ] `SwarmTopology` runs RAF animation without triggering React re-renders per frame — verified by a render-count assertion or by code review confirming no `setState` is called inside the RAF callback (only `ref.current.setAttribute(...)`).
- [ ] Center-column "Emerging draft" placeholder is rendered with the text "← Reporter streaming added in Part 4" (placeholder copy approved for Part 4 hand-off).
- [ ] `pnpm --filter web build` (nextjs-build CI step) succeeds with zero TypeScript errors and zero new `any` types in the new/modified files. `uv run pytest tests/ -v` remains green (no backend changes expected).

**Count:** 10 criteria. **WARN** — above the 3–7 target. Justification: this scope was already split out of `buzz_hc_frontend_redesign` and represents a single user-visible flow (live run screen + persistence). The 10 criteria each map 1:1 to either a route, a component, a hook contract, or a documented risk. Splitting further would lose the round-trip refresh-safety assertion that is the central requirement.

**CRITICAL:** These criteria are FROZEN at iteration start. New issues discovered during iteration → backlog for future scopes.

**Scope boundaries are guidance, not walls.** If meeting the acceptance criteria correctly requires touching files outside the list, the executor may do so with: documentation of what was added and why, validation script update if new files need scoped checks, and justification in `results.md`.

## Known Patterns & Constraints

**From knowledge base** (`.agent_process/knowledge/` — see `02-assess.md` for the full query):
- **pydantic_ai_testmodel_isolation_pattern** — Use `agent.override(model=TestModel(...))` for offline agent unit tests. *Not directly applicable to this frontend scope*, but confirms test-isolation discipline expected in the project.

**No matches found for:** SSE hooks, Next.js App Router dynamic routes, React `requestAnimationFrame` patterns, SVG packet animation. Assessment is primary research; patterns below are derived from Part 1 (`SwarmGraph.tsx`) and existing codebase (`useLiveSession.ts`, `PipelineProgress.tsx`).

**Project constraints carried into this scope (from `MEMORY.md` + Part 1):**
- `lead_agent` and other backend agents are imported **inside route handlers** — no changes here (this scope is frontend-only).
- `aiosqlite` connections open/close per-operation — no concurrency issues to consider on the FE.
- `pnpm` v10+ frozen-lockfile in CI; do not commit changes to `pnpm-lock.yaml` without justification.

**Critical implementation notes** (must be honored by the executor):

1. **SwarmTopology animation isolation** — Use imperative `setAttribute` via refs inside the RAF callback. **NEVER call `setState` inside RAF.** Same constraint as Part 1 `SwarmGraph.tsx`. Violating this triggers 60 React re-renders per second.
2. **`useLiveSession` is already refresh-safe** — Do not modify. On mount it calls `getSession(id)` (loads historical events from DB), then conditionally opens `EventSource` only when `status === "running"`. The consumer merges `session.events` (historical) with `liveEvents` (live) — same pattern already used in the current `/sessions/[id]/page.tsx` (lines 86–89).
3. **`/sessions/[id]` redirect must use `router.replace`, NOT `router.push`** — Using `push` creates a back-button trap (user presses back, returns to `/sessions/[id]`, gets re-redirected, repeat). The existing `/sessions/[id]/page.tsx` retry path uses `router.push('/sessions/' + new_id)` — that pattern must change in the new `/run/[id]` page to `router.push('/run/' + new_id)`.
4. **Stage inference** — Derive pipeline stage from `WorkflowEvent` `agent_start` / `agent_end` records keyed by `source` (`"Lead"` / `"Researcher"` / `"Analyst"` / `"Reporter"`). **There is no `progress` field on the API.** Existing `web/components/run/PipelineProgress.tsx` proves the pattern. Use the 5-stage constant from `web/app/query/page.tsx` (`PIPELINE_STAGES`) — do not invent a new 7-stage taxonomy; the API does not emit enough granularity to populate it.
5. **Per-agent token counts** — Not available from the API. Each `AgentCard` shows `"—"` for tokens. Do NOT parse `WorkflowEvent.details` for tokens unless the schema is verified first (out of scope).
6. **ETA display** — Show `"—"` unconditionally in the header bar. No estimation logic.
7. **Error banner failed-agent label** — Derive from `session.events`: the last `agent_start` whose `source` has no matching subsequent `agent_end` is the failed agent. `session.error_msg` provides the message text. `failed_stage` is NOT exposed in the current `/sessions/{id}` API response — do not add it to the API.
8. **Pause / Resume buttons** — No backend endpoint exists. Render the Pause button **disabled** when status is `running` (honest UI). Same for Resume on `paused`. Do not mock a fake pause.
9. **Design reference** — `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/run.jsx`. Layout / spacing / colors come from the prototype; the prototype's `useState(tick)` RAF pattern is intentionally **NOT** adopted (see constraint #1).

## Design Review

N/A — design review gate not triggered for this scope. Rationale: even though the requirement is marked `complexity: complex`, the design choices are constrained by Part 1 (tokens + atoms) and by the existing hook contracts (`useLiveSession`, `retrySession`). The 8 design decisions in the Design Decisions table were resolved during planning without unresolved architectural questions. No specialist domains (security, data, infra) have novel surface area in this scope.

## Technical Assessment (by Orchestrator)

**Code Review Findings** (full detail in `.run/planning/02-assess.md`):

- `web/hooks/useRunSession.ts` currently mixes start + watch responsibilities. SSE bookkeeping spans line 17 (`esRef`) plus lines 44–103 (the `EventSource` block + `onerror` handler) plus two cleanup statements in `reset()`. These must be removed in full. After refactor, `run()` calls `startRun()` then `router.push('/run/' + sessionId)`.
- `web/hooks/useLiveSession.ts` is refresh-safe. **Do not modify.** Flow: mount → `getSession(id)` → set state from DB → open `EventSource` only if `status === "running"` → on `done` re-fetch + merge → cleanup closes `EventSource`. The new `/run/[id]/page.tsx` consumes this hook directly.
- `web/app/sessions/[id]/page.tsx` is a 182-line full detail view today. It must shrink to a thin status-aware redirect (`router.replace('/run/<id>')` or `/report/<id>`).
- `web/lib/types.ts` `SessionDetail` has NO `progress` field. The prototype's `session.progress.stage` is fictional. Stage derivation must come from `session.events`.
- `retrySession()` exists in `web/lib/api.ts` (line 69) — wire the Retry button to it.

**Implementation Approach — Work Unit Decomposition:**

The 9 files split into 3 dependent work units. Executor should land them in order; A unblocks B, A+B unblock C.

### Unit A — Hook refactor (must go first; establishes clean start-only contract)
Files:
- `web/hooks/useRunSession.ts` — strip SSE; keep `RunState` type; add `useRouter` + `router.push('/run/' + sessionId)` inside the success branch of `run()`.
- `web/__tests__/useRunSession.test.ts` — **new test**. Stub global `EventSource` constructor with a Jest spy; mock `fetch` to return a fake `session_id`; mock `next/navigation`'s `useRouter`. Assert: (a) `EventSource` spy is never called across the `run()` cycle, (b) `router.push` is called exactly once with `/run/<returned_session_id>`.

**Rationale:** Doing this first means subsequent units cannot accidentally retain dual-EventSource behavior. The test is the safety net for criterion 5.

### Unit B — New `buzz/` components (depend on Part 1 tokens + atoms)
Files (order suggested; not strictly dependent on each other but listed top-down by visual region):
- `web/components/buzz/SwarmTopology.tsx` — extends Part 1 `SwarmGraph` patterns. SVG 540×400 with 3 dashed concentric rings (r=80/130/180), N/E/S/W compass labels, 4 agent nodes at r=130 (32px radius), hub center (20px). 5 edges (lead↔market, lead↔analyst, lead↔reporter, market↔analyst, analyst↔reporter). RAF tick stored in `useRef`, packet `cx`/`cy` written via `ref.current.setAttribute(...)`. Run-state-aware: error pulse via SVG `<animate>` on the errored node; pause freeze (cancel RAF); hub label switches HUB/ERR/PSE.
- `web/components/buzz/AgentCard.tsx` — single card. StatusDot + name in agent color + token count (`"—"`) + role + current task (↳ prefix) + 16-segment progress bar when running. Error: red-tinted bg overlay. Derives state by walking `session.events` for the most recent `agent_start`/`agent_end` matching this agent.
- `web/components/buzz/EventLog.tsx` — right-column event stream: last ~10 events as timestamp + agent (agent color) + message with opacity stair-step. Sources subpanel: domain list with counts; errored sources get red StatusDot + `"TIMEOUT"` label.
- `web/components/buzz/PipelineStrip.tsx` — 5-stage strip derived from `session.events`. Each cell: 2px top border (green/cyan/amber/red/border-color), label, glyph (✓/↻/✕/⏸/·). Stage labels exported as a shared constant; reuse `PIPELINE_STAGES` from `web/app/query/page.tsx` (or re-export from this file if the query page is the canonical home).

**Rationale:** These four components are pure presentational consumers of `SessionDetail`. They can be implemented and visually inspected in isolation before the page wires them together.

### Unit C — Pages (depend on A + B)
Files:
- `web/app/run/[id]/page.tsx` — **new**. Wraps `useLiveSession(id)`. Renders: session header bar (12×16 padding, surface bg, border-bottom, grid with session ID + query text + 4 KV metrics + StatusChip + action button), optional Error / Paused banner, `PipelineStrip`, 3-column body grid (300px / 1fr / 360px) = `[AgentCards stack + Brief panel]` / `[SwarmTopology + Emerging draft placeholder]` / `[EventLog + Sources]`. Loading + not-found states. On `status=complete`: surface "↗ Open report" button linking to `/report/[id]`. On `status=error`: error banner with `retrySession(id)` CTA + `router.push('/run/' + new_id)` after retry.
- `web/app/run/page.tsx` — modified. Replace contents with `useEffect` calling `router.replace('/query')` + minimal "Redirecting…" fallback.
- `web/app/sessions/[id]/page.tsx` — modified. Thin status-aware redirect: `getSession(id)` → branch on status → `router.replace('/run/<id>')` or `router.replace('/report/<id>')`. **Must use `replace`, not `push`** (back-button trap).

**Rationale:** Pages are the integration layer; they should be touched last so that any component-level surprises surface during isolated dev. The redirect pages are tiny but order-sensitive (the executor must remember the `replace` vs `push` distinction).

**Implementation Guidance:**
- Reuse `web/components/run/PipelineProgress.tsx`'s stage-derivation logic as the reference implementation for `PipelineStrip` (do not re-derive from scratch).
- Reuse `SwarmGraph.tsx`'s RAF + ref pattern verbatim; only add the run-state-aware branches (error pulse, pause freeze).
- For agent color tokens, use the names already defined in Part 1's `globals.css` (do not introduce new color names).
- The `lucide-react` library is **banned** in `web/components/buzz/` and the new `/run/[id]/page.tsx` — Bloomberg-terminal aesthetic uses unicode glyphs (✓/↻/✕/⏸/↳/↗/▸/·). Part 1 validator already enforces this; Part 2 validator extends the check to the new files.

**Design Decisions (made by orchestrator, not human prereqs):**

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Stage derivation source | Infer from `session.events` (`agent_start`/`agent_end`) | Add `progress` field to backend API | No backend change needed; existing `PipelineProgress.tsx` proves the pattern works; backend change is out of scope. |
| RAF animation isolation | Mutable SVG attribute refs + `setAttribute` (matches Part 1 `SwarmGraph.tsx`) | `useState(tick)` (as in prototype `RunSwarm`) | `useState` in RAF = 60 React re-renders/sec; explicitly violates acceptance criterion 8. |
| Stage count in `PipelineStrip` | 5 stages matching `PIPELINE_STAGES` from `web/app/query/page.tsx` | 7 stages as suggested by the prototype | API only emits events for 4 agents → ~5 logical stages; 7-stage model has no event source to infer from. |
| `/sessions/[id]` fate | Convert to thin `router.replace` redirect | Keep as full detail view | Requirement explicitly specifies; new `/run/[id]` is now the canonical detail surface for active/failed sessions. |
| `/run/page.tsx` fate | Redirect to `/query` | Keep query form inline at `/run` | `/query` exists (Part 1); separation of query input from live observation is the architectural intent. |
| Per-agent token display | `"—"` | Parse `WorkflowEvent.details` | No schema guarantee on `details` structure; safe default prevents runtime crash if events evolve. |
| ETA display | `"—"` unconditionally | Estimate from `timestamp` + heuristic | No ETA data from API; estimation would mislead the operator. |
| Pause/Resume buttons | Render disabled (no backend endpoint) | Omit entirely / wire to a mock endpoint | Requirement says "wire only if endpoint exists; show disabled if not"; honest UI state. |
| Retry post-navigation | `router.push('/run/<new_session_id>')` | Stay on the old `/sessions/<id>` (legacy behavior) | After retry, a new `session_id` is created; the new run screen is the correct destination. |

## Iteration Budget (ENFORCED)
- iteration_01: First attempt (Units A, B, C in that order)
- iteration_01_a: First revision (if needed — likely target: SwarmTopology RAF or hook test)
- iteration_01_b: Second revision (if needed)
- iteration_01_c: Final attempt (if needed)

After iteration_01_c → Escalate to human for decision (ship/pivot/abort).

## Files in Scope (Expected)

These are the files expected to change. The executor may touch additional files if necessary for correctness (e.g., shared `PIPELINE_STAGES` const) — see "Scope boundaries" note above.

**New (5 production + 1 test):**
- `web/app/run/[id]/page.tsx`
- `web/components/buzz/SwarmTopology.tsx`
- `web/components/buzz/AgentCard.tsx`
- `web/components/buzz/EventLog.tsx`
- `web/components/buzz/PipelineStrip.tsx`
- `web/__tests__/useRunSession.test.ts`

**Modified (3):**
- `web/app/run/page.tsx` — refactor to `router.replace('/query')` redirect
- `web/app/sessions/[id]/page.tsx` — refactor to status-aware `router.replace` redirect
- `web/hooks/useRunSession.ts` — strip SSE bookkeeping; add `router.push('/run/' + sessionId)`

**Total:** 9 files (within 4–10 target band).

## Documentation in Scope

**End User Documentation:**
- *None* — URL change (`/run` → `/run/[id]`) is internal; refresh-safe behavior is invisible to end users beyond "it works".

**Developer Documentation:**
- Updated: `/Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` — append a "Run screen architecture" subsection noting (a) `/run/[id]` is the live observation route, (b) `useRunSession` is start-only, (c) `useLiveSession` is the refresh-safe watch hook, (d) stages are derived from events (no `progress` field in API), (e) `SwarmTopology` uses mutable SVG refs in RAF (never `useState`).
- No README / CLAUDE.md updates required; project `.claude/CLAUDE.md` is personality-only.

**Documentation Requirements (from CLAUDE.md):**
- [ ] End user documentation updated — N/A (no user-facing behavior change beyond URL stability)
- [ ] Developer documentation updated — `MEMORY.md` Run screen subsection
- [ ] Documentation follows Diátaxis framework organization — N/A (no new doc files)
- [ ] Cross-references to changed code updated — `MEMORY.md` file table will reference the new files
- [ ] Migration guide created (if replacing systems) — N/A (no public surface removed; see "Removed Surfaces" below)

## Removed Surfaces

**N/A — no public surfaces removed or renamed.**

Justification: while `/sessions/[id]` and `/run` (bare) are repurposed as redirects, both URLs continue to respond and route the user to the correct destination. No HTTP route, MCP tool, CLI command, env var, config key, or exported function consumed by another repo is being removed. The `useRunSession` hook is being internally refactored, but its public signature (`{ run, reset, ... }`) is preserved for backward compatibility with the `/query` page that imports it. No grep-scrub block is required in the validator.

## Validation Requirements (SCOPED)

**Hook validation (after_edit):**
- Script: `.agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-02.sh`
- Checks (bash 3.2 compatible):
  1. `pnpm tsc` passes (TypeScript)
  2. `pnpm test` shows ≥4 Jest tests passing (3 existing + 1 new `useRunSession` test)
  3. `web/app/run/[id]/page.tsx` exists
  4. `web/components/buzz/SwarmTopology.tsx` exists
  5. `web/components/buzz/AgentCard.tsx` exists
  6. `web/hooks/useRunSession.ts` does NOT contain `new EventSource` (grep returns non-zero)
  7. `web/app/sessions/[id]/page.tsx` contains `router.replace` (redirect implemented)
  8. No `lucide-react` imports in any `web/components/buzz/` file or `web/app/run/[id]/page.tsx`

**RUN list (must pass for this scope):**
- `cd web && pnpm tsc` — TypeScript check
- `cd web && pnpm test` — Jest suite (≥4 passing)
- `cd web && pnpm build` — Next.js build (the CI `nextjs-build` step) — recommended sanity-check before review even though the validator script proxies via `pnpm tsc`
- `uv run pytest tests/ -v` — Python tests (no backend changes, but verify regression-free)

**SKIP list (pre-existing issues, NOT blocking this scope):**
- None identified at planning time. Baseline (confirmed via user-provided facts):
  - **53 Python tests passing** (pytest suite)
  - **3 Jest tests passing** (web suite — will become 4 after this scope)
  - **`pnpm build` succeeds** (Next.js production build is clean)
- If `pnpm lint` or `ruff check` surfaces unrelated debt during execution, document in `results.md` and add to SKIP — do not block this scope on out-of-file lint noise.

**Validation approach:**
- Scoped validation via hook for fast feedback during iteration.
- Document raw results in `iteration_01/test-output.txt`.
- Orchestrator review (Gate 4) confirms scoped pass + reads results.md.
- Note: CI's `nextjs-build` + `python-tests` jobs remain the canonical gate at PR time.

## Scope Changes

Track any files added to scope during iterations:
- **iteration_01:** Initial scope (see Files in Scope section above)

## Out of Scope

- Streaming draft text in the center column (placeholder only — moves to Part 4)
- Pause / Resume backend endpoint (no endpoint exists; UI shows disabled button)
- `/report/[id]` route implementation (Part 3)
- Reporter schema changes (Part 4)
- Mobile / responsive optimization
- Adding `progress` or `failed_stage` fields to the `/sessions/{id}` API response (events-derived in this scope)
- Backend changes of any kind (Python files / API / DB)
- Modifying `useLiveSession` (already refresh-safe)
- Re-styling Part 1 tokens / atoms

## Technical Notes

- Design reference: `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/run.jsx`
- RAF + ref pattern reference: existing `web/components/buzz/SwarmGraph.tsx` (Part 1)
- Stage derivation reference: existing `web/components/run/PipelineProgress.tsx`
- `useLiveSession` consumer reference (events merging): current `web/app/sessions/[id]/page.tsx` lines 86–89 (before this scope refactors that page)
- `WorkflowEvent.source` values consumed read-only: `"Lead"` / `"Researcher"` / `"Analyst"` / `"Reporter"` (case-sensitive). If a real session reveals different casing, normalize at the comparison boundary (do not edit backend).

## Time Budget

- Target: 2–4 hours implementation for iteration_01
- Maximum: 1–2 weeks across all revisions (3 iterations max)
- After time exceeded: Escalate to human for decision

## Success Metrics

- All 10 acceptance criteria checked
- Scoped validation script passes (`validate-buzz_hc_frontend_redesign-02.sh`)
- No regressions in Python suite (53 tests still green) or pre-existing Jest tests (3 still green)
- New `useRunSession.test.ts` passes (Jest total = 4)
- `pnpm build` succeeds (CI parity)
- Browser devtools confirm: navigate to `/run/<running-id>`, refresh → exactly ONE `EventSource` connection to `/run/<id>/stream`, historical events visible immediately
