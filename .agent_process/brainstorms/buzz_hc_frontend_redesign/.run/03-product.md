# Brainstorm: Product Strategist — Buzz HC UI Redesign

## Problem Statement

**Who is the user?** Pharma market access professionals, strategic planners, and commercial analytics teams. They are time-pressured, highly analytical, and accustomed to dense, data-forward tools like Bloomberg Terminal, Veeva Nitro, or IQVIA dashboards. They expect precision, not consumer-app polish.

**What are they trying to do?** Run structured research queries ("What is the payer access landscape for Dupixent in atopic dermatitis?") and get a publication-ready intelligence brief they can forward to a VP or use as briefing input for a launch team.

**Where does the current experience fail them?**

1. **Refresh kills the run.** The `/run` page has no URL ID. If a user navigates away, closes the tab, or refreshes mid-run (which takes several minutes), they lose all context and must rebuild state manually by hunting through `/sessions`. This is the most severe failure — it destroys trust in a tool meant for long-running AI work.

2. **The report appears all at once or not at all.** The reporter agent is a one-shot structured JSON output. During the Reporter phase — which can be the longest phase — the screen shows nothing but a spinner in the event log. There is no sense of the report taking shape. Users cannot tell if the tool is working or hung.

3. **The report is a prose dump, not a dossier.** The current `ReportViewer` renders the `markdown_content` blob as a single scrollable document. The structured `sections[]` data already exists but is ignored. A pharma professional scanning for the payer access table or competitive share estimate cannot find it without reading top to bottom.

4. **Sessions is a search bar over a card list.** A user who runs 20 queries needs to triage them: which finished? which errored? what was the query? how long did it take? The current list view provides no scannable density. A Bloomberg-style dense table would let them manage their research pipeline, not just browse it.

5. **The landing page undersells the tool's intelligence.** The bento grid shows placeholder content and static copy. A user landing cold has no sense of what a real output looks like or how the 4-agent pipeline actually works.

---

## Proposed Approach

### Option 1 (Simplest): Visual Skin + Routing Fix

Scope the redesign to pure front-end changes with one essential routing fix. No API changes.

**What changes:**
- Switch the app to dark mode as default (OKLCH vars exist, just need `dark` class on `<html>`)
- Move `/run` to `/run/[id]` — after `startRun()` resolves, router pushes to `/run/[id]` with the session ID; the new page uses `useLiveSession`, which already handles reconnection. This alone fixes the refresh-persistence bug.
- Redesign the report view as a panel card grid: render `sections[]` as side-by-side Bloomberg-style cards instead of the `markdown_content` prose blob. No schema changes needed.
- Redesign Sessions as a dense data table (shadcn `Table` component): columns for query truncated, status badge, timestamp, event count, duration. Replace the search-and-card-list with pagination.
- Add a "writing..." skeleton animation during the Reporter phase as the minimum viable interactivity — no actual streaming, but the three reporter placeholder cards (with pulsing skeletons) appear as soon as the `agent_start` event fires for the Reporter agent, then fill in when the `done` event resolves.
- Landing page: replace the static bento with a dark hero and a live query ticker (pull from `/sessions` on load; show last 3 queries as typed-out text).

**Trade-offs:**
- Zero API risk. Zero agent code risk. Entirely additive.
- The "streaming draft" is simulated — users will see the skeleton, not actual text appearing. Sophisticated users may find this hollow.
- Does not require any new event types or backend changes.
- Fastest path: an experienced frontend dev could ship this in 1–2 weeks.

---

### Option 2 (Recommended): Routed Screens + Replay Streaming

Build the full 5-screen information architecture and add fake-but-convincing reporter interactivity via post-completion replay.

**What changes (on top of Option 1):**
- Introduce a dedicated `/query` page — a focused full-screen query composer with no distractions. After submission, redirects to `/run/[id]`. The current `/run` page collapses into a loading/transition state, not a permanent URL.
- Introduce a dedicated `/report/[id]` page — the Bloomberg dossier as a standalone route. `/sessions/[id]` redirects here with `?tab=report` or becomes an alias. The report page has a two-column layout: left rail (exec summary + KPI strip), right rail (panel cards per section), footer (sources drawer).
- **Replay streaming for the reporter:** After the `done` event fires and `getSession()` resolves, the frontend chunked-replays `markdown_content` character-by-character (or sentence-by-sentence) into a streaming draft pane that was already visible during the Reporter phase. A 30–50ms per-chunk delay with cursor blink creates genuine interactivity feel. This is implemented entirely in the frontend state machine (`useRunSession`) with no API changes.
- The Run screen becomes a three-zone layout: top-left is the radial agent topology (static SVG with framer-motion activation states driven by `agent_start`/`agent_end` events), top-right is the streaming draft pane (reporter output area with skeleton → replay transition), bottom full-width is the EventFeed (already dark, just needs polish).
- Sessions table adds a "Report ready" column (boolean derived from `status === "complete"`), direct link to `/report/[id]`, and row-level retry action.

**Trade-offs:**
- Still zero API changes. The replay trick is a known product pattern (Notion AI, Linear AI summaries use it).
- The replay is not real token streaming — if a user knows how pydantic-ai works, it reads as a trick. For pharma business users, this does not matter.
- The new `/query` route creates a cleaner mental model but adds a navigation hop before the run starts. Acceptable if the query composer feels focused and intentional.
- The `/report/[id]` route requires a decision on whether `/sessions/[id]` stays or redirects (see Risks).
- Estimated scope: 3–4 weeks for a focused frontend dev.

---

### Option 3 (Ambitious): Genuine Token Streaming + Structured Panel Data

Full build: token-level reporter streaming, structured panel extraction from existing agent data, and a live swarm visualization.

**What changes (on top of Option 2):**
- **Real reporter streaming via API layer only (no agent code changes):** In `api/routes/run.py`, after the reporter agent call resolves, use pydantic-ai's `agent.run_stream()` / `result.stream_text()` API to re-run or emit the `markdown_content` as chunked `reporter_token` SSE events. Alternatively (and more honest), after the reporter finishes, the API emits the `markdown_content` in 100-character chunks as `reporter_chunk` SSE events with 30ms gaps. This requires adding `reporter_chunk` as a new event type — but `app/schema.py` cannot be modified per CLAUDE.md. This is the constraint that forces a decision: either `reporter_chunk` events bypass the `WorkflowEvent` type (emitted as a raw SSE event type not in the enum) or the schema constraint is revisited with the project owner.
- **Structured panel extraction:** The `MarketAccessFindings` and `AnalystFindings` schemas (from `research_json` and `analyst_json` in the session detail) contain rich structured data: `payer_coverage[]`, `competitive_landscape[]`, `market_sizes[]`, `prescription_metrics[]`. These power true Bloomberg-style KPI panels — a payer access table, a competitor share bar chart, a market size figure. No reporter output changes needed; the data comes from the researcher and analyst agents already.
- **Radial swarm topology:** An SVG/Canvas visualization showing 4 nodes (Lead, Researcher, Analyst, Reporter) with animated pulse rings driven by live event stream. Each `agent_start` activates a node; `tool_call` events show a secondary pulse on the active node; `agent_end` dims it.
- **Animated swarm on landing:** The landing hero replaces static copy with a live-animated swarm visualization (a smaller version of the run screen topology) that auto-plays a simulated run on loop.

**Trade-offs:**
- The schema constraint on `app/schema.py` is a real blocker for genuine SSE-level token streaming. Either the constraint is accepted and we use the replay trick (collapsing back to Option 2), or the constraint is formally relaxed for API-layer-only event types.
- Extracting KPI panels from `research_json`/`analyst_json` requires reading `SessionDetail.research_json` and `analyst_json` on the report page — this is already returned by `GET /sessions/{id}` and typed in `web/lib/types.ts`. Pure frontend work.
- The animated swarm visualization is the highest-effort item and the lowest business-value item. It is impressive but does not change what users can do.
- Estimated scope: 6–8 weeks. Risk of scope creep on the visualization feature.

---

## Success Criteria

- [ ] **Refresh survivability:** A user who refreshes the browser mid-run within 5 seconds of the page loading sees the correct running state, with all prior events, without losing their session — verified for sessions started more than 10 seconds ago.
- [ ] **Reporter interactivity:** From the moment the Reporter `agent_start` event fires, users see visible activity in the report draft area within 2 seconds — either a skeleton or actual text appearing — before the pipeline completes.
- [ ] **Report scanability:** A user looking for payer access status or competitive landscape can find the relevant section in under 10 seconds without scrolling through unrelated content — measured by section card headings being visually distinct and above the fold in a two-column layout on 1440px wide viewport.
- [ ] **Sessions triage speed:** A user with 20+ sessions can identify all errored or in-progress sessions within 5 seconds of the page loading — verified by status column visibility without horizontal scroll.
- [ ] **Zero regression on existing functionality:** All 26 Python tests and 3 Jest tests pass. Retry flow, PDF export, and SSE reconnection work after routing changes.
- [ ] **Dark mode is the default:** The Bloomberg terminal aesthetic applies immediately on first load without a mode toggle — confirmed by checking `<html>` class or CSS variable rendering on fresh session.

---

## Risks & Open Questions

**Risk 1: The schema constraint may block genuine streaming.**
`app/schema.py` defines `WorkflowEvent.event_type` as a `Literal[...]` union. Adding `reporter_chunk` would require modifying this file, which CLAUDE.md marks as off-limits ("Agent code in `app/` cannot be modified"). The API layer could emit raw SSE events with a non-`WorkflowEvent` shape, bypassing the type system — but this creates a maintenance inconsistency. Decision needed: is `app/schema.py` truly frozen, or is that constraint specifically about agent logic?

**Risk 2: `/sessions/[id]` vs `/report/[id]` route conflict.**
If both routes exist and render similar content, users will be confused about which URL to share. If `/sessions/[id]` redirects to `/report/[id]`, any existing bookmarks or external links to session detail pages break. Recommendation: keep both routes, but `/sessions/[id]` shows the ops view (events, status, retry) and `/report/[id]` shows the dossier view. The sessions table links to sessions; the run page links to report. Open question: does the user want a unified route or two distinct views?

**Risk 3: Replay streaming feels dishonest at the wrong moment.**
If the report replay starts and the user sees "writing..." but can also see the report already linked in the "Sessions ↗" sidebar, the illusion breaks. The replay trick only works if it is the only way to see the report during the run. This requires gating the report link until the replay completes, which is a design constraint to enforce in the run screen state machine.

**Risk 4: Reporter sections are archetype-driven, not schema-driven.**
The `sections[]` headings (e.g. "Payer Coverage Landscape") are generated by the LLM, not from an enum. A Bloomberg-style dossier that reserves specific panel slots (country mix, payer table, catalysts) assumes predictable section names. If a query produces unexpected section names (e.g. a very narrow query yields only 2 sections with non-standard headings), the panel layout breaks. Mitigation: render section cards dynamically from whatever headings appear — do not hard-code panel positions. The "Bloomberg style" is aesthetic (dark, dense, KPI strip) not structural.

**Risk 5: The `_active_streams` in-memory dict means backend restart loses live streams.**
If the backend restarts mid-run, the SSE stream is gone. `useLiveSession` will reconnect and get the persisted events but the stream is dead — the session stays "running" in the DB forever. This is a pre-existing architectural issue, not introduced by the redesign. But the redesign's persistence promise ("refresh-safe") could create false expectations. The refresh-safe guarantee should be scoped to "browser refresh" not "server restart."

**Open Questions for the User:**
1. Should `/sessions/[id]` redirect to `/report/[id]`, or do both routes serve different audiences?
2. Is `app/schema.py` strictly frozen, or can new SSE event types (emitted only at the API layer) be added without touching agent code?
3. Is the radial swarm visualization a must-have for launch, or a phase-2 feature? (It is the highest-effort, lowest-utility item.)
4. Should the Query page be a standalone route (`/query`) with its own URL, or should it remain embedded in the run flow? A dedicated query route enables linking ("open this query in Buzz HC") but adds a navigation step.
5. What is the target viewport? Bloomberg Terminal users typically run 1440px+ wide on dual monitors. Should the report dossier be optimized for wide viewports or remain max-w-5xl?

---

## Scope Boundaries (Out of Scope)

- **Agent code changes** (`app/agents/`, `app/tools/`, `app/schema.py`, `app/context.py`) — explicitly frozen. Any streaming additions must be purely in `api/` and `web/`.
- **Backend persistence architecture** — the `_active_streams` in-memory dict, aiosqlite connection model, and SQLite schema are not changed by this redesign.
- **PDF export changes** — the existing PDF endpoint (`/run/{id}/pdf`) and `getPdfUrl()` helper are preserved as-is. PDF styling is out of scope.
- **Authentication or multi-user support** — Buzz HC is single-user; no auth layer, user accounts, or permission system is in scope.
- **Mobile responsiveness** — the Bloomberg terminal aesthetic targets desktop. Mobile layout polish is out of scope.
- **New data sources or agent capabilities** — no new tools, no new agents, no changes to what research the pipeline produces.
- **Streamlit UI (`app/ui.py`)** — kept as-is per existing convention. Not deleted, not updated.
- **Query history / saved queries** — the sessions table shows past runs; saving queries as templates or favorites is not in scope.
- **Real-time collaboration** — no multi-user live editing or shared session views.
