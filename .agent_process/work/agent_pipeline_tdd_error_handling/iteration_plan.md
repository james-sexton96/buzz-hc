# Iteration Plan – agent_pipeline_tdd_error_handling

## Scope Overview
- **Scope Name:** agent_pipeline_tdd_error_handling
- **Date:** 2026-05-24
- **Summary:** Fix four live crash bugs in the pipeline's error-handling paths and add supporting smoke tests. Phase A of a two-phase scope.

## Requirements Source
- **Path:** `.agent_process/requirements_docs/agent_pipeline/agent_pipeline_tdd_error_handling.md`

## Current Status
- Latest iteration: iteration_02 (Phase B — TDD harness + retry wrapper)
- Decision: APPROVE (2026-05-24) — both phases complete, full requirement satisfied
- Next: Run `/ap_release pr`

## Acceptance Criteria (LOCKED — iteration_01 = Phase A only)

- [ ] `WorkflowEvent(event_type="agent_limit", source="x", message="x")` constructs without pydantic ValidationError
- [ ] `ResearchContext.add_event` is `async def`; confirmed by `inspect.iscoroutinefunction()`
- [ ] All 13 call sites in `lead.py` (7), `researcher.py` (4), `analyst.py` (2) have `await` prepended — verified by grep
- [ ] A test confirms `StreamingResearchContext.add_event` appends to `ctx.events` AND puts the event in the asyncio queue when awaited
- [ ] `run_reporter` tool in `lead.py` has a `try/except` that returns a degraded `MarketReport(title=..., executive_summary="Error: ...", sections=[], sources=[], markdown_content=...)` instead of propagating the exception
- [ ] Each sub-agent call (`researcher_agent.run`, `analyst_agent.run`, `reporter_agent.run`) in `lead.py` is wrapped with `asyncio.wait_for(..., timeout=float(os.environ.get("AGENT_TIMEOUT", "120")))`; `asyncio.TimeoutError` handled gracefully per stage (returns Limited object for researcher/analyst, degraded MarketReport for reporter)
- [ ] `api/database.py` has idempotent `ALTER TABLE sessions ADD COLUMN failed_stage TEXT` migration (runs without error on fresh DB and on DB already having the column)
- [ ] `mark_error` signature is `mark_error(session_id, error_msg, events_json, failed_stage=None)` and persists `failed_stage` to DB
- [ ] `uv run pytest tests/ -v` passes — all tests green

**Phase B criteria (iteration_02 — NOT in this iteration):**
- TestModel/FunctionModel fixtures for per-agent isolation
- Full retry matrix tests
- Per-stage retry wrapper in lead tools
- `tests/test_pipeline_stages.py`

## Known Patterns & Constraints

- `lead_agent` must be imported INSIDE route handlers (not at module top) — `get_model()` reads env vars at import time. Do NOT add top-level imports of lead_agent in routes.
- `DB_PATH` in `api/database.py` is monkeypatched in `tests/conftest.py` — tests use temp DB automatically.
- The `OllamaChatModel` patches `_map_messages` — do not modify `app/llm.py`.
- All agent files (`lead.py`, `researcher.py`, `analyst.py`, `reporter.py`) are in `app/agents/` and currently import `model = get_model()` at module top — this is acceptable and intentional.
- pydantic-ai agents are module-level singletons — do not move them into functions.

## Design Review

**Gate triggered:** Yes (complexity: complex)
**Decision:** Proceeding without external review agents — design decisions already captured in requirement via multi-agent brainstorm (pipeline_reliability_review). Brainstorm covered Product, Architect, and Devil's Advocate perspectives.

## Technical Assessment

**Current state:**
- `app/schema.py`: `WorkflowEvent.event_type` is `Literal["agent_start", "tool_call", "tool_result", "agent_end", "info"]` — missing `"agent_limit"`
- `app/context.py`: `ResearchContext.add_event` is sync `def` — override in StreamingResearchContext is async but never awaited
- `app/agents/lead.py`: 7 add_event calls without await; `run_reporter` has no try/except; no asyncio.wait_for on any sub-agent call
- `app/agents/researcher.py`: 4 add_event calls without await
- `app/agents/analyst.py`: 2 add_event calls without await
- `api/db_sessions.py`: `mark_error` takes 3 params, no failed_stage
- `api/database.py`: sessions table has no `failed_stage` column

**Implementation approach:**
1. `app/schema.py` — add `"agent_limit"` to Literal (one line)
2. `app/context.py` — change `def add_event` to `async def add_event`
3. `app/agents/researcher.py`, `app/agents/analyst.py` — prepend `await` to each add_event call
4. `app/agents/lead.py`:
   - prepend `await` to all 7 add_event calls
   - add `import asyncio` and `import os` at top (not currently imported in lead.py)
   - wrap each sub-agent `.run()` with `asyncio.wait_for`
   - add try/except to `run_reporter` mirroring researcher/analyst pattern
5. `api/database.py` — add `failed_stage` ALTER TABLE migration (idempotent, same pattern as existing `research_json`/`analyst_json` migrations)
6. `api/db_sessions.py` — add `failed_stage: str | None = None` param to mark_error, include in UPDATE
7. `api/routes/run.py` — update mark_error calls to pass `failed_stage="pipeline"` (or derive from context)
8. `tests/test_api_run.py` — add smoke tests (see below)

**Smoke tests to add:**
- `test_agent_limit_event_valid()` — unit test in test_schema.py: construct WorkflowEvent with event_type="agent_limit"
- `test_add_event_is_coroutine()` — verify ResearchContext.add_event is async
- `test_streaming_context_enqueues_event()` — verify StreamingResearchContext.add_event puts event in queue
- `test_reporter_failure_produces_degraded_report()` — mock reporter_agent.run to raise, verify pipeline completes with degraded MarketReport (not error status)

**Design decisions:**

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| add_event fix strategy | await-everywhere | sync-everywhere | sync approach creates coordination problem with async DB write in StreamingResearchContext; await-everywhere is grep-verifiable and explicit |
| Timeout value | 120s default, AGENT_TIMEOUT env var | hard-coded | Ollama on M1 can take 90-180s; must be configurable per deployment |
| Reporter failure outcome | degraded MarketReport + mark_complete | mark_error with failed_stage | Reporter failure after successful researcher+analyst is a partial success; the findings are captured; user should be able to read the findings even without a polished report |
| failed_stage scope | pipeline-level only (iteration_01) | per-tool tracking | Per-tool tracking (via context attribute) adds complexity; tool-level failures are now handled gracefully (return Limited objects); only unhandled lead-level failures reach mark_error |

## Iteration Budget
- **iteration_01:** Phase A — crash bug fixes (current)
- **iteration_01_a:** Revision if needed
- **iteration_02:** Phase B — full TDD harness (TestModel fixtures, per-agent isolation tests, retry matrix)

## Files in Scope (iteration_01)

- `app/schema.py` — add "agent_limit" to Literal
- `app/context.py` — make add_event async
- `app/agents/lead.py` — await all add_event; timeout wrappers; reporter try/except; add asyncio+os imports
- `app/agents/researcher.py` — await all add_event
- `app/agents/analyst.py` — await all add_event
- `api/database.py` — failed_stage migration
- `api/db_sessions.py` — failed_stage in mark_error
- `api/routes/run.py` — pass failed_stage to mark_error
- `tests/test_schema.py` — add agent_limit event type test
- `tests/test_api_run.py` — add smoke tests for async add_event and reporter failure

**Total:** 10 files

## Documentation in Scope

**Developer Documentation:**
- N/A — internal implementation only; no API changes visible to frontend

## Out of Scope (iteration_01)
- Per-stage retry wrapper in lead tools (Phase B)
- TestModel/FunctionModel fixtures (Phase B)
- `tests/test_pipeline_stages.py` (Phase B)
- `api/routes/sessions.py` — not touched
- Frontend changes

## Technical Notes
- `app/cli_resume.py` is imported by `api/routes/run.py` for `_SYNTHESIS_PROMPT` — do not delete
- Test for reporter failure: patch `reporter_agent.run` directly, then run `_run_pipeline` with full mock (or patch at the right level)
- `aiosqlite.OperationalError` is the correct exception to catch for "column already exists" in SQLite ALTER TABLE

## Validation Requirements

**Script:** `.agent_process/scripts/after_edit/validate-agent_pipeline_tdd_error_handling.sh`

**Pre-existing issues:** None known.

## Success Metrics
- All acceptance criteria checked
- `uv run pytest tests/ -v` green
- No regressions in existing tests
