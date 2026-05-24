# Execution Preparation

**Scope:** buzz_hc_frontend_redesign-01
**Iteration:** iteration_01
**Type:** first_iteration

## Criteria (LOCKED)

- [ ] `web/app/globals.css` defines the full Bloomberg OKLCH palette in `:root` (background, foreground, surface, surface-2, amber, cyan, green, red, violet, text-hi/md/lo); `--radius: 0.125rem`; `--status-running-*`, `--status-complete-*`, `--status-error-*`, `--status-queued-*`, `--status-paused-*` all defined with dark-appropriate values; `@theme inline` block retained so shadcn aliases continue to resolve; `web/app/layout.tsx` renders `<html lang="en" className="dark">` server-side (no client toggle, no FOUC).
- [ ] `web/app/layout.tsx` imports `IBM_Plex_Sans` (weights 300–700) and `JetBrains_Mono` (weights 400–600) from `next/font/google`; `Plus_Jakarta_Sans`, `Geist_Mono`, and `Lora` imports are removed; the `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper around `{children}` is removed (children render directly inside `<body>`); the inline `<nav>` is removed from layout.
- [ ] `web/app/query/page.tsx` exists at the route `/query`, imports `startRun` directly from `@/lib/api` (does NOT use `useRunSession`), reads `?q=` via `useSearchParams()` inside a `<Suspense>` boundary to pre-fill the textarea, calls `router.push('/run/' + session_id)` after `startRun()` resolves, and a `Cmd/Ctrl+Enter` keydown handler submits the form.
- [ ] `web/app/sessions/page.tsx` renders a 9-column table (ID, Query, Status, Started, Duration, Tokens, Sources, Cost, Agents) with `—` shown for fields absent from `SessionSummary`; status filter chips for All/Running/Complete/Queued/Error each display a client-side count and filter the rendered rows; clicking a row with status `complete` navigates to `/report/[id]` and any other status navigates to `/run/[id]`.
- [ ] `web/app/page.tsx` renders all 3 zones (top status strip with live stats, hero with H1 + inline query input + suggestion chips + stats row on the left and `SwarmGraph` + event log on the right, feature strip with 4 cells); the landing query form submits via `router.push('/query?q=' + encodeURIComponent(query))` and never calls `startRun` directly; `SwarmGraph` animates packet flow via `requestAnimationFrame` using imperative `setAttribute` on `<circle>` refs with no `useState`/`setState` calls inside the RAF callback.
- [ ] `web/components/buzz/TopNav.tsx` is imported and rendered at the top of `web/app/page.tsx`, `web/app/query/page.tsx`, and `web/app/sessions/page.tsx`; it contains the BuzzLogo SVG, `BUZZ·HC` wordmark, nav links with an active amber underline driven by `usePathname()`, and a pharma ticker that rotates every 4000ms via `setInterval` cleaned up on unmount.
- [ ] `uv run pytest tests/ -q` shows 53 passed / 0 failed; `cd web && pnpm test` shows 3 passed / 0 failed; `cd web && pnpm build` completes with zero TypeScript errors.
- [ ] `grep -rn "from 'lucide-react'" web/app/page.tsx web/app/sessions/page.tsx web/app/query/page.tsx web/app/layout.tsx web/app/globals.css` returns zero matches; no buzz component under `web/components/buzz/` imports from `lucide-react`.

## Concrete Scenario Coverage

### AC #4 — Sessions row click (divergent alternatives)

| Input (user action) | State context | Observable outcome |
|---|---|---|
| Click row with status `complete` | Sessions table populated; row has status=complete | Router navigates to `/report/<id>`; URL changes to `/report/<id>` |
| Click row with status `running` | Sessions table populated; row has status=running | Router navigates to `/run/<id>`; URL changes to `/run/<id>` |
| Click row with status `error` | Sessions table populated; row has status=error | Router navigates to `/run/<id>`; URL changes to `/run/<id>` |
| Click row with status `queued` | Sessions table populated; row has status=queued | Router navigates to `/run/<id>`; URL changes to `/run/<id>` |

### AC #5 — SwarmGraph RAF isolation (state-dependent)

| Input | State context | Observable outcome |
|---|---|---|
| Page renders with SwarmGraph | Component mounts | Packets animate (move); no React re-render triggered per animation frame |
| Inspect React DevTools Profiler during animation | SwarmGraph mounted and animating | Zero commits to React fiber tree per animation frame |
| Source code review: RAF callback body | SwarmGraph.tsx opened | No `setState` / `useState` setter calls present inside the RAF callback |

### AC #6 — TopNav on all 3 pages (universal quantifier)

| Input | State context | Observable outcome |
|---|---|---|
| Navigate to `/` | App rendered | TopNav 44px sticky header visible at top of page |
| Navigate to `/query` | App rendered | TopNav visible; "Research" nav link shows active amber underline |
| Navigate to `/sessions` | App rendered | TopNav visible; "Sessions" nav link shows active amber underline |

## Files in Scope

| Path | Action | Work Unit |
|------|--------|-----------|
| `web/app/globals.css` | Modified | A: Foundation |
| `web/app/layout.tsx` | Modified | A: Foundation |
| `web/lib/types.ts` | Modified | A: Foundation |
| `web/components/buzz/StatusDot.tsx` | New | B: Atoms |
| `web/components/buzz/StatusChip.tsx` | New | B: Atoms |
| `web/components/buzz/SectionLabel.tsx` | New | B: Atoms |
| `web/components/buzz/Btn.tsx` | New | B: Atoms |
| `web/components/buzz/KV.tsx` | New | B: Atoms |
| `web/components/buzz/TopNav.tsx` | New | B: Atoms |
| `web/components/buzz/SwarmGraph.tsx` | New | B: Atoms |
| `web/app/page.tsx` | Modified (full replacement) | C: Pages |
| `web/app/sessions/page.tsx` | Modified (full replacement) | C: Pages |
| `web/app/query/page.tsx` | New | C: Pages |

## Validation

- **RUN:** `bash .agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-01.sh buzz_hc_frontend_redesign-01 iteration_01`
- **SKIP:** Global lint (pre-existing issues outside scope); lucide-react in `web/components/ui/` and `web/components/run/` (Part 2 scope)

## Human Checkpoint

- **Required:** NO
- **Source file:** `.agent_process/work/buzz_hc_frontend_redesign-01/human-prereqs.md` (present: NO)
- **Pre-execution items:** none
- **Mid-execution items:** none
- **Post-execution items:** none

## Decomposition

DECOMPOSE: YES — 13 files, 2+ layers (components + pages)

### Work Units (DAG)

**Unit A: Foundation** (`globals.css`, `layout.tsx`, `types.ts`)
- No dependencies. Execute first.
- Validation gate: `pnpm build` passes; `layout.tsx` renders `<html className="dark">`; `globals.css` contains `oklch`.

**Unit B: Atoms** (all 8 `components/buzz/` files)
- Depends on A (needs design tokens from `globals.css`).
- Execute after A. All 8 written in one agent pass in order: `StatusDot` → `StatusChip` → `SectionLabel` → `Btn` → `KV` → `TopNav` → `SwarmGraph`.
- Validation gate: TypeScript passes; no lucide-react imports; all 8 files exist.

**Unit C: Pages** (`page.tsx`, `sessions/page.tsx`, `query/page.tsx`)
- Depends on A+B (needs tokens + atoms).
- Execute after B.
- Validation gate: full validation script passes; `pnpm build` zero errors; 3 Jest tests pass.

Execution order: A → B → C (sequential; validate before advancing to next unit)

## Critical Implementation Notes

1. **`max-w-5xl` removal** — Remove `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper from `layout.tsx`. BEFORE removing, verify whether the existing `/run/[id]` page has its own max-width container — if not, add one inside `web/app/run/[id]/page.tsx` so that route stays self-contained. This is a precondition for AC #2.

2. **`startRun` import** — `/query/page.tsx` must import `startRun` from `@/lib/api` directly. DO NOT use `useRunSession` hook (it bundles SSE setup that would leave a dangling EventSource on navigation away from the page).

3. **SwarmGraph RAF** — Use `useRef` for packet state; mutate `<circle>` positions via `setAttribute('cx', ...)` / `setAttribute('cy', ...)` inside the RAF callback. NEVER call `setState` inside the RAF callback. The prototype's `setTick(t => t+1)` pattern is explicitly forbidden.

4. **`useSearchParams` Suspense** — The query page must export a default component that wraps its `useSearchParams()` consumer in `<Suspense fallback={null}>`. Missing this causes a build-time error in Next.js 16.

5. **Status tokens** — When replacing `:root`, include ALL 5 status token sets: `--status-running-bg/fg`, `--status-complete-bg/fg`, `--status-error-bg/fg`, `--status-queued-bg/fg`, `--status-paused-bg/fg`. Missing any will cause StatusDot/StatusChip to render transparent.

6. **Build order for atoms** — `StatusDot` → `StatusChip` → `SectionLabel` → `Btn` → `KV` → `TopNav` → `SwarmGraph`. Atoms before composites.

7. **Font weight arrays** — `IBM_Plex_Sans` and `JetBrains_Mono` require explicit `weight` arrays in the `next/font/google` import (not all weights available by default).

8. **`SessionStatus` extension** — Before extending the union to add `"queued" | "paused"`, search for exhaustive `switch`/`if-else` consumers of `SessionStatus` and update them.

9. **Landing form** — `page.tsx` query form does `router.push('/query?q=' + encodeURIComponent(query))` and NEVER calls `startRun` directly.

**Spec Concerns channel:** Pause and write a `## Spec Concerns` section at the top of `results.md` if any of these fire: prepare-doc gap, about-to-weaken-a-failing-check, test-failure-points-at-production-code.

## Agent Selection

- **Mode:** single agent (all units)
- **Agent type:** `frontend-developer`
- **Reasoning:** All 13 files are React/TSX/CSS/TypeScript frontend. The frontend-developer agent is purpose-built for this. Implement all 3 units sequentially in one pass (A → B → C) for context continuity.
