# Brainstorm: Buzz HC Bloomberg-Terminal UI/UX Redesign

**Date:** 2026-05-24
**Perspectives:** Product, Architecture, Critical

---

## Problem Statement

Buzz HC's current Next.js frontend underserves its target user — pharma market access professionals running multi-minute, multi-agent research pipelines who expect Bloomberg-grade information density and reliability. Five concrete failures define the gap:

1. **Refresh kills the run.** `/run` has no URL identity. Any browser refresh, tab switch, or accidental navigation mid-pipeline destroys live state. For a tool whose runs take 2–5 minutes, this is the most severe trust-eroding failure.
2. **The reporter phase looks dead.** The reporter is a one-shot structured JSON output, so during what is often the longest phase, the user sees only a spinner. No sense the system is making progress, no visible draft taking shape.
3. **The report is a prose dump, not a dossier.** The current `ReportViewer` renders `markdown_content` as a single scrollable blob. The structured `sections[]` already exists but is ignored, and richer structured data in `research_json` / `analyst_json` is invisible to the user entirely.
4. **Sessions is browse, not triage.** A search-bar-over-cards layout cannot help a user with 20+ runs identify which finished, which errored, and how long each took.
5. **The landing page undersells the product.** Static bento copy gives a cold user no sense of the 4-agent pipeline or what a real output looks like.

The redesign target: a dark, dense, Bloomberg-terminal-meets-modern-AI aesthetic across 5 routed screens (Landing, Query, Run, Sessions, Report), with refresh-safe live runs, visible reporter activity, and a scannable structured dossier — without touching the frozen `app/` agent code.

---

## Proposed Approach

Build all 5 screens in a **tiered implementation** that lands functional improvements first, visual polish second, and the highest-risk items last. Total scope: ~3–5 weeks of focused frontend work, with one small additive change in the `api/` layer.

### Tier 1 — Functional Backbone (must ship first)

- **Route migration to `/run/[id]`.** Create `web/app/run/[id]/page.tsx` wrapping the existing `useLiveSession(id)` hook. After `startRun()` resolves, `useRunSession` calls `router.push('/run/' + sessionId)`. This single change fixes the refresh-loses-state bug — the highest-impact functional improvement in the entire plan.
- **Dark-only theme migration.** Copy the existing `.dark {}` OKLCH palette into `:root {}` in `globals.css`, set `--radius: 2px`, swap fonts to IBM Plex Sans + JetBrains Mono via `next/font/google`, and audit hard-coded `bg-white` / `text-black` / light-only utility classes. Set dark as default with no toggle.
- **Sessions data table.** Replace `web/app/sessions/page.tsx`'s search-and-card list with a shadcn `Table`-based dense view: query (truncated), status pip, timestamp, event count, duration, "Report ready" pip, retry action.
- **Removal of `lucide-react`.** Per the design spec ("ASCII/Unicode glyphs only"), replace lucide imports across `QueryForm.tsx`, `PipelineProgress.tsx`, `sessions/page.tsx`, `sessions/[id]/page.tsx`, and `layout.tsx`.

### Tier 2 — Screen Architecture (the redesign's information architecture)

- **`/query` as a dedicated route.** New `web/app/query/page.tsx` containing the redesigned `QueryComposer` (depth selector, token budget UI, scenario picker). On submit, `startRun()` → redirect to `/run/[id]`.
- **`/run/[id]` three-zone layout.** Top-left: `SwarmTopology` (radial SVG agent graph). Top-right: streaming reporter draft pane (skeleton during reporter phase, fills via Tier-3 replay). Bottom full-width: redesigned `AgentLog` (Bloomberg-style event log).
- **`/report/[id]` as a standalone dossier route.** Two-column layout: left rail (executive summary + KPI strip), right rail (panel cards per `MarketReport.sections[]`), footer slide-up `FootnoteDrawer` for sources. The old `/sessions/[id]` page redirects to `/report/[id]` for completed sessions and `/run/[id]` for in-progress sessions.
- **Landing redesign.** Dark hero, a live "query ticker" pulling the last 3 queries from `/sessions`, and a smaller demo-mode `SwarmTopology` running in a loop. The full animated swarm is Tier 3.

### Tier 3 — High-Risk Polish (defer if schedule slips)

- **Reporter chunked replay (Option B).** In `api/routes/run.py`'s `_sse_generator()`, after the workflow events drain and before emitting `done`, split the completed `markdown_content` into chunks (~200 chars each, ~5ms inter-chunk delay) and emit them as raw `event: reporter_chunk` SSE frames. These events are **not** `WorkflowEvent` instances — they're emitted directly in the generator, bypassing the `app/schema.py` Literal union entirely. Frontend `useLiveSession` adds a `reporter_chunk` listener that accumulates into `draftMarkdown` for progressive render. **Label this clearly in code and the UI as "animated report reveal," not "live streaming."**
- **Full animated swarm.** `SwarmTopology.tsx` with `requestAnimationFrame`-driven packet flow animation along edges between agent nodes, triggered by real `agent_start` / `tool_call` / `agent_end` events. Direct DOM `setAttribute('cx', ...)` mutations only — never `setState` inside the RAF loop. Pause via `IntersectionObserver` when offscreen.
- **Landing hero swarm.** Demo-mode loop variant of `SwarmTopology` with synthetic packet flows.

### Where the agents disagreed — and the decision

**Disagreement 1: Reporter streaming approach.**
Product wants reporter interactivity. Architect confirmed Option A (real pydantic-ai token streaming) is technically blocked because the reporter uses `output_type=MarketReport` — `stream_text()` is unavailable for structured outputs, and `stream_structured()` yields partial JSON, not coherent prose. Critical correctly called the post-completion replay "fake" and warned against misnaming it. **Decision: Ship Option B (post-completion chunked replay) labeled as "animated report reveal" in both code identifiers and UI copy. Real token streaming is a future upgrade path that requires either relaxing the `app/` freeze or adding a separate text-output reporter agent in `api/` (rejected as architecturally unsound for now).**

**Disagreement 2: Bloomberg dossier panel data sources.**
Product's Option 3 proposed using `research_json` / `analyst_json` for KPI panels. Critical identified the load-bearing problem: `MarketReport.sections[]` is just `(heading: str, content: str)` markdown blobs with no structured numeric data. Specific design panels — country mix table, payer access donut with percentages, competitive bar chart, scenario/risk table with probability columns — have **no** data source in the current schema. Two of those four are entirely unbacked. **Decision: Render the report dossier in two layers. (a) Always-available layer: render each `MarketReport.sections[]` entry as a discrete panel card with markdown content — dynamic heading-driven layout, no hard-coded panel slots. (b) Optional enhancement layer: build typed KPI panels (payer coverage donut, competitor bar chart) backed by `research_json.payer_coverage[]` and `analyst_json.competitive_landscape[]` — these fields exist and are already returned by `GET /sessions/{id}`. Panels backed by fields that do not exist (country mix table, scenario/risk probability columns) are dropped from scope entirely.** This is called out as an Open Question for the user — see below.

**Disagreement 3: Scope and timeline.**
Critical estimated 3–5 weeks across multiple sprints; Product's Option 2 estimated 3–4 weeks. All five screens are required per user direction. **Decision: All 5 screens in scope, tiered as above. Tier 1 + Tier 2 in ~3 weeks. Tier 3 (reporter replay + full swarm animation) added if Tier 1/2 land cleanly. Reporter replay is the higher-value Tier-3 item; full swarm animation is lower priority and shippable as polish.**

**Disagreement 4: Is Bloomberg aesthetic right for pharma users?**
Critical raised legitimate concern that pharma researchers use this episodically (one query at a time, read at leisure) — not like Bloomberg traders monitoring live feeds — and the dense dark aesthetic may be team-preference projection. **Decision: User has explicitly requested the Bloomberg aesthetic. Build it. But honor the underlying concern: prioritize legibility (text contrast, font sizing, line-height for the markdown body content within panels) over maximal density. The dossier's panel layout is dense; the panel *content* is readable.**

**Disagreement 5: `/sessions/[id]` route fate.**
Product asked whether it should redirect to `/report/[id]` or coexist. Architect recommended deprecation with a redirect. **Decision: `/sessions/[id]` redirects — to `/run/[id]` if status is `running` or `queued`, to `/report/[id]` if status is `complete` or `error`. This preserves existing bookmarks via redirect and gives each URL a single semantic purpose.**

---

## Success Criteria

- [ ] **Refresh survivability.** A user refreshing the browser at any point during a run (after the first 5 seconds) lands on `/run/[id]` and sees the correct running state with all prior events restored — verified against a session started >10 seconds ago.
- [ ] **Reporter visible activity.** From the moment the Reporter `agent_start` event fires, the report draft area shows visible activity (skeleton or appearing text) within 2 seconds — never just a spinner.
- [ ] **Dossier scanability.** A user looking for the payer access or competitive landscape section can locate the corresponding panel within 10 seconds without scrolling past unrelated content, on a 1440px-wide viewport.
- [ ] **Sessions triage.** A user with 20+ sessions can identify all errored or in-progress sessions within 5 seconds of page load — status column visible without horizontal scroll, sortable by status.
- [ ] **Zero regression.** All 26 Python tests and 3 Jest tests pass. PDF export, retry flow, and SSE reconnection all work after route migration.
- [ ] **Dark default.** Bloomberg aesthetic applied immediately on first load, no toggle, no FOUC.
- [ ] **No `lucide-react` imports remain.** ESLint rule (or grep check in CI) confirms removal.
- [ ] **Empty-state honesty.** Optional KPI panels backed by `research_json`/`analyst_json` render an explicit, designed "data not available for this query" state when fields are `None` — never empty space or stub values.

---

## Technical Assessment

**Overall complexity:** Moderate-to-Complex. No single hard technical problem, but many coordinated changes across routing, theming, components, and one API-layer addition.

**Per-screen complexity:**

| Screen | Complexity | Notes |
|---|---|---|
| Landing | Moderate | Dark layout is simple; demo-mode swarm animation needs RAF isolation |
| Query | Simple | New page wrapping existing `startRun()` and `getScenarios()` |
| Run | Moderate | Route migration is surgical; `SwarmTopology` is the biggest new component |
| Sessions | Simple | Card list → shadcn `Table` swap; no new state |
| Report | Moderate | Two-column dossier layout + dynamic panel cards + footnote drawer; KPI panels add complexity |

### Key Components

**New components (all under `web/components/buzz/`):**

- `SwarmTopology.tsx` — radial SVG agent graph (replaces `PipelineProgress`)
- `AgentLog.tsx` — redesigned Bloomberg-style event feed (replaces `EventFeed`)
- `ReportDossier.tsx` — panel-card report layout (replaces `ReportViewer`)
- `KpiPanel.tsx` — single Bloomberg-style panel card primitive
- `FootnoteDrawer.tsx` — slide-up sources drawer (framer-motion)
- `QueryComposer.tsx` — redesigned query form
- `SessionsTable.tsx` — dense data table
- `StatusPip.tsx` — reusable status indicator with pulse logic

**Reused as-is (logic only):**

- `web/hooks/useLiveSession.ts` — the right primitive for `/run/[id]`; add `reporter_chunk` handler if Tier 3 ships
- `web/hooks/useRunSession.ts` — add `router.push('/run/' + sessionId)` after session start
- `web/lib/api.ts` — all wrappers stay
- `web/lib/types.ts` — extend with `ReporterChunkEvent` (if Tier 3)
- `web/components/ui/*` — shadcn primitives; theme-driven via CSS variables

### Files Likely Affected

**New files (frontend):**
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/query/page.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/run/[id]/page.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/report/[id]/page.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/SwarmTopology.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/AgentLog.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/ReportDossier.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/KpiPanel.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/FootnoteDrawer.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/QueryComposer.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/SessionsTable.tsx`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/components/buzz/StatusPip.tsx`

**Modified files (frontend):**
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/layout.tsx` — nav links, font swap, dark body class
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/globals.css` — dark `:root {}` palette, `--radius: 2px`, OKLCH tokens
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/page.tsx` — landing rebuild
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/run/page.tsx` — converted to redirect shell or removed
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/sessions/page.tsx` — swap to `SessionsTable`
- `/Users/james/Documents/CodeProjects/buzz-hc/web/app/sessions/[id]/page.tsx` — converted to redirect based on status
- `/Users/james/Documents/CodeProjects/buzz-hc/web/hooks/useRunSession.ts` — add `router.push` after session create
- `/Users/james/Documents/CodeProjects/buzz-hc/web/hooks/useLiveSession.ts` — add `reporter_chunk` handler (Tier 3)
- `/Users/james/Documents/CodeProjects/buzz-hc/web/lib/types.ts` — add `ReporterChunkEvent` (Tier 3)

**Modified files (API layer, Tier 3 only):**
- `/Users/james/Documents/CodeProjects/buzz-hc/api/routes/run.py` — extend `_sse_generator()` to emit chunked `reporter_chunk` events post-completion

**Untouched (frozen or unaffected):**
- All `app/` agent code (`app/agents/`, `app/tools/`, `app/schema.py`, `app/context.py`)
- `api/database.py`, `api/db_sessions.py`, `api/stream.py`, `api/routes/sessions.py`
- `web/lib/api.ts`, all `web/components/ui/*` shadcn primitives
- `app/ui.py` (Streamlit fallback preserved)

---

## Risks & Mitigations

**Risk 1: Bloomberg panels backed by missing schema data.**
Critical's core finding: country mix tables and scenario/risk probability columns have no source in `MarketReport`, `MarketAccessFindings`, or `AnalystFindings`. Building empty panels actively looks broken.
*Mitigation:* Render `MarketReport.sections[]` dynamically as panel cards from whatever headings appear — no hard-coded panel slots. Build typed KPI panels only for fields that exist (`payer_coverage[]`, `competitive_landscape[]`). Drop panels with no data source from scope. Designed empty states for optional panels when fields are `None`.

**Risk 2: Reporter replay misnamed as streaming.**
Critical was right: calling post-hoc chunked replay "live streaming" is dishonest.
*Mitigation:* Use the identifier `reporter_chunk` in code (accurate — it's a chunk) but label the user-facing concept "animated report reveal" in copy. Internal docs and component names use `ReplayDraft` or `RevealDraft`, not `StreamDraft`. The progress indicator says "Compiling report…" not "Streaming…".

**Risk 3: `/run` → `/run/[id]` route migration breaks in-flight sessions or external links.**
Any user with the old `/run` page open mid-run during deployment loses state. External bookmarks to `/sessions/[id]` may break.
*Mitigation:* Keep `web/app/run/page.tsx` as a thin redirect to `/query`. Keep `web/app/sessions/[id]/page.tsx` as a status-aware redirect to `/run/[id]` or `/report/[id]`. CI runs the existing Jest + Python suites against the new routes.

**Risk 4: SVG swarm animation performance under live SSE load.**
Critical flagged that the run screen is simultaneously running an SSE connection, React state updates per event, and (proposed) a continuous animation loop. Naive `setState` inside RAF will jank.
*Mitigation:* RAF particle updates use direct DOM `setAttribute` only — never React state. `will-change: transform`, `transform`/`opacity` only (not `left`/`top`). Cap active packets at ~10. Pause via `IntersectionObserver` when offscreen. Defer landing animation to Tier 3 — desktop dev hardware first, lower-end testing before final ship.

**Risk 5: Font swap shifts layout metrics.**
JetBrains Mono is wider per character than Geist Mono; `AgentLog` column alignment depends on character width.
*Mitigation:* QA the agent log with real event data before locking the font. Use explicit `font-feature-settings` for tabular nums. Consider letter-spacing adjustment if column drift is visible.

**Risk 6: `_active_streams` lost on backend restart.**
Pre-existing architectural limitation: in-memory stream tracker means a backend restart mid-run leaves the session as `status='running'` in SQLite forever, with no live stream to reconnect to.
*Mitigation:* Out of scope for this redesign (not introduced by it). But add an explicit "Resume / Retry" affordance in `/run/[id]` when SSE fails to connect for a session that DB says is still running — calling the existing `POST /run/{id}/retry`. Scope the "refresh-safe" claim to *browser* refresh, not server restart.

**Risk 7: 1440px min-width clips on 13" laptops.**
MacBook Air 13" logical width is 1280px — the dossier may horizontally scroll.
*Mitigation:* Design for 1440px primary target but use fluid breakpoints down to ~1280px with denser panel stacking. No mobile support, no horizontal scroll on standard laptop screens.

**Risk 8: Tailwind v4 + shadcn class reconciliation.**
v4's `@theme inline` may conflict with shadcn's CSS variable structure when the OKLCH palette swaps.
*Mitigation:* The `@theme inline` block already maps to shadcn's variable names — single `:root {}` palette swap should cascade. Visual QA every shadcn component (`Dialog`, `Popover`, `Select`, `ScrollArea`) at `--radius: 2px`. Roll back radius for components that look broken at 2px (e.g., scrollbar thumbs).

---

## Scope Boundaries (Out of Scope)

- **Agent code (`app/agents/`, `app/tools/`, `app/schema.py`, `app/context.py`).** Frozen. Any streaming, panel-data, or event-shape additions happen in `api/` or `web/`.
- **Backend persistence architecture.** `_active_streams` in-memory dict, aiosqlite per-operation connection model, and SQLite schema are unchanged.
- **PDF export.** `/run/{id}/pdf` endpoint and `getPdfUrl()` helper preserved as-is. PDF styling out of scope.
- **Authentication / multi-user.** Single-user app remains single-user.
- **Mobile responsiveness.** Desktop-only (1280px+).
- **New data sources or agents.** No new tools, no new agents, no changes to what the pipeline researches or produces.
- **Streamlit UI (`app/ui.py`).** Preserved as fallback per existing convention.
- **Query templates / saved queries / favorites.**
- **Real-time collaboration / shared sessions.**
- **Bloomberg dossier panels for non-existent data.** Country mix table, scenario/risk probability column tables are dropped — the schema has no data for them and inventing it via display-time LLM calls is fragile.
- **Real LLM token streaming for the reporter.** Blocked by `output_type=MarketReport`; deferred to a future spike that decides whether to relax the `app/` freeze or add a separate text-output agent in `api/`.

---

## Open Questions

These need user input before implementation begins. Most have a default that can proceed without explicit answer, but the user should confirm.

1. **Should optional KPI panels (payer coverage donut, competitor bar chart) be in scope, or render those sections as markdown like the rest?** Defaulting to: build the two typed panels for `payer_coverage[]` and `competitive_landscape[]`; render everything else as markdown panel cards. Confirms how much custom panel work to invest.

2. **Are panels backed by non-existent schema fields (country mix, scenario/risk probability) acceptable to drop entirely?** Defaulting to: yes, drop them. Alternative is extending the reporter schema in `app/schema.py` (currently frozen) or generating data at display time (rejected as fragile).

3. **Is the radial swarm visualization required for v1, or shippable as Tier 3 polish?** Defaulting to: Tier 3 — the static `PipelineProgress` replacement (a more attractive linear/staged indicator) is sufficient for Tier 1/2. Full animated swarm is a polish add.

4. **Is "animated report reveal" labeling acceptable, or does the user want this called streaming externally?** Defaulting to: label honestly as "reveal" / "compiling" — Critical's point on this stands. Real streaming is a known future upgrade.

5. **Target hardware confirmation: is 1280px the lowest acceptable viewport?** Defaulting to: yes, 1280px–1440px+. No mobile.

6. **Should `/sessions` retain a public-facing list of all queries, or is it an admin/ops view?** Defaulting to: public-facing for the single-user case — it's the user's own research history. No change to existing GET /sessions endpoint.

---

## Alternative Approaches Considered

**Alt A: Theme-only pass (1–2 days).** Just OKLCH dark palette + font + radius + drop `tw-animate-css`. Delivers ~80% of the "feel" for ~5% of effort. **Rejected because** it doesn't solve the refresh-loses-state bug, doesn't deliver the dossier scanability or sessions triage improvements, and ignores the explicit user requirement for all 5 screens.

**Alt B: Top-3-impact screens only.** Just `/run/[id]` migration + report dossier + sessions table. **Rejected because** user requirement explicitly includes all 5 screens. The tiered approach captures Alt B's prioritization (those 3 land in Tier 1+2) while still delivering the full scope.

**Alt C: Richer SSE events instead of reporter replay.** Add `tool_result` events with structured payloads, percentage progress on `agent_start`/`agent_end`, and a dedicated `reporter_start` event with estimated time. **Partially adopted** — the existing agent_start for Reporter triggers Tier 1's skeleton state, which delivers some of the value. Full event-stream enrichment is deferred but compatible with future work.

**Alt D: Option A — real pydantic-ai token streaming via `agent.run_stream()` / `stream_text()`.** **Rejected** — `output_type=MarketReport` is incompatible with `stream_text()`; `stream_structured()` yields partial JSON, not coherent prose. Implementing real streaming requires either modifying `app/agents/reporter.py` (frozen) or creating a parallel text-output agent in `api/` that duplicates reporter behavior (architecturally unsound, drift risk). Future upgrade path noted.

**Alt E: Extend the schema (`app/schema.py`) to add missing dossier fields.** **Rejected for v1** — the `app/` freeze is in place for a reason, and the missing fields (country mix percentages, scenario probabilities) would require corresponding prompt and agent logic changes. Could be revisited if the user authorizes a controlled schema extension; for now, panels lacking data are dropped, not stubbed.

**Alt F: Cleaner readable layout instead of Bloomberg density.** Critical's challenge that pharma users may prefer Notion/Substack-style readability over Bloomberg density. **Rejected** — user has explicitly requested the Bloomberg aesthetic. Mitigated by prioritizing legibility of body content within the dense panel structure (good contrast, body-text sizing within panels, generous line-height for the markdown rendering inside each card).
