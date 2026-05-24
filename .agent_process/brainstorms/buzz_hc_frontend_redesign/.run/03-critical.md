# Brainstorm: Devil's Advocate — Buzz HC UI Redesign

## Assumption Check

### 1. "MarketReport.sections[] is sufficient for Bloomberg dossier panels" — FALSE

This is the single most broken assumption in the plan. The Bloomberg dossier concept requires panels with structured numeric data: a country mix table (country codes + percentages), a payer access donut (segment + share), a competitive bar chart (competitor + TRx/NBRx volume), a catalysts grid, a scenario/risk table with probability columns.

`MarketReport.sections[]` is a list of `ReportSection` objects, each with a `heading: str` and `content: str` (markdown blob). There are no numeric fields, no typed data objects, no percentages, no country codes. The rich structured data — payer coverage entries, competitor TRx, market size estimates, HEOR findings — lives in `MarketAccessFindings` and `AnalystFindings`, which are stored as `research_json` and `analyst_json` checkpoint columns in SQLite. They are NOT part of `MarketReport` at all.

To render Bloomberg panels, the frontend would need to:
- Parse `research_json` → `MarketAccessFindings` (payer coverage, care delivery, HEOR)
- Parse `analyst_json` → `AnalystFindings` (market sizes, competitors, prescription metrics)
- Map those to panel-specific data models

Both fields are already returned by `GET /sessions/{id}` (see `api/routes/sessions.py`), so the raw data is accessible. But the frontend would need bespoke panel components for each data shape, and the LLM doesn't always populate all optional fields (most are `None`-defaulted), so panels could silently render empty or with stub values.

### 2. "Reporter streaming is worth the effort" — UNPROVEN

Reporter streaming requires changing how pydantic-ai's `Agent` with `output_type=MarketReport` runs. Today, `reporter_agent.run()` returns a fully formed, validated `MarketReport` object. Switching to streaming requires using pydantic-ai's `agent.run_stream()` or `stream_text()`, which either:
- (a) Streams partial structured output tokens — but pydantic-ai's structured output streaming is partial JSON, not readable prose
- (b) Switches to a text-mode agent that streams prose, then you lose the structured `MarketReport` validation entirely

Option (b) — simulating streaming by chunking the completed `markdown_content` field into SSE tokens after the reporter finishes — is possible without touching `app/` code. It's essentially fake streaming done at the API layer in `api/routes/run.py`. It would feel responsive but provides no actual interactivity benefit if the report is already done. Users would wait the full reporter runtime and then watch the text "type out."

Real streaming (actual token-by-token output during reporter inference) requires modifying `app/agents/reporter.py`, which the "NEVER modify app/" constraint prohibits. The constraint exists for a reason; working around it in the API layer adds fragility.

### 3. "Users want a dense Bloomberg terminal aesthetic" — UNVALIDATED

Bloomberg terminal aesthetics are optimized for professional traders who live in the interface 8+ hours a day and have memorized the layouts. Pharma market access researchers use the tool episodically: they submit a query, wait 2-5 minutes for the pipeline to finish, then read the report. They are not monitoring live blinking data feeds.

The high-density dark aesthetic creates cognitive load that is appropriate when data changes constantly and every millisecond matters. For a report that runs once and is read at leisure, a cleaner, readable report view (even a well-typeset PDF-style layout) likely serves the use case better. There is zero user research evidence cited that the target persona prefers Bloomberg density over, say, a well-structured McKinsey-style report layout.

The risk is that "Bloomberg terminal" is a developer team aesthetic preference being projected onto pharma users who may find it intimidating or hard to read.

### 4. "The swarm visualization adds value vs. being decoration" — LIKELY DECORATION

An animated SVG swarm on the landing screen and a "swarm topology" diagram on the run screen are explicitly called out in the plan. The swarm topology during an active run is the riskiest: it runs JS animations alongside an active SSE connection, alongside asyncio event writes to SQLite. On a slow machine or constrained browser, this is three competing asynchronous processes.

More fundamentally: what does a user learn from watching dots animate between "Researcher," "Analyst," "Reporter" nodes that they don't already learn from the existing 3-stage `PipelineProgress` component? The existing progress bar already communicates which agent is active. The topology diagram would be isomorphic information in a more expensive rendering format.

The landing page swarm animation is pure visual branding and carries no functional information — this is acceptable if the cost is low and render performance is acceptable, but it still needs a performance budget.

---

## Alternative Approaches

### Alt A: Theme-only pass (1-2 days)

Change `globals.css` CSS custom properties to the OKLCH dark palette. Swap `Plus Jakarta Sans` + `Geist Mono` for `IBM Plex Sans` + `JetBrains Mono`. Add `2px` border-radius overrides. Drop `tw-animate-css` for a stripped-down motion config. Set dark mode as the forced default.

This delivers 80% of the "feel" of the Bloomberg redesign with roughly 5% of the effort. The existing `EventFeed` is already `bg-zinc-950` monospace — it would fit natively in a dark terminal theme. No new routes, no new components, no streaming protocol changes, no CI risk.

The only thing this doesn't deliver: new route structure for persistence (`/run/[id]`), the Bloomberg panel layout for the report, and the swarm animations. Those are the genuinely novel parts of the plan.

### Alt B: 2-3 highest-value screens only

Priority ranking by impact vs. effort:

1. `/run/[id]` migration (HIGH value, MEDIUM effort): Adding URL-based routing to the run screen solves the "refresh loses state" complaint immediately. The SSE reconnection logic via `useLiveSession` already exists. This is the most impactful functional change in the entire plan.
2. Report dossier redesign using `research_json`/`analyst_json` panels (HIGH value, HIGH effort): This is the most visually distinctive part of the redesign and the hardest to build. But it uses data that's already in the DB — no backend changes needed beyond confirming the fields are returned in the session detail response (they are).
3. Sessions data table (MEDIUM value, LOW effort): Replace the current card list with a shadcn/ui `DataTable`. This is a contained component swap with no backend changes.

Defer: Landing SVG swarm animation, Query as a separate screen, reporter streaming.

### Alt C: Improve event stream richness instead of streaming reporter output

Instead of adding reporter draft text streaming (which requires either violating the `app/` constraint or doing fake post-hoc streaming), add richer SSE events for existing pipeline stages. Examples:
- Emit a `tool_result` event with structured data when `save_research_checkpoint` fires
- Add a progress percentage field to `agent_start`/`agent_end` events
- Emit a dedicated `reporter_start` event with an estimated completion time

This makes the event feed more informative without touching `app/` code, at a much lower risk profile than reporter streaming. The `StreamingResearchContext.add_event()` call in `api/stream.py` can emit additional synthetic events.

---

## Failure Modes

### Failure Mode 1: Scope explosion kills the sprint

Five screens + new routes + animations + streaming protocol changes + Bloomberg panel data mapping is a multi-sprint project being scoped as one sprint. Historical pattern: designs with 5 interconnected screens where any one screen's data contract is unresolved tend to stall at screen 3 when the data reality doesn't match the mockup.

The specific stall point here will be the Bloomberg report dossier panels. The design calls for a "country mix table," a "payer access donut," a "competitive bar chart," and a "scenario/risk table." These require:
- Country codes and percentage shares (not in current schema)
- Donut chart segments (payer coverage entries exist in `MarketAccessFindings.payer_coverage[]` — this one IS achievable)
- Bar chart competitor volume (exists in `AnalystFindings.competitive_landscape[]` with optional `trx_weekly`/`nbrx_weekly`)
- Scenario/risk table with probability columns (DOES NOT EXIST anywhere in the current schema)

Two of the four Bloomberg panels have no data source in the current schema. Building placeholder panels that render "data not available" in 50% of real runs is not a Bloomberg terminal — it's a broken Bloomberg terminal.

### Failure Mode 2: pydantic-ai streaming conflicts with structured output

If the team decides to implement real reporter streaming (not the fake post-hoc version), they'll hit a hard wall: pydantic-ai agents with `output_type=MarketReport` cannot natively stream validated Pydantic model instances token by token. The `run_stream()` API in pydantic-ai returns a `StreamedRunResult` that emits partial `str` or partial structured deltas, but partial structured output is streamed as raw JSON fragments, not as coherent prose sentences. The UI cannot display partial JSON as readable report text.

Workarounds:
- Use `stream_text()` instead of `run_stream()` — but this requires a text-output agent, losing structured output validation. The `MarketReport` would then need to be parsed from the streamed text via a second pass, which is fragile.
- Use `markdown_content` field streaming: if the reporter always populates `markdown_content`, stream that field's value using pydantic-ai's partial structured output streaming. This is theoretically possible but requires deep pydantic-ai internals knowledge and is not documented as a first-class use case.
- Fake streaming via post-hoc chunking: viable, but then you're not streaming — you're simulating it, and users can tell the difference (no partial sentences, no "thinking" feel, just text appearing at reading speed after a delay).

### Failure Mode 3: SVG swarm animation degrades run-screen performance

The run screen during an active pipeline is already doing:
- One open SSE EventSource connection delivering events every few seconds
- React state updates on every event (appending to `events[]` array)
- Per-event SQLite writes in the backend (aiosqlite, per-operation open/close)

Adding a continuous CSS/SVG animation to this screen means the browser is running layout/paint on every animation frame (60fps) while also processing SSE message events. If the animation is not GPU-compositor-only (i.e., it animates `left/top/width/height` instead of `transform/opacity`), this will cause visible jank on the SSE event feed, particularly on lower-end hardware.

The 1440px min-width desktop constraint helps (no mobile to worry about), but it does not eliminate the risk of poorly composited animations blocking the main thread.

### Failure Mode 4: Route migration breaks CI

Moving from `/run` (stateless) to `/run/[id]` (dynamic) requires:
1. Deleting or converting `web/app/run/page.tsx`
2. Creating `web/app/run/[id]/page.tsx`
3. Updating all internal links (`/run` → `/run/[id]`)
4. Updating `useRunSession` to redirect to `/run/{session_id}` after `POST /run` returns

If any step is incomplete, `nextjs-build` will fail (CI required check). The build failure is catchable in PR CI, but a partial migration that passes build can still break the user experience (e.g., SSE reconnection not wired to the new route, or the old `/run` route left as a zombie with no state).

### Failure Mode 5: `_active_streams` lost on backend restart mid-design

The plan states "streaming output persists on page refresh" as a key requirement. This is only partially true. Events persist because `update_events()` writes to SQLite on every `add_event()` call. But the live SSE stream is driven by `_active_streams` — an in-memory dict in `api/routes/run.py`.

If the backend process restarts during an active run (deploy, crash, OOM, `uvicorn --reload` file watch), `_active_streams` is empty. The run task is also gone. The session stays in `status='running'` in SQLite forever unless manually fixed. The new frontend's "reconnect to live stream" feature will hit a 404 on `GET /run/{id}/stream` and have no recovery path beyond showing the historical events and a "connection lost" error.

The design should explicitly decide: is a dead-stream session recoverable? The existing retry mechanism (`POST /run/{id}/retry`) handles this case at the API level, but the frontend needs explicit UI for it — a "Resume" button on a stuck running session, not just an error state.

---

## Dependencies & Blockers

### Blocker 1: "NEVER modify app/" vs. reporter streaming

The app/ constraint is the most significant architectural constraint in this project. Reporter streaming (real or fake) requires either:
- (a) Touching `app/agents/reporter.py` — prohibited
- (b) Doing post-hoc fake streaming in `api/routes/run.py` after `reporter_agent.run()` completes — permitted but misleading

If fake streaming is used, the design specification should not describe this as "streaming report writing." It should be described as "animated report reveal" — which is a lower-value feature and may not justify the API-layer complexity.

### Blocker 2: Bloomberg panels require data that doesn't exist

A "country mix table" with country codes and percentages has no data source in `MarketAccessFindings`, `AnalystFindings`, or `MarketReport`. The schema would need to be extended — which means either modifying `app/schema.py` (touching app/) or adding a new schema file in `api/` that the reporter agent populates via a new API-layer prompt. The latter is architecturally unsound and would produce inconsistent results.

A "scenario/risk table with probability columns" similarly has no data source. It would need to be LLM-generated at report display time, or parsed from the markdown `content` field of specific sections using regex — both fragile approaches.

### Blocker 3: IBM Plex Sans + JetBrains Mono licensing/availability on Google Fonts

The design calls for IBM Plex Sans and JetBrains Mono. Both are available on Google Fonts via `next/font/google`. However, these fonts have notably different metrics from the current `Plus Jakarta Sans` + `Geist Mono` stack, meaning existing spacing, line heights, and component layouts will shift visually after font swap. Every component needs visual QA after font change.

### Blocker 4: Tailwind v4 + shadcn/ui class naming

The project is on Tailwind v4 (confirmed by `@import "tailwindcss"` and `"tailwindcss": "^4"` in package.json). Some shadcn/ui components ship with Tailwind v3 class names that need manual migration when using v4. The OKLCH theme is also a Tailwind v4 native feature (v3 required plugins). If the CSS custom property redesign conflicts with shadcn/ui's default CSS variable structure, component theming will need careful manual reconciliation. This is known but time-consuming.

### Blocker 5: 1440px min-width decision

A hard 1440px minimum width makes this explicitly a desktop-only app. This is a valid constraint, but it should be a deliberate product decision, not a design default. If pharma researchers access this on laptops (13" or 14" screens at standard DPI), horizontal scrolling will occur. Standard MacBook Pro 14" at native resolution is 1512px logical width — just barely adequate. MacBook Air 13" M-series is 1280px logical width — this will clip. The constraint should be validated against the target hardware before locking it in.

---

## Honest Assessment

### Is this a one-sprint or multi-sprint effort?

Multi-sprint. Here is a realistic breakdown:

**Sprint 1 (1 week, achievable):**
- Dark OKLCH theme migration + font swap (global CSS + visual QA)
- `/run/[id]` route migration (URL-based session routing + SSE reconnection)
- Sessions `DataTable` component (replace card list)

**Sprint 2 (1-2 weeks, harder):**
- Landing page redesign (animated SVG is optional; static dark hero is fine)
- `/query` as a standalone screen (low functional value — consider skipping)
- Report dossier with panels sourced from `research_json`/`analyst_json` checkpoint data

**Sprint 3 (1-2 weeks, highest risk):**
- Bloomberg panel components that require schema extensions (country mix, scenario/risk table)
- Reporter fake streaming (if decided)
- Swarm topology visualization on run screen

Total: 3-5 weeks of focused frontend work, assuming no backend schema changes. If Bloomberg panels require schema changes, add 1-2 weeks for backend + integration.

### What is the risk of a partially complete redesign?

High, specifically on the report dossier. The run screen with a partial Bloomberg aesthetic is coherent — it still works. A Bloomberg dossier with 2 of 4 panels empty (because the schema data doesn't exist) actively looks broken. Shipping a "Bloomberg-style" report screen that shows empty chart panels for most queries is worse than shipping the current `ReportViewer` markdown renderer, which at least always has content.

The risk mitigation is: implement the report dossier panels only for data that ALWAYS exists in the schema (executive summary, sources, event log), and treat panels backed by optional fields (competitor charts, payer donuts) as progressive enhancements with explicit "data not available" empty states that are visually designed — not just blank space.

### Is "Bloomberg terminal" the right UX for pharma researchers?

Probably not for the full Bloomberg aesthetic. Pharma researchers producing market access reports value:
1. Legibility of dense text (clinical notes, payer policies, regulatory language)
2. Easy citation-tracing (what source backs this claim)
3. Exportability (PDF, Word, slide-ready formats)
4. Confidence signals (source quality, data freshness indicators)

Bloomberg terminal is optimized for speed, pattern recognition across live feeds, and muscle-memory keyboard shortcuts. None of those are the primary pharma researcher use case. The actual use case is closer to a Notion/Substack reading experience on the report screen, and a structured data explorer for the checkpoint findings.

The current `ReportViewer` (react-markdown + prose classes) actually serves the legibility use case reasonably well. The dark theme + dense layout could work for a power-user aesthetic, but it should be tested against real pharma users before being locked as the production aesthetic.

The swarm topology and animated landing are clearly team-preference features. They're fine to ship as polish, but they should not drive architecture decisions or be on the critical path.

### Recommended approach

Do not scope all 5 screens in one sprint. Prioritize in this order:

1. **`/run/[id]` route migration** — solves a real functional problem (refresh loses state), low risk, uses existing `useLiveSession` primitive
2. **Dark theme pass** — highest visual impact for lowest effort, validates the aesthetic direction before committing to Bloomberg-density layouts
3. **Report dossier using existing checkpoint data** — build only panels backed by fields that reliably populate; use graceful empty states for the rest
4. **Defer reporter streaming** — fake streaming is low value; real streaming violates app/ constraints; move this to a future spike
5. **Defer swarm animation** — pure decoration, non-zero performance risk, should be validated against the redesign theme before building

The plan as written is a coherent vision. The data contract gap between `MarketReport.sections[]` and the Bloomberg panel designs is the single biggest risk and should be resolved in design before any code is written for the report screen.
