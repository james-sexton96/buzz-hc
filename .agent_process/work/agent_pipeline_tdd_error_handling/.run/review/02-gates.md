# Quality Gates

**Scope:** agent_pipeline_tdd_error_handling
**Iteration:** iteration_02 (Phase B — TDD harness + retry wrapper)
**Input:** `.run/review/01-verify.md` (10/10 criteria MET)

---

## Fast-Track Check

All three fast-track conditions satisfied for documentation/integration gates:

- **Internal refactor only:** retry wrapper added inside `app/agents/lead.py` tool functions; their signatures, return types, and contract (LimitedXFindings on failure) are unchanged. No API endpoint, DB schema, frontend, or env-var contract changed (the new `STAGE_RETRIES` env var is additive with a default).
- **Test-only or doc-only adjacent:** the two non-test files touched are `app/agents/lead.py` (retry wrapper, internal) and the two test files. No production code outside `lead.py` changed.
- **results.md asserts no external impact:** iteration_02/results.md line 39 — "all 8 Phase A checks still green; test suite count 53/53"; no behavior-visible changes documented.

Per step instructions, adversarial and validation gates still run with full analysis. Documentation and integration gates are fast-tracked with quick verification.

---

## Gate 1: Documentation — PASS (fast-tracked)

**Verification performed:**

- **Removed Surfaces declared in iteration_plan.md?** No. `grep -n "Removed Surfaces"` in `iteration_plan.md` returns no matches. Phase B is purely additive (new tests + retry wrapper). The Removed-Surface Scrub clause therefore does not apply.
- **Spec Concerns in results.md?** No. `grep -n "Spec Concerns"` in `iteration_02/results.md` returns no matches. The "Known Issues / Follow-up" section (line 74–81) documents the `request_tokens` DeprecationWarning as a non-blocking, out-of-scope follow-up — it is a library deprecation in pydantic-ai, not a contract concern about this iteration's work.
- **Weakened-Assertion check:** scanned `results.md` for signature phrases ("dropped the X assertion", "rephrased the comment", "future scope can extend", "weakened to match current behavior"). None present. The retry-wrapper change *adds* assertions (F1–F4 lock in retry semantics) rather than removing any.
- **End-user docs:** N/A — no user-visible behavior change. The retry loop silently absorbs transient `UnexpectedModelBehavior` failures before they would have manifested as a degraded `Limited` finding. The user-visible contract (Limited finding on terminal failure) is identical.
- **Developer docs:** the retry contract is encoded directly in `app/agents/lead.py` docstrings (`:108-111` for researcher, `:180-183` for analyst) — "Retries on UnexpectedModelBehavior up to `_STAGE_RETRIES` additional attempts." The `_STAGE_RETRIES` constant is module-level and self-documenting via the `os.environ.get("STAGE_RETRIES", "2")` default. No external README, runbook, or API doc references the previous retry-free behavior.
- **Orphaned references:** none. The two changed tool functions (`run_market_access_research`, `run_analyst_research`) keep their original signatures; the only external caller is `lead_agent`'s LLM-driven tool invocation, which is unchanged.

**Verdict:** PASS. No Removed Surfaces, no Spec Concerns, no weakened assertions, docstrings reflect the new contract.

---

## Gate 2: Integration — PASS (fast-tracked)

**Verification performed:**

Searched for external call sites of the two changed tool functions:

```
grep -rn "run_market_access_research\|run_analyst_research" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.md"
  → all hits are inside app/agents/lead.py (prompt strings + the two function defs themselves) and inside tests/
```

- **Tool function signatures:** unchanged. Both functions still take `ctx: RunContext[ResearchContext]` + `query: str` and return `MarketAccessFindings | LimitedMarketAccessFindings` / `AnalystFindings | LimitedAnalystFindings`.
- **Return-type contract on failure:** unchanged. All four failure branches still return `LimitedXFindings(...)` exactly as before — only the path *to* that return is now wrapped in a retry loop for the `UnexpectedModelBehavior` case.
- **`add_event` calls:** the new `"info"` retry events use the existing `add_event(event_type, source, message)` signature — no schema change. WorkflowEvent already accepts `event_type="info"` (free-form string field per `app/schema.py`).
- **`_STAGE_RETRIES` env var:** new, additive, with default `"2"`. No existing deployment needs to set it to preserve previous behavior.
- **api/routes/run.py:** unchanged. The dispatch logic at `:240-245` (full pipeline vs reporter-only) was confirmed by E1–E4 to match the four checkpoint states; no signature on the route side moved.

**Verdict:** PASS. All integration points compatible; no caller signature drift.

---

## Gate 3: Adversarial Review — 4/4 PASS (rubric self-review)

No `adversarial-review.md` was produced by the executor (justification in `results.md:53` — "Phase B is additive test infrastructure plus a mechanical retry-wrapper change"). Performed rubric self-review against the four contract dimensions for the retry wrapper, since that is the only production-code change. The test infrastructure changes (Scenarios A/B/C/D/E) effectively *are* the adversarial layer for the surrounding code, so the rubric focuses on F-scenarios + retry semantics.

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| R1 | Retry budget arithmetic correct (`range(_STAGE_RETRIES + 1)` = initial + N retries) | PASS | `app/agents/lead.py:117,189` use `range(_STAGE_RETRIES + 1)`. F1 (`test_pipeline_stages.py:492-541`) and F2 (`:544-585`) set `_STAGE_RETRIES=2` and assert exactly 3 attempts + 2 info events — locks in "initial + N additional," not "total N." |
| R2 | Exception discrimination is precise (only `UnexpectedModelBehavior` retries; `UsageLimitExceeded`, `TimeoutError`, generic `Exception` do not) | PASS | `app/agents/lead.py:135-166` has four distinct `except` branches; only the `UnexpectedModelBehavior` branch `continue`s the loop. F3 (`:588-624`) sets `_STAGE_RETRIES=5` and asserts only 1 attempt for `UsageLimitExceeded` — proves the budget is genuinely unused. F4 (`:627-678`) does the same for `asyncio.TimeoutError` via `patch("app.agents.lead._AGENT_TIMEOUT", 0.001)`. |
| R3 | Log level semantics correct (`"info"` for retries; `"agent_limit"` for terminal failure) | PASS | `app/agents/lead.py:143-147` and `:214-218` use `add_event("info", ...)`. F1/F2 assert `evt.event_type == "info"` and `"Retry"` substring — explicitly differentiates from `"agent_limit"`. The terminal `agent_limit` event remains on `UsageLimitExceeded` and on retry-loop exhaustion paths, per criterion 4. |
| R4 | No infinite-loop risk; last attempt cleanly returns Limited | PASS | The retry condition `if attempt < _STAGE_RETRIES:` (`:142, :213`) prevents continuation on the final attempt; the loop falls through to the final `return Limited...` (`:170, :230`) which is the documented safety-net path. F1/F2 confirm exactly `_STAGE_RETRIES + 1` attempts — no extra. |

**Verdict:** 4/4 PASS. Retry contract is correctly implemented and tightly tested. The verification step's "Semantic Understanding" assessment (six dimensions, all confirmed) is consistent with this gate's findings.

One stylistic observation flagged in 01-verify.md line 51 — `except (UsageLimitExceeded, UnexpectedModelBehavior, Exception)` in `run_reporter` collapses three classes into one branch — is intentional (reporter has no retry budget per iteration_01 design) and not a contract violation.

---

## Gate 4: Scoped Validation — PASS

Read `iteration_02/test-output.txt`:

- **Scoped validation ran:** YES. `uv run pytest tests/ -v` executed against the `tests/` directory only — the project's full unit-test scope, not "entire codebase" in a broader sense (no frontend, no integration, no manual smoke included).
- **Pre-existing issues excluded:** YES (and none were excluded — all 30 pre-existing tests still pass alongside the 23 new ones, for 53/53).
- **Test count matches plan:** plan called for 23 new tests (17 in `test_pipeline_stages.py` + 6 in `test_api_run.py`); test output confirms 23 net new (53 total − 30 baseline from iteration_01).
- **Timing budget:** 0.90s vs 10s threshold — well within budget.
- **Warnings:** 28 `request_tokens` DeprecationWarnings, all from `app/agents/lead.py:128, :200`. Non-failing; documented as known follow-up in `results.md:76-81`. Not a regression — they existed before iteration_02 and are inherited from pydantic-ai 1.59.0's library deprecation, not introduced by this iteration.

**Verdict:** PASS. Scoped validation correctly run; all checks green.

---

## Gate Summary

| Gate | Status | Notes |
|------|--------|-------|
| Documentation | PASS (fast-tracked) | No Removed Surfaces, no Spec Concerns, no weakened assertions; docstrings updated in-place; no orphaned references |
| Integration | PASS (fast-tracked) | Tool signatures unchanged; only caller is lead_agent LLM dispatch; STAGE_RETRIES env var is additive with default |
| Adversarial | 4/4 PASS (rubric self-review) | Retry budget arithmetic, exception discrimination, log level, no-infinite-loop — all locked in by F1–F4 tests |
| Scoped Validation | PASS | 53/53 in 0.90s; 23 new tests; 28 inherited deprecation warnings (non-blocking, documented) |

## Overall Signal

- Toward APPROVE: **4** gates
- Toward ITERATE: **0** gates
- Toward BLOCK: **0** gates

## Details

No gates failed. Standard PASS path — proceed to step 03 (decide) for the iteration verdict.

**One follow-up to surface in the decision step (not gate-blocking):** the inherited `request_tokens` DeprecationWarning is a trivial 2-line fix (`request_tokens → input_tokens`, `response_tokens → output_tokens` at `app/agents/lead.py:128-129` and `:200-201`). Recommend bundling into the next maintenance iteration to keep iteration_02 strictly Phase B.
