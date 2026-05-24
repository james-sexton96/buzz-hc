# Iteration Results – agent_pipeline_tdd_error_handling/iteration_01

**Date:** 2026-05-24
**Status:** ✅ COMPLETE

---

## Summary

Phase A crash bug fixes are fully implemented. Four root-cause bugs that caused silent event loss, ValidationErrors, and unhandled pipeline crashes have been resolved across 11 files (10 planned + `api/stream.py` which had a cascading `super().add_event()` issue discovered during testing).

The core fixes: `WorkflowEvent` now accepts `"agent_limit"` as a valid event type; `ResearchContext.add_event` is now `async def`; all 13 call sites in `lead.py`, `researcher.py`, and `analyst.py` now properly `await` the call; `StreamingResearchContext.add_event` now correctly `await super().add_event(...)` instead of calling the sync base; `run_reporter` in `lead.py` has full try/except returning a degraded `MarketReport` rather than propagating; all three sub-agent calls in `lead.py` are wrapped with `asyncio.wait_for`; `mark_error` now persists `failed_stage`; and both pipeline entry points pass `failed_stage` values to `mark_error`.

**Acceptance Criteria Status:**

- [x] `WorkflowEvent(event_type="agent_limit", ...)` constructs without ValidationError — `"agent_limit"` added to Literal in `app/schema.py`
- [x] `ResearchContext.add_event` is `async def` — confirmed by `inspect.iscoroutinefunction()` in test
- [x] All 13 call sites in `lead.py` (7), `researcher.py` (4), `analyst.py` (2) have `await` — grep verified by validation script
- [x] Test confirms `StreamingResearchContext.add_event` appends to `ctx.events` AND puts event in queue when awaited
- [x] `run_reporter` tool has try/except returning degraded `MarketReport` on any failure
- [x] All three sub-agent `.run()` calls wrapped with `asyncio.wait_for(..., timeout=AGENT_TIMEOUT)`; TimeoutError handled per stage
- [x] `api/database.py` idempotent `ALTER TABLE sessions ADD COLUMN failed_stage TEXT` migration added
- [x] `mark_error` signature updated to `(session_id, error_msg, events_json, failed_stage=None)` and persists to DB
- [x] `uv run pytest tests/ -v` passes — 30/30 green

---

## Changed Files

- `app/schema.py` — Added `"agent_limit"` to `WorkflowEvent.event_type` Literal
- `app/context.py` — Changed `def add_event` → `async def add_event`
- `app/agents/lead.py` — Added `import asyncio`, `import os`; prepended `await` to all 7 `add_event` calls; wrapped `researcher_agent.run`, `analyst_agent.run`, `reporter_agent.run` with `asyncio.wait_for`; added full try/except to `run_reporter` tool; added `LimitedMarketAccessFindings` and `LimitedAnalystFindings` models; added `_AGENT_TIMEOUT` env-configurable constant
- `app/agents/researcher.py` — Prepended `await` to all 4 `add_event` calls
- `app/agents/analyst.py` — Prepended `await` to both `add_event` calls
- `api/database.py` — Added `"ALTER TABLE sessions ADD COLUMN failed_stage TEXT"` to idempotent migration list
- `api/db_sessions.py` — Added `failed_stage: str | None = None` param to `mark_error`; included in UPDATE SQL
- `api/routes/run.py` — Updated both `mark_error` calls: `_run_pipeline` passes `failed_stage="pipeline"`, `_run_reporter_only` passes `failed_stage="reporter_retry"`
- `api/stream.py` — Fixed `super().add_event(...)` → `await super().add_event(...)` (discovered during test run: base class is now async, subclass was calling it without await)
- `tests/test_schema.py` — Added `test_workflow_event_agent_limit` smoke test
- `tests/test_api_run.py` — Fixed unawaited `ctx.add_event` calls in `_fake_pipeline`; added `test_add_event_is_coroutine`, `test_streaming_context_enqueues_event`, `test_mark_error_persists_failed_stage`

---

## Validation

**Scoped validation (hook):** PASS
All 8 checks passed:
1. `agent_limit` in WorkflowEvent Literal — OK
2. `ResearchContext.add_event` is async — OK
3. No unawaited `add_event` calls — OK
4. `run_reporter` has try/except — OK
5. 3x `asyncio.wait_for` in `lead.py` — OK
6. `failed_stage` migration in `database.py` — OK
7. `mark_error` accepts `failed_stage` — OK
8. `uv run pytest tests/ -v` — 30 passed

**E2E tests:** SKIPPED — no Playwright config in this project; backend/frontend integration not in Phase A scope

**Manual verification:** SKIPPED — pipeline requires Ollama; Phase B will add FunctionModel/TestModel fixtures for offline verification

**Detailed logs:** See `test-output.txt` for complete pytest output (30 passed, 0 failed)

---

## Adversarial Review

Adversarial review not performed — scope is a targeted bug fix with mechanical, grep-verifiable changes. Brainstorm review (pipeline_reliability_review) covered Product, Architect, and Devil's Advocate perspectives prior to implementation.

---

## Implementation Notes

**What went well:**
- All 9 acceptance criteria met on first pass
- Validation script caught nothing unexpected
- Parallel execution of schema + context + agent files was clean

**Challenges encountered:**
- `api/stream.py` had a cascading issue: `StreamingResearchContext.add_event` called `super().add_event(...)` synchronously. After the base class was made async, this silently returned an unawaited coroutine, causing the events list to be empty when `self.events[-1]` was read. Caught immediately by `test_streaming_context_enqueues_event` — fixed by adding `await` to the super call.
- `tests/test_api_run.py` `_fake_pipeline` helper had unawaited `ctx.add_event(...)` calls that needed fixing alongside the new tests.

**Technical decisions:**
- `AGENT_TIMEOUT` defaults to 120s configurable via env var — Ollama on M1 can take 90-180s
- Reporter failure returns `mark_complete` with degraded `MarketReport` (not `mark_error`) — findings are still captured and readable; reporter stage is best-effort after research+analyst succeed
- `failed_stage` is pipeline-level only in Phase A; per-tool tracking deferred to Phase B as noted in design decisions table

---

## Known Issues / Follow-up

**No blocking issues.** All Phase A criteria met.

**Out of scope (Phase B — iteration_02):**
- `tests/test_pipeline_stages.py` — per-agent isolation tests using `FunctionModel`/`TestModel`
- Full retry matrix tests (pydantic-ai `retries=` vs outer wrapper interaction)
- Per-stage retry wrapper in lead tools
- `test_reporter_failure_produces_degraded_report` integration test (requires mocking at reporter_agent level — Phase B with FunctionModel)

---

## Ready for Review?

YES — All 9 acceptance criteria met, all 30 tests passing, no regressions, scoped validation script fully green.

**Next step:** Open a fresh orchestrator session with `orchestration/review-iteration.md` to review this iteration.
