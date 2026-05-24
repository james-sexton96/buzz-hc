# Release Complete: PR Mode

**Context:** scope mode
**Scope:** agent_pipeline_tdd_error_handling
**Build:** build/1

## Actions Taken
- ✅ Changelog updated: [Unreleased] (new CHANGELOG.md created)
- ✅ USER_CHANGELOG.md: N/A (pr mode)
- ✅ Version files: N/A (not release mode)
- ✅ Committed: 9dcdf08568c668b42a5fe1303c15f7826308754a
- ✅ Build tagged: build/1
- ✅ Release tagged: N/A
- ✅ Pushed to: origin/scope/agent_pipeline_tdd_error_handling
- ✅ PR created: https://github.com/james-sexton96/buzz-hc/pull/11
- ✅ PR shepherd: launched
- ✅ Central sync: skipped

## PR Status
**Status:** MERGE-READY
**CI:** all passing (3/3 — Python Tests, Next.js Build, Lint)
**Tests:** 53 passing, 0.90s
**CI fix:** Shepherd resolved pre-existing issue by pinning pnpm v10 in `.github/workflows/ci.yml`

## Changelog Entry

### Added
- Comprehensive offline test harness for the agent pipeline, covering per-agent isolation, full lead orchestration, retry-route checkpoint states, and per-stage retry behavior (17 new tests).

### Fixed
- Resolved pipeline crash bugs caused by unawaited async event calls that could silently drop events during agent runs.
- Agent pipeline now tracks which stage failed when a run errors out, making retry and debugging more reliable.
- Researcher, analyst, and reporter agents are now individually timeout-guarded; a slow or failing sub-agent no longer stalls the entire pipeline.
- Reporter failures now return a degraded report instead of crashing the run.

## Release Summary

This PR completes the two-phase `agent_pipeline_tdd_error_handling` scope:

**Phase A (iteration_01):** Fixed four live crash bugs
- Made `ResearchContext.add_event` async with `await` at all 13 call sites
- Added `"agent_limit"` event type to schema
- Added `asyncio.wait_for()` timeout wrappers on all sub-agent calls in lead
- Added try/except fallback in `run_reporter` to return degraded report on failure
- Added `failed_stage` column and logic to track pipeline stage failures in DB

**Phase B (iteration_02):** Added comprehensive offline test harness
- Per-agent isolation tests using `TestModel` fixtures (scenarios A-C: researcher, analyst, reporter)
- Full lead orchestration sequence (scenario D)
- Retry-route checkpoint state tests (scenario E)
- Per-stage retry wrapper behavior with configurable retries (scenario F)

## Next Steps
- Merge PR when ready
- Run `/ap_release release minor` to ship as a release version (closes GitHub issue #10)
