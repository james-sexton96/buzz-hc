# Step 03: Devil's Advocate — Critical Review

**Requirement under review:** `agent_pipeline_tdd_error_handling`

---

## 1. Assumption Check

**"pydantic-ai TestModel is a stable investment."**
Questionable. pydantic-ai is still pre-1.0, and the TestModel API has shifted between minor versions. The team already has evidence of API instability — the `OllamaChatModel` in `app/llm.py` exists precisely because pydantic-ai's Ollama integration required manual patching for null content and newline issues. Building a test harness on TestModel fixtures locks the test suite to the same moving target. If pydantic-ai changes how TestModel handles structured output or `output_validator` callbacks, all eight test fixtures could break simultaneously.

**"Local Ollama is the long-term LLM."**
Likely wrong. Ollama is the current default, but `get_model()` already reads from env vars — the design anticipates swapping providers. If the team moves to Claude Haiku or GPT-4o-mini within six months, the TestModel investment is still useful (TestModel is provider-agnostic), but the timeout logic, retry counts, and the `OllamaChatModel` patches become dead code. The bugs that matter most — Pydantic `ValidationError` on `agent_limit`, the async/sync `add_event` mismatch, the reporter having no safety net — are entirely LLM-agnostic and will survive any provider switch.

**"The bugs are causing failures."**
Bug 1 (async/sync mismatch) and Bug 2 (`agent_limit` not in Literal) are confirmed crash paths, not latent risks. Specifically: whenever a sub-agent hits a usage limit, `lead.py` calls `ctx.deps.add_event("agent_limit", ...)` which triggers a Pydantic `ValidationError` — crashing the pipeline at the exact moment the limit-exceeded fallback is supposed to protect it. This is a live production failure, not a hypothetical.

---

## 2. Alternative Approaches

**Cloud LLM for fast dev loops.**
The stated goal of the test harness is speed — avoid 2-minute Ollama runs per test. Using Claude Haiku or GPT-4o-mini as a `TEST_MODEL` env var would achieve the same fast-loop goal without building a custom TestModel fixture layer. Real model tests catch output_validator logic (which TestModel cannot exercise meaningfully). The cost for 50 test runs against Haiku is negligible. This is probably simpler than eight TestModel fixtures.

**Thin integration test with hardcoded JSON.**
The three sub-agents each have structured output types. A fixture that patches `researcher_agent.run()` to return `MarketAccessFindings(raw_evidence_summary="test")` directly — without invoking any model — tests the orchestration logic in `lead.py` without any pydantic-ai TestModel complexity. This is two files and half a day of work, not eight files and two weeks.

**Checkpoint-based retry: skip entirely for now.**
The retry route (`POST /run/{id}/retry`) already works and is tested. The `failed_stage` DB column adds diagnostic value but not user-visible reliability. The most user-visible improvement is making the pipeline not crash in the first place (Bugs 1, 2, 3), not making failed runs resume more gracefully.

---

## 3. Scope Concerns — These Are Three Different PRs

The requirement bundles three distinct problems with different urgency and risk profiles:

**Tier 1 — Crash bugs (1 day, one PR):** Fix `agent_limit` Literal, fix `add_event` async/sync split, add try/except to `run_reporter`. These are urgent, the fix is small, and they have zero architectural risk. There is no good reason to block these on a two-week TDD build.

**Tier 2 — Test infrastructure (3-5 days, one PR):** TestModel fixtures or hardcoded-JSON patches for lead/researcher/analyst. Valuable but not urgent. Can ship after Tier 1 without any dependency.

**Tier 3 — Architectural improvements (1 week+, separate PR):** Timeouts on Ollama calls, `update_events` write batching, unifying `history.py` and DB checkpoint systems, fixing `_run_reporter_only` to use lead's synthesis prompt. These touch the streaming core and deserve their own review cycle.

Combining all three into one "complex" requirement means Tier 1 bug fixes are blocked until Tier 3 architectural work is reviewed and merged.

---

## 4. Failure Modes

**Retry logic vs pydantic-ai ModelRetry conflict.** Both `researcher_agent` and `reporter_agent` already raise `ModelRetry` in their `output_validator` hooks. Adding a custom retry wrapper in `lead.py` that catches `Exception` and retries the whole agent run creates two competing retry loops. If the model returns empty output three times, pydantic-ai's internal retry exhausts first and raises `UnexpectedModelBehavior` — which the outer wrapper then catches and retries again. The effective retry count becomes `(inner_retries + 1) * outer_retries`.

**TestModel false confidence.** `output_validator` hooks run during the agent's model call cycle. TestModel returns whatever you configure — it will trivially pass validators unless you explicitly configure a failing response. Tests that pass with TestModel will not catch cases where the validator logic itself is wrong (e.g., the current `validate_researcher_output` accepts any non-empty output — a model returning a single `raw_evidence_summary="."` passes). Real model tests are needed to validate the validators.

**Timeout values.** Ollama on a MacBook M1 can take 90–180 seconds for a complex structured output call. If timeouts are set below 120 seconds, they will fire on legitimate slow runs and trigger the retry path, burning the usage budget on false failures. There is no established baseline to calibrate against.

---

## 5. The Valuable 20%

Fix Bugs 1, 2, and 3 this week. They are small, isolated, and cover the three most likely crash paths in production:

1. **`agent_limit` in the Literal** — one-line schema fix, prevents ValidationError on limit exhaustion.
2. **`add_event` async resolution** — make `StreamingResearchContext.add_event` synchronous (matching the base class contract) and batch DB writes at pipeline end, or call `asyncio.create_task` inline. Removes the silent event loss and the per-event DB write.
3. **try/except in `run_reporter`** — add the same pattern already used in `run_market_access_research` and `run_analyst_research`. Reporter failure after two successful sub-agent runs is the most expensive possible failure; it should not propagate uncaught.

These three changes touch three files, require no test infrastructure, and eliminate the most painful user-visible failures. Everything else in the current requirement is valuable but not urgent.
