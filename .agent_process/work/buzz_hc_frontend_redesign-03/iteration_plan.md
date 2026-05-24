# Iteration Plan – buzz_hc_frontend_redesign-03

## Scope Overview
- **Scope Name:** buzz_hc_frontend_redesign-03
- **Date:** 2026-05-24
- **Summary:** Implement the `/report/[id]` Bloomberg-style dossier screen — renders `MarketReport.sections[]` as `PanelCard` panels and surfaces structured KPI data from `research_json` / `analyst_json` as typed visualizations (donut + bar) with a slide-in `FootnoteDrawer` for citations.

## Requirements Source
- **Path:** `.agent_process/requirements_docs/ui_redesign/buzz_hc_frontend_redesign-03.md`
- **Document:** `buzz_hc_frontend_redesign-03.md`

*Work folder name derived from requirements path per naming convention.*

## Current Status
- Latest iteration: iteration_01 (not started)
- Decision: N/A
- Next: Run `/ap_exec buzz_hc_frontend_redesign-03 iteration_01`

## Acceptance Criteria (LOCKED - DO NOT MODIFY)

- [ ] Navigating to `/report/<id>` for a session with `status === 'complete'` and a non-null `report` renders the dossier page without runtime errors; if `status !== 'complete'` OR `report` is null, the page redirects to `/run/<id>`.
- [ ] Every entry in `session.report.sections[]` is rendered as a `PanelCard` with its `heading` shown in the header and its `content` rendered via `react-markdown` + `remark-gfm`; sections at index 0 and index 3 span 2 columns, all others span 1 (verified in DOM via `grid-column` style).
- [ ] When `research_json` parses to a non-null object with `payer_coverage.length > 0`, the Payer Coverage KPI panel renders with a `<DonutChart>` whose filled fraction equals `(covered + restricted) / total` after `normalizeCoverageStatus()` bucketing; when the array is empty/null OR all entries normalize to `unknown`, the panel shows the "data not available" state.
- [ ] When `analyst_json` parses to a non-null object with `competitive_landscape.length > 0`, the Competitive Landscape KPI panel renders one row per competitor with name, parsed `%` from `share_or_notes` (regex `/(\d+(?:\.\d+)?)%/`, fallback 0%), and a 5px bar whose width matches the parsed percent.
- [ ] Citation `[N]` tokens inside section markdown render as cyan superscripts with a dotted underline; clicking one opens `FootnoteDrawer` populated from `sources[N-1]` (URL as title fallback, `new URL(src).hostname` as domain); `FootnoteDrawer` animates `translateX(100%) → 0` in 220ms via framer-motion; pressing ESC closes it.
- [ ] The Re-run button on the report page navigates to `/query?q=<encoded original_query>`; clicking it from a session with a known `query` field arrives at `/query` with the textarea pre-populated (relies on existing Part 2 query-param behavior — if not yet implemented, the URL is still set correctly with the encoded `q`).
- [ ] `nextjs-build` CI job passes (`cd web && pnpm build`) with no TypeScript or lint errors introduced by the new files; `TopNav` highlights the Sessions tab when pathname starts with `/report`.

**Count:** 7 (target: 3-7)

**CRITICAL:** These criteria are FROZEN at iteration start.
New issues discovered during iteration → backlog for future scopes.

**Scope boundaries are guidance, not walls.** If meeting the acceptance criteria
correctly requires touching files outside this list, the executor may do so with:
- Documentation of what was added and why
- Validation script updated to cover new files
- Justification in results.md for reviewer assessment

## Known Patterns & Constraints

**From knowledge base:**
- No directly applicable KB entries — the two indexed entries (`pydantic_ai_testmodel_isolation_pattern`, `output_validator_failures_surface_as_unexpectedmodelbehavior`) target the agent/backend layer, not the frontend.

**No matches found for:** `react-markdown`, `framer-motion`, `report dossier`, `KPI panel`, `citation rendering`.

**Project-specific constraints (carry over from Parts 1 & 2):**
- Font CSS variables in `web/app/globals.css` are `--font-sans` (IBM Plex Sans) and `--font-mono` (JetBrains Mono). The design prototype uses shorthand `var(--sans)` / `var(--mono)` — those names do not exist in this codebase. **All inline styles in new components must use `var(--font-sans)` / `var(--font-mono)`.**
- Color/surface tokens (already defined in `globals.css` from Part 1): `--bg`, `--surface`, `--border`, `--text-hi`, `--text-md`, `--text-lo`, `--amber`, `--cyan`, `--green`, `--red`, `--violet`.
- `lucide-react` is NOT installed and is forbidden in scoped components (carry-over rule from Part 2).
- `research_json` / `analyst_json` on `SessionDetail` are **raw JSON strings** (typed `string | null`) — every consumer must `JSON.parse()` inside a `try/catch` and null-guard before rendering.
- `MarketReport.sources` is `string[]` of URLs only — no structured citation object exists; the UI synthesizes `{ n, url, title, domain }` from index + URL parsing.
- `aiosqlite` / API behavior unchanged in this scope; no backend changes required.

## Design Review

N/A — scope complexity is `moderate` (not `complex`); design review gate not triggered.

## Technical Assessment (by Orchestrator)

**Code Review Findings:**
- `web/lib/types.ts` (existing): `MarketReport.sources: string[]` confirmed line 29. `SessionDetail.research_json` / `analyst_json` typed `string | null`, lines 53-54. No `MarketAccessFindings` / `AnalystFindings` TS interfaces exist — only Python schema definitions in `app/schema.py`. Executor must add partial TS mirrors covering only the fields rendered by the UI.
- `web/lib/api.ts` (existing): `getSession(id)` returns `SessionDetail` and is the correct fetch for the report page — no new API call needed; `getPdfUrl(sessionId)` is available for the Export PDF placeholder.
- Backend (`api/routes/sessions.py` lines 67-68): confirmed pass-through of `research_json` / `analyst_json` as raw JSON strings (NOT parsed); `report_json` IS parsed and arrives as the typed `MarketReport` object. No backend changes required.
- `web/package.json`: `react-markdown` v10.1.0, `remark-gfm` v4.0.1, `framer-motion` v12.37.0 all installed.
- `web/components/buzz/` (existing): seven atoms present (`TopNav`, `Btn`, `KV`, `SectionLabel`, `StatusChip`, `StatusDot`, `SwarmGraph`) — all directly reusable. `TopNav.resolveActive()` does NOT currently recognize `/report` and would fall through to `"research"` — minor fix required so `/report/<id>` highlights the Sessions tab.
- `web/app/` routes: `/`, `/query`, `/run`, `/sessions` exist; `/report/[id]` is additive and brand new.
- Design reference: `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/report.jsx`.

**Implementation Approach:**
- Build `/report/[id]/page.tsx` as a Next.js App Router **client component** (`"use client"`) — `useState` is required for the drawer; `useEffect` fetches `getSession(id)` on mount; `router.replace("/run/" + id)` when `session.status !== "complete"` OR `session.report == null`.
- Render a top strip (breadcrumb + meta row + H1 + lede + button row + source/cite counts), a headline KPI row (one surface cell + four secondary cells, all using `<SparkLine>`), the panel grid (`grid-template-columns: repeat(3, 1fr)`, gap 16px) of `<PanelCard>`s from `report.sections[]`, conditional Payer Coverage / Competitive Landscape KPI panels, the footnotes strip (first 6 of `sources[]` as cards), and mount `<FootnoteDrawer open={!!citation} citation={citation} onClose={...} />`.
- Implement citation rendering by **pre-processing the markdown string** before `react-markdown`: replace `/\[(\d+)\]/g` with a unique placeholder element (e.g. `<cite data-n="N">[N]</cite>`), then register `components.cite` to render the cyan dotted-underline `<sup>` and call `onCitationClick(n)`. Pre-process is preferred over walking children of `components.p` because it composes cleanly with nested elements and is testable as a pure string transform.
- Add partial TS interfaces (`PayerCoverageEntry`, `CompetitorEntry`, `MarketAccessFindings`, `AnalystFindings`) to `web/lib/types.ts` covering only the fields the UI renders. `SessionDetail.research_json` / `analyst_json` typing (`string | null`) stays — client-side `JSON.parse()` produces these typed objects.
- Patch `TopNav.resolveActive()`: add a branch so pathnames matching `^/report` return `"sessions"`.

**Known Risks:**
- **`coverage_status` normalization is lossy** — free text like "PA required", "Tier 3 specialty", "covered with step edit" must map to 4 buckets. Mitigation: implement `normalizeCoverageStatus()` as a pure helper with lowercase + ordered regex (covered → restricted → not_covered → unknown). Default unrecognized to `unknown`.
- **`research_json` / `analyst_json` JSON parse failure** — malformed stored JSON would throw. Mitigation: wrap every parse in `try / catch`; on failure return `null` and hide the KPI panel.
- **`react-markdown` v10 + custom `cite` renderer** — `cite` is a standard HTML element so it should pass through, but if v10 strips unknown elements, fall back to `components.a` with a custom URL scheme (e.g. `cite://N`). Low risk.
- **Reporter agent may omit `[N]` citations entirely** — in that case the footnote strip still renders from `sources[]` and no superscripts appear. Acceptable graceful degradation.
- **`session.report` may be null on a "complete" session race** — redirect guard must check `session.report !== null` in addition to `session.status === 'complete'`, both go to `/run/<id>`.
- **No `/report` link from existing pages yet** — out of scope for Part 3 to wire (the route works via direct URL); a "View Dossier" link from sessions detail can be added by the executor if it's easy, otherwise deferred.

**Implementation Guidance:**
- Use `var(--font-sans)` / `var(--font-mono)` — NEVER `var(--sans)` / `var(--mono)` (those tokens do not exist).
- NEVER import from `lucide-react` in any new file under `web/components/buzz/` or `web/app/report/[id]/`.
- Always wrap `JSON.parse(session.research_json ?? "null")` in `try / catch`; on failure treat as null.
- Column-span logic is **index-based** (index 0 and 3 span 2 cols); fall back to all 1-col when `sections.length < 4`.
- Competitive bar parsing uses `/(\d+(?:\.\d+)?)%/`; fallback to 0% bar width when no match.
- FootnoteDrawer uses framer-motion v12: `AnimatePresence` + `motion.div` with `initial={{ x: "100%" }}`, `animate={{ x: 0 }}`, `exit={{ x: "100%" }}`, `transition={{ duration: 0.22, ease: "easeOut" }}`. Backdrop is a separate `motion.div` with `initial/animate/exit` opacity 0→1 over 180ms. ESC handler attaches on `window` `keydown` inside a `useEffect` while `open` is true.

**Design Decisions (made by orchestrator, not human prereqs):**

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Citation superscript rendering | Pre-process markdown to swap `[N]` → `<cite data-n="N">[N]</cite>`; override `components.cite` in react-markdown | Override `components.p` and walk the React children tree | Pre-processing is a pure string transform — testable in isolation; the `components.p` walk gets fragile with nested inline elements (bold, links) inside the same paragraph |
| Report page data fetching | Client component (`"use client"`) with `useEffect` + `useState` + `getSession()` | Server component with top-level `async fetch` | The page owns the drawer-open state (`useState`) and must redirect imperatively (`router.replace`); a server component would force a layout split and add no benefit since the data is mutable per request |
| Column span heuristic | Fixed indices (0 and 3 span 2 cols); fall back to all 1-col when `< 4` sections | Heading-keyword matching ("Country", "Catalysts") | Reporter agent phrasing varies per query; index-based layout is deterministic and matches the prototype |
| `research_json` / `analyst_json` typing | Add partial `MarketAccessFindings` / `AnalystFindings` TS interfaces covering only UI-rendered fields | Mirror the full Python schema OR use `unknown` | Full mirror is over-broad maintenance burden; `unknown` removes type safety on the consumers that matter; partial coverage is the right surface |
| Competitive bar % source | Regex `/(\d+(?:\.\d+)?)%/` on `share_or_notes` (free text), 0% fallback | Require structured numeric share field on `CompetitorEntry` | Schema has no numeric share field; adding one is out of scope for Part 3 |
| FootnoteDrawer animation | framer-motion `AnimatePresence` + `motion.div` (`translateX(100%) → 0`) | Pure CSS transition on conditional mount | CSS transitions don't fire reliably when toggling `display:none` / unmount; framer-motion is already a dependency and handles enter/exit cleanly |
| TopNav active state for `/report` | Add a branch in `resolveActive()` so `^/report` returns `"sessions"` | Leave it falling through to `"research"` default | Report is a session artifact; the Sessions tab should remain highlighted on the dossier view |
| SparkLine data source | Static placeholder flat-line data in headline + secondary KPI cells | Synthesize sparkline from `analyst_json.market_sizes[].value_usd / year` | `MarketSize` is sparse (single value per row, not a time series); synthesized lines add noise without signal — explicit placeholder is honest |

## Iteration Budget (ENFORCED)
- iteration_01: First attempt
- iteration_01_a: First revision (if needed)
- iteration_01_b: Second revision (if needed)
- iteration_01_c: Final attempt (if needed)

After iteration_01_c → Escalate to human for decision (ship/pivot/abort)

## Work Unit Decomposition (sequential)

**Unit A — Types + TopNav fix** (no dependencies, goes first)
- Modify `web/lib/types.ts`: add partial `PayerCoverageEntry`, `CompetitorEntry`, `MarketAccessFindings`, `AnalystFindings` interfaces.
- Modify `web/components/buzz/TopNav.tsx`: extend `resolveActive()` so pathnames starting with `/report` resolve to `"sessions"`.

**Unit B — New buzz components** (depend on Part 1 tokens only)
- `web/components/buzz/SparkLine.tsx` — pure SVG, no other component deps; built first.
- `web/components/buzz/DonutChart.tsx` — pure SVG, no other component deps.
- `web/components/buzz/PanelCard.tsx` — pure layout primitive; uses existing `SectionLabel`; consumed by Unit C.
- `web/components/buzz/FootnoteDrawer.tsx` — framer-motion drawer; uses existing `KV`; consumed by Unit C.

**Unit C — Report page** (depends on Units A + B)
- `web/app/report/[id]/page.tsx` — assembles all atoms; owns drawer state; implements `normalizeCoverageStatus()` + `parseSharePercent()` helpers + markdown citation pre-processor.

## Files in Scope (Expected)

These are the files expected to change. The executor may touch additional files
if necessary for correctness — see "Scope boundaries" note above.

**New:**
- `web/app/report/[id]/page.tsx`
- `web/components/buzz/PanelCard.tsx`
- `web/components/buzz/FootnoteDrawer.tsx`
- `web/components/buzz/SparkLine.tsx`
- `web/components/buzz/DonutChart.tsx`

**Modified:**
- `web/lib/types.ts`
- `web/components/buzz/TopNav.tsx`

**Total:** 7 files

## Documentation in Scope

**End User Documentation:**
- *None — internal UI redesign; no external user docs exist for this app.*

**Developer Documentation:**
- *None — no API/architecture change. New TS interfaces in `web/lib/types.ts` are self-documenting; `MEMORY.md` already describes `research_json` / `analyst_json` as raw strings on `SessionDetail`.*

**Documentation Requirements (from CLAUDE.md):**
- [x] End user documentation updated (N/A — no user-facing public docs exist)
- [x] Developer documentation updated (N/A — no contract change; partial TS interfaces are self-describing)
- [x] Documentation follows Diátaxis framework organization (N/A — nothing added)
- [x] Cross-references to changed code updated (N/A — no docs reference the new files)
- [x] Migration guide created (N/A — additive scope)

## Removed Surfaces

*N/A — no public surfaces removed or renamed.* This scope is purely additive (new page, new components, new TS interfaces, one minor in-place adjustment to `TopNav.resolveActive()` that only **adds** a route mapping — no surface removed).

## Validation Requirements (SCOPED)

**Hook validation (after_edit):**
- Script: `.agent_process/scripts/after_edit/validate-buzz_hc_frontend_redesign-03.sh`
- Runs the scope-specific checks listed below; provides immediate feedback (not enforcement).

**Checks the validator runs (RUN list):**
1. `cd web && pnpm tsc` — TypeScript compiles with zero errors.
2. `cd web && pnpm build` — Next.js production build succeeds (covers lint + build).
3. `web/app/report/[id]/page.tsx` exists.
4. `web/components/buzz/PanelCard.tsx` exists.
5. `web/components/buzz/FootnoteDrawer.tsx` exists.
6. `web/components/buzz/DonutChart.tsx` exists.
7. `web/components/buzz/SparkLine.tsx` exists.
8. No `lucide-react` imports in `web/app/report/[id]/page.tsx` or any of the four new `web/components/buzz/` files (PanelCard, FootnoteDrawer, DonutChart, SparkLine).

**Pre-existing baseline (out of scope, will not block):**
- 53 Python tests passing (no changes to Python in this scope).
- 3 Jest tests passing (this scope does not add Jest tests; existing 3 remain green via `pnpm tsc` / `pnpm build` proxy).
- `pnpm build` succeeds today.

**SKIP list (not run by the validator):**
- Python `pytest` — backend untouched in this scope; coverage owned by Part 1 / 2 baselines.
- `ruff check .` — backend untouched.
- `pnpm test` (Jest) — no new Jest tests are added in this scope; existing tests pass under baseline. Build success is the gate.

**Bash 3.2 portability:** validator confirmed bash 3.2.57 compatible — uses `case` / `if`, no associative arrays, no `mapfile`, no `${var^^}`, no `&>>`. `bash -n` smoke check should pass under macOS default `/bin/bash`.

**Important:** If scope expands during iterations (new files needed for fixes), the orchestrator must update the validation script to include new files.

**Validation approach:**
- Scoped validation via hook (fast feedback)
- Document results in `iteration_01/results.md`
- Orchestrator review is the quality gate (not automated enforcement)

## Scope Changes

Track any files added to scope during iterations:
- **iteration_01:** Initial scope (see Files in Scope section)
- *(Orchestrator adds entries here if scope expands during ITERATE decisions)*

## Out of Scope

- Country mix table panel (requires schema extension → Part 4)
- Scenario / risk probability table panel (requires schema extension → Part 4)
- Export PDF functionality (placeholder button only — onClick wired to existing `getPdfUrl(id)` is optional, not required)
- Share functionality (placeholder button only)
- Streaming draft in the report (report is final by definition)
- Mobile / responsive optimization
- Linking `/report/<id>` from `/sessions/<id>/page.tsx` ("View Dossier" CTA) — direct URL access is sufficient for Part 3 acceptance
- New Jest tests for `normalizeCoverageStatus()` / `parseSharePercent()` — pure helpers are validated via TS + build; targeted unit tests can land in a follow-up
- Backend changes (none required — `research_json` / `analyst_json` are already exposed)

## Technical Notes

- **Critical font var names:** `var(--font-sans)` / `var(--font-mono)` — NOT `var(--sans)` / `var(--mono)`.
- **TopNav fix shape:** `resolveActive()` cascade must return `"sessions"` for pathnames starting with `/report`.
- **Column-span logic:** sections at index 0 and 3 get `gridColumn: "span 2"`; all others get `span 1`. When `sections.length < 4`, all cards render at 1-col width.
- **Competitive bar:** regex `/(\d+(?:\.\d+)?)%/` on `share_or_notes`; 0% width fallback.
- **FootnoteDrawer:** framer-motion v12 `AnimatePresence` + `motion.div` `translateX(100%) → 0` 220ms ease; ESC closes via `window` `keydown` listener inside a `useEffect`; backdrop `rgba(0,0,0,0.55)` opacity 0→1 over 180ms.
- **Redirect guard on `/report/[id]`:** `if (session.status !== "complete" || !session.report) router.replace("/run/" + id);`.
- **Citation pre-processor:** transform markdown string with `String.prototype.replace(/\[(\d+)\]/g, '<cite data-n="$1">[$1]</cite>')` before passing to `<ReactMarkdown>`; register `components.cite` to render a cyan dotted-underline `<sup>` and call `onCitationClick(n)`.
- **Source synthesis from `string[]`:** `domain = new URL(src).hostname` (wrap in try/catch); `title = src` (URL fallback); `n = index + 1`.
- **Design reference:** `/Users/james/Downloads/design_handoff_buzz_hc_redesign/prototype/proto/report.jsx`.
- **No `lucide-react`:** none of the five new/edited UI files may import from `lucide-react`.

## Time Budget
- Target: 2-4 hours implementation per iteration
- Maximum: 1-2 weeks total (3 iterations max)
- After time exceeded: Escalate to human

## Success Metrics
- All 7 acceptance criteria checked
- Scoped validator (`validate-buzz_hc_frontend_redesign-03.sh`) passes
- `cd web && pnpm tsc` clean
- `cd web && pnpm build` clean
- No regressions in baseline (53 Python tests, 3 Jest tests, prior `pnpm build`)
- Manual smoke: `/report/<id>` for a real completed session renders sections + KPI panels; FootnoteDrawer slides in on `[N]` click; ESC closes; redirect to `/run/<id>` when status not complete
