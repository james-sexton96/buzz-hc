# Release Complete: pr

**Context:** scope mode
**Scope:** buzz_hc_frontend_redesign-01
**Build:** 2

## Actions Taken
- ✅ Changelog updated: [Unreleased]
- ✅ USER_CHANGELOG.md: N/A (pr mode)
- ✅ Version files: N/A (not release mode)
- ✅ Committed: 4c2acdffacc1d7db4a294a4fc3357afb98e388f7
- ✅ Build tagged: build/2
- ✅ Release tagged: N/A
- ✅ Pushed to: origin/scope/buzz_hc_frontend_redesign-01
- ✅ PR created: https://github.com/james-sexton96/buzz-hc/pull/13
- ✅ PR shepherd: skipped
- ✅ Central sync: skipped

## Changelog Entry

### Added
- Redesigned the app with a dark Bloomberg-terminal aesthetic: new landing page with animated swarm graph, dense sessions table with status filter chips, and a dedicated query entry page.
- New `/query` route accepts a question, starts a research run, and navigates directly to the live run view — no extra clicks required.
- Added `queued` and `paused` as valid session statuses throughout the UI.

## Next Steps
- `pr` mode: Merge PR when ready, run `/ap_release release <type>` to ship
