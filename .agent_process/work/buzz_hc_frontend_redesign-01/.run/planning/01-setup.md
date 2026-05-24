# Scope Setup

**Requirement:** `.agent_process/requirements_docs/ui_redesign/buzz_hc_frontend_redesign-01.md`
**Scope name:** `buzz_hc_frontend_redesign-01`
**Work folder:** `.agent_process/work/buzz_hc_frontend_redesign-01/`

---

## 5-Second Check

| Check | Status | Notes |
|-------|--------|-------|
| One sentence? | YES | "Replace the current light-theme bento-grid frontend with a dark Bloomberg-terminal aesthetic by migrating global design tokens, building a shared component library, and implementing the Landing, Query, and Sessions screens." |
| Done definition? | YES | 8 success criteria covering design tokens, fonts, component rendering, navigation, table, CI, and lucide removal. Clear and measurable. |
| Timeframe? | YES | Part 1 of 4-part design system; focused on foundation + static screens (no backend, no live session page). Appropriately scoped for 1–2 week sprint. |
| Specific name? | YES | `buzz_hc_frontend_redesign-01` — split from parent brainstorm; child requirement status. |

---

## Size Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Acceptance criteria count | 8 | 3–7 (warn 8–10, fail >10) | **WARN** |
| Files to change | 13 | 4–10 (warn 11–15, fail >15) | **WARN** |

---

## Metric Justification

**Criteria (8 = upper warn boundary):**
- All 8 criteria are tightly coupled to the redesign scope (design tokens → fonts → components → pages → CI)
- No redundancy; each is a distinct requirement validated by dev server or CI
- Appropriate for a "foundation + implementation" scope

**Files (13 = mid-warn range):**
- 5 modified (`globals.css`, `layout.tsx`, `page.tsx`, `sessions/page.tsx`, `types.ts`)
- 8 new component files (`TopNav`, `StatusDot`, `StatusChip`, `SectionLabel`, `Btn`, `KV`, `SwarmGraph`, `query/page.tsx`)
- All frontend, zero backend changes
- High cohesion: all serve the Bloomberg terminal redesign aesthetic

---

## Breakdown

Not needed — already a child requirement from brainstorm breakdown (parent: `buzz_hc_frontend_redesign`; context in `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`).

---

## Known Risks (from Requirement)

1. **SwarmGraph RAF isolation** — `requestAnimationFrame` callback must never call React setState; use `useRef` for animation state
2. **FOUC on dark theme** — must set `className="dark"` on `<html>` server-side in `layout.tsx`
3. **Status pip CSS tokens** — `--status-*` variables must be ported from light theme to new dark `:root`
4. **shadcn radius bleed** — `--radius: 0.125rem` affects all shadcn primitives; needs QA
5. **Sessions API shape** — confirm `SessionSummary` type has all fields for table (tokens, cost, sources)

---

## VERDICT: WARN

**Scope is well-defined and justified:**
- Slightly above size thresholds (8 criteria, 13 files) but all cohesive and frontend-only
- Clear split point: Part 1 (static foundation + 3 pages) vs Part 2–4 (live session, report, streaming)
- Design reference and prototype JSX provided; no ambiguity
- No backend API changes required

**Ready to proceed to assessment.**

---

## Ready

Work folder created at `.agent_process/work/buzz_hc_frontend_redesign-01/.run/planning/`.

Next step: Assessment — validate design decisions, identify dependencies, and prepare implementation roadmap.
