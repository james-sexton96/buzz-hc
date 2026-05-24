# Scope Size Check

**Requirement:** Buzz HC Bloomberg-Terminal UI/UX Redesign
**Checked:** 2026-05-24

## 5-Second Check

1. **One sentence:** YES — "Replace the Buzz HC Next.js frontend with a Bloomberg-terminal-aesthetic 5-screen app featuring live swarm visualization, persistent streaming, and structured report dossiers."
2. **Done definition:** YES — Each screen has pixel-level design specs from the design handoff; streaming is testable via SSE events; CI gates exist.
3. **Timeframe:** NO — 5 screens + real reporter streaming + schema extension + swarm animation is 4–6 weeks. Exceeds the 1–2 week target.
4. **Specific name:** YES — "Bloomberg-Terminal UI/UX Redesign" is specific.

## Size Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Criteria count | 12 | 3-7 (warn 8-10, fail >10) | **FAIL** |
| Files to change | ~25 | 4-10 (warn 11-15, fail >15) | **FAIL** |
| Subsystems | 5 | 1-3 (warn 4, fail >4) | **FAIL** |

**Criteria counted:**
1. All 5 screens implemented to Bloomberg terminal design fidelity
2. Dark-only OKLCH theme (IBM Plex Sans + JetBrains Mono) deployed globally
3. `/run/[id]` URL-based routing — streaming persists on page refresh
4. Sessions table with status filters + click-to-navigate
5. Report dossier renders `MarketReport.sections[]` as Bloomberg panel cards
6. KPI panels (payer coverage donut, competitive bar chart) from `research_json`/`analyst_json`
7. Real reporter token streaming via pydantic-ai streaming + `reporter_token` SSE events
8. `MarketReport` schema extended with structured panel data fields
9. Swarm visualization SVG on Landing and Run screens
10. Footnote drawer on Report screen
11. All 26 Python tests + 3 Jest tests pass; `nextjs-build` CI passes
12. `useRunSession` refactored to "start only" (handover to `useLiveSession`)

**Subsystems:**
1. Frontend screens (web/app/)
2. Shared component library (web/components/buzz/)
3. React hooks (web/hooks/)
4. Backend API (api/routes/)
5. Agent/Schema layer (app/schema.py + app/agents/)

## Override Status

`scope_override: false` — no override requested.

## Red Flags

- Timeframe exceeds 1–2 week target (estimated 4–6 weeks)
- Touches 5 distinct architectural subsystems simultaneously

## VERDICT: FAIL

All three size thresholds exceeded.

---

## Recommended Breakdown

4 child requirements, sequenced by dependency:

| Child | Name | Focus | Est. |
|-------|------|-------|------|
| `-01` | Foundation + Static Screens | Theme, atoms, Landing, Query, Sessions | 1 week |
| `-02` | Run Screen + Persistence | `/run/[id]`, `useLiveSession`, Run UI, swarm graph | 1 week |
| `-03` | Report Dossier + KPI Panels | `/report/[id]`, panel cards, footnote drawer, KPI charts | 1 week |
| `-04` | Reporter Streaming | Schema extension, pydantic-ai streaming, SSE events, draft reveal | 1-2 weeks |

**Dependency order:** -01 → -02 → -03 (parallel with -02) → -04 (depends on -02 for run screen)
