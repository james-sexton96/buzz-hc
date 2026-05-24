# Brainstorm Synthesis: Pipeline Reliability Review

**Topic:** Gap analysis of `agent_pipeline_tdd_error_handling` requirement
**Date:** 2026-05-24
**Agents:** Product Strategist, Software Architect, Devil's Advocate

---

## Unanimous Findings (All Three Agents Agree)

### 1. `agent_limit` Literal bug is a live production crash (NOT in current requirement)
- `WorkflowEvent.event_type` Literal does NOT include `"agent_limit"`
- `lead.py` emits `"agent_limit"` on UsageLimitExceeded — causes pydantic ValidationError
- This is a crash on the DESIGNED fallback path — the graceful degradation that was meant to protect users is itself crashing
- Fix: add `"agent_limit"` to Literal in `app/schema.py` (one line)
- Required file: `app/schema.py` — MISSING from current file list

### 2. Reporter has no try/except — highest-value missing protection (NOT in current requirement)
- `run_reporter` tool in `lead_agent` has zero error handling
- Researcher + analyst have `try/except` with `LimitedXFindings` — reporter has none
- Reporter failure after 7+ minutes of successful prior work = total loss, no recovery
- Fix: mirror the existing pattern; return a degraded `MarketReport` with error in executive_summary
- Required file: `app/agents/reporter.py` — MISSING from current file list

### 3. `researcher.py` and `analyst.py` missing from file list
- The add_event fix (req #1) requires `await` at EVERY call site
- Both files contain `ctx.deps.add_event(...)` calls without `await`
- These files MUST be in the implementation list

---

## Strong Consensus (Two of Three Agents)

### 4. `await`-everywhere is the correct fix for add_event
- Make `ResearchContext.add_event` an `async def` (or keep sync base + make all call sites await the override)
- Product + Architect both confirm: all call sites in lead/researcher/analyst/reporter must use `await`
- The fix is mechanical and grep-verifiable
- Devil's Advocate proposes sync-everywhere as simpler — but Architect correctly identifies that would create a coordination problem with the async DB write

### 5. Timeouts are low-risk, high-value and belong in this scope
- Ollama hangs = pipeline hangs forever, background task orphaned in `_active_streams`
- Fix: `asyncio.wait_for(agent.run(...), timeout=float(os.environ.get("AGENT_TIMEOUT", "120")))` per tool
- Env-var configurable, ~3 lines per tool wrapper, high operational value
- Explicit timeout produces a clean `failed_stage` label — makes the DB field actually useful

### 6. New success criteria are needed
Currently missing from the requirement:
- **Observability**: After each stage completes, ≥1 SSE event with that stage's name reaches the stream (verifies add_event fix is real)
- **Last-mile resilience**: Reporter failure produces `failed_stage='reporter'` + findings preserved, not a lost run
- **Timeout signal**: Sub-agent timeout produces `failed_stage='researcher|analyst|reporter'` + "timeout" in error_msg
- **CI gate**: Full test suite runs < 10 seconds on cold start with no Ollama process

---

## Debated Items

### 7. Scope split: one requirement vs three PRs
- **Devil's Advocate:** Split into Tier 1 (crash bugs), Tier 2 (test infra), Tier 3 (arch improvements) — avoids blocking urgent bug fixes on a 2-week TDD build
- **Product + Architect:** Keep as one — the fixes are causally coupled; fixing add_event without agent_limit still fails limit path tests; fixing bugs without tests leaves them unvalidated
- **Synthesis:** Keep as one requirement BUT structure implementation as Phase A (bugs first, smoke tests) then Phase B (full TDD harness). This preserves the coherent scope while allowing the urgent fixes to be done first in iteration_01 and tested quickly.

### 8. TestModel stability risk
- **Devil's Advocate:** Pre-1.0 API could break; hardcoded-JSON patches are simpler
- **Architect:** Risk is real but manageable — assert on DB state + SSE events, not pydantic-ai internals
- **Synthesis:** Use `FunctionModel` (more stable than TestModel) where possible; test through public interfaces (DB state, event list); document the pydantic-ai version pin in Known Risks

### 9. Deferred items (do NOT add to this scope)
- Bug 4 (shared usage object) — token accounting, not reliability
- Bug 6 (update_events write frequency) — performance optimization, not correctness
- Bug 7 (_run_reporter_only template quality) — quality concern, separate scope
- Bug 8 (history.py divergence) — technical debt, separate scope

---

## Scope Check

**Updated metrics after adding gaps:**
- Files: 12 (was 8) → WARN threshold (11-15)
- Criteria: 11 (was 7, +4 new) → WARN threshold (8-10 is warn, >10 is fail... wait, re-checking: >10 is fail)
- Subsystems: 4 (agents, API/routes, test infra, DB+schema) → WARN threshold

**VERDICT: WARN** (criteria count at fail boundary, files at warn)

**Recommendation:** Keep as one scope but note in Known Risks. The criteria count can be kept at 10 by merging the observability criteria and keeping timeout signal as a sub-criterion.

---

## Required Requirement Updates

1. Add Technical Requirement 9: Fix `agent_limit` event type (app/schema.py)
2. Add Technical Requirement 10: Reporter try/except with degraded MarketReport fallback
3. Add Technical Requirement 11: Per-agent timeout (asyncio.wait_for, env-configurable)
4. Clarify Req 1 add_event fix: specify await-everywhere approach
5. Add to Files: app/schema.py, app/agents/reporter.py, app/agents/researcher.py, app/agents/analyst.py
6. Add 4 missing Success Criteria
7. Update Known Risks: retry multiplication (pydantic-ai inner + outer), TestModel stability, timeout calibration
8. Add implementation phasing note: Phase A = bugs + smoke tests (iteration_01), Phase B = full harness (iteration_02)
