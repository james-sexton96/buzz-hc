# Iteration Results – agent_pipeline_tdd_error_handling/iteration_02

**Date:** 2026-05-24
**Status:** ✅ COMPLETE

---

## Summary

Phase B TDD harness is fully implemented. The pipeline now has a fast offline test loop (53 tests in under 1 second, no Ollama required) covering every stage in isolation, the full lead orchestration sequence, all four retry-route checkpoint states, and the per-stage retry wrapper behavior.

The core additions: `tests/test_pipeline_stages.py` (new, 17 tests) covers per-agent isolation (Scenarios A/B/C), lead orchestration (D), and retry-wrapper behavior (F). `tests/test_api_run.py` gained 6 retry-route matrix tests (Scenarios E/E5). `app/agents/lead.py` has a new `_STAGE_RETRIES` module constant and the two research/analyst tool wrappers now retry only on `UnexpectedModelBehavior`, logging each attempt as an `"info"` event before returning `LimitedXFindings`.

**Acceptance Criteria Status:**

- [x] `tests/test_pipeline_stages.py` exists with per-agent isolation tests using `TestModel`; no Ollama required
- [x] `uv run pytest tests/ -v` completes in 0.90s on cold start — 30 pre-existing tests still pass; 23 new tests also pass (53 total)
- [x] Each of `researcher_agent`, `analyst_agent`, `reporter_agent` has isolated `TestModel` tests that do not mock `_run_pipeline`
- [x] Researcher isolation tests A1–A4: valid output, validator rejects empty, `UsageLimitExceeded` → `LimitedMarketAccessFindings`, add_event in `ctx.events`
- [x] Analyst isolation tests B1–B3: same pattern as researcher
- [x] Reporter isolation tests C1–C3: valid output, validator rejects missing fields, lead `run_reporter` failure → degraded `MarketReport`
- [x] Lead orchestration tests D1–D3: all three tools in sequence → `MarketReport`; Limited researcher doesn't stop pipeline; reporter failure → degraded (not exception)
- [x] Retry route tests E1–E4 + E5 cover all four checkpoint states and `failed_stage` readability
- [x] Per-stage retry wrapper: retries up to `_STAGE_RETRIES` (default 2) on `UnexpectedModelBehavior` only; each retry logged via `add_event("info", ...)`; `asyncio.TimeoutError` and `UsageLimitExceeded` are NOT retried; configurable via `STAGE_RETRIES` env var
- [x] `mark_error` with `failed_stage` readable by retry endpoint — covered by `test_retry_endpoint_reads_failed_stage_from_db`

---

## Changed Files

- `app/agents/lead.py` — Added `_STAGE_RETRIES = int(os.environ.get("STAGE_RETRIES", "2"))`; rewrote exception handling in `run_market_access_research` and `run_analyst_research` as retry loops with four distinct `except` clauses (TimeoutError no-retry, UnexpectedModelBehavior retried with event logging, UsageLimitExceeded no-retry, Exception catch-all no-retry)
- `tests/test_pipeline_stages.py` — NEW; 17 tests covering Scenarios A1–A4, B1–B3, C1–C3, D1–D3, F1–F4
- `tests/test_api_run.py` — Appended 6 Scenario E retry-route matrix tests; no existing tests modified

---

## Validation

**Scoped validation (hook):** PASS — all 8 Phase A checks still green; test suite count 53/53

**E2E tests:** SKIPPED — no Playwright config in this project

**Manual verification:** SKIPPED — TestModel fixtures provide full offline coverage; Ollama not required

**Timing:** 0.90s total (well under 10s threshold)

**Detailed logs:** See `test-output.txt` (53 passed, 28 warnings)

---

## Adversarial Review

Adversarial review not performed — Phase B is additive test infrastructure plus a mechanical retry-wrapper change. The retry semantics were specified precisely in the prepare doc (Scenario Table F) with no ambiguity; the test results directly verify the contract.

---

## Implementation Notes

**What went well:**
- TestModel override pattern worked cleanly across all four-agent nesting levels
- `patch("app.agents.lead._AGENT_TIMEOUT", 0.001)` gave reliable instant-timeout behavior for F4 scenario without requiring sub-agent overrides
- Retry loop structure was clean: four distinct except clauses exactly as designed; F1/F2 tests confirm retry counting and event logging

**Challenges encountered:**
- `RunUsage.request_tokens` is deprecated in pydantic-ai 1.59.0 (now `input_tokens`); `ctx.usage.request_tokens += ...` in lead.py generates DeprecationWarnings (28 total) but does not fail. Preserved as-is to avoid scope creep — the catch-all `except Exception` in the non-retry path swallows it cleanly. Flagged as a known issue below.

**Technical decisions:**
- Retry loop uses `for attempt in range(_STAGE_RETRIES + 1):` so the final attempt (attempt == `_STAGE_RETRIES`) logs the retry event and then returns Limited, consistent with the spec
- `STAGE_RETRIES=0` disables retries (single attempt only) — zero retries is the correct interpretation of `range(0 + 1) = range(1)` with no retry branch hit
- Analyst retry wrapper mirrors researcher exactly — same four except clauses, same log format

---

## Known Issues / Follow-up

**`RunUsage.request_tokens` deprecation warning (out of scope):**
- `app/agents/lead.py:128` and `:200` — `ctx.usage.request_tokens += result.usage().request_tokens`
- pydantic-ai 1.59.0 deprecated `request_tokens` in favor of `input_tokens`
- Generates 28 DeprecationWarnings in the test output (not failures)
- Fix: replace `request_tokens` with `input_tokens` and `response_tokens` with `output_tokens` in both accumulation lines
- Recommend addressing in next iteration or maintenance pass; non-blocking

---

## Ready for Review?

YES — All 10 acceptance criteria met, 53/53 tests passing in under 1 second with no Ollama, scoped validation fully green.

**Next step:** Open a fresh orchestrator session with `orchestration/review-iteration.md` to review this iteration.
