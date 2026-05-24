# Iteration Plan – buzz_hc_frontend_redesign-01

## Scope Overview
- **Scope Name:** buzz_hc_frontend_redesign-01
- **Date:** 2026-05-24
- **Summary:** Replace the current light-theme bento-grid frontend with a dark Bloomberg-terminal aesthetic by migrating global design tokens, building a shared component library under `web/components/buzz/`, and implementing the Landing, Query, and Sessions screens (Part 1 of 4 from `buzz_hc_frontend_redesign`).

## Requirements Source
- **Path:** `.agent_process/requirements_docs/ui_redesign/buzz_hc_frontend_redesign-01.md`
- **Document:** `buzz_hc_frontend_redesign-01.md`

*Work folder name derived from requirements path per naming convention.*

## Current Status
- Latest iteration: iteration_01 - complete
- Decision: APPROVE
- Next: `/ap_release pr`

## Acceptance Criteria (LOCKED - DO NOT MODIFY)

- [ ] `web/app/globals.css` defines the full Bloomberg OKLCH palette in `:root` (background, foreground, surface, surface-2, amber, cyan, green, red, violet, text-hi/md/lo); `--radius: 0.125rem`; `--status-running-*`, `--status-complete-*`, `--status-error-*`, `--status-queued-*`, `--status-paused-*` all defined with dark-appropriate values; `@theme inline` block retained so shadcn aliases continue to resolve; `web/app/layout.tsx` renders `<html lang="en" className="dark">` server-side (no client toggle, no FOUC).
- [ ] `web/app/layout.tsx` imports `IBM_Plex_Sans` (weights 300–700) and `JetBrains_Mono` (weights 400–600) from `next/font/google`; `Plus_Jakarta_Sans`, `Geist_Mono`, and `Lora` imports are removed; the `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper around `{children}` is removed (children render directly inside `<body>`); the inline `<nav>` is removed from layout.
- [ ] `web/app/query/page.tsx` exists at the route `/query`, imports `startRun` directly from `@/lib/api` (does NOT use `useRunSession`), reads `?q=` via `useSearchParams()` inside a `<Suspense>` boundary to pre-fill the textarea, calls `router.push('/run/' + session_id)` after `startRun()` resolves, and a `Cmd/Ctrl+Enter` keydown handler submits the form.
- [ ] `web/app/sessions/page.tsx` renders a 9-column table (ID, Query, Status, Started, Duration, Tokens, Sources, Cost, Agents) with `—` shown for fields absent from `SessionSummary`; status filter chips for All/Running/Complete/Queued/Error each display a client-side count and filter the rendered rows; clicking a row with status `complete` navigates to `/report/[id]` and any other status navigates to `/run/[id]`.
- [ ] `web/app/page.tsx` renders all 3 zones (top status strip with live stats, hero with H1 + inline query input + suggestion chips + stats row on the left and `SwarmGraph` + event log on the right, feature strip with 4 cells); the landing query form submits via `router.push('/query?q=' + encodeURIComponent(query))` and never calls `startRun` directly; `SwarmGraph` animates packet flow via `requestAnimationFrame` using imperative `setAttribute` on `<circle>` refs with no `useState`/`setState` calls inside the RAF callback.
- [ ] `web/components/buzz/TopNav.tsx` is imported and rendered at the top of `web/app/page.tsx`, `web/app/query/page.tsx`, and `web/app/sessions/page.tsx`; it contains the BuzzLogo SVG, `BUZZ·HC` wordmark, nav links with an active amber underline driven by `usePathname()`, and a pharma ticker that rotates every 4000ms via `setInterval` cleaned up on unmount.
- [ ] `uv run pytest tests/ -q` shows 53 passed / 0 failed; `cd web && pnpm test` shows 3 passed / 0 failed; `cd web && pnpm build` completes with zero TypeScript errors.
- [ ] `grep -rn "from 'lucide-react'" web/app/page.tsx web/app/sessions/page.tsx web/app/query/page.tsx web/app/layout.tsx web/app/globals.css` returns zero matches; no buzz component under `web/components/buzz/` imports from `lucide-react`.

**CRITICAL:** These criteria are FROZEN at iteration start.
New issues discovered during iteration → backlog for future scopes.

**Scope boundaries are guidance, not walls.** If meeting the acceptance criteria
correctly requires touching files outside this list, the executor may do so with:
- Documentation of what was added and why
- Validation script updated to cover new files
- Justification in results.md for reviewer assessment

## Known Patterns & Constraints

**From project conventions (CLAUDE.md / MEMORY.md):**
- Tailwind v4 with `@import "tailwindcss"` and `@theme inline` block — shadcn token aliases (`--color-background`, etc.) must continue to resolve to the underlying CSS variables; do NOT rename existing tokens
- Next.js 16 App Router; `useSearchParams()` requires a `<Suspense>` boundary
- `pnpm` v10 (frozen-lockfile in CI); `web/` package uses `pnpm tsc` for type-only check (no separate `typecheck` script)
- Tests: `uv run pytest tests/ -v` for Python (53 passing), `cd web && pnpm test` for Jest (3 passing)
- `lead_agent` and other agent code under `app/agents/`, `app/tools/`, `app/schema.py`, `app/context.py` are NEVER modified — frontend-only scope
- Existing shadcn components under `web/components/ui/` (e.g. `select.tsx`) keep their lucide-react imports — this scope only audits in-scope app files

**No relevant knowledge base entries for this scope** (0 entries matched frontend/tailwind/theme queries).

## Design Review

N/A — design review gate not required.

While the requirement is `complexity: complex`, the design handoff (prototype JSX, OKLCH palette, exact 520×360 SwarmGraph spec at `/Users/james/Downloads/design_handoff_buzz_hc_redesign/`) already encodes the design intent pixel-by-pixel. Planning Step 02 verified all design decisions can be made from the prototype + requirement without human input. The execution risk is implementation-craft, not design ambiguity, so the design review gate does not add signal here.

## Technical Assessment (by Orchestrator)

**Code Review Findings:**

- `web/app/globals.css` uses Tailwind v4 `@import "tailwindcss"` with `@theme inline`. The `--radius` is currently `0.625rem` (must become `0.125rem`). `--status-*` tokens exist only in the light `:root` block and lack `--status-queued-*` / `--status-paused-*` entirely — these must be ported into the new dark `:root`.
- `web/app/layout.tsx` currently imports `Plus_Jakarta_Sans`, `Geist_Mono`, `Lora`; wraps `{children}` in `<div className="max-w-5xl mx-auto px-4 py-8">`; and has no `className="dark"` on `<html>`. All three need surgery.
- `web/app/page.tsx` (`"use client"`) imports 4 icons from `lucide-react` (`Search`, `BarChart2`, `FileText`, `ArrowRight`); uses framer-motion for bento hover. Full replacement.
- `web/app/sessions/page.tsx` (`"use client"`) imports `ChevronRight`, `FlaskConical` from `lucide-react`; uses shadcn `Card`/`CardContent`/`Button`/`Input`. Full replacement with buzz atoms.
- `web/lib/types.ts` `SessionStatus` is `"running" | "complete" | "error"` — must be extended with `"queued" | "paused"`. `SessionSummary` lacks `duration`, `tokens`, `sources`, `cost`, `activeAgents` — those columns render `—` for Part 1 (backend additions are explicitly out of scope).
- `useRunSession.run()` bundles `startRun` + SSE setup, so `/query` page MUST import `startRun` from `@/lib/api` directly to avoid a dangling EventSource on navigation.
- Existing `lucide-react` usage in `web/components/run/` and `web/components/ui/select.tsx` is OUT of scope (Part 2+).

**Implementation Approach:**

1. **globals.css** — full `:root` replacement with Bloomberg OKLCH palette; retain `@theme inline` aliases verbatim; add `--surface`, `--surface-2`, `--amber`, `--cyan`, `--green`, `--red`, `--violet`, `--text-hi`, `--text-md`, `--text-lo` as raw CSS vars (not Tailwind aliases); port all 5 `--status-*` token pairs with dark values; set `--radius: 0.125rem`.
2. **layout.tsx** — minimal surgery: swap fonts to `IBM_Plex_Sans` + `JetBrains_Mono`; add `className="dark"` to `<html>`; remove inline `<nav>`; remove the `max-w-5xl` wrapper around `{children}`.
3. **components/buzz/** — flat dir with 8 files: `TopNav`, `StatusDot`, `StatusChip`, `SectionLabel`, `Btn`, `KV`, `SwarmGraph`. Use raw `var(--amber)` etc. — no shadcn primitives.
4. **page.tsx (landing)** — 3-zone layout; query form does `router.push('/query?q=' + encodeURIComponent(query))` (never `startRun`); reuse existing `EventFeed` from `components/run/EventFeed.tsx` with placeholder `events={[]}`.
5. **SwarmGraph** — RAF-isolated animation: static SVG (nodes/edges/grid/glow) as JSX; animated packets live in a `<g>` whose `<circle>` children are imperatively repositioned via `setAttribute('cx', ...)` in the RAF callback through a `useRef`. ZERO setState inside RAF.
6. **query/page.tsx** — `"use client"`; inner component wrapped in `<Suspense>`; pre-fills textarea from `useSearchParams().get('q')`; submit calls `startRun(query)` → `router.push('/run/' + session_id)`; `Cmd/Ctrl+Enter` keydown listener.
7. **sessions/page.tsx** — full rewrite as a 9-column dense table; client-side filter chips; row click branches on status (`complete` → `/report/[id]`, else → `/run/[id]`); render `—` for columns missing from `SessionSummary`.
8. **types.ts** — extend `SessionStatus` union to add `"queued" | "paused"`.

**Critical Implementation Notes:**

- **`max-w-5xl` wrapper removal in `layout.tsx`** — affects the existing `/run/[id]` route (Part 2 scope). Before removing the wrapper from layout, add an explicit max-width container inside `web/app/run/[id]/page.tsx` (or the equivalent run page file) so that route stays self-contained. This is a precondition for AC #2.
- **`startRun` is imported from `@/lib/api`** on the query page, NOT via `useRunSession`. The hook combines `startRun` + SSE setup, which would leave a dangling EventSource when the page navigates away to `/run/[id]`.
- **SwarmGraph RAF isolation** — `requestAnimationFrame` MUST NOT call `setState`. Use a ref-driven imperative SVG mutation pattern: keep packet state in `useRef<PacketState[]>`, mutate `<circle>` positions via `setAttribute`, and never trigger React re-renders during the animation. The prototype's `setTick(t => t+1)` pattern is explicitly forbidden.
- **`useSearchParams` Suspense boundary** — Next.js App Router requires `useSearchParams()` consumers to be wrapped in `<Suspense fallback={null}>`. The query page must export a default component that wraps the inner client component.
- **Status tokens** — when replacing `:root`, do not omit `--status-running-bg/fg`, `--status-complete-bg/fg`, `--status-error-bg/fg`. Add new `--status-queued-*` and `--status-paused-*`. Forgetting these makes `StatusDot`/`StatusChip` render as transparent.

**Known Risks:**

- **Layout wrapper removal**: affects `/run/[id]` (Part 2). Mitigate by moving the max-width container inside the run page before removing it from layout.
- **shadcn radius bleed**: `--radius: 0.125rem` (2px) affects all remaining shadcn primitives (e.g. `ScrollArea` inside `EventFeed`). Acceptable per design intent but should be QA'd visually.
- **`SessionStatus` extension**: search for any `switch`/`if-else` exhaustive consumers before adding `"queued" | "paused"`. Most consumers are in scope or already gone.
- **Font weights**: `IBM_Plex_Sans` and `JetBrains_Mono` need explicit `weight` arrays in the `next/font/google` import (not all weights are available by default).
- **Suspense for `useSearchParams`**: forgetting this causes a build-time error in Next.js 16.

**Implementation Guidance:**

- Build the 8 buzz components first (in order: `StatusDot` → `StatusChip` → `SectionLabel` → `Btn` → `KV` → `TopNav` → `SwarmGraph`) — atoms before composites.
- Update `globals.css` and `layout.tsx` together; verify dev server renders dark before touching pages.
- Land `query/page.tsx` before `page.tsx` so the landing form has a valid target route.
- Run the validation script after each file group.

**Design Decisions (made by orchestrator, not human prereqs):**

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| CSS token naming | Mix: Bloomberg tokens use prototype's `--bg`, `--surface`, `--amber`, etc. as raw CSS vars; Tailwind-integrated tokens keep existing `--background`, `--foreground` names in `@theme inline` | Pure `--buzz-*` namespace OR pure `--color-*` | The `@theme inline` block already maps `--color-background: var(--background)` — renaming would break all shadcn components. Bloomberg accent tokens (`--amber`, etc.) are only consumed by buzz components via `var()` so they need no Tailwind alias. Two-tier naming is the minimal-churn approach. |
| Dark mode strategy | Static `<html className="dark">` server-side; `:root` block becomes the dark palette directly | CSS `prefers-color-scheme` media query, client JS class toggle | Server-rendered `className="dark"` prevents FOUC entirely. App is dark-only by design. Media-query and JS toggle approaches add complexity and risk a flash. |
| SwarmGraph animation | RAF + imperative SVG DOM mutations via ref (`setAttribute`) | framer-motion, CSS animation, setState-in-RAF | framer-motion adds JSX re-render overhead. CSS animation can't do dynamic positional math along edges. setState-in-RAF causes 60fps React re-renders (choppy). Imperative ref mutation is idiomatic. |
| `components/buzz/` structure | Flat — all 8 files directly in `components/buzz/` | Subdirectories (atoms/, nav/, graph/) | Only 8 files; subdirs add import-path complexity with no scale benefit. Flat layout cleanly separates buzz from shadcn's `ui/`. |
| Query page `startRun` usage | Import `startRun` directly from `@/lib/api` | Import `useRunSession` hook | `useRunSession` bundles `startRun` + SSE EventSource setup. The query page navigates away immediately after `startRun` resolves — using the hook would leave a dangling EventSource. |
| Sessions table data gaps | Render `—` for Duration, Tokens, Sources, Cost, Agents | Fetch `SessionDetail` per row, add backend fields | Backend changes are out of scope. Per-row `getSession()` would be N+1 requests. The `—` approach matches the prototype's sparse data rendering. |

## Iteration Budget (ENFORCED)
- iteration_01: First attempt
- iteration_01_a: First revision (if needed)
- iteration_01_b: Second revision (if needed)
- iteration_01_c: Final attempt (if needed)

After iteration_01_c → Escalate to human for decision (ship/pivot/abort)

## Files in Scope (Expected)

These are the files expected to change. The executor may touch additional files
if necessary for correctness — see "Scope boundaries" note above.

| Path | Action | Purpose |
|------|--------|---------|
| `web/app/globals.css` | Modified | Replace `:root` with Bloomberg OKLCH dark palette; add `--status-*` tokens for all 5 states (running/complete/error/queued/paused); set `--radius: 0.125rem` (2px); retain `@theme inline` block to preserve shadcn token aliases |
| `web/app/layout.tsx` | Modified | Swap fonts to `IBM_Plex_Sans` + `JetBrains_Mono`; remove `Lora`; add static `className="dark"` to `<html>`; remove inline `<nav>`; REMOVE the `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper around `{children}` so pages render full-bleed |
| `web/app/page.tsx` | Modified | Full replacement with Bloomberg landing — 3-zone layout (status strip + hero with SwarmGraph + live event log + feature strip); landing query form pushes to `/query?q=<encoded>` |
| `web/app/sessions/page.tsx` | Modified | Full replacement with dense 9-column data table; status filter chips (All/Running/Complete/Queued/Error) with client-side counts; row click navigates `complete → /report/[id]`, others → `/run/[id]` |
| `web/lib/types.ts` | Modified | Extend `SessionStatus` union to include `"queued" \| "paused"`; sparse optional fields (`tokens`, `cost`, `sources`, `duration`) tolerated as `undefined` and rendered `—` |
| `web/app/query/page.tsx` | New | Two-column query composer; imports `startRun` from `@/lib/api` directly (NOT `useRunSession`); supports `?q=` pre-fill via `useSearchParams()` inside a `<Suspense>` boundary; `Cmd/Ctrl+Enter` submits and `router.push('/run/' + session_id)` |
| `web/components/buzz/TopNav.tsx` | New | 44px sticky nav: BuzzLogo SVG + `BUZZ·HC` wordmark + nav links with active amber underline + rotating pharma ticker (4s interval) + search hint + avatar |
| `web/components/buzz/StatusDot.tsx` | New | 6px square pip with status color + optional pulse animation |
| `web/components/buzz/StatusChip.tsx` | New | StatusDot + label with status-tinted border/bg |
| `web/components/buzz/SectionLabel.tsx` | New | 4px accent square + mono uppercase label |
| `web/components/buzz/Btn.tsx` | New | Primary (amber) and default variants; mono uppercase; 2px radius |
| `web/components/buzz/KV.tsx` | New | Key/value pair atom (mono label + tabular value) |
| `web/components/buzz/SwarmGraph.tsx` | New | Radial SVG graph — static nodes/edges/grid/glow rendered as JSX; animated packets via `requestAnimationFrame` mutating `<circle>` attributes through refs; NO `useState` inside RAF callback |

**Total:** 13 files
**Contract consumers:** N/A — no API, schema, or payload changes; backend untouched

## Documentation in Scope

**End User Documentation:**
- *None — internal tool, no public documentation*

**Developer Documentation:**
- *None — internal refactor; changes are self-evident in code (component locations under `web/components/buzz/`, new route at `web/app/query/page.tsx`)*

**Documentation Requirements (from CLAUDE.md):**
- [x] End user documentation updated (N/A — internal tool)
- [x] Developer documentation updated (N/A — self-evident refactor)
- [x] Documentation follows Diátaxis framework organization (N/A — no docs)
- [x] Cross-references to changed code updated (N/A)
- [x] Migration guide created (N/A — no replaced public surfaces)

## Removed Surfaces

**Removed Surfaces:** N/A — routes unchanged, only page content replaced. New `/query` route added (additive).

This scope replaces the page-component content of `web/app/page.tsx` and `web/app/sessions/page.tsx` but the public route URLs (`/` and `/sessions`) remain. The only new route is `/query`, which is purely additive.

## Validation Requirements (SCOPED)

**Hook validation (after_edit):**
- Script: `.agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-01.sh`
- Checks:
  1. `cd web && pnpm tsc` passes (TypeScript)
  2. `cd web && pnpm test` shows 3/3 Jest tests passing
  3. `<html` in `web/app/layout.tsx` contains `className="dark"`
  4. `web/app/globals.css` contains `oklch` (token migration happened)
  5. `web/app/query/page.tsx` exists
  6. `web/components/buzz/TopNav.tsx` exists
  7. `web/components/buzz/SwarmGraph.tsx` exists
  8. No `lucide-react` imports in `web/app/page.tsx`, `web/app/sessions/page.tsx`, `web/app/query/page.tsx`

**Run:** `bash .agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-01.sh`

**Skip (out of scope):**
- Global lint passes — the repo currently has no enforced lint baseline outside CI's non-blocking job; lint failures outside scope MUST NOT block this iteration.
- Pre-existing lucide-react imports in `web/components/ui/select.tsx` and `web/components/run/*.tsx` (Part 2 scope).

**Pre-existing issues (documented, out of scope):**
- 0 documented pre-existing failures. Baseline (2026-05-24):
  - `uv run pytest tests/ -q` → 53 passed
  - `cd web && pnpm test` → 3 passed
  - `cd web && pnpm build` → succeeds (4 static routes + 1 dynamic)

**Validation approach:**
- Scoped validation via hook (fast feedback)
- Document results in test-output.txt
- Orchestrator review is the quality gate (not automated enforcement)

## Scope Changes

Track any files added to scope during iterations:
- **iteration_01:** Initial scope (see Files in Scope section)
- *(Orchestrator adds entries here if scope expands during ITERATE decisions)*

## Out of Scope

- `/run/[id]` route and live session page (→ Part 2)
- `/report/[id]` route and dossier (→ Part 3)
- Reporter token streaming (→ Part 4)
- Backend API changes of any kind
- `app/schema.py` changes
- Mobile/responsive optimization below 1024px
- Command palette (`⌘K`) implementation (reserve the affordance, don't implement)
- Sessions export CSV functionality
- Lucide-react removal from `web/components/ui/` and `web/components/run/` (Part 2 scope)

## Technical Notes

- **Design handoff:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/`
- **Prototype reference:** `proto/shared.jsx`, `proto/landing.jsx`, `proto/query.jsx`, `proto/sessions.jsx`
- **Brainstorm doc:** `.agent_process/brainstorms/buzz_hc_frontend_redesign/brainstorm.md`
- **Parent requirement:** `buzz_hc_frontend_redesign` (4-part split; this is Part 1)
- Tailwind v4 `@theme inline` pattern: `--color-*` aliases in the `@theme inline` block must continue to map to the underlying `--background`/`--foreground`/etc. CSS variables — DO NOT rename or remove these aliases.
- `useRunSession` lives at `web/hooks/useRunSession.ts`; `startRun` is exported from `web/lib/api.ts` with signature `(query: string, tavilyApiKey?: string) => Promise<{ session_id: string; stream_url: string }>`.

## Time Budget
- Target: 2-4 hours implementation per iteration
- Maximum: 1-2 weeks total (3 iterations max)
- After time exceeded: Escalate to human

## Success Metrics
- All 8 acceptance criteria checked
- Scoped validation passes (`validate-buzz_hc_frontend_redesign-01.sh`)
- No regressions in scope files
- 53 Python tests still passing, 3 Jest tests still passing, `pnpm build` succeeds
