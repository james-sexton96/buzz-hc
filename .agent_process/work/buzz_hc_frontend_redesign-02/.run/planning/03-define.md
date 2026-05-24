# Scope Definition

**Scope:** buzz_hc_frontend_redesign-02

## Files in Scope

| Path | Action | Purpose |
|------|--------|---------|
| `web/app/run/[id]/page.tsx` | New | Dynamic route — wraps `useLiveSession(id)`, renders 3-column Bloomberg run layout (header bar, optional banners, pipeline strip, agent cards / swarm + draft placeholder / event log + sources). Handles loading + not-found states; on `status=complete` exposes "↗ Open report" link to `/report/[id]`. |
| `web/components/buzz/SwarmTopology.tsx` | New | 540×400 SVG with 3 concentric rings (r=80/130/180 dashed), compass labels (N/E/S/W), 4 agent nodes at r=130 + hub center. RAF-driven packet animation along 5 edges using mutable SVG refs + `setAttribute` (no `useState` in RAF). Run-state-aware: error pulse, pause freeze, hub label switches HUB/ERR/PSE, completed nodes green. |
| `web/components/buzz/AgentCard.tsx` | New | Single agent card: StatusDot + agent name in agent color + token count (total or "—") + role + current task (↳ prefix) + 16-segment progress bar when running. Error state: red-tinted bg overlay. Derives state from latest `agent_start`/`agent_end` for the agent in `session.events`. |
| `web/components/buzz/EventLog.tsx` | New | Right-column event stream: last ~10 events rendered as timestamp + agent name (agent color) + message with opacity stair-step. Includes Sources subpanel: domain list with counts, errored sources shown with red StatusDot + "TIMEOUT". |
| `web/components/buzz/PipelineStrip.tsx` | New | 5-stage strip (matches `web/app/query/page.tsx` `PIPELINE_STAGES`) derived from `session.events` (`agent_start`/`agent_end` by `source`). Each cell: 2px top border colored by state (green=complete / cyan=running / amber=paused / red=error / border=queued), label, state glyph (✓/↻/✕/⏸/·). Stage labels exported as shared const. |
| `web/app/run/page.tsx` | Modified | Replace existing query-form contents with a `useEffect` `router.replace('/query')` redirect (plus minimal "Redirecting…" fallback). Removes the stateless entry point. |
| `web/app/sessions/[id]/page.tsx` | Modified | Replace 182-line detail view with thin status-aware redirect: fetch session via `getSession(id)`, then `router.replace('/run/' + id)` for running/queued/paused/error or `router.replace('/report/' + id)` for complete. Must use `replace` (not `push`) to avoid back-button trap. |
| `web/hooks/useRunSession.ts` | Modified | Strip SSE bookkeeping (line 17 `esRef` + lines 44–103 EventSource block + `esRef` cleanup in `reset`). After refactor: `run(query, tavilyApiKey)` calls `startRun()`, then `router.push('/run/' + sessionId)`. Add `useRouter` import from `next/navigation`. Keep `RunState` shape for backward-compat consumers if any remain after page refactors. |
| `web/__tests__/useRunSession.test.ts` | New (Test) | Jest test asserting no `EventSource` is constructed during `run()` — spies on global `EventSource`/mocks `fetch`, verifies the constructor is never called and `router.push('/run/<id>')` fires once with the returned session_id. |

**Total:** 9 files (5 new components + 1 new page + 3 modified + 1 new test = within 4–10 target band)

**Contract consumers:** N/A — no API/payload contract changes. All data sourced from existing `getSession`/`useLiveSession`/`startRun`/`retrySession` surfaces. `WorkflowEvent.source` values ("Lead"/"Researcher"/"Analyst"/"Reporter") are consumed read-only.

## Acceptance Criteria (LOCKED)

**DO NOT MODIFY during iteration. New issues → backlog.**

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

**Count:** 10 criteria (at upper bound of 3–7 target; one criterion above target is justified by 9-file scope spanning route refactor + 5 components + animation + hook refactor + test — splitting further would lose the round-trip refresh-safety assertion that is the central requirement).

## Documentation

- End user docs: N/A — no user-facing documentation exists for `/run` route behavior; UI is self-evident. URL change (`/run` → `/run/[id]`) is internal and refresh-safe by design.
- Developer docs: Updated: `/Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` — append a "Run screen architecture" subsection noting (a) `/run/[id]` is the live observation route, (b) `useRunSession` is start-only, (c) `useLiveSession` is the refresh-safe watch hook, (d) stages are derived from events (no `progress` field in API), (e) SwarmTopology uses mutable SVG refs in RAF (never `useState`). No README/CLAUDE.md updates required; project instructions in `.claude/CLAUDE.md` are personality-only.
