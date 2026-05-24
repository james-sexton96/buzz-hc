---
id: agent_pipeline_tdd_error_handling
type: requirement
category: agent_pipeline
status: approved
priority: high
complexity: complex
---

# Requirements: Pipeline TDD Harness and Error Recovery

---

## Objective

Fix live crash bugs in the pipeline's error-handling paths, build a fast TDD harness that exercises each pipeline stage in isolation with mock models, and implement robust per-stage error handling so that individual agent failures trigger targeted retries or checkpoint-based restarts rather than killing the whole run.

## Background

The current agentic pipeline (researcher → analyst → reporter, orchestrated by lead_agent) runs against a slow local Ollama model. When any stage fails — due to a model producing invalid JSON, a tool call timeout, a usage limit, or an unexpected exception — the entire long-running pipeline fails and the session is marked as error with no recovery path beyond a full restart.

Several compounding problems exist today:

1. **`add_event` async/sync mismatch**: `StreamingResearchContext.add_event` is `async` but all call sites in `lead.py`, `researcher.py`, `analyst.py` call it without `await`, silently dispatching to the base-class sync method. SSE events from sub-agent tool calls never reach the SSE queue or DB.

2. **`agent_limit` event type crash** *(live production bug)*: `WorkflowEvent.event_type` is a Literal that does NOT include `"agent_limit"`, but `lead.py` emits that string when a sub-agent hits `UsageLimitExceeded`. This causes a pydantic `ValidationError` on the graceful-degradation path — the designed fallback crashes instead of protecting the user.

3. **Reporter has no error handling** *(highest-value crash)*: `run_reporter` in `lead_agent` has no `try/except`. After 7+ minutes of successful researcher and analyst work, a reporter failure propagates uncaught, marking the entire session as `error` with no recovery path and no checkpoint saved.

4. **No per-agent timeouts**: Ollama can hang indefinitely. There is no `asyncio.wait_for` timeout on any of the three sub-agent calls. A hung Ollama request stalls the pipeline forever and orphans the background task in `_active_streams`.

5. **No fast test path for individual agents**: Every test that exercises the full pipeline requires mocking `_run_pipeline` entirely. There is no way to test a single agent in isolation.

6. **Retry route untested for partial checkpoints**: The `/retry` endpoint has four distinct states (no checkpoints / research only / analyst only / both) but only the happy path is tested.

**Implementation phasing:**
- **Phase A (iteration_01)**: Fix crash bugs first (items 1–4 above) with smoke tests. Restore the developer's observable feedback loop before building the full harness.
- **Phase B (iteration_02)**: Full TDD harness — per-agent TestModel/FunctionModel fixtures, retry matrix tests, orchestration tests.

---

## Technical Requirements

### Phase A — Crash Bug Fixes

1. **Fix `agent_limit` event type** *(schema.py)*: Add `"agent_limit"` to `WorkflowEvent.event_type` Literal so `lead.py`'s limit-exceeded fallback path does not raise a ValidationError. All agents' calls to `ctx.deps.add_event("agent_limit", ...)` must produce valid events.

2. **Fix `add_event` async/sync — await-everywhere**: Make `ResearchContext.add_event` an `async def` (no-op coroutine that appends to `self.events`). `StreamingResearchContext` keeps its async override. ALL call sites in `lead.py`, `researcher.py`, `analyst.py`, and `reporter.py` must prepend `await`. This is mechanical and grep-verifiable: `grep -n "ctx.deps.add_event\|ctx.add_event"` should find every site.

3. **Add reporter error handling**: `run_reporter` in `lead_agent` must get a `try/except` block mirroring the existing `run_market_access_research` and `run_analyst_research` pattern. On exception, return a minimal `MarketReport(title="Reporter failed", executive_summary=f"Error: {exc}", sections=[], sources=[])` and record `failed_stage='reporter'`. The pipeline must continue to `mark_complete` (with the degraded report) rather than propagating the exception.

4. **Per-agent timeout** *(env-configurable)*: Wrap each of the three sub-agent calls in `lead_agent` tools with `asyncio.wait_for(..., timeout=float(os.environ.get("AGENT_TIMEOUT", "120")))`. On `asyncio.TimeoutError`, treat as an error for that stage (return `LimitedXFindings` for researcher/analyst, degrade gracefully for reporter) and record `failed_stage` + `"timeout"` in the error message.

### Phase B — TDD Harness

5. **Per-stage test fixtures using `FunctionModel`**: Create `tests/test_pipeline_stages.py` with fixtures that wire each agent (`researcher_agent`, `analyst_agent`, `reporter_agent`, `lead_agent`) to a pydantic-ai `FunctionModel` (or `TestModel`) returning deterministic structured output. Tests must NOT require Ollama. Assert on DB state and event list contents, not on pydantic-ai internals (version-resilient).

6. **Researcher agent isolation tests**: (a) Returns valid `MarketAccessFindings`. (b) `output_validator` raises `ModelRetry` on completely empty output. (c) Tool calls produce at least one `add_event` call that reaches `ctx.events`. (d) `UsageLimitExceeded` produces `LimitedMarketAccessFindings` without crashing.

7. **Analyst agent isolation tests**: Same pattern as researcher — valid `AnalystFindings`, validator behavior, graceful limit handling.

8. **Lead agent orchestration tests**: (a) Three tools called in sequence. (b) `LimitedMarketAccessFindings` from researcher does NOT stop analyst or reporter. (c) Reporter failure produces a degraded `MarketReport` rather than an uncaught exception.

9. **Retry route tests** *(expand `test_api_run.py`)*: All four checkpoint states — (a) no checkpoints → full pipeline; (b) research checkpoint only → full pipeline; (c) both checkpoints → `_run_reporter_only`; (d) analyst only (malformed state) → full pipeline fallback.

10. **Per-stage retry wrapper in lead tools**: `run_market_access_research` and `run_analyst_research` retry up to N times (configurable, default 2) on `UnexpectedModelBehavior` or JSON parse failures before returning `LimitedXFindings`. Each retry attempt logged via `add_event("info", ...)`. Note: pydantic-ai's own `retries=get_retries()` (output validator retries) is separate — document the combined retry budget: `outer_retries * (inner_retries + 1)` max attempts.

11. **Structured error context in DB**: `mark_error` persists `failed_stage` (e.g., `'researcher'`, `'analyst'`, `'reporter'`, `'timeout_researcher'`) alongside the error message. The retry endpoint reads this to decide which checkpoint path to take. Add idempotent `ALTER TABLE` migration in `api/database.py`.

---

## Success Criteria

- [ ] `uv run pytest tests/ -v` completes in under 10 seconds on cold start with no Ollama running (CI gate)
- [ ] `WorkflowEvent(event_type="agent_limit", ...)` is valid — no pydantic ValidationError on usage-limit path
- [ ] After each stage completes, at least one SSE event with that stage's name is present in `ctx.events` (verifies add_event fix is real — test via `test_pipeline_stages.py`)
- [ ] A pipeline where the reporter raises an exception produces a DB record with `failed_stage='reporter'` and a degraded `MarketReport`; researcher and analyst findings remain in the DB as checkpoints
- [ ] A sub-agent timeout produces `failed_stage` containing `'timeout'` in the DB error record
- [ ] Each of `researcher_agent`, `analyst_agent`, `reporter_agent` has at least one isolated test using `FunctionModel`/`TestModel` that does not mock `_run_pipeline`
- [ ] A test confirming `lead_agent` continues to analyst + reporter when researcher returns `LimitedMarketAccessFindings`
- [ ] Retry route tests cover all four checkpoint combinations (no/research-only/analyst-only/both)
- [ ] Per-stage retry in `run_market_access_research` and `run_analyst_research`: at least 2 attempts logged as events before returning `LimitedXFindings`
- [ ] `mark_error` persists `failed_stage` readable by the retry endpoint

---

## Files Expected to Change

- `app/schema.py` — add `"agent_limit"` to WorkflowEvent event_type Literal
- `app/context.py` — make `ResearchContext.add_event` async
- `api/stream.py` — keep `StreamingResearchContext.add_event` async override
- `app/agents/lead.py` — add await to all add_event calls; add reporter try/except; add timeout wrappers; add per-stage retry logic
- `app/agents/researcher.py` — add await to all add_event calls
- `app/agents/analyst.py` — add await to all add_event calls
- `app/agents/reporter.py` — add await to all add_event calls
- `api/routes/run.py` — pass `failed_stage` to `mark_error`; update retry logic
- `api/db_sessions.py` — add `failed_stage` to `mark_error`
- `api/database.py` — idempotent `ALTER TABLE` migration for `failed_stage` column
- `tests/test_pipeline_stages.py` — new: per-agent isolation tests (Phase B)
- `tests/test_api_run.py` — expand checkpoint retry coverage + smoke tests for crash fixes (Phase A)

**Estimated:** 12 files

---

## Out of Scope

- UI changes to display retry count or stage progress (separate scope)
- Replacing pydantic-ai with a different orchestration framework
- `_run_reporter_only` synthesis quality (uses template prompt vs lead's dynamic synthesis — noted as a known regression in the retry feature, separate scope)
- `update_events` write-per-event optimization (performance, not correctness — separate scope)
- `app/history.py` / DB checkpoint system unification (tech debt — separate scope)
- Shared `usage=ctx.usage` between lead and reporter (token accounting, not user-visible)

---

## Known Risks

- **Retry multiplication**: pydantic-ai's `retries=get_retries()` (output validator) + the outer retry wrapper in lead tools = `(outer_retries + 1) * inner_retries` max attempts. For Ollama this could be 9 attempts before giving up. Document the intended budget in code comments; the timeout bounds wall-clock time regardless.
- **Timeout calibration**: Ollama on a MacBook M1 can take 90–180 seconds for a complex structured output call. The 120-second default must be documented as configurable (`AGENT_TIMEOUT` env var) and tested at startup to avoid silently killing legitimate slow runs.
- **pydantic-ai version pinning**: `FunctionModel`/`TestModel` API may shift between minor versions. Tests should assert on DB state and `ctx.events` list, not on pydantic-ai internal call recording. Pin pydantic-ai version in `pyproject.toml` and document.
- **`add_event` is on the hot path**: The await-everywhere change touches every agent tool callback. Write Phase A smoke tests for add_event behavior before touching this — the test is your safety net for the refactor.
- **Scope warning**: 12 files across 4 subsystems (schema/models, agent logic, API/routes, test infra) is at the upper warning boundary. Avoid scope creep into UI or tooling changes; anything touching `web/` is out.
