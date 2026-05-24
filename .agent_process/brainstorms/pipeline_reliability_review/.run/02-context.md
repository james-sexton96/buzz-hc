# Step 02: Project Context

**Topic:** Review and expand the `agent_pipeline_tdd_error_handling` requirement — evaluate gaps in a TDD harness + error recovery scope for a multi-agent healthcare market intelligence pipeline.

---

## Project Summary

Buzz-HC is a healthcare market intelligence tool. Users submit a query (e.g., "GLP-1 market size") via a Next.js frontend → FastAPI backend → multi-agent pipeline → SSE-streamed results → Markdown report.

**Stack:** FastAPI + SQLite (aiosqlite) backend, Next.js 16 frontend, pydantic-ai for agent orchestration, Ollama (local) as default LLM provider.

---

## Pipeline Architecture

```
POST /run
  → insert_session(DB)
  → asyncio.create_task(_run_pipeline)
      → lead_agent.run(query, deps=ctx)
          → run_market_access_research  (tool: calls researcher_agent.run())
          → run_analyst_research        (tool: calls analyst_agent.run())
          → run_reporter                (tool: calls reporter_agent.run())
  → GET /run/{id}/stream (SSE)
```

### Key files
- `app/agents/lead.py` — orchestrator agent
- `app/agents/researcher.py` — Market Access agent (tools: tavily_search, clinical_trials, deep_scrape)
- `app/agents/analyst.py` — Data Analyst agent (tools: tavily_search, deep_scrape)
- `app/agents/reporter.py` — Reporter agent (NO tools — synthesis only)
- `app/context.py` — `ResearchContext` dataclass (sync `add_event`)
- `api/stream.py` — `StreamingResearchContext(ResearchContext)` — async `add_event`, SSE queue
- `api/routes/run.py` — POST /run, GET /run/{id}/stream, POST /run/{id}/retry
- `api/db_sessions.py` — insert/mark_complete/mark_error/save_*_checkpoint/update_events
- `app/llm.py` — `OllamaChatModel` (patches null content + newline issues), `get_model()`, `get_retries()`
- `app/history.py` — file-based checkpoint system (legacy, predates DB system)
- `app/schema.py` — all Pydantic models

---

## Critical Bugs Found During Requirement Creation

### Bug 1: `add_event` async/sync mismatch
- `ResearchContext.add_event` is SYNC
- `StreamingResearchContext.add_event` overrides it as ASYNC
- Agents call `ctx.deps.add_event(...)` WITHOUT `await` — they're calling the BASE CLASS sync method
- Result: SSE events from sub-agent tool calls (researcher/analyst) are added to `self.events` list but NOT pushed to the SSE queue and NOT persisted to DB
- The lead agent's tool wrappers DO call `ctx.deps.add_event(...)` and those DO reach the queue (because lead_agent's ctx.deps IS the StreamingResearchContext, and it has `await` in lead's own code... wait, actually lead.py also calls WITHOUT await: `ctx.deps.add_event("agent_start", "Researcher", ...)` — NO await. So lead's events also don't reach the queue!

### Bug 2: `agent_limit` event type not in Literal
- `WorkflowEvent.event_type: Literal["agent_start", "tool_call", "tool_result", "agent_end", "info"]`
- `lead.py` uses `ctx.deps.add_event("agent_limit", ...)` — this is not in the Literal
- This will raise a pydantic ValidationError when this code path is hit

### Bug 3: No reporter retry/error handling
- `run_reporter` in lead_agent has NO try/except — if reporter fails, the entire pipeline fails at the last mile
- Reporter is the most expensive stage (comes after researcher + analyst complete)
- The current requirement only adds retry wrappers to researcher and analyst

### Bug 4: `usage=ctx.usage` shared between lead and reporter
- In `run_reporter` tool: `result = await reporter_agent.run(synthesis_prompt, deps=ctx.deps, usage=ctx.usage, ...)`
- This passes the LEAD agent's usage object to the reporter — could cause double-counting or mutation issues

### Bug 5: No timeout on individual agent runs
- Ollama can hang indefinitely on slow/bad requests
- No `asyncio.wait_for(..., timeout=...)` wrapping any of the three sub-agent calls
- If Ollama hangs, the pipeline hangs forever with no recovery

### Bug 6: `update_events` called on EVERY event
- `StreamingResearchContext.add_event` (async) calls `await update_events(self._session_id, events_json)` every time
- This means a DB write for EVERY single event — could be 20-30 writes per pipeline run
- Under contention this could slow down the SSE stream and add latency

### Bug 7: `_run_reporter_only` skips lead agent
- The retry path for "both checkpoints present" calls `reporter_agent.run()` DIRECTLY, bypassing lead_agent
- This means the reporter doesn't get the orchestrated synthesis prompt that lead_agent constructs
- The `_SYNTHESIS_PROMPT` template is used instead — a separate prompt, not the lead's dynamic synthesis

### Bug 8: Divergent checkpoint systems
- `app/history.py` has `CheckpointSession` with `stage_reached` and `failure_reason` fields
- The DB system (`db_sessions.py`) has no equivalent `stage_reached` column
- The requirement adds `failed_stage` to the DB, but this is reinventing what history.py already modeled

---

## Existing Test Structure

```
tests/
  conftest.py         — temp_db fixture (monkeypatches DB_PATH), async client fixture
  test_api_run.py     — uses patch("api.routes.run._run_pipeline", side_effect=_fake_pipeline)
  test_api_sessions.py
  test_db_sessions.py
  test_schema.py
```

Current tests mock `_run_pipeline` entirely — no agent-level testing at all.

---

## Existing Requirement (what we're evaluating)

```
agent_pipeline_tdd_error_handling — 8 requirements, 7 success criteria, 8 files, complexity: complex

Technical Requirements:
1. Fix add_event async mismatch
2. Per-stage TestModel fixtures
3. Researcher isolation tests
4. Analyst isolation tests
5. Lead agent orchestration tests
6. Retry route tests (4 checkpoint states)
7. Per-stage retry wrapper in lead_agent tools (researcher + analyst only)
8. Structured error context in DB (failed_stage field)

Files: app/context.py, api/stream.py, app/agents/lead.py, api/routes/run.py,
       api/db_sessions.py, api/database.py, tests/test_pipeline_stages.py,
       tests/test_api_run.py
```

---

## What the Requirement Does NOT Cover (potential gaps)

1. Reporter stage error handling (try/except + graceful degradation)
2. `agent_limit` event type bug fix
3. `usage=ctx.usage` sharing issue in reporter
4. Per-agent timeout (asyncio.wait_for)
5. `update_events` write frequency (buffering/debouncing)
6. The `history.py` / DB checkpoint system divergence
7. `_run_reporter_only` synthesis prompt quality (uses template vs lead's dynamic prompt)
8. How the OllamaChatModel newline sanitization interacts with structured output fields
