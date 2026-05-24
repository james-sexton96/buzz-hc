# Review Decision: APPROVE

**Scope:** agent_pipeline_tdd_error_handling
**Iteration:** iteration_02 (Phase B — TDD harness + retry wrapper)
**Attempt:** 1 of 4
**Date:** 2026-05-24

---

## Evidence

- **Criteria:** 10/10 MET (0 PARTIAL, 0 NOT MET)
- **Gates:** 4/4 PASS (Documentation fast-tracked, Integration fast-tracked, Adversarial 4/4 rubric, Scoped Validation 53/53)
- **Validation:** PASS — `uv run pytest tests/ -v` → 53 passed, 28 warnings, 0.90s

This decision closes the full **two-phase scope**:
- iteration_01 (Phase A — crash bug fixes) — previously APPROVED
- iteration_02 (Phase B — TDD harness + retry wrapper) — APPROVE (this decision)

---

## Rationale

Every Phase B acceptance criterion is met with both letter-correct implementation and demonstrated semantic understanding. The retry contract is locked in by four targeted tests (F1–F4) that prove the retry budget is exhausted only on `UnexpectedModelBehavior`, never on `UsageLimitExceeded` or `TimeoutError`, with `"info"`-level event logging for transient retries and `"agent_limit"` reserved for terminal failures. The wider test suite (53/53, sub-second, no Ollama) gives the project a durable offline TDD harness for future agent work. No scope expansion, no regressions, no weakened assertions.

---

## Criteria Status

- MET (1/10) — `tests/test_pipeline_stages.py` exists with `TestModel` per-agent isolation, no Ollama
- MET (2/10) — `uv run pytest tests/ -v` passes in 0.90s; 53 total, 23 new
- MET (3/10) — researcher/analyst/reporter each have isolated `TestModel` tests not mocking `_run_pipeline`
- MET (4/10) — Researcher A1–A4: valid output, validator rejects empty, `UsageLimitExceeded` → Limited via lead, `add_event` reaches `ctx.events`
- MET (5/10) — Analyst B1–B3: same coverage as researcher
- MET (6/10) — Reporter C1–C3: valid output, validator rejects missing fields, lead `run_reporter` failure → degraded `MarketReport`
- MET (7/10) — Lead D1–D3: all three tools in sequence; Limited researcher doesn't stop pipeline; reporter failure degrades
- MET (8/10) — Retry-route E1–E4 + E5 cover all four checkpoint states and `failed_stage` round-trip
- MET (9/10) — Per-stage retry wrapper: retries on `UnexpectedModelBehavior` only via `_STAGE_RETRIES` (default 2, env-overridable); `"info"` event logged on each retry; `TimeoutError` and `UsageLimitExceeded` short-circuit
- MET (10/10) — `mark_error` with `failed_stage` readable by retry endpoint

---

## Gates Status

| Gate | Status | Notes |
|------|--------|-------|
| Documentation | PASS (fast-tracked) | No Removed Surfaces, no Spec Concerns, no weakened assertions; docstrings on retry tools self-document the new contract |
| Integration | PASS (fast-tracked) | Tool signatures unchanged; `STAGE_RETRIES` env var additive with default; no caller drift |
| Adversarial | 4/4 PASS (rubric self-review) | Retry budget arithmetic (R1), exception discrimination (R2), log-level semantics (R3), no infinite loop (R4) |
| Scoped Validation | PASS | 53/53 in 0.90s; 23 net new tests; deprecation warnings inherited from pydantic-ai 1.59.0 (non-blocking) |

---

## APPROVE — Next Steps

**Knowledge deposits (3 entries):**

1. **patterns.jsonl** — `pydantic_ai_testmodel_isolation_pattern` — Use `agent.override(model=TestModel(call_tools=[...], custom_output_args=...))` for fast offline per-agent tests; avoids brittle internal-method mocking and runs the full pydantic-ai validation/retry contract.

2. **gotchas.jsonl** — `output_validator_failures_surface_as_unexpectedmodelbehavior` — When a pydantic-ai `output_validator` raises `ModelRetry` and the model exhausts retries, the surfacing exception in the caller is `UnexpectedModelBehavior`, NOT `ValidationError`. Catch `UnexpectedModelBehavior` if you want to recover from validator-driven failures.

3. **decisions.jsonl** — `stage_retry_only_on_unexpectedmodelbehavior` — The per-stage retry wrapper in `lead.py` retries only on `UnexpectedModelBehavior` (validator-driven recoverable failures). `UsageLimitExceeded` and `asyncio.TimeoutError` short-circuit on first attempt because retrying would not change the underlying constraint; generic `Exception` short-circuits to avoid masking real bugs.

**Follow-up (non-blocking, deferred to maintenance):**

- `RunUsage.request_tokens` deprecation in pydantic-ai 1.59.0 — 28 warnings emitted from `app/agents/lead.py:128-129` and `:200-201`. Trivial substitution (`request_tokens → input_tokens`, `response_tokens → output_tokens`). Bundle into next maintenance iteration.

**Suggested release command:** `/ap_release pr`

---

## Next Step

Run `/ap_release pr` to open a PR for the full two-phase scope. Both iteration_01 (Phase A — crash fixes) and iteration_02 (Phase B — TDD harness + retry wrapper) are now APPROVED; the requirement's acceptance criteria are fully satisfied.
