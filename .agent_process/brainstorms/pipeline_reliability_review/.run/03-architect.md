# Architect Review: Pipeline Reliability Requirement

## 1. Technical Feasibility

The overall approach is sound — fixing `add_event` first, then layering test infrastructure, then adding error handling is the right order of operations. The architecture itself (asyncio task, SSE queue, pydantic-ai agents) is coherent. The three specific risks worth naming:

**Subclass async method override.** Python does NOT automatically await async overrides when called from sync context. `StreamingResearchContext.add_event` is `async def`, but every call site (`ctx.deps.add_event(...)`) has no `await`. Python silently calls the base class sync version because the dispatcher does not do method resolution by return type — it dispatches by name, and the sync base class method is found first on the MRO since the call is non-awaited. This is the core bug. The correct fix is **not** to make the base class async — it's to audit every call site and add `await`, or to make the base class itself async with a no-op coroutine. The `await`-everywhere approach is simpler and more correct.

**asyncio.Queue lifecycle.** The `_queue` is created in `__init__`, which must run on the event loop. If `StreamingResearchContext` is ever instantiated outside an async context (e.g., in a sync test setup), `asyncio.Queue()` will attach to the wrong loop. Tests using `asyncio.get_event_loop()` vs `asyncio.new_event_loop()` create subtle lifetime bugs here.

**Background task exception swallowing.** `asyncio.create_task(_run_pipeline(...))` will silently swallow any exception from `_run_pipeline` that isn't caught internally. The current try/except is broad enough to handle this, but if the outer `mark_error` call itself raises (DB unavailable), the exception disappears with no logging. This is a latent risk not addressed by the current requirement.

---

## 2. Missing Technical Requirements

**Must add — these are blockers or near-blockers:**

**Bug 2 (`agent_limit` ValidationError):** This is a runtime crash on every usage-limit path, which is the designed fallback for slow/long Ollama runs. Fix is one line: add `"agent_limit"` to the `WorkflowEvent.event_type` Literal in `app/schema.py`. Or replace the literal with `str` and validate in the model validator. This is trivially small but will silently break the graceful degradation path. Add as a sub-task under the existing Bug 1 fix — same file context, same test. File affected: `app/schema.py` (not currently in the file list).

**Bug 3 (Reporter has no try/except):** The requirement adds retry wrappers for researcher and analyst but explicitly skips reporter. This is architecturally asymmetric — reporter is the most expensive stage, running only after both prior stages complete successfully. A reporter failure discards all prior work with no recovery path. The fix mirrors what researcher/analyst get: a `try/except` in `run_reporter` that catches `UnexpectedModelBehavior`, `UsageLimitExceeded`, and the general `Exception`, stores the error, and returns a minimal `MarketReport` with an error message in `executive_summary`. Add as Requirement 9, with a companion test asserting the pipeline completes with a degraded report rather than raising.

**Bug 5 (No timeouts):** Ollama hangs are a production reality. A hung Ollama request blocks the asyncio event loop's ability to service the SSE connection, eventually timing out the HTTP client but leaving the background task orphaned in `_active_streams`. The fix is `asyncio.wait_for(agent.run(...), timeout=float(os.environ.get("AGENT_TIMEOUT", "120")))` in each of the three tool wrappers in `lead.py`. This is low risk to implement, high value for stability, and belongs in this requirement since it's part of the same "pipeline won't hang" reliability scope.

**Should add — non-blocking but worth capturing:**

**Bug 6 (`update_events` write frequency):** 20-30 DB writes per run is not catastrophic for SQLite with a local file, but it does serialize on the event loop. The fix — write only at stage boundaries (after researcher completes, after analyst completes) rather than on every event — can be deferred to a follow-on requirement, but should be noted. The current approach is functionally correct, just inefficient.

**Do not add to this requirement:**

Bug 4 (`usage=ctx.usage`) is a cosmetic/accounting issue, not a reliability bug. Bug 7 (`_run_reporter_only` synthesis prompt) is a quality concern, not a correctness bug — it still produces a report. Bug 8 (divergent checkpoint systems) is technical debt, not a reliability blocker. These belong in separate requirements.

---

## 3. Implementation Approach: add_event Fix

**Await-everywhere is the correct choice.** Here is why:

Making `ResearchContext.add_event` async (no-op coroutine) means every tool in every agent must `await ctx.deps.add_event(...)`. That is the correct call pattern regardless — it makes the contract explicit and prevents the silent sync-dispatch problem from recurring. The alternative (sync-everywhere, removing async from `StreamingResearchContext`) would require moving the `queue.put_nowait()` and DB write out to a separate async "flush" method called externally. That creates a new coordination problem: who calls flush, when, and what happens if it's missed.

The concrete change: make `ResearchContext.add_event` an `async def` that just appends to `self.events`. `StreamingResearchContext` keeps its override. ALL call sites in `researcher.py`, `analyst.py`, `reporter.py`, and `lead.py` get `await` prepended. This is mechanical and grep-verifiable. The test assertion is simple: mock the queue and assert `put_nowait` is called.

One caution: `add_event` is also called from sync tool callbacks registered via `@agent.tool` in `researcher.py` and `analyst.py`. Those tool functions are already `async def`, so `await ctx.deps.add_event(...)` is valid inside them without any additional scaffolding.

---

## 4. Files and Components Affected

Current file list is missing two files:

- `app/schema.py` — required for the `agent_limit` Literal fix (Bug 2)
- `app/agents/reporter.py` — required for the reporter try/except fix (Bug 3); currently listed as key context but not in the implementation file list

`app/agents/researcher.py` and `app/agents/analyst.py` are also affected by the await-everywhere change but are not in the current file list. They should be added — every `ctx.deps.add_event(...)` call in those files needs `await`.

`app/cli_resume.py` (the `_SYNTHESIS_PROMPT` template) is imported by `run.py` and is part of Bug 7's scope, but that bug is being deferred, so it can stay out.

Updated file list: `app/context.py`, `api/stream.py`, `app/agents/lead.py`, `app/agents/researcher.py`, `app/agents/analyst.py`, `app/agents/reporter.py`, `app/schema.py`, `api/routes/run.py`, `api/db_sessions.py`, `api/database.py`, `tests/test_pipeline_stages.py`, `tests/test_api_run.py`

---

## 5. Complexity Assessment

**Complex — but borderline splittable.** The core bug fixes (add_event, agent_limit Literal, reporter try/except, timeouts) are tightly coupled: fixing add_event without also fixing agent_limit means the limit path still crashes, and fixing the limit path without timeouts means the most common trigger for that path (Ollama hang) is still unhandled. These four fixes belong together.

The test infrastructure (TestModel fixtures, per-stage isolation tests, retry route tests) is a separate concern that could ship independently — but shipping the bug fixes without the tests would leave the fixes unvalidated. Keep it as one requirement, but structure the implementation as two phases: (1) bug fixes with minimal smoke tests, (2) full TDD harness.

If the team wants to split: Req A = Bug fixes (Bugs 1-3, 5) + smoke tests; Req B = Full TDD harness (TestModel fixtures, per-stage isolation, retry matrix). This reduces the blast radius of either effort.

---

## 6. Integration Risks

**pydantic-ai TestModel API stability:** pydantic-ai is pre-1.0 and has changed `TestModel` interfaces between minor versions. The test approach should avoid relying on internal `TestModel` call recording and instead use `output_type` factories with deterministic outputs. Assert on the final DB state and SSE events, not on pydantic-ai's internal call graph. This makes tests version-resilient.

**asyncio interaction with Ollama:** The `OllamaChatModel` subclass patches `_map_messages` — an internal method of `OpenAIChatModel`. If pydantic-ai upgrades its OpenAI backend and renames or refactors this method, the Ollama patches silently stop applying. The timeout addition (`asyncio.wait_for`) wraps the public `.run()` interface and is not affected by this, but it's worth noting the newline-sanitization patch is fragile.

**Retry logic conflict with pydantic-ai retries:** pydantic-ai agents have their own `retries=get_retries()` (default 3) via `output_validator`. The proposed per-stage retry wrapper in `lead_agent` tools adds an additional outer retry layer. If both fire simultaneously — pydantic-ai exhausts its retries and raises `UnexpectedModelBehavior`, then the outer wrapper catches and retries — the effective retry count is `outer_retries * inner_retries`. For a slow Ollama model this could mean 9 total attempts before giving up. Document the intended retry budget explicitly in code comments and tests. The timeout addition partially mitigates this by bounding wall-clock time regardless of retry count.
