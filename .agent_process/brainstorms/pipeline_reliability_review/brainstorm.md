# Brainstorm: Pipeline Reliability Review

**Date:** 2026-05-24
**Topic:** Gap analysis of `agent_pipeline_tdd_error_handling` requirement

## Summary

The existing requirement captured the core TDD + error handling intent but missed three critical bugs that are live production crashes, four files that must be touched, and four success criteria.

## Key Additions Made to Requirement

### Added (crash bugs — were not in requirement)
1. `agent_limit` missing from WorkflowEvent Literal → ValidationError on usage-limit path
2. `run_reporter` has no try/except → last-mile failure loses all prior work
3. Per-agent timeouts (asyncio.wait_for) → Ollama hangs = orphaned pipeline forever

### Corrected
4. `app/schema.py` missing from file list
5. `app/agents/reporter.py` missing from file list
6. `app/agents/researcher.py` + `app/agents/analyst.py` missing (add_event await fix)
7. add_event fix strategy specified: await-everywhere (not sync)

### New success criteria added
8. Observability: SSE events reach stream after add_event fix
9. Last-mile resilience: reporter failure produces degraded report + failed_stage, not lost run
10. Timeout signal: timeout produces failed_stage + "timeout" in error_msg
11. CI gate: < 10 seconds with no Ollama (explicit, measurable)

## Deferred (not added, separate scope)
- _run_reporter_only synthesis quality regression
- update_events write-per-event optimization
- history.py / DB checkpoint system unification
- shared usage=ctx.usage between lead + reporter

## Agent Perspectives
- [Product](/.run/03-product.md) — developer pain, prioritized gaps, success criteria
- [Architect](/.run/03-architect.md) — technical feasibility, await-everywhere rationale, file list
- [Devil's Advocate](/.run/03-critical.md) — scope split option, TestModel risks, 20% recommendation
