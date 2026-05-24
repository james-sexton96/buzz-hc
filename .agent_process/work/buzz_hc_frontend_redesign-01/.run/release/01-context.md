# Release Context

**Mode:** scope
**Scope:** buzz_hc_frontend_redesign-01
**Iteration:** iteration_01
**Build number:** 2
**GitHub issue:** #12

## Changes Summary
- Replaced light-theme bento-grid frontend with a dark Bloomberg-terminal aesthetic (Part 1 of 4)
- Migrated `web/app/globals.css` to full Bloomberg OKLCH dark palette with all 5 status token sets (running/complete/error/queued/paused); `--radius` set to `0.125rem`; `@theme inline` block retained for shadcn alias compatibility
- Updated `web/app/layout.tsx`: swapped fonts to IBM Plex Sans + JetBrains Mono, added `<html className="dark">` server-side (no FOUC), removed layout wrapper div and inline nav
- Built 8 new buzz atom components under `web/components/buzz/`: `StatusDot`, `StatusChip`, `SectionLabel`, `Btn`, `KV`, `TopNav`, `SwarmGraph`
- Full replacement of `web/app/page.tsx` with 3-zone Bloomberg landing (status strip + hero with SwarmGraph + feature strip); landing form pushes to `/query?q=` (never calls `startRun` directly)
- New route `web/app/query/page.tsx`: imports `startRun` directly from `@/lib/api`; `useSearchParams` wrapped in `<Suspense>`; `Cmd/Ctrl+Enter` submit; navigates to `/run/{session_id}` after run starts
- Full replacement of `web/app/sessions/page.tsx` with dense 9-column table; status filter chips with client-side counts; row click routes `complete → /report/[id]`, others → `/run/[id]`; sparse fields render `—`
- Extended `SessionStatus` in `web/lib/types.ts` to include `"queued" | "paused"`
- SwarmGraph uses RAF + imperative `setAttribute` on SVG `<circle>` refs — zero `useState` inside RAF callback

**Change type:** feature
**User-facing:** YES

## Changed Files (from git)

### root
- web/app/globals.css
- web/app/layout.tsx
- web/app/page.tsx
- web/app/query/page.tsx
- web/app/sessions/page.tsx
- web/components/buzz/Btn.tsx
- web/components/buzz/KV.tsx
- web/components/buzz/SectionLabel.tsx
- web/components/buzz/StatusChip.tsx
- web/components/buzz/StatusDot.tsx
- web/components/buzz/SwarmGraph.tsx
- web/components/buzz/TopNav.tsx
- web/lib/types.ts

## Files from Plan (for reference)

The iteration plan listed 13 files — exact match with git diff. No unplanned files were added.

| Path | Action |
|------|--------|
| `web/app/globals.css` | Modified |
| `web/app/layout.tsx` | Modified |
| `web/app/page.tsx` | Modified |
| `web/app/sessions/page.tsx` | Modified |
| `web/lib/types.ts` | Modified |
| `web/app/query/page.tsx` | New |
| `web/components/buzz/TopNav.tsx` | New |
| `web/components/buzz/StatusDot.tsx` | New |
| `web/components/buzz/StatusChip.tsx` | New |
| `web/components/buzz/SectionLabel.tsx` | New |
| `web/components/buzz/Btn.tsx` | New |
| `web/components/buzz/KV.tsx` | New |
| `web/components/buzz/SwarmGraph.tsx` | New |

**Note:** The git diff is authoritative. All 13 changed files were in scope — no out-of-plan files were introduced.
