# Technical Assessment

**Scope:** buzz_hc_frontend_redesign-02

---

## Knowledge Base

1 relevant entry:
- **pydantic_ai_testmodel_isolation_pattern**: Use `agent.override(model=TestModel(...))` for offline agent unit tests — not directly applicable to this frontend scope, but confirms test-isolation discipline expected in project.

No entries for SSE hooks, Next.js routing, or React RAF patterns. Assessment is primary research.

---

## Code Review Findings

### 1. `useRunSession.ts` — SSE Code to Remove

File: `web/hooks/useRunSession.ts`

The hook currently has TWO responsibilities:
1. **Start responsibility** (keep): `startRun(query, tavilyApiKey)` → gets `session_id` from `POST /run`
2. **Watch responsibility** (remove): Opens `EventSource`, listens on `workflow_event` + `done` + `onerror`, updates React state with `events`, `report`, `phase`

Exact SSE lines to remove (lines 17, 44–103):
- `const esRef = useRef<EventSource | null>(null)` — the ref
- `esRef.current?.close()` inside `reset()` — the cleanup
- `esRef.current = null` inside `reset()` — the cleanup
- The entire block from `const es = new EventSource(...)` through `es.onerror = () => { ... }` — ~55 lines
- The `EventSource` import is not explicit (it's a browser global) — no import to remove

After refactor, `run(query, tavilyApiKey)` should:
1. Call `startRun()`
2. Get `sessionId`
3. Call `router.push('/run/' + sessionId)` — requires adding `useRouter` import

The `RunState` type in `web/lib/types.ts` still needs to exist for backward compat with the current `run/page.tsx` (which becomes a redirect), but may be dead type after the refactor is complete.

The `reset` function is currently exported — after SSE removal it reduces to just `setState(INITIAL_STATE)` with no `esRef` cleanup. Can keep it if the query form still needs "New run" reset behavior before the redirect fires.

### 2. `useLiveSession.ts` — Refresh Safety Confirmed

File: `web/hooks/useLiveSession.ts`

Refresh-safety is VERIFIED. Exact flow on mount:
1. Calls `getSession(sessionId)` — fetches historical data from DB (events already in `SessionDetail.events`)
2. Sets `session` state with full historical events
3. Only opens `EventSource` if `detail.status === "running"`
4. On `done` event: re-fetches full session from DB, merges into state
5. Cleanup: `useEffect` return closes `EventSource`

The `liveEvents` array accumulates SSE events received after mount. The consumer must merge `session.events` (historical) with `liveEvents` (live) — exactly what `/sessions/[id]/page.tsx` already does at line 86–89.

No changes needed to `useLiveSession.ts` itself.

### 3. `/sessions/[id]` Route — Exists But Needs Refactor

File: `web/app/sessions/[id]/page.tsx` — EXISTS and is a full session detail page (182 lines), using `useLiveSession` + shadcn UI cards. It renders the report, events, retry button.

Per requirement, this must become a **thin status-aware redirect**:
- `router.replace('/run/' + id)` for running/queued/paused/error
- `router.replace('/report/' + id)` for complete

Important: must use `router.replace` (not `router.push`) to avoid back-button trap. The existing page uses `router.push` for retry (`router.push('/sessions/' + session_id)`) — that pattern must change in the new `/run/[id]` page to navigate to `/run/` + new session_id.

The existing functionality in `/sessions/[id]/page.tsx` (live pipeline card, retry button, report viewer, event trace) is being moved to `/run/[id]/page.tsx`. The new page is richer (3-column Bloomberg layout), so this is a migration, not a loss.

### 4. `SessionDetail` Type — What's Available

From `web/lib/types.ts` (lines 49–55):
```
SessionDetail extends SessionSummary:
  session_id: string
  timestamp: string
  query: string
  status: SessionStatus  ("running"|"complete"|"error"|"queued"|"paused")
  error_msg?: string | null
  report?: MarketReport | null
  events: WorkflowEvent[]
  usage: UsageStats | Record<string, never>
  research_json?: string | null
  analyst_json?: string | null
```

**No `progress` field** exists on `SessionDetail`. The prototype `run.jsx` references `session.progress.stage`, `session.progress.elapsed`, `session.progress.eta` — these fields DO NOT EXIST in the backend API or TS type.

The `PipelineStrip` component must derive stage from available data. The existing `PipelineProgress` component in `web/components/run/PipelineProgress.tsx` already does this correctly: it infers stage by checking `events` for `agent_start`/`agent_end` event types, mapping to 3 stages (Researcher/Analyst/Reporter). The new `PipelineStrip` must follow the same events-derived approach for 7 stages OR be simplified to 5 stages matching what the backend actually produces (Plan/Research/Analyst/Reporter confirmed by `web/app/query/page.tsx`'s PIPELINE_STAGES definition with 5 entries).

The `failed_stage` column exists in the DB (string like "pipeline" or "reporter_retry") but is NOT currently exposed in the `/sessions/{id}` API response. To show which stage failed in the error banner, we can either: (a) derive from events (preferred, no API change), or (b) add `failed_stage` to the API response. Option (a) is in-scope; option (b) requires backend change (borderline).

**Timing fields** (elapsed/ETA in header bar KV): No timing data from API. `timestamp` (session start) is available; elapsed can be derived as `Date.now() - new Date(session.timestamp)`. ETA is not calculable — show "—" for ETA unless running (show elapsed tick).

**Token count per agent**: Not broken out per-agent in the API. `session.usage.total_tokens` is the total. Per-agent token counts shown in the prototype (8,402 / 12,118 etc.) are not available. The `AgentCard` must either show "—" or derive tokens from `WorkflowEvent.details` if the backend emits token counts in event details (not verified in schema).

### 5. Progress/Stage Data from API

No `progress` object in the API. Stage must be inferred from `session.events`. The pipeline has these observable stages via events:
- `agent_start` where `source === "Lead"` → stage 1 (Orchestration)
- `agent_start` where `source === "Researcher"` → stage 2
- `agent_end` where `source === "Researcher"` → stage 2 complete
- `agent_start` where `source === "Analyst"` → stage 3
- `agent_end` where `source === "Analyst"` → stage 3 complete
- `agent_start` where `source === "Reporter"` → stage 4 (or stage 5 if separate synthesis)
- `agent_end` where `source === "Reporter"` → final stage complete

The 7-stage prototype strip maps to more granularity than what the 4-agent pipeline produces. For this scope, using 5 stages (matching query page's `PIPELINE_STAGES`) derived from events is correct. The stage count should be a named constant shared between `PipelineStrip` and the query page.

### 6. `run.jsx` Prototype — SwarmTopology and Layout Spec

**SwarmTopology (`RunSwarm` in prototype)**:
- SVG 540×400
- 3 concentric reference rings at r=80, 130, 180 (dashed)
- 4 compass labels: N/E/S/W at edges
- 4 nodes at r=130 (matching ring 2), 32px-radius circles
- Hub center: 20px circle, text "HUB"/"ERR"/"PSE"
- 5 edges (same as SwarmGraph Part 1): lead-market, lead-analyst, lead-reporter, market-analyst, analyst-reporter
- Packet animation: RAF-based tick increment, particles travel edges when `status === "running"` and both endpoints are "running"
- Node states per global status: running→running, error→error node pulses, others queued
- SVG `<animate>` used for node ping (r 6→9→6) and error pulse (opacity 0.3→1→0.3)
- Prototype uses `useState(tick)` + `setTick` inside RAF — **this causes 60 React re-renders/sec**. The requirement explicitly requires using mutable refs instead (same pattern as `SwarmGraph.tsx` from Part 1). This is a required deviation from the prototype.

**Layout (3-column)**:
- Left: `300px` fixed — agent cards + brief panel
- Center: `1fr` — SwarmTopology (top) + Emerging Draft (bottom)
- Right: `360px` fixed — event stream + sources
- Above body: session header bar (grid, surface bg, border-bottom) + optional error/pause banner + pipeline strip (grid: 150px label + 1fr strip)

**Component boundaries from prototype**:
- `RunAgentsCol` → `AgentCard` × 4 + brief panel
- `RunEventCol` → `EventLog` + Sources subpanel
- `RunSwarm` → `SwarmTopology`
- `PipelineStrip` → `PipelineStrip`

---

## Implementation Approach

**Phase 1: Route scaffold + useRunSession refactor**
1. Create `web/app/run/[id]/page.tsx` — uses `useLiveSession(id)`, renders loading/error states
2. Refactor `web/app/run/page.tsx` → redirect to `/query` (or render the query form directly, since `/query` may not exist; confirm first)
3. Refactor `web/app/sessions/[id]/page.tsx` → thin redirect
4. Refactor `web/hooks/useRunSession.ts` → strip SSE, add `router.push`

**Phase 2: New buzz components**
5. `SwarmTopology.tsx` — extends SwarmGraph patterns (RAF with mutable refs, SVG animate for node states)
6. `AgentCard.tsx` — single agent card component
7. `EventLog.tsx` — event stream + sources panel
8. `PipelineStrip.tsx` — 5-stage strip with event-derived state

**Phase 3: Assemble run screen + tests**
9. Assemble 3-column layout in `/run/[id]/page.tsx`
10. Add `web/__tests__/useRunSession.test.ts` — assert no EventSource constructed

**Why this approach over alternatives:**
- **Reuse `useLiveSession` rather than enhancing `useRunSession`**: `useLiveSession` already has the full refresh-safe pattern. Building the run screen on top of it means page refresh is automatically handled. Enhancing `useRunSession` would duplicate the DB-fetch-then-SSE logic.
- **Event-derived stage vs. API `progress` field**: No `progress` object exists in backend. Deriving from events is already proven by `PipelineProgress.tsx`. Adding a `progress` field to the API would require backend change and is out of scope.
- **RAF with mutable refs vs. `useState` for animation**: `useState` in RAF causes 60 re-renders/sec, violating the success criterion. The Part 1 `SwarmGraph.tsx` already established the correct pattern — follow it exactly.
- **router.replace vs router.push in `/sessions/[id]`**: `replace` prevents back-button redirect loop. Critical distinction from existing code which uses `push`.

**Key Assumptions:**
- The `/query` route exists for the `/run` page redirect (confirmed: `web/app/query/page.tsx` exists)
- `WorkflowEvent.source` values are "Lead", "Researcher", "Analyst", "Reporter" (exactly, case-sensitive) — derived stage mapping depends on this
- Per-agent token counts are not available from `WorkflowEvent.details` without verification; show "—" or total from `session.usage.total_tokens`
- Pause/resume backend endpoint does not exist; Pause button shown disabled or omitted; Resume button shown disabled
- The `retrySession()` API function already exists in `web/lib/api.ts` (confirmed, line 69)
- `nextjs-build` CI must pass — no `any` types without justification, no missing imports

---

## Design Decisions

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Stage derivation | Infer from `session.events` (agent_start/agent_end) | Add `progress` field to backend API | No backend change needed; existing `PipelineProgress.tsx` proves the pattern works |
| RAF animation isolation | Mutable SVG attribute refs (same as SwarmGraph Part 1) | `useState(tick)` as in prototype `RunSwarm` | `useState` in RAF = 60 re-renders/sec; violates success criterion; ref pattern proven in Part 1 |
| Stage count in PipelineStrip | 5 stages matching query page `PIPELINE_STAGES` | 7 stages as implied by requirement | API only produces events for 4 agents mapping to ~5 logical stages; 7-stage model has no event source to infer from |
| `/sessions/[id]` fate | Convert to thin redirect (`router.replace`) | Keep as full detail view | Requirement explicitly specifies; new `/run/[id]` is the canonical detail view for all active/failed sessions |
| `/run/page.tsx` fate | Redirect to `/query` | Keep query form inline | `/query` route exists; separation of query form from live observation is the architectural intent |
| Per-agent tokens | Show "—" or total only | Parse `WorkflowEvent.details` | No schema guarantee on details structure; safe default prevents runtime crash |
| Pause button | Show disabled (no backend endpoint) | Omit entirely / implement mock | Requirement says "wire to endpoint only if it exists; show disabled if not"; honest UI state |
| `router.replace` in retry | Navigate to `/run/{new_session_id}` with `router.push` | Stay on `/sessions/{id}` | After retry, a new session_id is created; navigation to new run screen is correct UX |

---

## Risks

- **Double EventSource if useRunSession SSE not fully removed**: If any SSE code survives the refactor and the query form submits, both `useRunSession` (legacy SSE) and `useLiveSession` (from `/run/[id]`) will connect. Mitigation: the Jest test (`assert no EventSource constructed`) is the safety net; also verify in browser devtools.
- **`agent_start`/`agent_end` source casing**: Stage derivation assumes exact source values. If the backend emits "researcher" vs "Researcher", stage detection silently fails and all stages show as queued. Mitigation: check a real completed session's events JSON, or make matching case-insensitive.
- **SwarmTopology `<animate>` + RAF coexistence**: The prototype uses SVG `<animate>` for node pulses (declared in JSX) and RAF for packet movement. These coexist fine since `<animate>` runs independently. But React may re-create the SVG `<animate>` elements on re-render, resetting animation timing. Mitigation: ensure `SwarmTopology` renders SVG `<animate>` elements with stable keys; the RAF ref approach means no React re-renders from packet movement, only from prop changes (status transitions).
- **`/run/page.tsx` redirect breaks existing query form users**: The existing `/run` page IS the query form for current users. Redirecting it to `/query` means bookmarked `/run` URLs go to `/query` instead of showing a run form. Mitigation: ensure `/query` has the full query form; this is the intended new home for query input (confirmed by `web/app/query/page.tsx` existing).
- **`_active_streams` server restart**: Already noted in requirement. Not fixable here. The retry affordance is the mitigation.
- **ETA display**: No ETA data from API. Show "—" unconditionally for now. Do not attempt to estimate.

---

## Clarification Needed

None — all blocking questions resolved by code review. Proceeding with assumptions documented above.

### Implementation note on `failed_stage` in error banner
The error banner in the prototype shows `STAGE {n} · {AGENT}` — this requires knowing which stage index failed. `session.error_msg` contains the error text; `failed_stage` column in DB contains "pipeline" or "reporter_retry" string but is NOT exposed in the current API response. For the error banner, use `session.error_msg` for the message text, and derive the agent name by checking which agent's `agent_start` event appears last without a corresponding `agent_end`. This is derivable from events without API changes.
