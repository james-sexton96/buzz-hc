# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Redesigned the app with a dark Bloomberg-terminal aesthetic: new landing page with animated swarm graph, dense sessions table with status filter chips, and a dedicated query entry page.
- New `/query` route accepts a question, starts a research run, and navigates directly to the live run view — no extra clicks required.
- Added `queued` and `paused` as valid session statuses throughout the UI.
- Comprehensive offline test harness for the agent pipeline, covering per-agent isolation, full lead orchestration, retry-route checkpoint states, and per-stage retry behavior (17 new tests).

### Fixed
- Resolved pipeline crash bugs caused by unawaited async event calls that could silently drop events during agent runs.
- Agent pipeline now tracks which stage failed when a run errors out, making retry and debugging more reliable.
- Researcher, analyst, and reporter agents are now individually timeout-guarded; a slow or failing sub-agent no longer stalls the entire pipeline.
- Reporter failures now return a degraded report instead of crashing the run.
