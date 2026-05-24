# Technical Assessment

**Scope:** buzz_hc_frontend_redesign-03

---

## Knowledge Base

2 relevant entries:

- **pydantic_ai_testmodel_isolation_pattern**: Not directly applicable to this frontend scope — this pattern applies to agent testing. No carryover needed here.
- **output_validator_failures_surface_as_unexpectedmodelbehavior**: Not applicable to this scope. Backend agent error handling is already in place.

No UI-specific knowledge base entries exist yet. This scope creates the first major data-driven report screen; learnings from the citation/normalization patterns should be added post-iteration.

---

## Code Review Findings

### 1. TypeScript types — `web/lib/types.ts`

- `MarketReport.sources` is `string[]` (confirmed line 29). **No structured citation object exists.**
- `SessionDetail.research_json` and `analyst_json` are typed as `string | null` (lines 53-54). They arrive as **raw JSON strings** from the API — the frontend must call `JSON.parse()` before use.
- **No `MarketAccessFindings` or `AnalystFindings` TypeScript interfaces exist** in `web/lib/types.ts`. The Python models (`app/schema.py`) are the only definitions. The executor must add TS mirror types for the fields used by KPI panels.
- Fields needed from Python schema:
  - `PayerCoverageEntry`: `payer_name`, `coverage_status`, `formulary_tier`, `prior_auth_required`, `step_therapy_required`
  - `CompetitorEntry`: `name`, `share_or_notes`, `formulary_position`, `channel`
  - `MarketAccessFindings`: `payer_coverage: PayerCoverageEntry[]`, `regulatory_snapshots`, `access_hurdles_summary`
  - `AnalystFindings`: `competitive_landscape: CompetitorEntry[]`, `market_sizes: MarketSize[]`, `summary`

### 2. API layer — `web/lib/api.ts`

- `getSession(id)` returns `SessionDetail` (confirmed line 53-55). This is the correct call to use in the report page.
- No report-specific API call needed. The full session including `research_json` / `analyst_json` is already available in one call.
- `getPdfUrl(sessionId)` exists and returns the correct URL for the PDF export button (placeholder action in this scope).

### 3. Backend response shape — `api/routes/sessions.py`

- Lines 67-68 confirmed: `research_json` and `analyst_json` are passed through **as raw strings** (not parsed). They are the JSON-serialized Pydantic model outputs from `app/schema.py`.
- `report_json` is parsed to dict on the backend (line 43-48), so `session.report` arrives as a parsed object. `research_json` and `analyst_json` do NOT — they require client-side `JSON.parse()`.
- `report.sections[]` is an array of `{heading: string, content: string}` objects — confirmed in Python schema lines 205-210.
- `report.sources` is `list[str]` — bare URL strings only, no title or domain structure.

### 4. react-markdown — `web/package.json`

- `react-markdown` v10.1.0 is installed (line 21). Also `remark-gfm` v4.0.1 (line 22).
- Both are confirmed available. The custom text renderer approach for citation `[N]` interception is viable.
- `react-markdown` v10 uses the `components` prop for custom renderers. The relevant hook is `text` node interception via a custom `components.p` (paragraph) renderer that post-processes children to detect `[N]` patterns.

### 5. framer-motion — `web/package.json`

- `framer-motion` v12.37.0 confirmed installed (line 17). `AnimatePresence` and `motion.div` are available.
- The FootnoteDrawer slide-in pattern (`translateX(100%) → translateX(0)`) is straightforward with `motion.div` + `AnimatePresence`.

### 6. Existing components in `web/components/buzz/`

Seven atoms confirmed on disk. All are compatible with the report screen:
- `TopNav` — accepts no props; resolves active from pathname. The `/report/[id]` route will need to be added to `resolveActive()` — currently routes not matching `/sessions`, `/query`, or `/run` fall through to `"research"`. The report page should resolve to `"sessions"` (it is a session detail view). **Minor TopNav change required.**
- `Btn` — supports `primary` variant and `onClick`. Used for Share / Export PDF / Re-run buttons.
- `KV` — renders key-value pairs in mono font. Used directly in FootnoteDrawer (Domain, Source, Retrieved via, Retrieved at).
- `SectionLabel` — accepts optional `accent` color. Used in panel card headers and footnote strip.
- `StatusDot`, `StatusChip` — not used in report screen.
- `SwarmGraph` — not used in report screen.

### 7. Existing route structure — `web/app/`

Current routes: `/` (root), `/query`, `/run`, `/sessions`. No `/report/[id]` route exists. The new route is additive.

The sessions detail page (`web/app/sessions/[id]/page.tsx`) uses `useLiveSession` hook for SSE streaming. The report page is for **completed** sessions only and can use a simpler `getSession()` fetch with no streaming.

### 8. Design token compatibility

`globals.css` defines all tokens used in `report.jsx`: `--bg`, `--surface`, `--border`, `--text-hi`, `--text-md`, `--text-lo`, `--amber`, `--cyan`, `--green`, `--red`, `--violet`. Font vars are `--font-sans` (IBM Plex Sans) and `--font-mono` (JetBrains Mono) — the prototype uses `var(--sans)` / `var(--mono)` shorthand names, but in the actual codebase these are `var(--font-sans)` / `var(--font-mono)`. **All inline styles in the new components must use the longer `--font-*` variable names.**

---

## Implementation Approach

**Recommended approach:** Build the report page as a Next.js App Router page (`"use client"` since it needs `useState` for the drawer). Fetch session data via `getSession()` on mount using `useEffect` + `useState`. Redirect to `/run/[id]` (or `/sessions/[id]`) if status is not `complete`.

**Why this approach over alternatives:**
- The design calls for static rendering of a completed report, not streaming. A simple `useEffect` fetch is correct — no `useLiveSession` SSE hook needed.
- The `/report/[id]` URL is distinct from `/sessions/[id]` (which shows the run trace). This matches the design's "DOSSIER" concept as a separate artifact from the run monitor.
- KPI panels are rendered conditionally from `research_json`/`analyst_json` — parsed client-side after fetch. This avoids any backend changes.

**Citation rendering approach:**
The `sources[]` array is plain URLs. The design prototype shows structured citations with title, domain, number, and excerpt. Since the real data only has URLs:
- Assign sequential numbers (`[1]`, `[2]`, ...) by index in `sources[]`.
- Parse domain from URL using `new URL(source).hostname`.
- Use the URL itself as the title fallback.
- The "excerpt" block in FootnoteDrawer gracefully shows "No excerpt available" for real data.
- Citation superscripts `[N]` in markdown body text are authored by the reporter agent and reference `sources[N-1]` by position. Clicking `[N]` opens the drawer for `sources[N-1]`.

**Citation markdown interception approach:**
Use `react-markdown` with a custom `components` config. Override the `text` renderer is not directly available in v10; instead, override `p` (paragraph) to process `children` as a React node tree, splitting string nodes on `/\[(\d+)\]/g` and replacing matches with `<CiteLink>` elements. This is slightly complex but well-established in the react-markdown ecosystem.

Simpler alternative: Pre-process the markdown string before passing to `react-markdown`, replacing `[N]` with `<cite data-n="N">[N]</cite>`, then use a `components.cite` override. This is cleaner to implement and easier to test — **prefer this approach**.

**Key Assumptions:**
- `session.report.sections[]` always contains at least 1 section when status is `complete`. If 0 sections, show executive summary as single prose block only.
- `research_json` / `analyst_json` can be null even for completed sessions (e.g. if run was retried from reporter only). Always null-guard before rendering KPI panels.
- Column span heuristic: sections at index 0 and index 3 span 2 columns (matches prototype layout). If fewer than 4 sections, all cards render at 1-col width. This is more predictable than heading-keyword matching.
- SparkLine data for KPI cells: no real sparkline data exists in the schema. KPI cells will render static placeholder sparklines (flat lines) unless market_sizes provides time-series data. This is explicitly acceptable per requirement §3 ("gracefully degrade to placeholder if data is absent").
- `CompetitorEntry.share_or_notes` is a free-text string (e.g. "~24% market share"). For the bar chart, parse the first numeric value via regex (`/(\d+(?:\.\d+)?)%/`) to get a percentage. If no match, render 0% bar width.

---

## Design Decisions

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Citation superscript rendering | Pre-process markdown string; replace `[N]` with `<cite data-n="N">` before react-markdown; use `components.cite` | Override `components.p` and walk React children tree | `components.p` approach is fragile with nested elements; pre-processing is testable with a pure string transform |
| Report page data fetching | `useEffect` + `useState` simple fetch on mount | Server component with `async` fetch | Page needs `useState` for drawer open state; mixing server/client would require layout split; simple client fetch is correct |
| Column span logic | Fixed index-based (index 0 and 3 span 2 cols) | Heading-keyword heuristic | Keyword matching is brittle as reporter agent headings vary per query; index-based is deterministic and matches the prototype |
| `research_json`/`analyst_json` typing | Add `MarketAccessFindings` and `AnalystFindings` TS interfaces to `web/lib/types.ts` (partial — only fields used by UI) | Generate from Python schema / use `unknown` | Full schema mirroring is too broad; `unknown` removes type safety; partial TS types covering rendered fields is the right tradeoff |
| Competitive bar chart % | Regex parse `share_or_notes` string for first `\d+%` | Require structured numeric field from schema | Schema has no numeric share field (`share_or_notes` is free text); regex fallback avoids schema change (out of scope for Part 3) |
| FootnoteDrawer animation | framer-motion `AnimatePresence` + `motion.div` with `initial/animate/exit` | CSS transition on conditional render | CSS transitions don't work well with `display:none` toggling; framer-motion is already installed and handles mount/unmount cleanly |
| TopNav active state for `/report` | Map `/report` prefix to `"sessions"` in `resolveActive()` | Leave as `"research"` default | Report is a session artifact — "Sessions" nav tab should remain highlighted |
| SparkLine data source | Static placeholder flat-line data for all KPI cells | Parse market_sizes for time series | `MarketSize` has `value_usd` + `year` but not time-series arrays; synthesizing sparklines from sparse data adds noise not signal |

---

## Risks

- **`coverage_status` normalization is lossy**: Free-text values like "PA required", "covered with step edit", "Tier 3 Specialty" must map to 4 buckets. The bucketing regex will miss edge cases. Mitigation: include `normalizeCoverageStatus()` as a pure function with unit tests covering known agent output variants. Default unrecognized values to `unknown` rather than crashing.
- **`research_json` / `analyst_json` JSON parse failure**: Malformed stored JSON would throw on `JSON.parse()`. Mitigation: wrap in `try/catch`; treat parse failure same as null (hide KPI panels, log to console in dev).
- **react-markdown v10 API changes**: v10 dropped some previously stable renderer APIs. The `components.cite` approach requires confirming that `cite` is a valid HTML element react-markdown will pass through. Alternative fallback: use `components.a` override pattern with a custom URL scheme if `cite` does not work. Low risk — `cite` is a standard HTML element.
- **`[N]` citation numbers in real agent output**: The reporter agent may not always produce `[N]`-style inline citations in markdown content. If no citations appear in section body text, the footnote strip still renders from `sources[]`, but `CiteLink` superscripts simply won't appear. This is acceptable graceful degradation.
- **Session without `report`**: If `session.report` is null (run errored but status shows complete due to a race), the page should redirect rather than render a blank panel grid. The redirect guard must check `session.report !== null` in addition to `session.status === 'complete'`.
- **No `/report` link from existing pages**: The new route won't be linked from anywhere yet. The sessions list and run page still point to `/sessions/[id]`. Adding a "View Dossier" link to `sessions/[id]/page.tsx` when the report is complete is in scope as a minor modification (one-liner Link addition).

---

## Clarification Needed

None. All design decisions can be made from the prototype, requirement doc, and existing code. The citation/sources limitation is a known constraint with an agreed fallback documented above.
