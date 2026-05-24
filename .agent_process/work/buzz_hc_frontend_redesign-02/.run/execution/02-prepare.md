# Execution Preparation

**Scope:** buzz_hc_frontend_redesign-02
**Iteration:** iteration_01
**Type:** first_iteration

---

## Criteria (LOCKED)

- [ ] AC-1: Navigating to `/run/<id>` for a session with `status=complete` renders the full historical session (header bar, pipeline strip showing all stages complete, agent cards, event log) without `EventSource` being opened — verified via DOM snapshot + EventSource spy in component test or manual devtools check.
- [ ] AC-2: Navigating to `/run/<id>` for a session with `status=running`, then refreshing the page, results in (a) historical events from DB rendered immediately, (b) a single `EventSource` connection to `/run/<id>/stream`, and (c) new events appended to the existing list — no duplicate connections, no lost historical events.
- [ ] AC-3: `/sessions/<id>` calls `router.replace('/run/<id>')` when fetched status ∈ {running, queued, paused, error} and `router.replace('/report/<id>')` when status = complete. Browser back button after redirect returns to the prior page (not the `/sessions/<id>` URL).
- [ ] AC-4: `/run` (no id) calls `router.replace('/query')` on mount; no query form rendered on `/run`.
- [ ] AC-5: Jest test `web/__tests__/useRunSession.test.ts` passes and asserts `global.EventSource` constructor is never invoked across a full `run()` call; also asserts `router.push` is called exactly once with `/run/<returned_session_id>`.
- [ ] AC-6: `PipelineStrip` rendered against a real completed session's `events` array shows all 5 stages with `state=complete` (green border + ✓ glyph). Against a running session with `agent_start` for Researcher but no `agent_end`, the Researcher stage shows `state=running` (cyan + ↻); later stages show `state=queued` (border + ·).
- [ ] AC-7: Error banner is rendered when `session.status === "error"` containing `session.error_msg`, derived failed-agent label (from last `agent_start` without matching `agent_end`), and a "↻ Retry stage" button. Clicking the button invokes `retrySession(id)` and navigates to `/run/<new_session_id>`.
- [ ] AC-8: `SwarmTopology` runs RAF animation without triggering React re-renders per frame — verified by a render-count assertion or by code review confirming no `setState` is called inside the RAF callback (only `ref.current.setAttribute(...)`).
- [ ] AC-9: Center-column "Emerging draft" placeholder is rendered with the text "← Reporter streaming added in Part 4" (placeholder copy approved for Part 4 hand-off).
- [ ] AC-10: `pnpm --filter web build` (nextjs-build CI step) succeeds with zero TypeScript errors and zero new `any` types in the new/modified files. `uv run pytest tests/ -v` remains green (no backend changes expected).

---

## Files in Scope

| Path | Action | Unit |
|------|--------|------|
| `web/hooks/useRunSession.ts` | Modified | A |
| `web/__tests__/useRunSession.test.ts` | New (Test) | A |
| `web/components/buzz/SwarmTopology.tsx` | New | B |
| `web/components/buzz/AgentCard.tsx` | New | B |
| `web/components/buzz/EventLog.tsx` | New | B |
| `web/components/buzz/PipelineStrip.tsx` | New | B |
| `web/app/run/[id]/page.tsx` | New | C |
| `web/app/run/page.tsx` | Modified | C |
| `web/app/sessions/[id]/page.tsx` | Modified | C |

**Boundary flexibility (mirrors the iteration-plan rule):** This list is the *expected* touch surface, not a *forbidden* boundary. If meeting the acceptance criteria correctly — including any negative-case tests for quality-gate artifacts (§1.2) or stale-surface whitelist updates for removed surfaces (§1.1) — requires touching files outside this list, the implementer may do so. Document the expansion in `results.md` under "Implementation Notes" with what was added and why. The narrower list keeps sub-iterations focused; it does not wall off soundness fixes.

---

## Removed Surfaces

**N/A** — The iteration plan explicitly declares `Removed Surfaces: N/A`. Both `/sessions/[id]` and `/run` URLs continue to respond (as redirects). `useRunSession`'s public signature is preserved. No scrub block required.

---

## Validation

**RUN (must pass):**
```bash
cd web && pnpm tsc                    # TypeScript — zero errors, zero new `any` types
cd web && pnpm test                   # Jest suite — ≥4 tests passing (3 existing + 1 new)
cd web && pnpm build                  # Next.js production build — must succeed
uv run pytest tests/ -v              # Python tests — 53 must remain green (no backend changes)
```

**Scoped validation script (fast feedback during iteration):**
```bash
.agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-02.sh
```
Checks (bash 3.2 compatible):
1. `pnpm tsc` passes
2. `pnpm test` shows ≥4 Jest tests passing
3. `web/app/run/[id]/page.tsx` exists
4. `web/components/buzz/SwarmTopology.tsx` exists
5. `web/components/buzz/AgentCard.tsx` exists
6. `web/hooks/useRunSession.ts` does NOT contain `new EventSource` (grep returns non-zero)
7. `web/app/sessions/[id]/page.tsx` contains `router.replace`
8. No `lucide-react` imports in any `web/components/buzz/` file or `web/app/run/[id]/page.tsx`

Document raw output in `iteration_01/test-output.txt`.

**SKIP:** None. Baseline confirmed: 53 Python tests green, 3 Jest tests green, `pnpm build` clean. If `pnpm lint` or `ruff check` surfaces unrelated debt during execution, document in `results.md` and add to SKIP — do not block this scope on out-of-file lint noise.

---

## Human Checkpoint

- **Required:** NO
- **Source file:** `.agent_process/work/buzz_hc_frontend_redesign-02/human-prereqs.md` (present: NO)
- **Pre-execution items:** none
- **Mid-execution items:** none
- **Post-execution items:** none
- **Allowed Responses:** N/A

**Note for coordinator:** no human gate is required for this iteration. The actual gate runs in the main conversation per `execute.md` Steps 0.5 and 6. This section confirms there is no `human-prereqs.md` to surface.

---

## Quality-Gate Artifact Check (§1.2)

No file in the Files in Scope list is a quality-gate artifact (validator script, lint config, type-check config, adversarial-review prompt, etc.). The scoped validation script (`.agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-02.sh`) is invoked by the executor but not modified in this scope — it is not in the Files in Scope table. Section §1.2 negative-case test requirement is therefore silent.

---

## Concrete Scenario Coverage (§1.5)

The following ACs fire the §1.5 triggers (universal quantifiers, multiple subjects, alternatives with divergent semantics, state-dependent behavior). Scenario tables are enumerated below so the implementer covers each cell and the reviewer can re-run each row.

---

### AC-1 and AC-2 — `/run/<id>` complete vs running (state-dependent + divergent alternatives)

Two status values with structurally divergent behavior (complete: no SSE; running: SSE opened):

| Input | State context | Observable outcome |
|-------|---------------|--------------------|
| Navigate browser to `/run/<id>` | Session `status=complete` in DB; all stages have `agent_start`+`agent_end` | Full session rendered (header bar, pipeline strip all green + ✓, agent cards, event log); `EventSource` constructor never called (spy records 0 invocations); `pnpm test` passes for this assertion |
| Navigate browser to `/run/<id>` | Session `status=running` in DB; Researcher `agent_start` present, no `agent_end` yet | Historical events rendered immediately (from `getSession(id)`); exactly one `EventSource` opened to `/run/<id>/stream`; SSE `workflow_event` messages append to existing list without duplicating historical events |
| Navigate browser to `/run/<id>`, then press F5 (refresh) | Session `status=running`; some events already in DB | After refresh: historical events visible immediately (not blank-then-load); `EventSource` count is exactly 1 (not 2); no events are lost or duplicated |

**Test binding:** AC-1 is covered by the component/hook test (EventSource spy). AC-2 refresh safety is covered by `useLiveSession` behavior (which must not be modified) — verify via browser devtools or a dedicated integration test note in `results.md`.

---

### AC-3 — `/sessions/<id>` redirect across 5 status alternatives (divergent redirect targets)

Status values split into two redirect targets — not symmetric:

| Input | State context | Observable outcome |
|-------|---------------|--------------------|
| Browser navigates to `/sessions/<id>` | Fetched session `status=running` | `router.replace('/run/<id>')` called; URL in address bar becomes `/run/<id>`; pressing Back returns to page *before* `/sessions/<id>`, not back to `/sessions/<id>` |
| Browser navigates to `/sessions/<id>` | Fetched session `status=queued` | Same as running: `router.replace('/run/<id>')` |
| Browser navigates to `/sessions/<id>` | Fetched session `status=paused` | Same as running: `router.replace('/run/<id>')` |
| Browser navigates to `/sessions/<id>` | Fetched session `status=error` | Same as running: `router.replace('/run/<id>')` |
| Browser navigates to `/sessions/<id>` | Fetched session `status=complete` | `router.replace('/report/<id>')` called; URL becomes `/report/<id>`; pressing Back returns to prior page (not `/sessions/<id>`) |

**Critical divergence:** `router.replace` (not `push`) is required for ALL five cases. Using `push` for any status creates a back-button trap. The test for this AC must verify `replace` is called (not `push`) — mock `useRouter` and assert on `router.replace`, not `router.push`.

---

### AC-6 — `PipelineStrip` across two session states (state-dependent: complete vs running-partial)

| Input | State context | Observable outcome |
|-------|---------------|--------------------|
| `PipelineStrip` rendered with events array | All 5 stages have both `agent_start` and `agent_end` (complete session) | All 5 stage cells show green 2px top border + ✓ glyph |
| `PipelineStrip` rendered with events array | `agent_start` for Researcher present; no `agent_end` for Researcher; no events for Analyst/Reporter stages | Researcher cell: cyan border + ↻ glyph; Analyst, Reporter, and remaining stages: default border + · glyph; Lead/Orchestration stage (before Researcher): green + ✓ |
| `PipelineStrip` rendered with empty events array | Session `status=queued` (no events yet) | All 5 cells: default border + · glyph (queued state) |

**Note:** The third row (empty events, queued) is a state-dependency edge case. The stage-derivation logic must not crash on an empty array.

---

### AC-7 — Error banner (state-dependent: error status + multiple derived fields)

| Input | State context | Observable outcome |
|-------|---------------|--------------------|
| `/run/<id>` page renders | `session.status === "error"`, `session.error_msg = "Connection timeout after 30s"`, events: `agent_start source="Researcher"` at t=1, no subsequent `agent_end` for Researcher | Error banner visible; contains text "Connection timeout after 30s"; contains derived label "Researcher" (last agent_start without matching agent_end); "↻ Retry stage" button present |
| User clicks "↻ Retry stage" | Same error state; `retrySession(id)` resolves with `{ session_id: "new-abc" }` | `retrySession(id)` invoked exactly once; `router.push('/run/new-abc')` called; user navigates to the new run screen |
| `/run/<id>` page renders | `session.status === "error"`, events: `agent_start source="Analyst"` at t=1, `agent_end source="Analyst"` at t=2, `agent_start source="Reporter"` at t=3, no `agent_end` for Reporter | Derived label is "Reporter" (last agent_start without matching agent_end is Reporter, not Analyst) |

---

### AC-8 — SwarmTopology RAF isolation (state-dependent: running vs paused vs error)

| Input | State context | Observable outcome |
|-------|---------------|--------------------|
| `SwarmTopology` mounted and animating | `status=running` | RAF callback fires at ~60fps; React render count does NOT increase each frame — confirmed by code review: no `setState`/`useState` setter called inside RAF callback; only `ref.current.setAttribute(...)` |
| `SwarmTopology` receives `status=paused` | Previously running | RAF loop cancelled (no new `requestAnimationFrame` scheduled); packet animation freezes; hub label updates to "PSE" |
| `SwarmTopology` receives `status=error` | Previously running | RAF loop continues or stops (implementation choice); errored node receives SVG `<animate>` opacity pulse (0.3→1→0.3); hub label updates to "ERR" |

**Verification method:** Code review is the primary method per AC-8. Reviewer confirms: (1) the RAF callback function body contains zero calls to any React state setter; (2) only `ref.current.setAttribute(...)` or similar DOM mutations appear inside the RAF frame. A render-count assertion in a test is also acceptable as additional proof.

---

## Implementation Notes for Executor

### Unit A — Hook refactor (land first)

**Why first:** If any SSE code survives in `useRunSession.ts`, subsequent units cannot accidentally re-introduce dual-EventSource behavior. The unit A test is the safety net.

**Exact lines to remove from `web/hooks/useRunSession.ts`:**
- Line 17: `const esRef = useRef<EventSource | null>(null)` — remove
- Lines 44–103 (approximately): the entire `const es = new EventSource(...)` block through `es.onerror = () => { ... }` — remove (~55 lines)
- `esRef.current?.close()` inside `reset()` — remove
- `esRef.current = null` inside `reset()` — remove
- Add `import { useRouter } from 'next/navigation'` if not present
- Inside `run()` success branch, after obtaining `sessionId`: add `router.push('/run/' + sessionId)`

**Semantic intent:** The hook's single responsibility after refactor is to initiate a run and navigate. Observation is delegated to `useLiveSession` in the `/run/[id]` page. Separating these prevents the query page from accidentally opening a second EventSource alongside the one opened by the live run page.

**`RunState` preservation:** Keep `RunState` type and `reset()` in case the query form still needs "New run" reset behavior. Do not delete exported symbols that may have external consumers.

**New test `web/__tests__/useRunSession.test.ts`:**
- Spy on `global.EventSource` constructor with `jest.spyOn(global, 'EventSource')`
- Mock `fetch` to return `{ session_id: 'test-session-001' }`
- Mock `next/navigation` `useRouter` to return `{ push: mockPush }`
- Call `run('test query', 'api-key')`
- Assert: `EventSource` spy `.not.toHaveBeenCalled()`
- Assert: `mockPush` called exactly once with `'/run/test-session-001'`

---

### Unit B — New `buzz/` components (land after A)

**All four components must:**
- Import zero symbols from `lucide-react` — use unicode glyphs only (✓ ↻ ✕ ⏸ ↳ ↗ ▸ ·)
- Use design tokens from Part 1 `globals.css` — do not invent new CSS custom property names
- Accept `session: SessionDetail` (or a subset) as prop — derive all display state from `session.events`

**`PipelineStrip` stage derivation:**
- Import or reference `PIPELINE_STAGES` from `web/app/query/page.tsx` (or re-export from `PipelineStrip.tsx` as the canonical home)
- Stage state per cell:
  - `complete` — both `agent_start` and `agent_end` present for the stage's source
  - `running` — `agent_start` present, no `agent_end` yet
  - `error` — session `status=error` AND this stage's agent is the derived failed agent
  - `paused` — session `status=paused` AND this stage is the current stage
  - `queued` — no events for this stage yet
- The Lead/Orchestration stage is complete if `session.status` ∈ {running, complete, error} — Lead's `agent_end` may not be emitted separately; treat as complete once any Researcher event appears
- Reference `web/components/run/PipelineProgress.tsx` as the verified reference implementation for stage derivation; do not re-derive from scratch

**`SwarmTopology` RAF constraint:**
- Copy the RAF + `useRef` pattern from `web/components/buzz/SwarmGraph.tsx` (Part 1) exactly
- The RAF callback must contain ONLY: read from refs, compute positions, `el.setAttribute('cx', ...)`, `el.setAttribute('cy', ...)`, `rafIdRef.current = requestAnimationFrame(tick)`
- Absolutely no `setState`, `setTick`, `forceUpdate`, or any React state setter inside the RAF callback
- SVG `<animate>` elements for node pulses are declared in JSX (static) — they run independently of RAF and do not trigger React re-renders when React is not re-rendering the component
- Packet movement: each edge has a `t` value (0→1) stored in a mutable ref; each RAF frame increments `t` by `speed * dt`; when `t >= 1` reset to 0 and spawn the next packet

**`AgentCard` task derivation:**
- Current task = most recent `workflow_event` matching this agent's source, event type `agent_start` or a progress-type event — display the `event.message` field with `↳` prefix
- Token count: show `"—"` (do not parse `WorkflowEvent.details` for per-agent tokens)
- 16-segment progress bar: render when agent is in `running` state; animate via CSS or a mutable ref (do not drive with state)
- Error overlay: red-tinted background when session `status=error` AND this is the derived failed agent

**`EventLog` sources subpanel:**
- Domain extraction: parse source domains from `WorkflowEvent.message` (URLs in research events) — or show domain list from `session.research_json` if available and parsed
- If domain extraction is uncertain, show a static "Sources" heading with the count of research events — do not crash on missing data
- Errored sources (TIMEOUT) are only shown if identifiable; otherwise omit rather than show incorrect data

---

### Unit C — Pages (land after A + B)

**`web/app/run/[id]/page.tsx`:**
- Import and call `useLiveSession(id)` where `id` comes from `useParams()`
- Merge events: `const allEvents = [...(session?.events ?? []), ...liveEvents]` — same pattern as current `/sessions/[id]/page.tsx` lines 86–89 (before refactor)
- Loading state: render `<div>Loading…</div>` (or a spinner atom from Part 1) while `session === null`
- Not-found state: render `<div>Session not found</div>` when the fetch returns 404
- Header bar: 12×16 padding, surface bg, border-bottom, grid layout with session ID + query text + 4 KV metrics (Elapsed, ETA="—", Agents, Status) + `StatusChip` + action button
- ETA: show `"—"` unconditionally — do not estimate
- Pause button: render `disabled` when `status=running` (no backend endpoint)
- Resume button: render `disabled` when `status=paused`
- On `status=complete`: show "↗ Open report" button linking to `/report/<id>`
- On `status=error`: show error banner (from AC-7 scenario table) with `retrySession(id)` CTA; after retry resolves, call `router.push('/run/' + new_session_id)`
- On `status=paused`: show paused banner
- 3-column grid: `grid-template-columns: 300px 1fr 360px`
  - Left: `<AgentCard>` × 4 (one per source) + brief panel
  - Center: `<SwarmTopology>` + placeholder `<div>← Reporter streaming added in Part 4</div>`
  - Right: `<EventLog>`
- Pipeline strip above body: `<PipelineStrip events={allEvents} status={session.status} />`

**`web/app/run/page.tsx`:**
```tsx
'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function RunPage() {
  const router = useRouter()
  useEffect(() => { router.replace('/query') }, [router])
  return <div>Redirecting…</div>
}
```

**`web/app/sessions/[id]/page.tsx`:**
- Must use `router.replace` — NOT `router.push` — for both redirect branches
- Fetch session with `getSession(id)` (existing API helper)
- Branch on `session.status`:
  - `running` | `queued` | `paused` | `error` → `router.replace('/run/' + id)`
  - `complete` → `router.replace('/report/' + id)`
- Render a "Redirecting…" fallback while fetch is in flight
- The page must shrink to ~20–30 lines; discard the 182-line detail view body entirely
- **`replace` vs `push` is a contract requirement** — back-button behavior depends on it; both the AC and the scenario table above specify this; a reviewer will test it manually

---

## Spec Concerns Channel

**Spec Concerns channel:** Pause and write a `## Spec Concerns` section at the top of `results.md` if any of these fire:

- **Prepare-doc gap.** A missing acceptance test, an instruction that conflicts with the iteration plan or framework rules, a soundness question about a quality-gate artifact you're modifying, or a fix spec that names a symptom rather than a root cause.
- **About to weaken a failing check.** You're about to remove an assertion, relax a test, comment-out a guard, document a known regression as "future work," or rephrase a doc/comment to dodge a string match. This is the failure mode the channel exists to catch. Treat the weakening as a Spec Concern, not a local fix.
- **Test failure points at production code, not the test.** If the assertion encodes the contract correctly and the production code doesn't honor it, the production code is the bug — even if it lives outside your file list. §1.3 (boundary flexibility) lets you fix it.

Then choose ONE:

- **Local fix is safe and obviously correct:** apply it, document it under Spec Concerns AND in Implementation Notes, including what changed and why.
- **Local fix is uncertain or expands scope significantly:** stop without applying it, leave the concern in `results.md`, and surface it to the coordinator so the prepare doc can be revised.

**There is no third option that weakens the check to make the failure go away.** Modifying or removing a failing test assertion is a *contract change*, not a local fix — even when the edit is mechanically simple. A test assertion is a piece of contract surface area; removing it silently reduces the contract. Contract changes always require coordinator escalation. The path forward is fix-the-issue (in scope, even when §1.3 boundary flexibility is needed to extend to a file outside your list) or stop-and-surface (out of scope). Weakening the check is the anti-pattern.

Concerns raised in good faith are never a failure mode; silently shipping work the implementer suspects is incomplete is.

---

## Key Risks (for executor attention)

1. **Double EventSource trap.** If any SSE code survives in `useRunSession.ts` AND the query page submits, two EventSource connections open: one from the legacy hook, one from `useLiveSession` in `/run/[id]`. The Jest test (AC-5) is the safety net — run it first before touching components.

2. **`router.replace` vs `router.push` in `/sessions/[id]`.** The existing code uses `push` for retry navigation. The new redirect in `/sessions/[id]` MUST use `replace`. Confusing the two is easy; test the back button explicitly.

3. **SwarmTopology `setState` inside RAF.** The prototype `run.jsx` uses `useState(tick)` + `setTick` inside the RAF callback — this causes 60 React re-renders/sec. The requirement explicitly forbids this. Follow `SwarmGraph.tsx` (Part 1) which uses `ref.current.setAttribute(...)` only.

4. **`agent_start`/`agent_end` source casing.** Stage derivation silently fails if casing differs from `"Lead"` / `"Researcher"` / `"Analyst"` / `"Reporter"`. If a real session reveals different casing, normalize at the comparison boundary — do NOT edit backend.

5. **Empty events array.** `PipelineStrip` and `AgentCard` must not crash when `session.events` is empty (queued session). Guard all `.find()` / `.filter()` calls on events.

---

## Decomposition

**DECOMPOSE: yes**

Work unit DAG (must execute in order):

```
Unit A (Hook refactor)
  web/hooks/useRunSession.ts
  web/__tests__/useRunSession.test.ts
       |
       v
Unit B (buzz/ components)
  web/components/buzz/SwarmTopology.tsx
  web/components/buzz/AgentCard.tsx
  web/components/buzz/EventLog.tsx
  web/components/buzz/PipelineStrip.tsx
       |
       v
Unit C (Pages)
  web/app/run/[id]/page.tsx
  web/app/run/page.tsx
  web/app/sessions/[id]/page.tsx
```

- **A unblocks B:** Components reference the clean hook contract (no SSE); the Jest test in A confirms SSE is gone before B adds components that would be affected by a dual-EventSource regression.
- **A + B unblock C:** The pages assemble and import the components from B and use the hook contract established in A.
- **Within B:** The four component files are not interdependent; they can be implemented in parallel, but all should be completed before C begins.

Each unit is independently validatable:
- After A: `pnpm test` must show the new `useRunSession.test.ts` passing (1 new test, EventSource spy 0 invocations)
- After B: `pnpm tsc` must pass for the new component files; lucide-react grep must return non-zero for all four files
- After C: Full validation suite (`pnpm tsc`, `pnpm test` ≥4 passing, `pnpm build`, `uv run pytest tests/ -v` 53 green)

---

## Agent Selection

- **Mode:** single-agent
- **Agent(s):** `frontend-excellence:react-specialist`
- **Reasoning:** All 9 files are React/TypeScript (`*.tsx`, `*.ts`, `*.test.ts`). The dominant risks (RAF isolation, SSE cleanup, Next.js App Router routing semantics) are frontend-specific. No backend files are touched. A single React specialist agent can execute units A → B → C sequentially, using the scoped validator for fast feedback between units.
