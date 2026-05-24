---
id: buzz_hc_frontend_redesign-03
type: requirement
category: ui_redesign
status: not_started
priority: HIGH
complexity: moderate
split_from: buzz_hc_frontend_redesign
depends_on: [buzz_hc_frontend_redesign-01]
source: ap-brainstorm
---

# Requirements: Bloomberg-Terminal UI Redesign — Part 3: Report Dossier + KPI Panels

**Split from:** `buzz_hc_frontend_redesign` (see `buzz_hc_frontend_redesign-breakdown.md` for full context)

**Prerequisites:** `buzz_hc_frontend_redesign-01` must be complete (design tokens, shared atoms). Can run in parallel with Part 2.

---

## Objective

Implement the `/report/[id]` Bloomberg-style dossier screen that renders `MarketReport.sections[]` as panel cards and surfaces structured KPI data from `research_json`/`analyst_json` as typed visualizations.

## Background

The current report viewer is a single `ReportViewer` component rendering the full report as a markdown prose blob. The redesign replaces it with a Bloomberg-style panel grid: each `MarketReport.section` (heading + markdown content) becomes a `PanelCard`, and structured fields from `research_json`/`analyst_json` (payer coverage, competitive landscape) become typed KPI panels with simple charts.

The report screen also introduces the Footnote Drawer — a slide-in panel triggered by clicking any citation `[N]` superscript or footnote card.

`research_json` (type: `MarketAccessFindings`) and `analyst_json` (type: `AnalystFindings`) are already exposed on the session detail endpoint. These provide structured data for optional KPI panels beyond the markdown sections.

---

## Technical Requirements

1. **`/report/[id]` route** (`web/app/report/[id]/page.tsx`) — New page. Fetches `getSession(id)` on load. Requires `session.status === 'complete'` — if not, redirect to `/run/[id]`. Renders the Bloomberg dossier layout.

2. **Breadcrumb + Top strip** — Breadcrumb: `SESSIONS › <ID> › DOSSIER`. Top strip: dossier meta row (amber ID, category, period) + H1 56px + lede paragraph with inline citation links + button row (Share, Export PDF, Re-run) + source/cite counts.

3. **Headline KPI row** — First cell (surface bg): amber `HEADLINE · TAM 2030` label + large value + CAGR + sparkline (220×36 SVG). Four secondary cells: smaller KPIs with sparklines. Data source: `session.report.executive_summary` parsed for key metrics, OR synthesized from `analyst_json.market_size` fields. Gracefully degrade to placeholder if data is absent.

4. **`<PanelCard>` component** (`web/components/buzz/PanelCard.tsx`) — Reusable panel with header strip (4px accent stripe + section label + right-aligned title), optional KPI sub-panel, body (12×14 padding, markdown-rendered content), and footer (source attribution). Used for every `MarketReport.section`.

5. **Panel grid** (`grid-template-columns: repeat(3, 1fr)`, `gap: 16px`) — Renders one `PanelCard` per `MarketReport.section`. Sections that span 2 columns: detect by heading keyword (e.g. "Country" or "Catalysts") or use first and fourth sections. Falls back to equal 1-col cards for all sections if fewer than 5 sections present.

6. **Payer Coverage KPI panel** — Rendered when `session.research_json.payer_coverage[]` is non-empty. Shows a 64px SVG donut chart (filled % = `covered + conditional` / total) + labeled status breakdown (Full=green, Cond=cyan, None=red). Normalizes free-form `coverage_status` strings to four buckets: `covered`, `restricted`, `not_covered`, `unknown`. Shows "data not available" state when all normalize to `unknown`.

7. **Competitive Landscape KPI panel** — Rendered when `session.analyst_json.competitive_landscape[]` is non-empty. Shows sponsor rows: label + right-aligned % share + 5px filled bar in sponsor color. Product list in mono 9px below.

8. **Footnotes strip** — Fixed strip at bottom of page. Shows 6 of N citations from `MarketReport.sources[]`. Each card: `[N]` number + source title + domain URL. Click → opens Footnote Drawer.

9. **`<FootnoteDrawer>` component** (`web/components/buzz/FootnoteDrawer.tsx`) — Fixed right-side drawer. Backdrop: `rgba(0,0,0,0.55)` fade 180ms. Drawer: 480px wide, `translateX(100%) → translateX(0)` 220ms ease (framer-motion `AnimatePresence`). Contents: citation number + title + 4 KVs (Domain/Source/Retrieved via/Retrieved at) + excerpt block + sticky "↗ open source" CTA. ESC key closes.

10. **Citation rendering** — In section body markdown, render `[N]` references as `<sup>` elements in cyan with dotted underline. Clicking a `<sup>` opens the FootnoteDrawer for that citation. Use `react-markdown` with a custom `text` renderer to intercept `[N]` patterns.

11. **`<SparkLine>` component** (`web/components/buzz/SparkLine.tsx`) — Tiny SVG line chart. Props: `data: number[]`, `width`, `height`, `color`. Used in headline KPI cells and secondary KPI cells.

12. **Re-run button** — Navigates to `/query?q=<original_query>`. Query page reads `?q` param and pre-fills the textarea.

---

## Success Criteria

- [ ] `/report/<id>` renders for a real completed session without errors
- [ ] All `MarketReport.sections[]` render as `PanelCard` components with correct headings and markdown content
- [ ] Payer Coverage donut renders when `research_json.payer_coverage[]` is non-empty; shows "data not available" when empty
- [ ] Competitive Landscape bar chart renders when `analyst_json.competitive_landscape[]` is non-empty
- [ ] FootnoteDrawer slides in from right in 220ms on citation click; ESC key closes it
- [ ] Citation `[N]` superscripts render in cyan with dotted underline throughout section body text
- [ ] `/report/<id>` redirects to `/run/<id>` when session status is not `complete`
- [ ] Re-run button pre-fills the Query screen with the original query
- [ ] `nextjs-build` CI passes

---

## Files Expected to Change

**New:**
- `web/app/report/[id]/page.tsx`
- `web/components/buzz/PanelCard.tsx`
- `web/components/buzz/FootnoteDrawer.tsx`
- `web/components/buzz/SparkLine.tsx`
- `web/components/buzz/DonutChart.tsx`

**Modified:**
- `web/lib/types.ts` — add `DossierPanels` type, confirm `MarketAccessFindings`/`AnalystFindings` TS types match current Python schema

**Estimated:** 6 files

---

## Out of Scope

- Country mix table panel (requires schema extension → Part 4)
- Scenario/risk probability table panel (requires schema extension → Part 4)
- Export PDF functionality (placeholder button only)
- Share functionality (placeholder button only)
- Streaming draft in the report (not applicable — report is final)
- Mobile optimization

---

## Known Risks

- **`payer_coverage[].coverage_status` normalization** — Free-form string (e.g. "covered with PA requirement"). Must use lowercase + regex to bucket into `{covered, restricted, not_covered, unknown}`. Add a `normalizeCoverageStatus` utility with unit tests.
- **`research_json`/`analyst_json` type safety** — These are returned as raw JSON strings from the API (`JSON.parse` needed). Null when the run errored before that stage. Always check for null before rendering KPI panels.
- **Section span heuristic** — Detecting which sections should span 2 columns by keyword is fragile. The reporter agent produces archetype-driven headings but exact wording may vary. Consider a fallback: always render single-column if span heuristic fails.
- **`MarketReport.sources[]` is a list of URLs** — The design's footnote cards expect `{n, title, domain, url, agent, excerpt}` but `sources[]` is just `string[]`. The citation superscripts from markdown won't automatically map to `sources[]` indices. May need to number citations in order of appearance in markdown + use URL as title fallback.

---

## Notes

### Brainstorm Source
- **Brainstorm doc:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
- **Date:** 2026-05-24
- **Design handoff:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/report.jsx`

### Feasibility Review Key Findings
- `research_json` and `analyst_json` VERIFIED on `GET /sessions/{id}` response (api/routes/sessions.py:67-68)
- `payer_coverage[]` has fields: `coverage_status`, `formulary_tier`, `prior_auth_required`, `step_therapy_required`
- `competitive_landscape[]` confirmed in `AnalystFindings`
- `MarketReport.sources[]` is `list[str]` (URLs only) — footnote card needs graceful degradation

---
*Part 3 of 4 from `buzz_hc_frontend_redesign`. See breakdown file for complete context.*
