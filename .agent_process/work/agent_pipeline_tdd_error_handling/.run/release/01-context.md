# Release Context

**Mode:** scope
**Scope:** agent_pipeline_tdd_error_handling
**Iteration:** iteration_02
**Build number:** 1
**GitHub issue:** #10

## Changes Summary

Phase B (iteration_02) completes the two-phase pipeline error-handling TDD scope. Added comprehensive offline test harness covering:
- Per-agent isolation tests using `TestModel` fixtures (scenarios A-C: researcher, analyst, reporter)
- Full lead orchestration sequence (scenario D)
- Retry-route checkpoint state tests (scenario E)
- Per-stage retry wrapper behavior with configurable retries (scenario F)

Phase A (iteration_01) fixed four live crash bugs:
- Made `ResearchContext.add_event` async with `await` at all 13 call sites
- Added `"agent_limit"` event type to schema
- Added `asyncio.wait_for()` timeout wrappers on all sub-agent calls in lead
- Added try/except fallback in `run_reporter` to return degraded report on failure
- Added `failed_stage` column and logic to track pipeline stage failures in DB

**Change type:** feature (Phase B: TDD infrastructure) + fix (Phase A: crash bugs)
**User-facing:** NO

## Changed Files (from git)

### root
- `app/schema.py` — added "agent_limit" event type to Literal
- `app/context.py` — changed `add_event` from sync to async def
- `app/agents/researcher.py` — awaited all 4 add_event calls
- `app/agents/analyst.py` — awaited all 2 add_event calls
- `app/agents/lead.py` — awaited all 7 add_event calls; added asyncio.wait_for timeout wrappers; added try/except reporter fallback; added `_STAGE_RETRIES` constant and per-stage retry wrappers (Phase B)
- `api/database.py` — added idempotent `failed_stage` column migration
- `api/db_sessions.py` — added `failed_stage` parameter to `mark_error` signature
- `api/routes/run.py` — updated `mark_error` calls to pass `failed_stage`
- `api/stream.py` — supporting changes to streaming context
- `tests/test_schema.py` — added smoke test for "agent_limit" event construction
- `tests/test_api_run.py` — added 6 retry-route matrix tests covering checkpoint states
- `tests/test_pipeline_stages.py` — NEW (17 tests); per-agent isolation, lead orchestration, retry wrapper scenarios
- `.gitignore` — updated to exclude test artifacts
- `README.md` — documentation updates
- `main.py` — changes related to CLI resume functionality
- `app/history.py` — supporting changes
- `app/cli_resume.py` — NEW; imported by run route for synthesis prompt
- `web/package.json` — dependency updates

## Files from Plan (for reference)

**Phase A files (iteration_01):**
- `app/schema.py` ✓
- `app/context.py` ✓
- `app/agents/lead.py` ✓
- `app/agents/researcher.py` ✓
- `app/agents/analyst.py` ✓
- `api/database.py` ✓
- `api/db_sessions.py` ✓
- `api/routes/run.py` ✓
- `tests/test_schema.py` ✓
- `tests/test_api_run.py` ✓

**Phase B additions (iteration_02):**
- `tests/test_pipeline_stages.py` ✓ (17 new tests covering per-agent isolation, lead orchestration, retry wrapper)

**Ancillary files changed:**
- `app/cli_resume.py` — new utility file imported by routes
- `api/stream.py` — supporting streaming context changes
- Various: `.gitignore`, `README.md`, `main.py`, `app/history.py`, `web/package.json` — secondary changes

**Note:** The git diff is authoritative. All files above represent the actual state after both phases completed.
