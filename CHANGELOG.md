# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New live run observation page (`/run/<id>`) with a 3-column layout: per-agent status cards on the left, an animated swarm topology diagram in the centre, and a live event log on the right.
- Pipeline progress strip below the header showing the 5 pipeline stages (Research → Analysis → Reporting, etc.) and their current status at a glance.
- Per-agent cards that display running/idle/error state and an indeterminate progress bar while an agent is active.
- Live event log panel showing the last 10 events with source attribution and fading opacity for older entries.
- Error banner on the live run page that names the failing agent and offers a one-click **Retry Stage** button.
- Session header bar showing query text, elapsed time, agent count, token usage, and a status chip — all refreshed in real time.
- Redesigned the app with a dark Bloomberg-terminal aesthetic: new landing page with animated swarm graph, dense sessions table with status filter chips, and a dedicated query entry page.
- New `/query` route accepts a question, starts a research run, and navigates directly to the live run view — no extra clicks required.
- Added `queued` and `paused` as valid session statuses throughout the UI.
- Comprehensive offline test harness for the agent pipeline, covering per-agent isolation, full lead orchestration, retry-route checkpoint states, and per-stage retry behavior (17 new tests).

### Changed
- Navigating to `/run` (bare) now redirects to the query page instead of showing an empty shell.
- Navigating to `/sessions/<id>` now redirects automatically: completed sessions go to the report page (`/report/<id>`), all others go to the new live run page (`/run/<id>`).
- After submitting a query, the app immediately navigates to the live run page instead of watching the stream inline on the query page.

### Fixed
- Resolved pipeline crash bugs caused by unawaited async event calls that could silently drop events during agent runs.
- Agent pipeline now tracks which stage failed when a run errors out, making retry and debugging more reliable.
- Researcher, analyst, and reporter agents are now individually timeout-guarded; a slow or failing sub-agent no longer stalls the entire pipeline.
- Reporter failures now return a degraded report instead of crashing the run.
