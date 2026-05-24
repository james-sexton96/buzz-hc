---
id: buzz_hc_frontend_redesign-01
type: requirement
category: ui_redesign
status: approved
priority: HIGH
complexity: complex
split_from: buzz_hc_frontend_redesign
depends_on: []
source: ap-brainstorm
---

# Requirements: Bloomberg-Terminal UI Redesign — Part 1: Foundation + Static Screens

**Split from:** `buzz_hc_frontend_redesign` (see `buzz_hc_frontend_redesign-breakdown.md` for full context)

---

## Objective

Replace the current light-theme bento-grid frontend with a dark Bloomberg-terminal aesthetic by migrating global design tokens, building a shared component library, and implementing the Landing, Query, and Sessions screens.

## Background

The current Buzz HC frontend uses a light shadcn/ui default theme with Plus Jakarta Sans / Geist Mono / Lora fonts and a bento-grid landing page. The redesign targets a "Bloomberg terminal meets modern AI" aesthetic: dark navy surfaces, OKLCH color tokens, IBM Plex Sans + JetBrains Mono fonts, max 2px border-radius, and dense data-forward layouts.

This first part establishes the foundation (design tokens, shared atoms) and implements the three screens that require no backend changes: Landing (hero + static swarm graph + live log), Query (research brief composer), and Sessions (data table).

The design reference is in `/Users/james/Downloads/design_handoff_buzz_hc_redesign/`. The prototype JSX files (`proto/shared.jsx`, `proto/landing.jsx`, `proto/query.jsx`, `proto/sessions.jsx`) are the pixel-level source of truth.

---

## Technical Requirements

1. **Design token migration** — Replace `web/app/globals.css` `:root` with the Bloomberg dark palette (OKLCH). All eight surface/text/accent tokens defined per the design handoff. Dark-only: no `.dark` class toggle. `--radius: 0.125rem` (2px). Status pip tokens included.

2. **Font swap** — Replace Plus Jakarta Sans / Geist Mono / Lora with IBM Plex Sans (300–700) + JetBrains Mono (400–600) via `next/font/google`. Set `<html className="dark">` statically in `app/layout.tsx` to prevent FOUC. Remove Lora entirely.

3. **Shared atom components** (`web/components/buzz/`) — Build these once, used on all 5 screens:
   - `TopNav` — 44px sticky nav with BuzzLogo SVG, wordmark, nav links, rotating pharma ticker, search hint, avatar
   - `StatusDot` — 6px square with color + optional pulse animation per status
   - `StatusChip` — dot + label with status-tinted border/bg
   - `SectionLabel` — 4px accent square + mono uppercase label
   - `Btn` — primary (amber) and default variants, mono uppercase, 2px radius
   - `KV` — key/value pair for metrics (mono label + tabular value)

4. **Landing page** (`web/app/page.tsx`) — Full 3-zone layout: TopNav + status strip (live stats) + hero (left: H1, inline query input, suggestion chips, stats row; right: static SwarmGraph SVG + live event log) + feature strip (4 cells). SwarmGraph renders SVG with grid overlay, glow, hub, 4 satellite nodes, dashed edges, and animated packets (requestAnimationFrame). No real data needed on the right panel — can show placeholder events or last session's events.

5. **SwarmGraph component** (`web/components/buzz/SwarmGraph.tsx`) — Reusable radial SVG graph. Props: `size`, `nodeStates` (per-agent status). Uses `requestAnimationFrame` for packet flow animation isolated from React state (never calls `setState` inside the RAF loop). Implements the exact 520×360 spec from the design handoff.

6. **Query screen** (`web/app/query/page.tsx`) — New route. Two-column layout: left (brief textarea, depth selector 3-segment toggle, token budget slider, dispatch CTA); right (plan preview: brief echo, planned stages list, agents on call). On submit: `startRun()`, then `router.push('/run/' + sessionId)`. Keyboard shortcut: `Cmd/Ctrl+Enter` → submit.

7. **Sessions screen** (`web/app/sessions/page.tsx`) — Replace current card list with dense data table matching design spec: 9-column table, status filter chips (All/Running/Complete/Queued/Error with counts), search box, stats bar (6 KPIs), pagination footer. Row click: running/queued/error → `/run/[id]`; complete → `/report/[id]`. Uses existing `getSessions()` API — no backend changes.

8. **Lucide-react audit** — Grep all `from 'lucide-react'` imports across `web/` and replace with ASCII/Unicode equivalents per the design spec. Remove the import from `web/components/ui/` components being replaced.

9. **CI gate** — `pnpm build` must pass. Existing 3 Jest tests must remain green. Landing query form submission navigates to `/query?q=<encoded>` (not directly to run).

---

## Success Criteria

- [ ] All OKLCH design tokens defined in `globals.css`; `--radius: 0.125rem`; `<html className="dark">` set statically with no FOUC
- [ ] IBM Plex Sans + JetBrains Mono render correctly; Lora import removed
- [ ] TopNav renders on all implemented pages with correct ticker rotation (4s) and active-link underline
- [ ] SwarmGraph SVG renders with animated packet flows on the Landing page (verified via dev server)
- [ ] Landing page matches the 3-zone design spec: status strip, hero (left + right), feature strip
- [ ] Query screen submits via keyboard (`Cmd+Enter`) and navigates to `/run/<id>` after `startRun()`
- [ ] Sessions table renders all sessions with correct status-filter chips, row styling, and correct click navigation (complete → `/report/[id]`; active → `/run/[id]`)
- [ ] `nextjs-build` CI passes; 3 Jest tests green
- [ ] No `lucide-react` imports remain in redesigned pages/components

---

## Files Expected to Change

**Modified:**
- `web/app/globals.css` — design token migration
- `web/app/layout.tsx` — font swap, `<html className="dark">`
- `web/app/page.tsx` — landing redesign
- `web/app/sessions/page.tsx` — table redesign
- `web/lib/types.ts` — minor: ensure `SessionSummary` has all fields needed for table

**New:**
- `web/app/query/page.tsx`
- `web/components/buzz/TopNav.tsx`
- `web/components/buzz/StatusDot.tsx`
- `web/components/buzz/StatusChip.tsx`
- `web/components/buzz/SectionLabel.tsx`
- `web/components/buzz/Btn.tsx`
- `web/components/buzz/KV.tsx`
- `web/components/buzz/SwarmGraph.tsx`

**Estimated:** 13 files (WARN — complex but cohesive; all frontend)

---

## Out of Scope

- `/run/[id]` route and live session page (→ Part 2)
- `/report/[id]` route and dossier (→ Part 3)
- Reporter token streaming (→ Part 4)
- Backend API changes of any kind
- `app/schema.py` changes
- Mobile/responsive optimization below 1024px
- Command palette (`⌘K`) implementation (reserve the affordance, don't implement)
- Sessions export CSV functionality

---

## Known Risks

- **SwarmGraph RAF isolation** — `requestAnimationFrame` callback must never call React setState. Use a mutable ref (`useRef`) for animation state; read `nodeStates` prop via ref inside RAF. If setState is called from RAF, re-renders during animation will be choppy.
- **FOUC on dark theme** — must set `className="dark"` on `<html>` server-side (in `layout.tsx`), not via client JS. Next.js App Router `layout.tsx` is server-rendered; this is safe.
- **Status pip CSS tokens** — `--status-*` variables currently exist only in `:root` (light). Must port them into the new dark `:root`. Easy to miss; will silently use wrong colors if omitted.
- **shadcn component radius bleed** — shadcn components reference `--radius`. Setting it to `0.125rem` (2px) affects all shadcn primitives. QA every shadcn component at this radius before declaring done.
- **Sessions API shape** — confirm `SessionSummary` type includes `tokens`, `cost`, `sources` fields needed for the table; if missing, may need a minor backend route update (out of scope for this part).

---

## Notes

### Brainstorm Source
- **Brainstorm doc:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
- **Date:** 2026-05-24
- **Design handoff:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/`
- **Prototype reference:** `prototype/proto/shared.jsx`, `proto/landing.jsx`, `proto/query.jsx`, `proto/sessions.jsx`

### Feasibility Review Key Findings
- All 8 synthesis claims verified against actual code
- framer-motion v12 already installed (can use for drawer, but RAF preferred for swarm)
- Tailwind v4 `@theme inline` pattern confirmed; single `:root` swap cascades correctly
- `--status-*` tokens exist only in `:root` (light) — must be ported

---
*Part 1 of 4 from `buzz_hc_frontend_redesign`. See breakdown file for complete context.*
