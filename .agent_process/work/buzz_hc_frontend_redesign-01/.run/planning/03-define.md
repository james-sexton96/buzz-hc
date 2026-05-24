# Scope Definition

**Scope:** buzz_hc_frontend_redesign-01

## Files in Scope

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

## Acceptance Criteria (LOCKED)

**DO NOT MODIFY during iteration. New issues → backlog.**

- [ ] `web/app/globals.css` defines the full Bloomberg OKLCH palette in `:root` (background, foreground, surface, surface-2, amber, cyan, green, red, violet, text-hi/md/lo); `--radius: 0.125rem`; `--status-running-*`, `--status-complete-*`, `--status-error-*`, `--status-queued-*`, `--status-paused-*` all defined with dark-appropriate values; `@theme inline` block retained so shadcn aliases continue to resolve; `web/app/layout.tsx` renders `<html lang="en" className="dark">` server-side (no client toggle, no FOUC).
- [ ] `web/app/layout.tsx` imports `IBM_Plex_Sans` (weights 300–700) and `JetBrains_Mono` (weights 400–600) from `next/font/google`; `Plus_Jakarta_Sans`, `Geist_Mono`, and `Lora` imports are removed; the `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper around `{children}` is removed (children render directly inside `<body>`); the inline `<nav>` is removed from layout.
- [ ] `web/app/query/page.tsx` exists at the route `/query`, imports `startRun` directly from `@/lib/api` (does NOT use `useRunSession`), reads `?q=` via `useSearchParams()` inside a `<Suspense>` boundary to pre-fill the textarea, calls `router.push('/run/' + session_id)` after `startRun()` resolves, and a `Cmd/Ctrl+Enter` keydown handler submits the form.
- [ ] `web/app/sessions/page.tsx` renders a 9-column table (ID, Query, Status, Started, Duration, Tokens, Sources, Cost, Agents) with `—` shown for fields absent from `SessionSummary`; status filter chips for All/Running/Complete/Queued/Error each display a client-side count and filter the rendered rows; clicking a row with status `complete` navigates to `/report/[id]` and any other status navigates to `/run/[id]`.
- [ ] `web/app/page.tsx` renders all 3 zones (top status strip with live stats, hero with H1 + inline query input + suggestion chips + stats row on the left and `SwarmGraph` + event log on the right, feature strip with 4 cells); the landing query form submits via `router.push('/query?q=' + encodeURIComponent(query))` and never calls `startRun` directly; `SwarmGraph` animates packet flow via `requestAnimationFrame` using imperative `setAttribute` on `<circle>` refs with no `useState`/`setState` calls inside the RAF callback.
- [ ] `web/components/buzz/TopNav.tsx` is imported and rendered at the top of `web/app/page.tsx`, `web/app/query/page.tsx`, and `web/app/sessions/page.tsx`; it contains the BuzzLogo SVG, `BUZZ·HC` wordmark, nav links with an active amber underline driven by `usePathname()`, and a pharma ticker that rotates every 4000ms via `setInterval` cleaned up on unmount.
- [ ] `uv run pytest tests/ -q` shows 53 passed / 0 failed; `cd web && pnpm test` shows 3 passed / 0 failed; `cd web && pnpm build` completes with zero TypeScript errors.
- [ ] `grep -rn "from 'lucide-react'" web/app/page.tsx web/app/sessions/page.tsx web/app/query/page.tsx web/app/layout.tsx web/app/globals.css` returns zero matches; no buzz component under `web/components/buzz/` imports from `lucide-react`.

**Count:** 8 (WARN — within acceptable range for a foundation + 3-screens scope)

## Documentation

- End user docs: N/A — internal tool, no public documentation
- Developer docs: N/A — internal refactor; changes are self-evident in code (component locations under `web/components/buzz/`, new route at `web/app/query/page.tsx`)
- API docs: N/A — no backend, schema, or contract changes
