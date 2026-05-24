# Technical Assessment

**Scope:** buzz_hc_frontend_redesign-01
**Requirement:** Bloomberg-Terminal UI Redesign — Part 1: Foundation + Static Screens

## Knowledge Base
None relevant (0 entries matched frontend/tailwind/theme queries).

---

## Code Review Findings

### Current globals.css state

**File:** `web/app/globals.css`

- Uses Tailwind v4 `@import "tailwindcss"` pattern with `@theme inline` block
- `@theme inline` maps `--color-*` aliases to CSS vars (e.g., `--color-background: var(--background)`)
- **Current `--radius: 0.625rem` (10px)** — needs to become `0.125rem` (2px)
- Full dual `:root` / `.dark` split — both blocks exist and are fully populated
- `--status-running-bg/fg`, `--status-complete-bg/fg`, `--status-error-bg/fg` tokens exist **only in `:root` light block** — NOT in `.dark` block. Will silently use wrong (light) colors if `.dark` class is added without porting them.
- No `--status-queued-*` or `--status-paused-*` tokens exist at all (needed for new Sessions table)
- `@custom-variant dark (&:is(.dark *))` — requires `.dark` ancestor class to activate the dark variant

### Current layout.tsx state

**File:** `web/app/layout.tsx`

- Imports: `Plus_Jakarta_Sans`, `Geist_Mono`, `Lora` from `next/font/google`
- All three applied as body `className` via CSS variables: `--font-sans`, `--font-mono`, `--font-serif`
- `<html lang="en">` — **no `className="dark"` currently set** (will cause FOUC once dark tokens are in `:root`)
- Nav is inline in layout (44px sticky nav desired; current nav is 48px h-12 with basic logo + 2 links)
- Nav must be **removed from layout.tsx** and replaced by the `TopNav` buzz component (TopNav will be included per-page, since the layout `<div>` wrapper with max-width padding also needs removal for full-bleed layouts)
- The current layout wraps `{children}` in `<div className="max-w-5xl mx-auto px-4 py-8">` — this max-width container conflicts with full-bleed designs (landing page uses edge-to-edge status strip). The container div should be removed from layout, leaving full-bleed to each page.

### Current page.tsx state

**File:** `web/app/page.tsx`

- `"use client"` directive (needs to remain for SwarmGraph RAF)
- Imports `Search`, `BarChart2`, `FileText`, `ArrowRight` from `lucide-react` — all four will be removed
- Uses `framer-motion` for bento-grid hover animations — framer-motion stays installed but won't be used in the new landing (RAF for swarm, no hover scale on Bloomberg style)
- Structure: text-center hero → bento grid (col-span-2/1 cards with HeroPreview) → CTA card
- Full replacement: 3-zone layout (status strip + hero with left/right columns + feature strip)
- Current page links to `/run` — new landing query form goes to `/query?q=<encoded>` (NOT directly to run)

### Current sessions/page.tsx state

**File:** `web/app/sessions/page.tsx`

- `"use client"` directive
- Imports `ChevronRight`, `FlaskConical` from `lucide-react` — both will be removed
- Imports `Card`, `CardContent`, `Button`, `Input` from shadcn `components/ui/` — all replaced by buzz components
- Card-list layout with `StatusBadge` rendering `rounded-full` pill badges
- All row clicks go to `/sessions/${s.session_id}` — requirement changes this to `/run/[id]` for active and `/report/[id]` for complete
- Uses `getSessions({ search, limit: 50 })` — same call is reused in the redesign
- `SessionStatus` type currently has `"running" | "complete" | "error"` — missing `"queued"` and `"paused"` from prototype filter chips

### useRunSession / api.ts

**Hook:** `web/hooks/useRunSession.ts`

- Exports `useRunSession()` returning `{ state, run, reset }`
- The `run(query, tavilyApiKey?)` function internally calls `startRun()`, sets up SSE, and drives `state.phase` through `starting → running → complete/error`
- `startRun(query, tavilyApiKey?)` is exported separately from `web/lib/api.ts` — signature: `(query: string, tavilyApiKey?: string) => Promise<RunResponse>` where `RunResponse = { session_id: string; stream_url: string }`

**For `/query` page:** The query page only needs to call `startRun()` directly (not `useRunSession`). The page calls `startRun(query)`, gets back `{ session_id }`, then does `router.push('/run/' + session_id)`. There is no need to manage SSE state on the query page — that belongs to the `/run/[id]` page (Part 2). Import `startRun` directly from `@/lib/api`.

**Key detail:** `useRunSession.run()` combines `startRun` + SSE setup in one call — it is designed for the run page, not the query dispatch page. Using it on `/query` would create a dangling EventSource connection that navigates away before `done` fires.

### SessionSummary type check

**File:** `web/lib/types.ts`

Current `SessionSummary` fields:
- `session_id` — present (maps to table "ID" column)
- `timestamp` — present (maps to "Started")
- `query` — present (maps to "Query")
- `status` — present (`"running" | "complete" | "error"`) (maps to "Status")
- `error_msg?` — present (used for error row annotation)

**Missing from the 9-column table spec:**
| Table Column | Field Needed | Available? |
|---|---|---|
| Duration | `duration` or compute from `timestamp` | MISSING |
| Tokens | `tokens` / `usage.total_tokens` | MISSING on summary |
| Sources | `sources` (count) | MISSING |
| Cost | `cost` | MISSING |
| Agents | `activeAgents` (which agents ran) | MISSING |

`UsageStats` (with `total_tokens`) lives only on `SessionDetail`, not `SessionSummary`. The `getSessions()` API endpoint returns `SessionSummary[]` from `api/routes/sessions.py` / `api/db_sessions.py` — it does not include usage data.

**Implication:** For Part 1, the Sessions table must render `—` for Tokens, Sources, Cost, Duration, and Agents columns. Adding these to `SessionSummary` requires a backend route change (out of scope for this part per the requirement). The `web/lib/types.ts` update needed is **only**: extend `SessionStatus` to include `"queued"` and `"paused"`.

### Lucide-react usage

Files with `lucide-react` imports in `app/` and `components/` (source files only):
- `web/app/page.tsx` — `Search`, `BarChart2`, `FileText`, `ArrowRight` (full replacement, so remove naturally)
- `web/app/sessions/page.tsx` — `ChevronRight`, `FlaskConical` (full replacement, so remove naturally)
- `web/components/ui/select.tsx` — `ChevronDownIcon`, `CheckIcon`, `ChevronUpIcon` (shadcn primitive — do NOT touch, out of scope)
- `web/components/run/PipelineProgress.tsx` — `Search`, `BarChart2`, `FileText`, `CheckCircle2` (Part 2 scope — leave untouched for now)
- `web/components/run/QueryForm.tsx` — `Settings` (Part 2 scope — leave untouched for now)

**Verdict:** The requirement's "lucide-react audit" for Part 1 is naturally accomplished by replacing `page.tsx` and `sessions/page.tsx`. The `components/run/` and `components/ui/` files are explicitly not modified in Part 1. No separate audit step needed.

### Tailwind v4 setup

Confirmed:
- `tailwindcss: "^4"` (v4), `next: "16.1.6"`, `react: "19.2.3"`
- `@import "tailwindcss"` (v4 style, not `@tailwind base/components/utilities`)
- `@theme inline` pattern confirmed for Tailwind-usable color aliases
- `framer-motion` v12 already installed

---

## Implementation Approach

### 1. globals.css — full `:root` replacement

Replace the existing `:root` block entirely with the Bloomberg dark palette. The `.dark` block becomes a no-op kept for reference but inactive (since `<html className="dark">` is static and Tailwind's `dark:` variant activates via `.dark` ancestor). The `@theme inline` block is **retained exactly as-is** — the token aliases (`--color-background`, etc.) must continue to map to the same var names so shadcn components don't break.

The Bloomberg tokens are **additive** under the same var names that `@theme inline` already maps:
- `--background` → `oklch(0.13 0.025 250)` (replaces the light value)
- `--foreground` → `oklch(0.96 0.005 248)`
- etc.

New tokens to add alongside: `--surface`, `--surface-2`, `--amber`, `--cyan`, `--green`, `--red`, `--violet`, `--text-hi`, `--text-md`, `--text-lo` (the prototype's own naming). These are NOT mapped through `@theme inline` (they aren't needed as Tailwind color utilities; they're used as `var(--amber)` etc. in buzz components).

Status pip tokens — port ALL to the new `:root` dark values and add missing `--status-queued-*`, `--status-paused-*`.

### 2. layout.tsx — minimal surgery

- Replace three font imports with `IBM_Plex_Sans` and `JetBrains_Mono`
- Add `className="dark"` to `<html>`
- Remove the inline `<nav>` entirely
- Remove the `<div className="max-w-5xl mx-auto px-4 py-8">` wrapper around `{children}` — each page manages its own layout
- Keep `{children}` directly inside `<body>`

### 3. components/buzz/ — flat structure, 8 files

Create directory `web/components/buzz/`. All 8 files flat (no subdirs). This namespace is separate from `components/ui/` (shadcn) by directory name. Buzz components use `var(--amber)` etc. inline and Tailwind utilities sparingly. Do not use shadcn primitives inside buzz components.

### 4. page.tsx (Landing) — full rewrite

- Keep `"use client"` (SwarmGraph RAF requires it)
- 3-zone: TopNav (imported from buzz) → status strip → hero (2-col) → feature strip
- Landing form submits to `/query?q=<encoded>` via `router.push`
- SwarmGraph rendered in the hero right column with static `nodeStates` (all nodes active/idle placeholder)
- EventFeed below SwarmGraph: reuse existing `EventFeed` component from `components/run/EventFeed.tsx` with an empty `events={[]}` array or hardcoded placeholder events array

### 5. SwarmGraph — RAF isolation pattern

The prototype's current implementation calls `setTick(t => t+1)` inside the RAF loop — this causes a React re-render on every frame (60fps). The requirement explicitly forbids setState inside RAF.

**Correct pattern:**
```
const packetRef = useRef<PacketState[]>([])
const canvasRef = useRef<SVGElement>(null) // or use DOM manipulation
```
Use `useEffect` to start RAF loop, compute packet positions in the ref, and directly mutate SVG `<circle>` element positions via `ref.current` — no setState. Alternatively, draw packets onto a `<canvas>` overlay on top of the static SVG. The static SVG (nodes, edges, grid, glow) renders as pure JSX; the animated packet layer is a separate canvas or imperative DOM layer.

**Recommended approach:** SVG with a separate `<g ref={packetGroupRef}>` whose child `<circle>` elements are imperatively repositioned via `setAttribute('cx', x)` / `setAttribute('cy', y)` in the RAF callback. This avoids canvas setup complexity while keeping React state clean.

### 6. query/page.tsx

- New file at `web/app/query/page.tsx`
- `"use client"` (form state, keyboard listener, router.push)
- Read `?q=` param via `useSearchParams()` to pre-fill textarea
- Import `startRun` directly from `@/lib/api` (NOT `useRunSession`)
- On submit: `const { session_id } = await startRun(query); router.push('/run/' + session_id)`
- Keyboard: `useEffect` → `keydown` listener checking `e.metaKey || e.ctrlKey` + `e.key === 'Enter'`
- Token budget slider: purely UI state (no backend field yet — send fixed default)
- Depth selector: UI state — could pass as a future API param; for now, decorative

### 7. sessions/page.tsx — full rewrite

- Keep `"use client"`, `useEffect`, `useState`
- Keep `getSessions()` call with same params
- Extend `SessionStatus` type in `types.ts` to add `"queued" | "paused"` (frontend-only, backend sends only running/complete/error in practice)
- Table columns: ID, Query, Status, Started, Duration, Tokens, Sources, Cost, Agents
- Duration, Tokens, Sources, Cost, Agents → render `—` for all rows (data not in `SessionSummary`)
- Filter chips: All / Running / Complete / Queued / Error — counts derived client-side from loaded sessions
- Row click: `complete` → `/report/${id}`, all others → `/run/${id}`
- Replace all shadcn imports with buzz atoms

**Key Assumptions:**
- The layout.tsx `<div>` wrapper around `{children}` is removed; each page is responsible for its own max-width/padding
- The `components/run/EventFeed.tsx` component is reused on the landing page as-is (no changes) — it already uses `bg-zinc-950` which works fine on the dark theme
- Token budget and depth selectors on the query page are purely decorative UI — no backend parameter maps to them yet
- `"queued"` and `"paused"` statuses are added to `SessionStatus` in types.ts but the backend never sends them in practice; filter chip counts for those will always be 0 until backend changes
- The `TopNav` buzz component is NOT added to `layout.tsx`; instead it's imported directly in `page.tsx`, `query/page.tsx`, and `sessions/page.tsx` — this allows the layout to be truly minimal (just font vars + dark class)

---

## Design Decisions

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| CSS token naming | Mix: Bloomberg tokens use prototype's `--bg`, `--surface`, `--amber`, etc. as raw CSS vars; Tailwind-integrated tokens keep existing `--background`, `--foreground` names in `@theme inline` | Pure `--buzz-*` namespace OR pure `--color-*` | The `@theme inline` block already maps `--color-background: var(--background)` — renaming would break all shadcn components. Bloomberg tokens (`--amber`, `--cyan`, etc.) are only used by buzz components via `var()` so they need no Tailwind alias. Two-tier naming (shadcn vars + Bloomberg accent vars) is the minimal-churn approach. |
| Dark mode strategy | Static `<html className="dark">` server-side in layout.tsx, `:root` block becomes dark palette directly | CSS `prefers-color-scheme` media query, client JS class toggle | Server-rendered `className="dark"` prevents FOUC entirely. App is dark-only by design. Media query approach would require keeping a light `:root` fallback which conflicts with full replacement. No toggle needed. |
| SwarmGraph animation | RAF + imperative SVG DOM mutations via ref (`setAttribute`) | framer-motion, CSS animation, setState-in-RAF | framer-motion adds JSX re-render overhead and doesn't give packet-along-edge control. CSS animation can't do dynamic positional math. setState-in-RAF (prototype approach) causes 60fps React re-renders (choppy). Imperative ref mutation is idiomatic for this exact use case. |
| components/buzz/ structure | Flat — all 8 files directly in `components/buzz/` | Subdirectories (atoms/, nav/, graph/) | Only 8 files total; subdirs add import path complexity with no benefit at this scale. Flat also makes it trivially clear what's in the buzz namespace vs shadcn's `ui/`. |
| Query page startRun usage | Import `startRun` directly from `@/lib/api` | Import `useRunSession` hook | `useRunSession` bundles startRun + SSE EventSource setup together. On the query page, we navigate away immediately after `startRun` resolves — there's no page to receive SSE events. Using the hook would create a dangling EventSource. Direct import is simpler and correct. |
| Sessions table data gaps | Render `—` for Duration, Tokens, Sources, Cost, Agents columns | Fetch `SessionDetail` per row, add backend fields | Backend changes are out of scope for Part 1. Per-row `getSession()` calls would be N+1 requests and very slow. The `—` approach matches the prototype's own sparse data rendering and is honest about what the API provides. |

---

## Pre-existing Test State

**Python tests:** 53 passed (0 failed) — `uv run pytest tests/ -q`

**Jest tests:** 3 passed, 1 suite — `cd web && pnpm test`

Both test suites are fully green. The Jest tests do not exercise any of the files being modified (they test `lib/utils.ts` / `lib/api.ts` request logic, not page components).

---

## Risks

- **Layout wrapper removal**: Removing `max-w-5xl` wrapper from `layout.tsx` affects the existing `/run/[id]` route (Part 2 scope). The run page currently relies on the layout's padding. Mitigation: add the max-width container explicitly inside `run/page.tsx` so it is self-contained before removing it from layout.
- **shadcn radius bleed**: Setting `--radius: 0.125rem` (2px) affects all shadcn components still in use (the `/run/[id]` route uses `components/run/EventFeed.tsx` which uses `ScrollArea`). The `rounded-xl` on EventFeed will collapse to 2px. This is acceptable (matches the aesthetic) but should be QA'd at the dev server.
- **Status pip tokens in dark mode**: The existing `--status-running-bg/fg` etc. only exist in `:root` (light). When `:root` is replaced with dark values, these vars must be included with dark-appropriate values. If forgotten, StatusChip/StatusDot will silently use undefined values (transparent).
- **SessionStatus type extension**: Adding `"queued" | "paused"` to the union type in `types.ts` requires checking all exhaustive switch statements that currently handle the type. The existing `StatusBadge` in `sessions/page.tsx` will be replaced, but any other consumers (e.g., `PipelineProgress.tsx`) may have type errors if they switch on `SessionStatus`. Mitigation: search for all switch/if-else on `SessionStatus` before extending.
- **`useSearchParams` in query page**: In Next.js App Router, `useSearchParams()` requires the component to be wrapped in `<Suspense>`. The query page must either export a Suspense boundary or use `useRouter` + `usePathname` patterns. Mitigation: wrap the inner component in `<Suspense fallback={null}>` in the default export.
- **Font availability**: `IBM_Plex_Sans` and `JetBrains_Mono` are both available in `next/font/google`. Weight ranges (300–700 for IBM Plex Sans, 400–600 for JetBrains Mono) must be specified in the `weights` array or via `variable` font if available.

---

## Clarification Needed

None — all design decisions can be made from the prototype reference and requirement doc without human input.
