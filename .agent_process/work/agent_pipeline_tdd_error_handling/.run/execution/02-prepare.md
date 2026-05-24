# Execution Preparation

**Scope:** agent_pipeline_tdd_error_handling
**Iteration:** iteration_02
**Type:** first_iteration (Phase B — new work, not a sub-iteration revision)

---

## Criteria (LOCKED)

Phase B acceptance criteria from the requirement doc (Requirements 5–11) and the iteration_plan.md Phase B listing:

- [ ] `tests/test_pipeline_stages.py` exists with per-agent isolation tests using `FunctionModel` or `TestModel`; none of these tests requires Ollama to run
- [ ] `uv run pytest tests/ -v` completes in under 10 seconds on cold start with no Ollama running — 30 pre-existing tests continue to pass; new tests also pass
- [ ] Each of `researcher_agent`, `analyst_agent`, `reporter_agent` has at least one isolated test via `TestModel`/`FunctionModel` that does not mock `_run_pipeline`
- [ ] Researcher isolation tests: (a) valid `MarketAccessFindings` output; (b) `output_validator` raises `ModelRetry` on completely empty output; (c) `UsageLimitExceeded` produces `LimitedMarketAccessFindings` without crashing (via lead_agent tool wrapper); (d) at least one `add_event` call reaches `ctx.events` for a successful researcher run
- [ ] Analyst isolation tests: same pattern — valid `AnalystFindings`; validator rejects empty output; graceful limit handling via lead tool wrapper
- [ ] Reporter isolation tests: valid `MarketReport`; validator rejects missing title/summary/sections/markdown_content; reporter failure in lead's `run_reporter` tool produces degraded `MarketReport` (not exception)
- [ ] Lead orchestration tests: (a) all three tools called in sequence produce a `MarketReport`; (b) `LimitedMarketAccessFindings` from researcher does NOT stop analyst or reporter; (c) reporter failure produces degraded `MarketReport` rather than uncaught exception
- [ ] Retry route tests cover all four checkpoint states: (a) no checkpoints → `_run_pipeline` dispatched; (b) research_json only → `_run_pipeline` dispatched (full run); (c) both checkpoints → `_run_reporter_only` dispatched; (d) analyst_json only (malformed state) → `_run_pipeline` dispatched (full run fallback)
- [ ] Per-stage retry wrapper in `run_market_access_research` and `run_analyst_research`: each retries up to N times (default 2) on `UnexpectedModelBehavior`; at least 2 retry attempts are logged as `add_event("info", ...)` events before returning `LimitedXFindings`; retry count configurable via `STAGE_RETRIES` env var
- [ ] `mark_error` with `failed_stage` is readable by the retry endpoint (already wired in Phase A; this iteration adds the test coverage)

---

## Files in Scope

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_pipeline_stages.py` | NEW | Per-agent isolation tests + lead orchestration tests |
| `tests/test_api_run.py` | EXPAND | Add retry route checkpoint matrix tests (4 scenarios) |
| `app/agents/lead.py` | MODIFY | Add per-stage retry wrapper in `run_market_access_research` and `run_analyst_research` |

**Total:** 3 files (2 test, 1 production)

**Boundary flexibility (mirrors the iteration-plan rule):** This list is the *expected* touch surface, not a *forbidden* boundary. If meeting the acceptance criteria correctly — including any negative-case tests for quality-gate artifacts (§1.2) or stale-surface whitelist updates for removed surfaces (§1.1) — requires touching files outside this list, the implementer may do so. Document the expansion in `results.md` under "Implementation Notes" with what was added and why. The narrower list keeps sub-iterations focused; it does not wall off soundness fixes.

---

## Validation

- **RUN:** `uv run pytest tests/ -v` — must pass all tests (30 pre-existing + new Phase B tests), must complete under 10 seconds (no Ollama required)
- **SKIP:** E2E / Playwright tests — no Playwright config in this project
- **SKIP:** Manual pipeline verification — no Ollama needed; FunctionModel/TestModel fixtures provide offline coverage

---

## Human Checkpoint

- **Required:** NO
- **Source file:** `.agent_process/work/agent_pipeline_tdd_error_handling/human-prereqs.md` (present: NO)
- **Pre-execution items:** none
- **Mid-execution items:** none
- **Post-execution items:** none
- **Allowed Responses:** N/A — no gate required

**Note for coordinator:** the actual gate runs in the main conversation (Steps 0.5 and 6 of `execute.md`). This section is input for that gate, not a place to claim the gate already ran.

---

## Spec Concerns Channel

**Spec Concerns channel:** Pause and write a `## Spec Concerns` section at the top of `results.md` if any of these fire:

- **Prepare-doc gap.** A missing acceptance test, an instruction that conflicts with the iteration plan or framework rules, a soundness question about a quality-gate artifact you're modifying, or a fix spec that names a symptom rather than a root cause.
- **About to weaken a failing check.** You're about to remove an assertion, relax a test, comment-out a guard, document a known regression as "future work," or rephrase a doc/comment to dodge a string match. This is the failure mode the channel exists to catch. Treat the weakening as a Spec Concern, not a local fix.
- **Test failure points at production code, not the test.** If the assertion encodes the contract correctly and the production code doesn't honor it, the production code is the bug — even if it lives outside your file list. §1.3 (boundary flexibility) lets you fix it.

Then choose ONE:

- **Local fix is safe and obviously correct:** apply it, document it under Spec Concerns AND in Implementation Notes, including what changed and why.
- **Local fix is uncertain or expands scope significantly:** stop without applying it, leave the concern in `results.md`, and surface it to the coordinator so the prepare doc can be revised.

**There is no third option that weakens the check to make the failure go away.** Modifying or removing a failing test assertion is a *contract change*, not a local fix — even when the edit is mechanically simple. Contract changes always require coordinator escalation.

---

## Technical Guidance

### TestModel/FunctionModel — what works in this codebase

**Confirmed in local testing (pydantic-ai 1.59.0):**

- `TestModel(call_tools=[], custom_output_args={...})` — overrides the model used by an agent via `agent.override(model=TestModel(...))`. No network calls. Works for researcher/analyst/reporter in isolation.
- `TestModel(call_tools=['run_market_access_research', 'run_analyst_research', 'run_reporter'])` — makes the lead model call all three tools in sequence. The sub-agents inside those tools ALSO need model overrides to avoid hitting real Ollama.
- Nesting pattern: override lead model with `TestModel(call_tools=[...])` AND override each sub-agent model with `TestModel(call_tools=[], custom_output_args={...})`. Use `contextlib.ExitStack` or nested `with` blocks.
- Confirmed output shapes: `TestModel` with `custom_output_args` populates the agent's `output_type` Pydantic model by passing the dict as kwargs. Must match required fields.

**Important timing note:** When `lead_agent` is overridden with `TestModel` calling all tools, the sub-agent tools (`run_market_access_research`, `run_analyst_research`, `run_reporter`) execute their full `asyncio.wait_for` wrappers. If sub-agents are NOT also overridden, they will attempt Ollama calls and time out after `AGENT_TIMEOUT` (120s default). Set `AGENT_TIMEOUT=1` in tests OR ensure sub-agents are also overridden.

**Recommended pattern for lead orchestration tests:**
```python
import os
os.environ["AGENT_TIMEOUT"] = "5"  # fast timeout for test scenarios

from app.agents.lead import lead_agent, _AGENT_TIMEOUT
# Note: _AGENT_TIMEOUT is read at module import; use monkeypatch or patch to override
```

Actually, because `_AGENT_TIMEOUT` is read at module load time from `os.environ`, the implementer should use `unittest.mock.patch` on `app.agents.lead._AGENT_TIMEOUT` to set a short timeout for timeout scenarios, or ensure sub-agents are always overridden with TestModel so the `wait_for` completes immediately.

**Retry wrapper design for `run_market_access_research` / `run_analyst_research`:**

```python
_STAGE_RETRIES = int(os.environ.get("STAGE_RETRIES", "2"))

# Inside run_market_access_research, replace the single try/except with:
for attempt in range(_STAGE_RETRIES + 1):
    try:
        result = await asyncio.wait_for(
            researcher_agent.run(...),
            timeout=_AGENT_TIMEOUT,
        )
        # success path — break
        ...
        return result.output
    except UnexpectedModelBehavior as e:
        await ctx.deps.add_event("info", "Researcher", f"Retry {attempt+1}/{_STAGE_RETRIES}: {e}")
        if attempt == _STAGE_RETRIES:
            return LimitedMarketAccessFindings(warning=f"Failed after {_STAGE_RETRIES+1} attempts: {e}")
    except asyncio.TimeoutError:
        # Timeout is not retried — treat as immediate limit
        await ctx.deps.add_event("agent_limit", "Researcher", f"Timeout after {_AGENT_TIMEOUT}s")
        return LimitedMarketAccessFindings(warning=f"Timed out after {_AGENT_TIMEOUT}s")
    except (UsageLimitExceeded, Exception) as e:
        await ctx.deps.add_event("agent_limit", "Researcher", f"Limit reached: {e}")
        return LimitedMarketAccessFindings(warning=f"Hit a limit: {e}")
```

The AC says "retries on `UnexpectedModelBehavior` or JSON parse failures." JSON parse failures in pydantic-ai surface as `UnexpectedModelBehavior`. `UsageLimitExceeded` should NOT be retried (no point; budget is exhausted). `asyncio.TimeoutError` should NOT be retried (wall-clock is the bound). Only `UnexpectedModelBehavior` retries.

**Known import constraint (from iteration_plan.md):** `lead_agent` must be imported INSIDE route handlers, not at module top. Tests that import `lead_agent` directly for override must import it at test-function scope or at module level only after test DB patches are in place. The `app/agents/lead.py` module-level `model = get_model()` call is intentional and acceptable.

---

## Concrete Scenario Coverage (§1.5)

Multiple ACs use universal quantifiers ("each", "all", "every"), multiple subjects, and state-dependent behavior. Concrete scenario tables follow.

### Scenario Table A — Researcher agent isolation

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| A1: Valid output | `researcher_agent.run("GLP-1 market", deps=ctx)` with TestModel returning `raw_evidence_summary="GLP-1 findings"` | `call_tools=[]`, output_validator enabled | Returns `MarketAccessFindings` with `raw_evidence_summary` populated; no exception |
| A2: Validator rejects empty | `researcher_agent.run("query", deps=ctx)` with TestModel returning all-empty dict `{}` | `call_tools=[]`, output_validator enabled, `retries=0` on agent | Raises `UnexpectedModelBehavior` (ModelRetry exhausted) or pydantic-ai equivalent after validator fires `ModelRetry` |
| A3: UsageLimitExceeded → Limited | Lead's `run_market_access_research` tool called with sub-agent raising `UsageLimitExceeded` | `researcher_agent` raises `UsageLimitExceeded` on `.run()` | Lead tool returns `LimitedMarketAccessFindings`; `ctx.events` contains an `"agent_limit"` event with source "Researcher" |
| A4: add_event reaches ctx.events | Successful researcher run through lead tool | `researcher_agent` returns valid findings | `ctx.events` contains at least one event with source "Researcher" (`agent_start` and/or `agent_end`) |

### Scenario Table B — Analyst agent isolation

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| B1: Valid output | `analyst_agent.run("GLP-1 market", deps=ctx)` with TestModel returning `summary="test"` | `call_tools=[]` | Returns `AnalystFindings` with `summary` populated; no exception |
| B2: Validator rejects empty | `analyst_agent.run("query", deps=ctx)` with TestModel returning all-empty dict | `call_tools=[]`, retries=0 | Raises `UnexpectedModelBehavior`/equivalent |
| B3: UsageLimitExceeded → Limited | Lead's `run_analyst_research` tool called with sub-agent raising `UsageLimitExceeded` | Same pattern as A3 | Returns `LimitedAnalystFindings`; `ctx.events` contains `"agent_limit"` event with source "Analyst" |

### Scenario Table C — Reporter agent isolation

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| C1: Valid output | `reporter_agent.run("synthesis prompt", deps=ctx)` with TestModel returning `title="T"`, `executive_summary="S"`, `sections=[...]`, `markdown_content="# T"` | `call_tools=[]` | Returns `MarketReport` with all fields populated |
| C2: Validator rejects missing title | TestModel returning empty `title=""` | `call_tools=[]`, retries=0 | Raises `UnexpectedModelBehavior`/equivalent |
| C3: Reporter failure → degraded report | Lead's `run_reporter` tool called when `reporter_agent.run()` raises `Exception("boom")` | Any exception from reporter sub-agent | Lead tool returns degraded `MarketReport(title="Report Generation Failed", sections=[], sources=[])`; no exception propagates |

### Scenario Table D — Lead orchestration

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| D1: Full sequence | `lead_agent.run("GLP-1", deps=ctx)` | All three sub-agents overridden with TestModel; lead model calls all three tools | Returns `MarketReport`; `ctx.events` has events from all three stages (Researcher, Analyst, Reporter) |
| D2: Limited researcher does not stop pipeline | `lead_agent.run("query", deps=ctx)` | Researcher returns `LimitedMarketAccessFindings`; analyst and reporter overridden and succeed | Returns `MarketReport`; pipeline completes; analyst and reporter events present in `ctx.events` |
| D3: Reporter failure → degraded report | `lead_agent.run("query", deps=ctx)` | Researcher and analyst succeed; reporter raises exception | `lead_agent.run()` returns normally (does not raise); output is degraded `MarketReport` with `sections=[]`; `ctx.events` has `"agent_limit"` event for Reporter |

### Scenario Table E — Retry route checkpoint states

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| E1: No checkpoints → full pipeline | `POST /run/{id}/retry` where session has no `research_json`, no `analyst_json` | Session exists with status='error' | New session created; `_run_pipeline` task dispatched; response 202 with new `session_id` and `stream_url` |
| E2: Research only → full pipeline | `POST /run/{id}/retry` where session has `research_json` but no `analyst_json` | `research_json` present, `analyst_json` null | New session created; `_run_pipeline` dispatched (not `_run_reporter_only`); response 202 |
| E3: Both checkpoints → reporter only | `POST /run/{id}/retry` where session has both `research_json` and `analyst_json` | Both present and valid JSON | New session created; `_run_reporter_only` dispatched; response 202 |
| E4: Analyst only (malformed) → full pipeline | `POST /run/{id}/retry` where session has `analyst_json` but no `research_json` | `analyst_json` present, `research_json` null | New session created; `_run_pipeline` dispatched (fallback); response 202 |

### Scenario Table F — Per-stage retry wrapper

| Scenario | Input | State context | Observable outcome |
|----------|-------|---------------|-------------------|
| F1: UnexpectedModelBehavior retried | Lead's `run_market_access_research` called, sub-agent raises `UnexpectedModelBehavior` on first attempt, succeeds on second | `STAGE_RETRIES=2`, sub-agent mock fails then succeeds | Returns valid `MarketAccessFindings`; `ctx.events` has at least one `"info"` event with "Retry" in message |
| F2: All retries exhausted → Limited | Lead's `run_market_access_research` called, sub-agent raises `UnexpectedModelBehavior` every attempt | `STAGE_RETRIES=2`, sub-agent always fails | Returns `LimitedMarketAccessFindings`; `ctx.events` has 2 `"info"` retry events before the `"agent_limit"` event |
| F3: TimeoutError not retried | Lead's `run_market_access_research`, sub-agent times out | `AGENT_TIMEOUT=0.001` (instant timeout) | Returns `LimitedMarketAccessFindings` with "timed out" in warning; NO retry `"info"` events |
| F4: UsageLimitExceeded not retried | Lead's `run_market_access_research`, sub-agent raises `UsageLimitExceeded` | Sub-agent raises on first call | Returns `LimitedMarketAccessFindings`; NO retry `"info"` events; `"agent_limit"` event present |

---

## Decomposition

**DECOMPOSE: yes**

Three layers are touched (test infra, production agent logic, API route tests), meeting the threshold (>3 files, >2 layers). Work units:

| Unit | Files | Dependencies |
|------|-------|--------------|
| WU1: Per-agent isolation tests | `tests/test_pipeline_stages.py` (new) — Scenarios A, B, C | None — pure test authoring; sub-agents already correct from Phase A |
| WU2: Lead orchestration + retry wrapper | `app/agents/lead.py` (retry wrapper) + `tests/test_pipeline_stages.py` (Scenarios D, F) | WU1 must exist first (file must be created); or implement in same file |
| WU3: Retry route matrix tests | `tests/test_api_run.py` (Scenarios E1–E4) | Independent of WU1/WU2 |

**Recommended execution order:** WU1 + WU3 in parallel (both are test-only), then WU2 (adds production code change + the tests that exercise it). Alternatively, implement all in one pass since `test_pipeline_stages.py` is a new file.

**DAG:**
```
WU1 ─→ WU2
WU3 (independent, can run concurrently with WU1)
```

---

## Agent Selection

- **Mode:** single-agent (all work within one codebase layer — Python backend + test files)
- **Agent:** `dev-accelerator:test-automator`
- **Reasoning:** Phase B is entirely test-infrastructure work (new test file, expanded test coverage) plus a mechanical retry-wrapper change to one production file. The test-automator agent pattern fits: write fixtures first, then the production change that makes the harder tests pass. No frontend changes, no infra/CI changes. Backend-expert is not needed because no new API routes or security surfaces are introduced; the retry logic change is additive and confined to two tool functions in `lead.py`.

---

## Implementation Notes for Executor

### Key facts confirmed before handoff

1. **pydantic-ai version:** 1.59.0. `TestModel` and `FunctionModel` are both importable and functional.
   - `from pydantic_ai.models.test import TestModel`
   - `from pydantic_ai.models.function import FunctionModel`
   - `TestModel(call_tools=[], custom_output_args={...})` produces deterministic output without network calls.

2. **Agent override pattern:** Use `agent.override(model=TestModel(...))` as a context manager. For lead+sub-agent tests, nest overrides:
   ```python
   with researcher_agent.override(model=TestModel(call_tools=[], custom_output_args={...})):
       with analyst_agent.override(model=TestModel(call_tools=[], custom_output_args={...})):
           with reporter_agent.override(model=TestModel(call_tools=[], custom_output_args={...})):
               with lead_agent.override(model=TestModel(call_tools=['run_market_access_research', 'run_analyst_research', 'run_reporter'], custom_output_args={...})):
                   result = await lead_agent.run(...)
   ```

3. **AGENT_TIMEOUT in tests:** `_AGENT_TIMEOUT` is a module-level float read at import. Use `monkeypatch.setattr(lead_module, "_AGENT_TIMEOUT", 0.001)` (via pytest's monkeypatch) or `unittest.mock.patch("app.agents.lead._AGENT_TIMEOUT", 0.001)` to force fast timeouts in timeout scenario tests. Alternatively, always override sub-agents with TestModel so no timeout triggers.

4. **Retry route dispatch verification (Scenarios E1–E4):** The retry endpoint dispatches either `_run_pipeline` or `_run_reporter_only` via `asyncio.create_task`. In tests, patch both with `AsyncMock` and assert which one was called. Pattern already established by `test_post_run_returns_202` which patches `_run_pipeline`.

5. **Validator empty-output test (A2, B2):** `TestModel(call_tools=[], custom_output_args={})` produces an output dict with no fields set, which triggers the `validate_researcher_output`/`validate_analyst_output` `ModelRetry`. With `retries=0` on the agent (or default retries exhausted), this raises `UnexpectedModelBehavior`. To force `retries=0`: `agent.override(model=TestModel(...), instrument=False)` does not set retries — use `Agent(..., retries=0)` as a module-level fixture, OR just confirm that the exception is `UnexpectedModelBehavior` (which is what pydantic-ai raises when retries are exhausted).

6. **Reporter failure test (C3, D3):** `run_reporter` already has try/except (Phase A fix). To test it: patch `reporter_agent.run` with `AsyncMock(side_effect=Exception("boom"))` INSIDE the `run_reporter` tool invocation. Since `run_reporter` uses `asyncio.wait_for(reporter_agent.run(...))`, patch at `app.agents.reporter.reporter_agent.run` level.

7. **30 existing tests must remain green.** Do not modify `test_api_run.py` existing tests; only add new ones. Do not modify conftest.py.

8. **`pyproject.toml` pydantic-ai version:** Currently `>=1.57`. The requirement doc notes to pin the version. If you pin it, update `pyproject.toml` and document in results.md. This is optional but recommended per the Known Risks in the requirement.

### Retry wrapper design decision

The requirement (Req 10) specifies: retry on `UnexpectedModelBehavior` or JSON parse failures; do NOT retry on `UsageLimitExceeded` or `asyncio.TimeoutError`. The current `except (UsageLimitExceeded, UnexpectedModelBehavior, Exception) as e` catches everything in one block. The new retry wrapper must split these into separate `except` clauses:

1. `except asyncio.TimeoutError:` → no retry, return Limited immediately
2. `except UnexpectedModelBehavior as e:` → retry up to `_STAGE_RETRIES` times, log each via `add_event("info", ...)`
3. `except UsageLimitExceeded as e:` → no retry, return Limited immediately
4. `except Exception as e:` → no retry (unknown failure), return Limited immediately

This replaces the current single `except (UsageLimitExceeded, UnexpectedModelBehavior, Exception)` catch. The retry loop wraps only the `asyncio.wait_for` call and its `UnexpectedModelBehavior` arm.

---

## Quality-Gate Artifact Check (§1.2)

None of the files in scope (`tests/test_pipeline_stages.py`, `tests/test_api_run.py`, `app/agents/lead.py`) are quality-gate artifacts (validator scripts, audit hooks, scrub blocks, gate tests, lint configs). The validation script for this scope (`.agent_process/scripts/after_edit/validate-agent_pipeline_tdd_error_handling.sh`) is not in scope for modification. No §1.2 negative-case test requirements apply.

---

## Removed Surfaces

**N/A** — no surfaces are being removed in this iteration.
