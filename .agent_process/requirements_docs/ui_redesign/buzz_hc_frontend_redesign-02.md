---
id: buzz_hc_frontend_redesign-02
type: requirement
category: ui_redesign
status: approved
priority: HIGH
complexity: complex
split_from: buzz_hc_frontend_redesign
depends_on: [buzz_hc_frontend_redesign-01]
source: ap-brainstorm
---

# Requirements: Bloomberg-Terminal UI Redesign — Part 2: Run Screen + Persistence

**Split from:** `buzz_hc_frontend_redesign` (see `buzz_hc_frontend_redesign-breakdown.md` for full context)

**Prerequisites:** `buzz_hc_frontend_redesign-01` must be complete (design tokens, shared atoms, and `components/buzz/` must exist).

---

## Objective

Implement the live run observation screen at `/run/[id]` using `useLiveSession` so streaming output persists on page refresh, and refactor `useRunSession` to a start-only hook that hands off to `useLiveSession`.

## Background

The current `/run` page is stateless — it has no URL-based session ID, so refreshing the browser destroys all streaming context. The `useLiveSession` hook already handles refresh-safe reconnection (fetches historical events from DB on mount, then reconnects to live SSE if still running). The fix is to create a proper `/run/[id]` dynamic route and wire it to `useLiveSession`.

The Run screen is the most complex: three-column layout (agent cards left, swarm topology + emerging draft center, event stream + sources right), plus a session header bar, pipeline progress strip, and optional state banners (paused/error).

The animated SwarmTopology component built here reuses the SwarmGraph SVG approach from Part 1 but adds run-state-aware behavior (error pulse, pause freeze, node sizing).

---

## Technical Requirements

1. **`/run/[id]` dynamic route** (`web/app/run/[id]/page.tsx`) — New page wrapping `useLiveSession(id)`. Receives session ID from URL. Shows the full 3-column Bloomberg run layout. On mount: fetches session from DB + reconnects to live SSE if running. On complete: shows "↗ Open report" button linking to `/report/[id]`.

2. **`/run` page refactor** — Convert existing `web/app/run/page.tsx` to a redirect page: if navigated directly, redirect to `/query`. This ensures the old stateless entry point is gone.

3. **`/sessions/[id]` status-aware redirect** — Convert `web/app/sessions/[id]/page.tsx` to a thin redirect: fetch session status, then `router.replace('/run/' + id)` (if running/queued/paused/error) or `router.replace('/report/' + id)` (if complete). Use `router.replace` (not `push`) to avoid back-button trap.

4. **`useRunSession` refactor** — Split the hook into start-only responsibility. Current hook mixes "start a run" and "watch a run" (SSE bookkeeping). After refactor: calling `run(brief)` should call `startRun()`, get the session ID, then `router.push('/run/' + sessionId)`. All SSE bookkeeping inside the hook is removed (dead code). The new `/run/[id]` page uses `useLiveSession` directly for watching. Add a Jest test asserting no `EventSource` is constructed by `useRunSession` after the refactor.

5. **Session header bar** — 12×16 padding, surface bg, border-bottom, grid layout: session ID + query text (left), 4 KV metrics (Started/Elapsed/ETA/Tokens), StatusChip, action button (Pause when running → resume; "↗ Open report" when complete; "↻ Retry" when error via `retrySession(id)`).

6. **Pipeline progress strip** — 7-stage strip reading from `session.progress.stage`. Each stage cell has a 2px top border (color by state: green=complete, cyan=running, amber=paused, red=error, border=queued), stage label, and state glyph (✓/↻/✕/⏸/·).

7. **State banners** — Error banner (red, pulsing dot, error message, "↻ Retry stage" CTA) and Paused banner (amber, "▸ Resume" CTA). Only shown for error/paused states.

8. **Left column: Agent cards** — 4 cards stacked (Lead/Market/Analyst/Reporter). Each: StatusDot + agent name in agent color + token count + role + current task (↳ prefix) + 16-segment progress bar when running. Error card: red-tinted bg overlay. Below agent cards: Brief panel showing original query with Edit/Cancel buttons.

9. **Center column: SwarmTopology + Emerging Draft placeholder** — Top: SwarmTopology SVG (540×400) with 3 concentric reference rings, compass labels, 32px-radius nodes with run-state-aware animation (node ping, error pulse, hub label changes). Bottom: "Emerging draft" panel showing "← Reporter streaming added in Part 4" placeholder text for now. When Part 4 is complete, this will render the streaming draft text.

10. **Right column: Event stream + Sources** — 10-row event list (timestamp + agent name in agent color + message, opacity stair-step). Sources panel: domain list with counts, errored source shown with red StatusDot + "TIMEOUT".

11. **SwarmTopology component** (`web/components/buzz/SwarmTopology.tsx`) — Extends SwarmGraph from Part 1. Adds: concentric rings, compass labels, run-state-aware node animation via `requestAnimationFrame` + `SVG <animate>`. On error: edges dim red at 0.25 opacity, error node pulses, hub label = "ERR". On pause: packets freeze, hub label = "PSE". On complete: all nodes green, packets stop.

12. **AgentCard, EventLog, PipelineStrip components** (`web/components/buzz/`) — per design spec.

---

## Success Criteria

- [ ] Navigating to `/run/<id>` with a completed session shows the full session without triggering a new run
- [ ] Navigating to `/run/<id>` for a running session reconnects to live SSE and appends new events without losing historical events on page refresh
- [ ] `/sessions/<id>` redirects to `/run/<id>` (active) or `/report/<id>` (complete) with `router.replace`
- [ ] Old `/run` page redirects to `/query` when navigated directly
- [ ] `useRunSession` no longer constructs an `EventSource`; verified by Jest test
- [ ] Pipeline progress strip shows correct stage and state glyphs for a real completed session
- [ ] Error banner + Retry CTA visible for `status=error` sessions; calls `retrySession(id)` on click
- [ ] SwarmTopology RAF animation runs at 60fps without causing React re-renders per frame
- [ ] "Emerging draft" placeholder is visible in center column (will be replaced in Part 4)
- [ ] `nextjs-build` CI passes; all Python tests green

---

## Files Expected to Change

**New:**
- `web/app/run/[id]/page.tsx`
- `web/components/buzz/SwarmTopology.tsx`
- `web/components/buzz/AgentCard.tsx`
- `web/components/buzz/EventLog.tsx`
- `web/components/buzz/PipelineStrip.tsx`

**Modified:**
- `web/app/run/page.tsx` — refactor to redirect
- `web/app/sessions/[id]/page.tsx` — status-aware redirect
- `web/hooks/useRunSession.ts` — start-only refactor

**Test:**
- `web/__tests__/useRunSession.test.ts` — assert no EventSource constructed

**Estimated:** 9 files

---

## Out of Scope

- Streaming draft text in the center column (→ Part 4)
- Pause/resume backend endpoint (if not already implemented — wire UI to endpoint only if it exists; show disabled button if not)
- `/report/[id]` route (→ Part 3)
- Reporter schema changes (→ Part 4)
- Mobile optimization

---

## Known Risks

- **`useRunSession` refactor size** — Synthesis underestimated this. The hook currently owns SSE bookkeeping; removing it without breaking the existing query form flow requires care. The Jest test is the safety net.
- **Double EventSource** — If `useRunSession` SSE code is not fully removed and `/run/[id]` also opens `useLiveSession`, two EventSources will be opened for the same session. Must verify with browser devtools during testing.
- **SwarmTopology RAF isolation** — Same risk as SwarmGraph in Part 1. Use mutable refs; never call setState from RAF.
- **Back-button trap on redirect** — Using `router.replace` in `/sessions/[id]` is critical. If `router.push` is used, the user will be stuck in a redirect loop when hitting back.
- **`_active_streams` in-memory** — Server restart while a run is active will leave the session stuck as `running` in the DB with no live SSE stream. The "Retry" affordance mitigates this. Not fixable in this scope.

---

## Notes

### Brainstorm Source
- **Brainstorm doc:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
- **Date:** 2026-05-24
- **Design handoff:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/run.jsx`

### Feasibility Review Key Findings
- `useLiveSession` refresh-safety VERIFIED: fetches DB events on mount, reconnects SSE if running
- `useRunSession` refactor is larger than synthesis implied — SSE bookkeeping must be removed, not just `router.push` added
- `router.replace` vs `router.push` — critical distinction for `/sessions/[id]` redirect

---
*Part 2 of 4 from `buzz_hc_frontend_redesign`. See breakdown file for complete context.*
