# Scope Definition

**Scope:** buzz_hc_frontend_redesign-03

---

## Files in Scope

| Path | Action | Purpose |
|------|--------|---------|
| `web/app/report/[id]/page.tsx` | New | Bloomberg-style dossier page. Client component (`"use client"`). Fetches `getSession(id)` on mount; redirects to `/run/[id]` if `status !== 'complete'` or `report` is null. Renders breadcrumb, top strip with H1 + lede + button row (Share/Export PDF placeholders, Re-run → `/query?q=<original_query>`), headline KPI row, panel grid of `MarketReport.sections[]` as `PanelCard`s (index 0 and 3 span 2 cols), conditional Payer Coverage + Competitive Landscape KPI panels, footnotes strip, and mounts `FootnoteDrawer`. Pre-processes section markdown to swap `[N]` → `<cite data-n="N">[N]</cite>` and uses `react-markdown` + `remark-gfm` with a `components.cite` override to render cyan dotted-underline superscripts that open the drawer. Includes pure helpers `normalizeCoverageStatus()` (free-text → `covered`/`restricted`/`not_covered`/`unknown`) and `parseSharePercent()` (regex `/(\d+(?:\.\d+)?)%/` against `share_or_notes`, fallback 0). Wraps `JSON.parse` of `research_json`/`analyst_json` in try/catch — parse failure is treated as null. |
| `web/components/buzz/PanelCard.tsx` | New | Reusable panel atom. Props: `accent?: string`, `sectionLabel: string`, `title?: string`, `kpi?: ReactNode`, `children: ReactNode`, `footer?: ReactNode`, `colSpan?: 1 \| 2`. Header strip with 4px accent stripe, `SectionLabel`, right-aligned title; optional KPI sub-panel; 12×14 padded body slot; optional footer source attribution. Uses `var(--surface)`, `var(--border)`, `var(--font-sans)`, `var(--font-mono)`. No `lucide-react`. |
| `web/components/buzz/FootnoteDrawer.tsx` | New | Right-side slide-in drawer. Props: `open: boolean`, `citation: { n: number; url: string; domain: string; title: string } \| null`, `onClose: () => void`. Backdrop `rgba(0,0,0,0.55)` 180ms fade; drawer 480px wide, `translateX(100%) → 0` 220ms ease via `framer-motion` `AnimatePresence` + `motion.div`. Renders citation number, title, four `KV` rows (Domain, Source, Retrieved via, Retrieved at — graceful fallbacks for missing data), excerpt block ("No excerpt available" fallback), sticky "↗ open source" CTA. ESC key closes via window keydown listener. |
| `web/components/buzz/SparkLine.tsx` | New | Tiny SVG line chart. Props: `data: number[]`, `width?: number`, `height?: number`, `color?: string`. Renders polyline scaled to bounds; returns a flat-line placeholder when data is empty or has <2 points. Used in headline + secondary KPI cells. |
| `web/components/buzz/DonutChart.tsx` | New | 64px SVG donut. Props: `value: number` (0-1 filled fraction), `size?: number`, `stroke?: number`, `color?: string`, `track?: string`. Used inside Payer Coverage KPI panel. |
| `web/lib/types.ts` | Modified | Add partial TS interfaces matching the Python schema fields rendered by the UI: `PayerCoverageEntry { payer_name; coverage_status; formulary_tier?; prior_auth_required?; step_therapy_required? }`, `CompetitorEntry { name; share_or_notes?; formulary_position?; channel? }`, `MarketAccessFindings { payer_coverage: PayerCoverageEntry[] }`, `AnalystFindings { competitive_landscape: CompetitorEntry[] }`. Existing `SessionDetail.research_json`/`analyst_json` typing (`string \| null`) remains — client-side `JSON.parse()` produces these interfaces. |
| `web/components/buzz/TopNav.tsx` | Modified | Fix `resolveActive()` so URLs starting with `/report` map to `"sessions"` (Sessions tab stays highlighted on the dossier view). Single-line change inside the existing switch/if cascade. |

**Total:** 7 files
**Contract consumers:** N/A — no API/payload changes. `web/lib/types.ts` additions are additive and only consumed by the new report page.

## Acceptance Criteria (LOCKED)

**DO NOT MODIFY during iteration. New issues → backlog.**

- [ ] Navigating to `/report/<id>` for a session with `status === 'complete'` and a non-null `report` renders the dossier page without runtime errors; if `status !== 'complete'` OR `report` is null, the page redirects to `/run/<id>`.
- [ ] Every entry in `session.report.sections[]` is rendered as a `PanelCard` with its `heading` shown in the header and its `content` rendered via `react-markdown` + `remark-gfm`; sections at index 0 and index 3 span 2 columns, all others span 1 (verified in DOM via `grid-column` style).
- [ ] When `research_json` parses to a non-null object with `payer_coverage.length > 0`, the Payer Coverage KPI panel renders with a `<DonutChart>` whose filled fraction equals `(covered + restricted) / total` after `normalizeCoverageStatus()` bucketing; when the array is empty/null OR all entries normalize to `unknown`, the panel shows the "data not available" state.
- [ ] When `analyst_json` parses to a non-null object with `competitive_landscape.length > 0`, the Competitive Landscape KPI panel renders one row per competitor with name, parsed `%` from `share_or_notes` (regex `/(\d+(?:\.\d+)?)%/`, fallback 0%), and a 5px bar whose width matches the parsed percent.
- [ ] Citation `[N]` tokens inside section markdown render as cyan superscripts with a dotted underline; clicking one opens `FootnoteDrawer` populated from `sources[N-1]` (URL as title fallback, `new URL(src).hostname` as domain); `FootnoteDrawer` animates `translateX(100%) → 0` in 220ms via framer-motion; pressing ESC closes it.
- [ ] The Re-run button on the report page navigates to `/query?q=<encoded original_query>`; clicking it from a session with a known `query` field arrives at `/query` with the textarea pre-populated (relies on existing Part 2 query-param behavior — if not yet implemented, the URL is still set correctly with the encoded `q`).
- [ ] `nextjs-build` CI job passes (`cd web && pnpm build`) with no TypeScript or lint errors introduced by the new files; `TopNav` highlights the Sessions tab when pathname starts with `/report`.

**Count:** 7 (target: 3-7)

## Documentation

- End user docs: N/A — internal UI redesign; no external user docs exist for this app.
- Developer docs: N/A — no API/architecture change. The new TS interfaces in `web/lib/types.ts` are self-documenting; the existing `MEMORY.md` already describes the relevant API surface (`research_json`/`analyst_json` as raw strings).
