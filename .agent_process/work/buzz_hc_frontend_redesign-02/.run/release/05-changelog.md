# Changelog Update

**CHANGELOG.md:** Updated (entry added to [Unreleased])
**USER_CHANGELOG.md:** N/A (pr mode)

## Entry Added

### Added
- New live run observation page (`/run/<id>`) with a 3-column layout: per-agent status cards on the left, an animated swarm topology diagram in the centre, and a live event log on the right.
- Pipeline progress strip below the header showing the 5 pipeline stages (Research → Analysis → Reporting, etc.) and their current status at a glance.
- Per-agent cards that display running/idle/error state and an indeterminate progress bar while an agent is active.
- Live event log panel showing the last 10 events with source attribution and fading opacity for older entries.
- Error banner on the live run page that names the failing agent and offers a one-click **Retry Stage** button.
- Session header bar showing query text, elapsed time, agent count, token usage, and a status chip — all refreshed in real time.

### Changed
- Navigating to `/run` (bare) now redirects to the query page instead of showing an empty shell.
- Navigating to `/sessions/<id>` now redirects automatically: completed sessions go to the report page (`/report/<id>`), all others go to the new live run page (`/run/<id>`).
- After submitting a query, the app immediately navigates to the live run page instead of watching the stream inline on the query page.
