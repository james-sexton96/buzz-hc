# Changelog Update

**CHANGELOG.md:** Created (new file — entry added to [Unreleased])
**USER_CHANGELOG.md:** N/A (pr mode)

## Entry Added

### Added
- Comprehensive offline test harness for the agent pipeline, covering per-agent isolation, full lead orchestration, retry-route checkpoint states, and per-stage retry behavior (17 new tests).

### Fixed
- Resolved pipeline crash bugs caused by unawaited async event calls that could silently drop events during agent runs.
- Agent pipeline now tracks which stage failed when a run errors out, making retry and debugging more reliable.
- Researcher, analyst, and reporter agents are now individually timeout-guarded; a slow or failing sub-agent no longer stalls the entire pipeline.
- Reporter failures now return a degraded report instead of crashing the run.
