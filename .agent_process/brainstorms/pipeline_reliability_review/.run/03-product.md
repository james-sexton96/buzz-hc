# Product / Developer Experience Review
## Requirement: `agent_pipeline_tdd_error_handling`

---

## 1. Problem Statement — Who Hurts and How

**The core developer pain is invisible failure.** A 5-10 minute Ollama run dies silently and the developer has no signal about which stage failed, why, or whether 8 minutes of compute are recoverable. The current bugs compound this in a specific order:

- **Bug 2 (`agent_limit` event type)** hits a developer the moment they exercise the usage-limit fallback path — a ValidationError with no obvious cause, thrown deep inside pydantic-ai, pointing nowhere near the real problem in `lead.py`. A new contributor debugging a slow Ollama run will waste significant time chasing a pydantic stack trace before finding a one-word string mismatch.

- **Bug 1 (add_event async/sync mismatch)** means the SSE stream shows nothing during sub-agent runs. From the UI perspective the progress bar stalls. From a developer perspective, every log statement they add inside researcher/analyst disappears. This actively impedes debugging all the other bugs — you lose your primary observability mechanism at exactly the point you need it most.

- **Bug 3 (no reporter try/except)** is the worst user-facing failure. After 7+ minutes of successful researcher and analyst work, the reporter crashes and the entire run is marked `error`. The user sees a failed run with no report, retry creates a new session ID, and the retry path (`_run_reporter_only`) uses a static template prompt instead of lead_agent's dynamic synthesis — so even a successful retry may produce a lower-quality report than the original would have.

- **Bug 5 (no timeouts)** affects any developer running Ollama locally. A model that's swapping to disk or mid-download will hang the pipeline indefinitely with no recovery path. This is a frequent local dev scenario and makes the whole system feel broken rather than slow.

- **Bugs 4 and 6** (shared usage object, per-event DB writes) are performance/correctness concerns that won't block a demo but will cause subtle problems at scale. Bug 4 risks corrupting token counts; Bug 6 creates 20-30 synchronous DB round-trips per run that compete with the SSE stream's own event loop.

---

## 2. Prioritized Gaps

**Must include in this scope (blockers or silent failures):**

1. **Bug 2 first** — fix the `agent_limit` Literal gap before writing any tests that exercise the error path. Every retry/limit test will fail with a misleading ValidationError until this is patched. One-line fix, zero risk, should be done before anything else.

2. **Bug 3 (reporter error handling)** — the requirement explicitly scopes retry wrappers to researcher and analyst only, but the reporter has no wrapper at all. This is the highest-value failure point from a user perspective: 8 minutes of work, last-mile failure, unrecoverable. A `try/except` in `run_reporter` with a `LimitedReporterOutput` fallback (similar to the existing `LimitedMarketAccessFindings` pattern already in `lead.py`) should be included.

3. **Bug 1 (add_event mismatch) is already in scope** — but the fix strategy matters. The requirement should specify whether `add_event` becomes fully async (requiring `await` at every call site) or whether a sync-compatible queue-based approach is used. The current call sites in `lead.py` don't use `await`, so a naive async fix would still silently drop events.

**Should include but could be deferred:**

4. **Bug 5 (timeouts)** — high operational value, low code complexity. An `asyncio.wait_for(..., timeout=300)` wrapper around each sub-agent call is ~3 lines per tool and would make the `failed_stage` DB field actually useful (a timeout produces a clean stage label).

5. **Bug 7 (`_run_reporter_only` template vs dynamic prompt)** — the retry path for "both checkpoints present" produces a demonstrably different (likely lower quality) report than a normal run. This undermines the entire value of checkpointing. It should be noted as a known regression in the retry feature.

**Explicitly out of scope for this iteration:**

- Bug 6 (DB write frequency) — buffered event persistence is a performance optimization, not a correctness fix.
- Bug 4 (shared usage object) — token accounting is not user-visible and doesn't affect pipeline reliability.
- Bug 8 (history.py divergence) — dead code cleanup, separate concern.

---

## 3. Success Criteria Gaps

The current success criteria focus on test coverage percentages and retry mechanics. Missing:

- **Observability criterion**: "After each stage completes, at least one SSE event with that stage's name appears in the stream." This directly verifies the add_event fix and gives the developer confidence the fix is real.
- **Last-mile resilience criterion**: "A pipeline where the reporter raises an exception produces a DB record with `failed_stage='reporter'` rather than a null report — researcher and analyst findings remain available for retry."
- **Retry quality criterion**: "A retry from full checkpoints produces a report with the same structural quality (sections populated, sources present) as a fresh run." This catches the `_run_reporter_only` template degradation.
- **Timeout signal criterion**: "If a sub-agent call exceeds its timeout, the DB error record includes the stage name and 'timeout' in the error message." Without this, timeouts are indistinguishable from other failures.
- **Developer workflow criterion**: "The full test suite runs in under 10 seconds on a cold start with no Ollama running." This should be stated explicitly and measured in CI — TestModel must not trigger any model loading.

---

## 4. Scope Boundaries

This is one coherent scope — the bugs are tightly coupled. Fixing add_event without fixing the Literal gap will cause test failures. Adding reporter error handling without fixing add_event means reporter failures are still invisible in the stream. The checkpoint/retry tests require the `failed_stage` DB field, which requires the reporter error handling to populate it correctly.

**What should stay out:** The `_run_reporter_only` quality gap (Bug 7) is architecturally a separate concern — it requires either promoting `_run_reporter_only` to call `lead_agent` (which changes the retry UX significantly) or accepting the quality regression. Tackling that in the same iteration would expand scope into prompt engineering and synthesis quality, which is a different risk surface.

---

## 5. Quick Wins — Unblock the Developer Loop Now

**Win 1 (5 minutes):** Add `"agent_limit"` to the `WorkflowEvent.event_type` Literal in `app/schema.py`. This unblocks the error path immediately and stops the misleading ValidationError from polluting test output. Zero side effects, can be done before any other work begins.

**Win 2 (15 minutes):** Make `add_event` consistently sync across both `ResearchContext` and `StreamingResearchContext`, and push to the SSE queue via `asyncio.get_event_loop().call_soon_threadsafe()` or by making the queue put non-blocking. The key constraint: all existing call sites in `lead.py`, `researcher.py`, and `analyst.py` call without `await`, so the interface must stay sync-compatible. This restores SSE stream visibility and makes every subsequent debugging session productive again.

These two fixes together restore the developer's primary feedback loop (working SSE stream, no spurious validation errors) before the full TDD harness is built. Everything else is easier to test once you can see what the pipeline is actually doing.
