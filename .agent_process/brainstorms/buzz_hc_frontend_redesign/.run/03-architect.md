# Brainstorm: Software Architect — Buzz HC UI Redesign

## Technical Feasibility

**Overall verdict: Feasible without any backend rewrites.** The stack is already well-positioned for this redesign. Next.js 16 App Router, React 19, Tailwind v4 with OKLCH token system, framer-motion v12, and shadcn/ui are all current tools that support what the design calls for. The main work is frontend-only with a small, optional API-layer addition for reporter streaming.

The key risks are not about capability — they are about surgical precision in a few specific areas:

1. **The `/run` → `/run/[id]` migration is the highest-risk change.** It's currently a stateless page with no URL identity. Redirecting after `startRun()` completes is simple, but the transitional period where both routes must work (or the old one redirects) needs care.
2. **pydantic-ai token streaming for the reporter is genuinely uncertain.** The reporter uses `output_type=MarketReport` (structured JSON), which means `stream_text()` is unavailable — pydantic-ai only streams text for `output_type=str`. `stream_structured()` yields partial Pydantic objects, but mid-generation field completeness is model-dependent and unreliable for rich markdown fields. This is a real technical constraint, not an implementation detail.
3. **The `app/schema.py` freeze creates one constraint.** `EventType` in `app/schema.py` is a `Literal[...]` that controls what Python SSE events can carry. Adding `reporter_chunk` as an event type requires either modifying that Literal (blocked) or emitting it from the API layer as a separate SSE event name not tied to `WorkflowEvent` at all — which is the clean workaround.
4. **Dark-only migration.** The current CSS has `.dark {}` already fully defined. The migration is minimal, but any hard-coded `bg-white`, `text-black`, or light-specific Tailwind classes scattered across components need to be audited. The current EventFeed is already dark (`bg-zinc-950`), which is a good sign.

---

## Implementation Approach

### Route Migration

The route topology change is the structural backbone of the whole redesign. Current state:

- `/` — landing
- `/run` — stateless run (the broken one)
- `/sessions` — list
- `/sessions/[id]` — detail with live streaming

Target state:

- `/` — new landing
- `/query` — new, standalone query composer
- `/run/[id]` — new, ID-based persistent run page
- `/sessions` — redesigned as dense data table
- `/report/[id]` — new Bloomberg dossier view

**Migration strategy:**

Step 1: Create `web/app/run/[id]/page.tsx`. This is the new persistent run page. It wraps `useLiveSession(id)` (already exists, already handles reconnect-on-refresh). The page receives the session ID from the URL param, so it works identically on first load or after a browser refresh.

Step 2: Refactor the current `web/app/run/page.tsx` into a redirect-capable query entry that, on form submit, calls `startRun()`, receives the `session_id`, and immediately `router.push('/run/' + session_id)`. The query form itself moves to `/query`. The `/run` page becomes a redirect shell, or is deprecated entirely by pointing the "Start Research" CTA at `/query`.

Step 3: Create `web/app/query/page.tsx` — a standalone query composer that lives at `/query`. This is a new file containing the revamped `QueryComposer` component. It calls `startRun()` and redirects to `/run/[id]`.

Step 4: Create `web/app/report/[id]/page.tsx` — fetches `getSession(id)`, renders report-only view. For completed sessions, this is purely presentational. For in-progress sessions where the report isn't ready, it can show a loading state.

Step 5: Update navigation in `web/app/layout.tsx`: swap `/run` link to `/query`, add `/sessions` link (already present).

**No backend route changes are needed for this migration.** The `/run/{session_id}/stream` SSE URL and all session endpoints already use session IDs.

### Component Architecture

**Keep as-is (reuse with styling changes only):**

- `web/hooks/useRunSession.ts` — the `run()` callback and phase machine are solid; only needs a `router.push` added after `startRun()` succeeds
- `web/hooks/useLiveSession.ts` — this is the right primitive for `/run/[id]`; no logic changes needed
- `web/lib/api.ts` — all wrappers stay; only `getStreamUrl` alias rename is cosmetic
- `web/lib/types.ts` — add `reporter_chunk` to `EventType` union (TypeScript-only change, no backend impact)
- `web/components/ui/*` — shadcn/ui primitives; keep all, just retheme via CSS variables

**Rebuild with new design language:**

- `web/components/run/EventFeed.tsx` → `web/components/buzz/AgentLog.tsx` — same data model, new Bloomberg terminal aesthetic; columns: timestamp, agent tag, event type glyph, message
- `web/components/run/PipelineProgress.tsx` → `web/components/buzz/SwarmTopology.tsx` — replace the linear progress bar with the radial SVG graph (see Swarm Visualization section below)
- `web/components/report/ReportViewer.tsx` → `web/components/buzz/ReportDossier.tsx` — replace prose markdown blob with Bloomberg panel card grid; sections become discrete cards, sources become a footnote drawer

**New components to create:**

```
web/components/buzz/
  SwarmTopology.tsx       — animated radial SVG graph (replaces PipelineProgress)
  AgentLog.tsx            — redesigned event feed (Bloomberg terminal log)
  ReportDossier.tsx       — panel-card report layout with footnote drawer
  KpiPanel.tsx            — a single Bloomberg-style KPI card (used inside ReportDossier)
  FootnoteDrawer.tsx      — slide-up drawer listing sources
  QueryComposer.tsx       — redesigned query form (depth selector, token budget UI)
  SessionsTable.tsx       — dense data table (replaces the card list in sessions/page.tsx)
  StatusPip.tsx           — reusable status indicator dot with color + pulse logic
```

**Pages (new or fully rebuilt):**

```
web/app/page.tsx                    — Landing redesign (animated SVG swarm hero)
web/app/query/page.tsx              — New: query composer page
web/app/run/[id]/page.tsx           — New: ID-based run page wrapping useLiveSession
web/app/sessions/page.tsx           — Redesign: uses SessionsTable component
web/app/report/[id]/page.tsx        — New: report dossier page
```

**What happens to the old `/sessions/[id]`:**

The existing `web/app/sessions/[id]/page.tsx` can be deprecated — its functionality moves to `/run/[id]` (live activity) and `/report/[id]` (finished report). A redirect from `/sessions/[id]` → `/report/[id]` is the clean transition. The `useLiveSession` hook is reused verbatim in `/run/[id]`.

### Theme Migration

The dark-only migration is lower-risk than it looks. The CSS is already well-structured:

**Current state in `globals.css`:**
- `:root {}` defines the light theme (OKLCH values, light backgrounds)
- `.dark {}` defines the dark theme (already fully populated with OKLCH values)
- `@theme inline` block maps CSS vars → Tailwind color tokens

**Migration strategy — two steps:**

Step 1: In `:root {}`, replace all light-theme values with the dark-theme values (copy the `.dark {}` block into `:root {}`). Then delete or keep `.dark {}` as an alias — it will be identical. This makes the app dark by default without any class toggling.

Step 2: Audit and fix hard-coded values. Search for:
- `bg-white`, `bg-gray-*`, `bg-slate-*` — replace with `bg-background` or `bg-card`
- `text-black`, `text-gray-900`, `text-zinc-900` — replace with `text-foreground`
- Light-specific `text-indigo-900` in `ReportViewer.tsx` (prose-h2 color) — fix to use `text-primary`
- The `bg-emerald-50`, `border-emerald-500` classes in `PipelineProgress.tsx` — will need dark-safe equivalents using OKLCH vars

The Bloomberg design spec calls for custom OKLCH tokens (IBM-terminal style). The `@theme inline` block already uses the right pattern — the new dark palette just replaces the values inside `:root {}`. The new fonts (IBM Plex Sans + JetBrains Mono) replace the current `next/font/google` imports in `layout.tsx`. Both fonts are available via `next/font/google`, so this is a drop-in swap. The `--font-sans` and `--font-mono` CSS variables are already wired correctly throughout the codebase.

**One constraint:** `max-2px border-radius` is a significant departure from the current `rounded-2xl` usage everywhere. A global CSS override `--radius: 2px` in `:root {}` is the cleanest approach — all shadcn components derive their radius from `--radius` via the `@theme inline` block, so this single change cascades everywhere without touching individual components.

### Reporter Draft Streaming — 3 Options Assessed

**Option A: pydantic-ai `agent.run_stream()` + `stream_text()` in api/routes/run.py**

Architecture: In `_run_reporter_only()` (and in the `run_reporter` tool in `lead.py` — but `lead.py` is frozen), switch from `reporter_agent.run(...)` to `reporter_agent.run_stream(...)`. Inside the stream loop, call `result.stream_text()` to yield partial text chunks. Emit each chunk as a new SSE event: `event: reporter_chunk\ndata: {"chunk": "..."}\n\n`. On the frontend, `useLiveSession` adds a handler for `reporter_chunk` events, accumulating them into a `draftText` string rendered progressively.

**Feasibility verdict: Blocked by the agent architecture.** The reporter agent uses `output_type=MarketReport`, a Pydantic model. pydantic-ai's `stream_text()` is only available when `output_type=str`. For structured outputs, only `stream_structured()` is available — which yields partially-validated Pydantic objects as fields are filled. Critically, `markdown_content` is a single large string field that won't yield partial tokens; it only appears when the model finishes generating that field. So genuine token-level streaming of the report draft is not achievable without changing the reporter's output type from `MarketReport` to `str`. Since `reporter.py` in `app/` is frozen, and since `MarketReport` is the contract between frontend and backend, this option is only achievable if a new streaming-only API route is created that runs a *separate* text-output reporter agent in the api layer — but that would duplicate agent behavior and violate the spirit of the agent code freeze. **Recommendation: Do not pursue Option A as described.**

**Option B: Post-completion replay — chunk `markdown_content` as SSE events after done**

Architecture: In `_sse_generator()` in `api/routes/run.py`, after all `workflow_event` events are drained and before emitting the `done` event, fetch the completed report from DB, split `markdown_content` into ~50-char chunks, and emit each chunk as `event: reporter_chunk\ndata: {"chunk": "...", "index": N}\n\n` with a small asyncio sleep between them (e.g. `await asyncio.sleep(0.02)`). Then emit `done` normally.

**Feasibility verdict: Highly feasible. This is the recommended approach.** It requires only changes to `api/routes/run.py` (API layer — modifiable). The replay happens entirely server-side. The frontend adds a `reporter_chunk` event listener in `useLiveSession` that builds up `draftMarkdown`. The `ReportDossier` component renders `draftMarkdown` progressively using react-markdown. On page refresh during replay, the session is already `complete` in DB so `useLiveSession` will just fetch the full session immediately — the "streaming" effect is only cosmetic anyway. This is the pragmatically correct approach.

**SSE event additions needed for Option B:**
- New SSE event: `reporter_chunk` (not a `WorkflowEvent` — emitted directly in `_sse_generator` bypassing the WorkflowEvent model)
- New TypeScript type in `web/lib/types.ts`: `ReporterChunkEvent { chunk: string; index: number }`
- New listener in `useLiveSession` and `useRunSession`

**Option C: No streaming — "Reporter synthesizing..." spinner**

Architecture: Show a pulsing "Reporter is synthesizing the dossier..." placeholder in the report panel while `Reporter` agent_start has fired but agent_end has not. No backend changes. No new event types.

**Feasibility verdict: Trivially feasible. The right default if shipping speed matters.** The `PipelineProgress` already distinguishes "active" state for the Reporter stage. The `ReportDossier` component renders a spinner/skeleton when `report === null && reporterActive === true`. This is already achievable with existing event types — detect Reporter's `agent_start` event from the event stream, show placeholder until `done` fires and session re-fetches with report data. **Recommended as MVP; Option B is the right v2 enhancement.**

### Swarm Visualization

The radial SVG graph with `requestAnimationFrame` packet flow animations in React/Next.js is architecturally straightforward but requires careful implementation to avoid performance issues.

**Architecture approach:**

`SwarmTopology.tsx` is a `"use client"` component that receives `events: WorkflowEvent[]` as a prop. The SVG is rendered declaratively in JSX. The `requestAnimationFrame` loop drives packet animation only — it does not re-render the React tree. The approach is:

1. **Static SVG structure:** 5 nodes (Lead, Researcher, Analyst, Reporter, and a "Data Sources" satellite node) rendered as SVG `<circle>` + `<text>` elements. Edges rendered as SVG `<path>` elements (curved arcs using cubic bezier). Positions are fixed in a radial layout around a center point.

2. **Reactive node state:** `events` prop is processed to derive node status (idle/active/done) for each agent. This updates React state via `useMemo`, which drives SVG `fill` and `stroke` attribute changes — standard React re-render, no `requestAnimationFrame` needed here.

3. **Packet flow animation:** When a `tool_call` event fires, a "packet" (small circle) should animate along the edge from the source agent toward the target. This is done with a `useRef` pointing to a `<canvas>` overlay (or a group of SVG `<circle>` elements tracked in a ref array). The `useEffect` sets up a `requestAnimationFrame` loop that updates particle positions directly via DOM manipulation (`particle.setAttribute('cx', ...)`) without touching React state. The loop runs only when `isRunning` is true and tears down cleanly in the `useEffect` cleanup.

4. **Landing page version:** On the landing, a simplified version of `SwarmTopology` runs in "demo mode" with auto-generated random packet flows (no real events) using the same `requestAnimationFrame` particle loop. This is a cosmetic animation — trivially correct because it doesn't need to reflect real data.

**Key technical considerations:**

- Use `will-change: transform` on animated SVG elements to hint the GPU
- Throttle particle count — max ~10 active packets at once to avoid jank
- The SVG viewport should be responsive: use `viewBox` with `preserveAspectRatio="xMidYMid meet"` and a percentage `width`
- For the landing page animation, debounce when the component is off-screen using `IntersectionObserver` to pause the RAF loop

**What to avoid:** Do not use CSS keyframe animations for packet flows — they can't be interrupted mid-flight cleanly when agent state changes. `requestAnimationFrame` with direct DOM updates is the right primitive here.

---

## Files & Components Likely Affected

**New files (frontend):**
- `web/app/query/page.tsx`
- `web/app/run/[id]/page.tsx`
- `web/app/report/[id]/page.tsx`
- `web/components/buzz/SwarmTopology.tsx`
- `web/components/buzz/AgentLog.tsx`
- `web/components/buzz/ReportDossier.tsx`
- `web/components/buzz/KpiPanel.tsx`
- `web/components/buzz/FootnoteDrawer.tsx`
- `web/components/buzz/QueryComposer.tsx`
- `web/components/buzz/SessionsTable.tsx`
- `web/components/buzz/StatusPip.tsx`

**Modified files (frontend):**
- `web/app/layout.tsx` — new nav links, font swap (IBM Plex Sans + JetBrains Mono), dark-body class
- `web/app/globals.css` — dark-only `:root {}` palette, new OKLCH tokens, `--radius: 2px`, status color vars for dark
- `web/app/page.tsx` — full rebuild for animated hero + swarm visualization
- `web/app/run/page.tsx` — becomes a thin redirect shell (calls `startRun()` → redirect to `/run/[id]`), or is removed
- `web/app/sessions/page.tsx` — swap card list for `SessionsTable` component
- `web/app/sessions/[id]/page.tsx` — deprecate (redirect to `/run/[id]` or `/report/[id]`)
- `web/hooks/useRunSession.ts` — add `router.push('/run/' + sessionId)` after session created
- `web/hooks/useLiveSession.ts` — add `reporter_chunk` event handler (if Option B)
- `web/lib/types.ts` — add `reporter_chunk` to event union (if Option B), add `ReporterChunkEvent` type

**Modified files (API layer — if Option B reporter streaming):**
- `api/routes/run.py` — update `_sse_generator()` to replay `markdown_content` as chunked SSE events between workflow events draining and the `done` event

**Unchanged files:**
- `web/lib/api.ts` — no changes needed; all endpoints already correct
- `web/components/ui/*` — keep all shadcn primitives; theme changes are CSS-variable-driven
- All `app/` agent code — zero modifications
- `api/routes/sessions.py` — no changes needed
- `api/database.py`, `api/db_sessions.py` — no changes needed
- `api/stream.py` — no changes needed

---

## Integration Points (Backend Changes Needed)

**Minimal backend changes required for the full redesign. The API surface is already correct.**

**If Option C (spinner only) is chosen:** Zero backend changes. The existing SSE event stream is sufficient.

**If Option B (post-completion replay) is chosen:** One change to `api/routes/run.py`:

In `_sse_generator()`, after the `async for event in ctx.event_generator()` loop completes (i.e., stream is done), fetch the session from DB. If `status == "complete"` and `markdown_content` is populated, split it into ~60-character chunks and emit:

```python
event: reporter_chunk
data: {"chunk": "...", "index": 0, "total": N}
```

with `await asyncio.sleep(0.015)` between each chunk. Then emit the `done` event. This adds roughly `(len(markdown_content) / 60) * 0.015` seconds of delay to the `done` event — for a 5000-word report that is approximately 35-40 seconds. That is too long. A more practical approach is 200-character chunks with 0.005s delay, giving ~15s replay for a typical report, or make the chunk size configurable. **Alternative approach:** Buffer 500 chars per chunk, 0 delay, let the browser rendering create the visual effect — the SSE framing itself provides enough pacing.

**The `reporter_chunk` SSE event is NOT a `WorkflowEvent` and does not need to touch `app/schema.py`.** It is emitted directly from `_sse_generator` as a different event name (`event: reporter_chunk`) without going through `ctx.add_event()`. This is the clean workaround for the `app/schema.py` freeze.

**No database schema changes are needed.** The `sessions` table already stores `markdown_content` inside `report_json`.

**No new API routes are needed.** The existing SSE stream endpoint (`GET /run/{session_id}/stream`) carries both workflow events and the optional reporter chunks.

---

## Technical Risks

**Risk 1: pydantic-ai streaming incompatibility (HIGH for Option A, N/A for B/C)**

The reporter agent's `output_type=MarketReport` is fundamentally incompatible with `stream_text()`. Attempting Option A without changing the reporter to `output_type=str` will fail at runtime. If genuine LLM-token streaming is ever required in the future, it needs a new streaming-reporter agent defined in the API layer (not `app/`) that targets `output_type=str` and then parses the result into `MarketReport`. This is a larger architectural change than it appears.

**Risk 2: `/run` → `/run/[id]` transition — broken bookmarks and in-flight runs**

Any user with the `/run` page open mid-run during deployment will lose state. The new code flow requires a session ID to exist before the run page renders. The transition must be managed: the old `/run` page needs to either redirect to `/query` or remain as a shim that calls `startRun()` and redirects. Consider keeping `/run/page.tsx` as a redirect to `/query` for backward compatibility (external links, browser history).

**Risk 3: SVG animation performance on lower-end hardware**

The `requestAnimationFrame` particle loop combined with React re-renders on event stream updates could cause frame drops if not carefully isolated. The critical rule: RAF particle updates must never call `setState()`. Direct DOM mutation (`element.setAttribute(...)`) is the correct pattern. Testing on CPU-throttled DevTools is essential.

**Risk 4: Tailwind v4 `@theme inline` + radius override**

Setting `--radius: 2px` globally will affect all shadcn components including `Dialog`, `Popover`, `Select` dropdowns. This is intentional per the design spec, but needs visual QA across every component — some may look odd at 2px radius (e.g. `ScrollArea` scrollbar).

**Risk 5: Font swap breaking existing layout metrics**

Replacing Plus Jakarta Sans with IBM Plex Sans and Geist Mono with JetBrains Mono will shift character widths and line heights. The monospace `EventFeed`/`AgentLog` is particularly sensitive — column alignment in the terminal log depends on character width. JetBrains Mono is wider than Geist Mono per character. Test with real event data before finalizing.

**Risk 6: `lucide-react` icon removal (design spec: ASCII/Unicode only)**

The design spec says no external icons. The codebase currently uses `lucide-react` in `QueryForm.tsx`, `PipelineProgress.tsx`, `sessions/page.tsx`, `sessions/[id]/page.tsx`, and `layout.tsx`. Every icon import must be replaced with Unicode/ASCII glyphs. This is a widespread but mechanical change. CI will break if any lucide import remains after the "no icons" rule is enforced via ESLint.

---

## Complexity Assessment

- **Overall:** Complex — primarily due to scope (5 screens, routing restructure, theme migration, new visualization component) rather than any single hard technical problem. No individual piece is irreducible complexity, but there are many coordinated changes.

- **Landing:** Moderate — the animated SVG swarm visualization is the interesting part; the rest is layout work. The RAF animation loop needs careful isolation.

- **Query:** Simple — a new page with a redesigned form. Reuses `getScenarios()`, `startRun()`, and `useRouter()`. The depth selector and token budget UI are new form elements with no backend implications.

- **Run:** Moderate — the routing change from `/run` to `/run/[id]` is surgical and must be done carefully. The page logic itself is simpler than the current `/run/page.tsx` because it delegates everything to `useLiveSession`. The `SwarmTopology` component replaces `PipelineProgress` and is the main new piece.

- **Sessions:** Simple — swap the card list for a dense data table component. All data comes from the existing `getSessions()` call. No new state or hooks.

- **Report:** Moderate — new route, new `ReportDossier` layout with panel cards and footnote drawer. The `MarketReport.sections[]` data model maps cleanly to the panel-card structure. The main work is the CSS layout for the Bloomberg-style multi-column grid and the `FootnoteDrawer` slide-up interaction (framer-motion already available).
