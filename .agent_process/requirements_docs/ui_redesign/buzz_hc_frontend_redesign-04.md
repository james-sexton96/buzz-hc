---
id: buzz_hc_frontend_redesign-04
type: requirement
category: ui_redesign
status: scoped
priority: HIGH
complexity: complex
split_from: buzz_hc_frontend_redesign
depends_on: [buzz_hc_frontend_redesign-02]
source: ap-brainstorm
---

# Requirements: Bloomberg-Terminal UI Redesign — Part 4: Reporter Token Streaming

**Split from:** `buzz_hc_frontend_redesign` (see `buzz_hc_frontend_redesign-breakdown.md` for full context)

**Prerequisites:** `buzz_hc_frontend_redesign-02` must be complete (Run screen with `useLiveSession` integration and the "Emerging draft" placeholder). Part 3 can be in-progress concurrently.

---

## Objective

Implement real-time reporter token streaming so that the Run screen shows the reporter agent's draft text appearing word-by-word as it is generated, providing interactivity during the longest phase of the pipeline.

## Background

Currently the reporter agent (`app/agents/reporter.py`) produces a fully-structured `MarketReport` pydantic model via pydantic-ai's one-shot structured output (`output_type=MarketReport`). The full report only becomes visible when the pipeline completes — there is nothing to show during the reporter phase.

The user confirmed: real token streaming from the reporter is required, not a post-hoc replay. This means switching the reporter to use pydantic-ai's streaming API, emitting partial text tokens as new SSE events (`reporter_token`) through the `_sse_generator` in `api/routes/run.py`, and accumulating those tokens in the frontend's `useLiveSession` hook for display in the "Emerging draft" panel on the Run screen.

Additionally, this part extends `MarketReport` with structured panel data fields (country mix, payer scenario/risk) to enable the remaining Bloomberg dossier panels from the design, and updates the reporter agent to populate them.

**Important:** Since `app/` is fully modifiable, both `app/schema.py` and `app/agents/reporter.py` can be changed. The `_sse_generator` change in `api/routes/run.py` is the integration point between the agent streaming output and the frontend SSE stream.

---

## Technical Requirements

1. **`MarketReport` schema extension** (`app/schema.py`) — Add structured panel data fields to `MarketReport`:
   ```python
   country_mix: list[CountryMixEntry] | None = None
   scenario_probabilities: list[ScenarioEntry] | None = None
   ```
   New models:
   ```python
   class CountryMixEntry(BaseModel):
       code: str           # 2-letter country code (DE, FR, UK, IT, ES)
       share_2024: float   # % share
       share_2030: float   # % share
       spend_2024: str     # formatted string e.g. "€4.2B"
       spend_2030: str
   
   class ScenarioEntry(BaseModel):
       label: str          # e.g. "Base Case", "Bull Case", "Bear Case"
       probability: float  # 0.0–1.0
       value: str          # formatted e.g. "€18.4B"
       trend: str          # "up" | "down" | "neutral"
   ```
   All new fields are optional (existing saved reports won't break).

2. **Reporter agent streaming** (`app/agents/reporter.py`) — Switch from `agent.run()` to `agent.run_stream()` using pydantic-ai's streaming API. During streaming, emit partial text tokens to the pipeline context. After streaming completes and the full `MarketReport` is assembled, persist it as before. Verify pydantic-ai's `stream_text()` compatibility with `output_type=MarketReport` (may require using `result.stream_text(debounce_by=0.01)` or switching to `output_type=str` with post-hoc JSON parsing).

3. **Reporter instructs LLM to populate new fields** — Update the reporter's system prompt / output instructions to populate `country_mix` and `scenario_probabilities` when data is present in the research/analyst inputs. These fields are optional — the reporter should omit them if data is insufficient rather than hallucinating.

4. **`_sse_generator` extension** (`api/routes/run.py`) — The reporter agent's streaming tokens must reach the SSE stream. Approach: pass a callback or asyncio queue into the reporter that fires on each token chunk; the `_sse_generator` consumes these and yields `event: reporter_token` SSE frames:
   ```
   event: reporter_token
   data: {"chunk": "GLP-1 market", "token_index": 42}
   ```
   These frames are emitted DURING the pipeline run (not post-completion). The `done` frame is still the last frame. Existing `workflow_event` frames are not affected.

5. **`useLiveSession` extension** (`web/hooks/useLiveSession.ts`) — Add a `reporter_token` event listener on the existing `EventSource`. Accumulate chunks into a `draftText` state field (append `chunk` strings in order). Expose `draftText` from the hook. Do NOT create a second `EventSource`.

6. **`StreamingDraft` component** (`web/components/buzz/StreamingDraft.tsx`) — Renders the accumulated draft text in the Run screen's center column "Emerging draft" panel. Shows streaming cursor (8×14 cyan rectangle, `@keyframes blink`, 0.8s steps(2)) while `status === 'running'`. Freezes text (no cursor) on `complete`/`error`/`paused`. Renders citation marks `[N]` as cyan `<sup>` elements. Replaces the placeholder from Part 2.

7. **Run screen wiring** (`web/app/run/[id]/page.tsx`) — Connect `draftText` from `useLiveSession` to `StreamingDraft`. Show "Compiling report…" placeholder text in `StreamingDraft` when `status === 'running'` but `draftText` is empty (reporter not yet started). Show a `SectionLabel` status indicator: `↻ streaming…` (running), `⏸ paused`, `✓ finalized` (complete), `✕ truncated` (error).

8. **Country mix panel** (`web/app/report/[id]/page.tsx`) — Render `CountryMixEntry[]` as a 2-col panel: left = 5 EU5 country rows with stacked mini-bar chart (share24 → share30 delta), right = analyst commentary from the corresponding section. Only render when `country_mix` is non-null and non-empty.

9. **Scenario/risk panel** — Render `ScenarioEntry[]` as a scenario table: 4 rows (label + probability % in color + value). Only render when `scenario_probabilities` is non-null.

10. **Persistence of draft tokens** — `reporter_token` events are persisted via the existing event-persistence mechanism only if they are also written through `ctx.add_event()`. Decision: do NOT persist individual token events (they're high-frequency and would bloat `events_json`). Instead, persist the final `markdown_content` (already done via `mark_complete`). On refresh during reporter streaming, the draft text is lost — acceptable because `useLiveSession` will reconnect to the live SSE stream and receive subsequent tokens. This is a known limitation: only tokens emitted after reconnect will appear.

11. **Tests** — Add at least one Python test asserting that when a run completes, `reporter_token` SSE frames are emitted during the reporter phase and the final `done` frame still fires. Test that existing `workflow_event` frames are not affected.

---

## Success Criteria

- [ ] During an active run's reporter phase, the Run screen shows draft text appearing word-by-word in the "Emerging draft" panel
- [ ] Streaming cursor (blinking cyan rectangle) is visible while `status === 'running'` and reporter is streaming
- [ ] Draft text freezes with "✓ finalized" status when run completes; full report appears in `/report/[id]`
- [ ] Refreshing the Run page during reporter streaming reconnects to the live SSE and resumes receiving tokens (tokens before reconnect are lost — acceptable per spec)
- [ ] `MarketReport` schema extension is backwards-compatible: existing completed sessions load without error in `/report/[id]`
- [ ] Country mix panel renders correctly for a real GLP-1 or similar pharma query that produces country data
- [ ] Scenario/risk panel renders correctly when data is present
- [ ] All 26 Python tests pass; new `reporter_token` SSE test added and green
- [ ] `nextjs-build` CI passes; 3 existing Jest tests green

---

## Files Expected to Change

**Modified:**
- `app/schema.py` — `MarketReport` extension + new models
- `app/agents/reporter.py` — streaming mode + structured field population
- `api/routes/run.py` — `_sse_generator` extension for `reporter_token` events
- `web/hooks/useLiveSession.ts` — `reporter_token` event listener + `draftText` state
- `web/app/run/[id]/page.tsx` — wire `draftText` to `StreamingDraft`
- `web/app/report/[id]/page.tsx` — add country mix + scenario panels
- `web/lib/types.ts` — `CountryMixEntry`, `ScenarioEntry`, `reporter_token` event type

**New:**
- `web/components/buzz/StreamingDraft.tsx`
- `tests/test_reporter_streaming.py`

**Estimated:** 9 files

---

## Out of Scope

- Persisting draft token text for replay on browser refresh (high storage cost, low value — token events are not written to DB)
- Pause/resume at the token-streaming level (pausing the run stops token emission; no special handling needed)
- Streaming during research or analyst phases (only reporter phase has streaming text output)
- Mobile optimization

---

## Known Risks

- **pydantic-ai streaming + structured output compatibility** — `agent.run_stream()` with `output_type=MarketReport` may not directly support `stream_text()` (which works on text output types). May require: (a) switching reporter to `output_type=str` and parsing the JSON from the streamed text post-hoc, or (b) using `result.stream_structured()` with partial `MarketReport` object updates. Research pydantic-ai docs before starting. **This is the highest technical risk in the entire redesign.**
- **Token ordering at high concurrency** — asyncio queue approach for passing tokens from reporter to `_sse_generator` must handle backpressure if frontend is slow. Use bounded asyncio.Queue with discard-on-full as the fallback.
- **Reporter system prompt drift** — Asking the reporter to populate `country_mix` and `scenario_probabilities` may cause hallucination if the underlying research/analyst data doesn't contain country-level breakdown. System prompt must emphasize: populate only from provided data, not from LLM knowledge.
- **Draft token persistence gap** — Tokens emitted before a browser refresh are lost. This is accepted behavior but should be documented in UI copy ("Reconnected — showing new tokens only").
- **Schema migration for existing sessions** — `country_mix` and `scenario_probabilities` are optional fields on `MarketReport`. Existing serialized `report_json` in SQLite will deserialize correctly (fields default to `None`). No DB migration needed — verify with a test that loads an old session.

---

## Notes

### Brainstorm Source
- **Brainstorm doc:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
- **Date:** 2026-05-24

### Feasibility Review Key Findings
- `_sse_generator` schema bypass VERIFIED: raw SSE yield without WorkflowEvent wrapper is feasible
- `app/` is confirmed fully modifiable by user (overrides MEMORY.md "NEVER modified" note)
- pydantic-ai streaming compatibility with structured output is the PRIMARY UNKNOWN — must prototype before committing
- `reporter_token` events should NOT be persisted individually (high frequency, storage cost)

### Critical Pre-Work
Before beginning implementation, prototype pydantic-ai streaming with `output_type=MarketReport` in isolation. If `stream_text()` is not compatible, evaluate the `output_type=str` + post-hoc parse approach and update this requirement accordingly.

---
*Part 4 of 4 from `buzz_hc_frontend_redesign`. See breakdown file for complete context.*
