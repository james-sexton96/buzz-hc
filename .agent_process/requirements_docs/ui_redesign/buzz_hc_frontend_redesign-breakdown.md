---
id: buzz_hc_frontend_redesign
type: breakdown
status: split
children: [buzz_hc_frontend_redesign-01, buzz_hc_frontend_redesign-02, buzz_hc_frontend_redesign-03, buzz_hc_frontend_redesign-04]
---

# Buzz HC Bloomberg-Terminal UI/UX Redesign — BREAKDOWN

**Status:** Split into 4 child requirements.
**Original brainstorm:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
**Design handoff:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/`

## Child Requirements

1. [`buzz_hc_frontend_redesign-01.md`](buzz_hc_frontend_redesign-01.md) — Foundation + Static Screens: theme migration, shared atoms, Landing, Query, Sessions
2. [`buzz_hc_frontend_redesign-02.md`](buzz_hc_frontend_redesign-02.md) — Run Screen + Persistence: `/run/[id]`, `useLiveSession`, swarm topology, agent cards, event log
3. [`buzz_hc_frontend_redesign-03.md`](buzz_hc_frontend_redesign-03.md) — Report Dossier + KPI Panels: `/report/[id]`, panel cards, footnote drawer, payer/competitive KPIs
4. [`buzz_hc_frontend_redesign-04.md`](buzz_hc_frontend_redesign-04.md) — Reporter Token Streaming: pydantic-ai streaming, schema extension, SSE events, streaming draft UI

## Execution Order

```
-01 Foundation (no deps) ──────────────────────────────────┐
                                                           ▼
-02 Run Screen (depends on -01) ──────────────────── -04 Streaming (depends on -02)
-03 Report Dossier (depends on -01, parallel with -02)
```

1. **-01 first** — Establishes design tokens, shared atoms, and `components/buzz/` that all other parts depend on.
2. **-02 + -03 in parallel** — Both depend only on -01. Run screen and report dossier are independent.
3. **-04 last** — Depends on -02 (Run screen must have the "Emerging draft" placeholder ready).

Estimated total: 4–5 weeks.

## Coverage Map

| Original Criterion | Assigned To |
|--------------------|-------------|
| Dark OKLCH theme + IBM Plex/JetBrains Mono fonts | -01 |
| Shared atom components (TopNav, StatusDot, Btn, etc.) | -01 |
| Landing page (hero, static SwarmGraph, live log) | -01 |
| Query composer screen | -01 |
| Sessions data table | -01 |
| `/run/[id]` URL-based routing (refresh persistence) | -02 |
| `useRunSession` start-only refactor | -02 |
| `/sessions/[id]` status-aware redirect | -02 |
| Run screen 3-column layout (agent cards, event log, sources) | -02 |
| SwarmTopology animated SVG | -02 |
| Pipeline progress strip + state banners | -02 |
| `/report/[id]` route | -03 |
| MarketReport.sections[] as Bloomberg panel cards | -03 |
| Payer coverage KPI panel (donut chart) | -03 |
| Competitive landscape KPI panel (bar chart) | -03 |
| Footnote drawer | -03 |
| Citation `[N]` superscript rendering | -03 |
| MarketReport schema extension (country_mix, scenarios) | -04 |
| Reporter pydantic-ai streaming mode | -04 |
| `reporter_token` SSE events in `_sse_generator` | -04 |
| `useLiveSession` reporter_token handler | -04 |
| StreamingDraft component + blinking cursor | -04 |
| Country mix panel + scenario/risk panel in report | -04 |

## Key Decisions Made in Brainstorm

1. **`app/` fully modifiable** — User confirmed. Schema extension and reporter streaming changes are in-scope.
2. **Real token streaming** — pydantic-ai `agent.run_stream()` required (not post-hoc replay). Primary technical risk for Part 4 — prototype first.
3. **KPI panels where data exists** — Payer coverage donut and competitive bar chart are in scope. Country mix and scenario panels enabled by schema extension in Part 4.
4. **Reporter token draft persistence** — Individual tokens NOT persisted to DB (high frequency). Post-refresh, only tokens after reconnect are shown — documented limitation.
5. **`router.replace` vs `router.push`** — Use `replace` in all status-aware redirects to avoid back-button traps.
6. **SwarmGraph RAF isolation** — Never call React setState from requestAnimationFrame. Use mutable refs.
7. **Dark-only mode** — Static `className="dark"` on `<html>` in `layout.tsx`; no JS toggle.

## Original Scope Summary

Full 5-screen Bloomberg-terminal redesign for Buzz HC pharma AI swarm frontend: Landing (animated SVG swarm visualization + live log), Query (research brief composer with depth/budget controls), Run (live agent topology + streaming draft + event stream, URL-based with refresh persistence), Sessions (dense data table with filters), Report (Bloomberg-style dossier with KPI panels + footnote drawer). Includes real reporter token streaming via pydantic-ai streaming API and schema extension for structured panel data.
