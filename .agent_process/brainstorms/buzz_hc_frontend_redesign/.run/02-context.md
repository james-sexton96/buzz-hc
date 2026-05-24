# Project Context

**Project:** Buzz HC
**Idea:** Bloomberg-terminal UI/UX redesign for 4-agent pharma research swarm

## Project Overview
- Multi-agent pharma market intelligence tool: 4 agents (Lead orchestrator, Researcher, Analyst, Reporter) run in sequence to produce structured market access / competitive landscape reports
- Stack: FastAPI backend (port 8000) with SQLite persistence via aiosqlite; Next.js 16 App Router frontend (port 3000) with TypeScript, Tailwind CSS v4, shadcn/ui components
- Real-time agent activity is streamed to the browser via SSE (Server-Sent Events); events are also written to SQLite so they survive page refresh
- Reporter agent currently outputs a structured `MarketReport` Pydantic model (title, executive_summary, sections[], sources[], markdown_content) — it does NOT stream draft text token by token; the full object arrives in one shot when the agent finishes
- Session persistence is solid: events are written to DB on every `add_event` call, so refresh-safe streaming replay is already partially implemented via `useLiveSession`

## Relevant Context
- The redesign is a "Bloomberg terminal meets modern AI" aesthetic — dark, dense, data-forward, high information density
- 5 target screens: Landing, Query, Run (live agent activity), Sessions table, Report (Bloomberg-style dossier)
- A key requirement is that streaming output persists on page refresh — this is already architecturally supported (events are DB-persisted per-event, `useLiveSession` hook handles reconnection to live streams)
- Reporter agent streaming of draft text is a new requirement — it does not currently exist; the reporter is a one-shot structured JSON output via pydantic-ai, not a streaming text generator
- The design calls for "reporter agents should stream report writing for interactivity" — this would require either (a) switching the reporter to use pydantic-ai's streaming API and emitting partial text tokens as SSE events, or (b) faking streaming by chunking the final markdown into SSE text events after completion
- If reporter output structure needs changes for the new frontend, those specs are needed

## Existing Related Work
- No related requirements docs beyond the template
- Backlog had no UI/frontend items — this is net-new work
- Knowledge base entries are all about agent retry patterns, not UI

## Code Exploration

### Patterns & Conventions
- All pages are `"use client"` React components in Next.js App Router under `web/app/`
- shadcn/ui component library is installed (`components.json` present); components are in `web/components/ui/`
- framer-motion is already installed (v12) and used on the landing page for `initial/animate/whileHover` patterns
- Tailwind CSS v4 (confirmed by `@import "tailwindcss"` and `"tailwindcss": "^4"` in package.json)
- CSS custom properties use OKLCH color space; both light and dark themes are defined
- Font stack: Plus Jakarta Sans (sans), Geist Mono (mono), Lora (serif) — all loaded via `next/font/google`
- The current theme is light with a blue-indigo primary; dark mode vars exist but are not the default
- `tw-animate-css` is installed alongside Tailwind for animation utilities
- API base URL is configured via `NEXT_PUBLIC_API_URL` env var (defaults to localhost:8000)
- Agent code in `app/` is explicitly marked as "NEVER modified" in CLAUDE.md

### Relevant Files
| File | Summary |
|------|---------|
| `web/app/layout.tsx` | Root layout: sticky nav bar, max-w-5xl container, font loading |
| `web/app/page.tsx` | Landing page: hero text + bento grid with framer-motion cards |
| `web/app/run/page.tsx` | Run page: query form + live pipeline progress + event feed + report viewer |
| `web/app/sessions/page.tsx` | Sessions list: search bar + card list with status badges |
| `web/app/sessions/[id]/page.tsx` | Session detail: live-streaming or historical view; uses `useLiveSession` |
| `web/hooks/useRunSession.ts` | SSE state machine for a new run; phase: idle/starting/running/complete/error |
| `web/hooks/useLiveSession.ts` | Hook for watching any session (live or historical); auto-reconnects to running stream |
| `web/lib/types.ts` | All TypeScript types: `WorkflowEvent`, `MarketReport`, `SessionDetail`, `RunState` |
| `web/lib/api.ts` | Typed fetch wrappers for all backend endpoints |
| `web/components/run/EventFeed.tsx` | Monospace terminal-style event log with color-coded event types |
| `web/components/run/PipelineProgress.tsx` | 3-stage progress bar (Researcher → Analyst → Reporter) |
| `web/components/report/ReportViewer.tsx` | Markdown renderer using react-markdown + remark-gfm with prose classes |
| `api/stream.py` | `StreamingResearchContext`: asyncio queue that feeds SSE; events persisted to DB per event |
| `api/routes/run.py` | POST /run, GET /run/{id}/stream, POST /run/{id}/retry endpoints |
| `api/routes/sessions.py` | GET /sessions, GET /sessions/{id} — detail includes research_json and analyst_json |
| `app/agents/reporter.py` | Reporter agent: pydantic-ai Agent with `output_type=MarketReport`; no streaming |
| `app/schema.py` | All Pydantic models: `WorkflowEvent`, `MarketReport`, `ReportSection`, `MarketAccessFindings`, `AnalystFindings` |

### Technical Landscape
- **Framework:** Next.js 16 App Router, React 19, Tailwind CSS v4, shadcn/ui, framer-motion v12
- **Similar Features:** `EventFeed` is already a dark monospace terminal panel (`bg-zinc-950`), which fits the Bloomberg aesthetic — it just needs expansion and styling
- **Integration Points:** 
  - New routes needed: `/` (Landing redesign), `/query` (standalone query screen), `/run/[id]` (replace current `/run` with ID-based routing for persistence), `/sessions` (redesign as a data table), `/report/[id]` (standalone report dossier)
  - `useLiveSession` hook is the right primitive for the persistent run screen — already handles reconnection
  - `MarketReport.sections[]` provides the structured data for a Bloomberg-style dossier layout
- **Constraints:**
  - Agent code (`app/`) cannot be modified — any reporter streaming must be implemented in the API layer
  - The current `/run` page is stateless (no URL ID) — refresh loses state; a route change to `/run/[id]` is needed for persistence requirement
  - pydantic-ai's reporter agent uses `output_type=MarketReport` which means it returns a fully-formed JSON object, not a text stream; adding token-level streaming would require using pydantic-ai's `stream_text` or `stream_structured` API instead
  - `_active_streams` dict in `api/routes/run.py` is in-process only — if the backend restarts, active stream is lost (already a known limitation)

### Current SSE/Streaming Architecture

**Event types emitted** (from `app/schema.py` `WorkflowEvent.event_type` Literal):
- `agent_start` — agent begins (source: "Researcher", "Analyst", "Reporter", "Lead")
- `agent_end` — agent completes
- `tool_call` — agent is calling a tool
- `tool_result` — tool returned a result
- `info` — informational message (e.g. retry notices)
- `agent_limit` — agent hit a timeout, usage limit, or error

**SSE event format** (from `api/routes/run.py`):
```
event: workflow_event
data: {"timestamp":"...","event_type":"agent_start","source":"Researcher","message":"Starting research...","details":null}

event: done
data: {"session_id":"abc123","status":"complete"}
```

**Persistence mechanism:** Every `add_event()` call in `StreamingResearchContext` writes the full events array to `sessions.events_json` via `update_events()`. This means: on page refresh, `GET /sessions/{id}` returns all events so far, plus the client can reconnect to the live SSE stream via `useLiveSession`.

**Draft text streaming — current state:** There are NO streaming draft text events. The reporter agent runs to completion and the report appears in the `done` event → `GET /sessions/{id}` fetch. The report is entirely absent from the event stream.

**Refresh persistence — current state:** Events DO persist across refresh (they're DB-written per event). The report does NOT appear until the pipeline finishes. `useLiveSession` correctly handles the reconnection pattern for a running session.

### Reporter Agent Output Shape

The reporter outputs `MarketReport` (structured JSON, not raw markdown):
```python
class MarketReport(BaseModel):
    title: str                          # e.g. "GLP-1 Agonist Market Access Report 2030"
    executive_summary: str              # 3-paragraph free text
    sections: list[ReportSection]       # [{"heading": "...", "content": "markdown..."}]
    sources: list[str]                  # list of URLs
    markdown_content: str | None        # full report as single markdown string (also populated)
```

The `ReportSection` list structure maps directly to Bloomberg-style "panel" or "card" layout — each section is a named block with markdown content. The reporter is instructed to always populate `markdown_content` as well. Section headings are archetype-driven (e.g. "Payer Coverage Landscape", "Market Size & Growth Forecast", "Competitive Landscape & Market Share", "Gaps & Data Confidence", "Key Takeaways & Implications").

**For the Bloomberg dossier view:** The structured `sections[]` array is ideal for rendering as side-by-side panel cards (unlike a single markdown blob). The `executive_summary` can be a hero/masthead block. `sources[]` feeds a data table. No schema changes are strictly required for a dossier layout — the data is already well-structured.

**For streaming report writing:** To add interactivity during report generation, options are:
1. Use pydantic-ai's `agent.run_stream()` + `result.stream_text()` in `_run_reporter_only`/`run_reporter tool`, emit `reporter_draft` SSE events with partial text chunks — requires API changes only (not agent code), but pydantic-ai streaming API needs verification
2. After reporter completes, replay `markdown_content` as chunked SSE events with artificial delay — simpler but not genuine streaming
3. Add a new `reporter_section` event type that fires when each section is written — would require structured output changes and is harder with pydantic-ai's one-shot output model

### Feasibility Notes

**High feasibility / low risk:**
- Full visual redesign of all 5 screens — pure frontend work on existing routes + components
- Sessions screen as a Bloomberg-style data table — existing `getSessions()` API + `SessionSummary` type are sufficient
- Persistent run page via `/run/[id]` routing — `useLiveSession` already handles this; just needs new route file at `web/app/run/[id]/page.tsx`
- Bloomberg-style report dossier — `MarketReport.sections[]` is already structured; just needs new layout component
- Dark terminal aesthetic for the EventFeed (already dark with zinc-950 background)
- Landing page redesign — pure component work

**Medium feasibility / some work required:**
- "Streaming output persists on page refresh" — architecturally supported, but current `/run` page has no URL-based session ID; requires routing change from `/run` to `/run/[id]`; the run page also currently does not use `useLiveSession`
- Reporter streaming (genuine token streaming) — requires API-layer changes: switch reporter to pydantic-ai streaming API (`agent.run_stream()`), emit partial text as new SSE event type (e.g. `reporter_token` or `reporter_chunk`), add frontend handler in `useRunSession`/`useLiveSession`; must verify pydantic-ai streaming compatibility with current setup

**Potential blockers:**
- pydantic-ai structured output streaming: pydantic-ai's `stream_structured` returns partial objects, not text tokens — streaming meaningful markdown text mid-generation is possible via `stream_text` but requires the model to output text before the JSON wrapper; worth prototyping
- The `_active_streams` in-memory dict means stream is lost on server restart; for production persistence of streaming this is already a limitation (out of scope for UI redesign)
- No `/run/[id]` route exists today — the current `/run` page is stateless; migrating will require care not to break the existing flow
- New SSE event types (e.g. `reporter_chunk`) would need to be added to `EventType` in both `app/schema.py` (the Python schema that CANNOT be modified per CLAUDE.md) and `web/lib/types.ts` — this is a constraint to resolve with project owner if reporter streaming is required
