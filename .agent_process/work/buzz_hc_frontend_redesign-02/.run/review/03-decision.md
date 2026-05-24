# Review Decision: ITERATE

**Iteration:** buzz_hc_frontend_redesign-02 / iteration_01
**Attempt:** 1 of 4 (can ITERATE → next would be iteration_01_a)

## Evidence

- Criteria: 10/10 MET (per `01-verify.md`)
- Gates: Gate 1 FAIL (doc drift); Gates 2–4 PASS
- Validation: PASS — `pnpm tsc` clean, Jest 4/4, `pnpm build` SUCCESS, pytest 53/53

## Rationale

All 10 locked acceptance criteria are MET and the code change is correct, integration is clean, and the full validation pipeline is green. The only failing gate is documentation: the planned "Run screen architecture" MEMORY.md subsection was not added in this iteration, and two orphaned references (MEMORY.md line 21 + README.md line 131) still describe `useRunSession` as the "SSE state machine hook" — which is now factually wrong. Per the iteration plan (line 159), the MEMORY.md update was an in-scope deliverable for this iteration, so the right call is one targeted doc-only iteration rather than APPROVE-with-followup or BLOCK.

## Criteria Status

- MET — Criterion 1: `/run/<id>` complete renders without EventSource
- MET — Criterion 2: Refresh of running session yields single SSE + historical from DB
- MET — Criterion 3: `/sessions/<id>` uses `router.replace` for both redirect branches
- MET — Criterion 4: `/run` (bare) `router.replace('/query')`; no form
- MET — Criterion 5: Jest test asserts EventSource never called + `router.push` once with `/run/<id>`
- MET — Criterion 6: `PipelineStrip` derives 5 stages from events
- MET — Criterion 7: Error banner + failed-agent label + Retry → `retrySession` → `/run/<new>`
- MET — Criterion 8: `SwarmTopology` RAF — zero `setState`, refs + `setAttribute` only
- MET — Criterion 9: Center-column placeholder text exact-match
- MET — Criterion 10: `pnpm build` zero TS errors + zero new `any`; pytest 53/53 green

## ITERATE Fixes (next: iteration_01_a)

This is a documentation-only iteration. No code, tests, or validation script changes. Three targeted edits.

---

**Fix 1: Correct stale "SSE state machine" description in MEMORY.md**

- **File:** `/Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md:21`
- **Before:** `| `web/hooks/useRunSession.ts` | SSE state machine hook |`
- **After:** `| `web/hooks/useRunSession.ts` | Start-only hook — calls `startRun()` then `router.push('/run/<id>')`; no SSE ownership |`
- **Semantic Intent:** After this iteration, `useRunSession` no longer constructs `EventSource` or holds SSE state — that responsibility moved to `useLiveSession` on `/run/[id]`. Leaving the old description in MEMORY.md (which is auto-loaded into every future Claude session for this project) will cause downstream agents to assume the hook still owns SSE and reach for the wrong patch point. The corrected one-liner needs to (a) say "start-only" so the new role is unambiguous, and (b) point at `useLiveSession` implicitly by removing the SSE claim.
- **Acceptance Test:** `grep -n "SSE state machine" /Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` returns zero lines AND `grep -n "Start-only" /Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` returns exactly one line matching the `useRunSession.ts` row.

---

**Fix 2: Add "Run screen architecture" subsection to MEMORY.md**

- **File:** `/Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` — append a new `## Run screen architecture` section before `## CI/CD` (i.e. after `## Important constraints`)
- **Before:** No `## Run screen architecture` heading exists; MEMORY.md jumps from `## Important constraints` straight to `## CI/CD`.
- **After:** A new subsection covering the five facts the iteration plan committed to (line 159):
  1. `/run/[id]` is the live observation route — consumes `useLiveSession(id)` only; renders header, `PipelineStrip`, `AgentCard` stack, `SwarmTopology`, `EventLog`.
  2. `useRunSession` is start-only — calls `startRun()` then `router.push('/run/<session_id>')`. Public surface `{ state, run, reset }` preserved.
  3. `useLiveSession` is the refresh-safe watch hook — on mount, loads historical events from DB via `getSession(id)`, then opens `EventSource` only when `status === "running"`. Single SSE owner.
  4. Pipeline stages are derived from `session.events` (`agent_start` / `agent_end` keyed by `source`). The `SessionDetail` schema has **no** `progress` field — do not add one.
  5. `SwarmTopology` uses mutable SVG refs + `setAttribute` inside RAF (matches Part 1 `SwarmGraph` pattern). **Never** call `setState` inside RAF — would trigger 60 React re-renders/sec.

  Also add the four new files to the Key files table (or to a sub-table beneath the new heading): `web/app/run/[id]/page.tsx`, `web/components/buzz/SwarmTopology.tsx`, `web/components/buzz/AgentCard.tsx`, `web/components/buzz/EventLog.tsx`, `web/components/buzz/PipelineStrip.tsx`, `web/hooks/useLiveSession.ts` (referenced but not modified), `web/__tests__/useRunSession.test.ts`.
- **Semantic Intent:** MEMORY.md is the auto-loaded primer for future sessions in this repo. Without these five facts, the next agent picking up Part 3 or Part 4 will not know (a) which hook owns SSE, (b) that stages are events-derived (and will probably try to add a `progress` field to the API), or (c) the RAF-no-setState invariant that took explicit verification this iteration. The subsection exists to prevent those exact regressions in Parts 3/4.
- **Acceptance Test:** `grep -n "^## Run screen architecture" /Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` returns exactly one match AND the subsection body contains all five fact-markers: `/run/[id]`, `useRunSession` + "start-only", `useLiveSession` + "refresh-safe", `agent_start`/`agent_end` (or "events-derived"), and `setAttribute` + "never `setState`" (or equivalent RAF-isolation language). A grep for `progress` field warning in the same subsection should also match (to lock in the schema constraint).

---

**Fix 3: Correct README.md hook description**

- **File:** `/Users/james/Documents/CodeProjects/buzz-hc/README.md:131`
- **Before:** `│   ├── hooks/              # useRunSession (SSE state machine)`
- **After:** `│   ├── hooks/              # useRunSession (start-only), useLiveSession (refresh-safe SSE)`
- **Semantic Intent:** Same drift as Fix 1, but in the public-facing repo README. The `useLiveSession` mention is intentional: without it, a reader of the repo tree comment has no breadcrumb to the actual SSE owner. Keeping both hook names in the comment makes the directory listing accurate and self-documenting.
- **Acceptance Test:** `grep -n "SSE state machine" /Users/james/Documents/CodeProjects/buzz-hc/README.md` returns zero lines AND `grep -n "useLiveSession" /Users/james/Documents/CodeProjects/buzz-hc/README.md` returns at least one line (the new directory comment). README still builds in renderers (no markdown syntax broken).

---

**No code, test, or validator changes in iteration_01_a.** The `pnpm tsc` / `pnpm test` / `pnpm build` / `pytest` quartet should remain green with no diff to any `.ts` / `.tsx` / `.py` file. The validator script does not need to be extended — Gate 1 (Documentation) is enforced by review-time inspection, not the scoped validator hook.

## Post-Decision Actions (FOR COORDINATOR — do not execute in this step)

Per `03-decide.md` ITERATE protocol:
1. Create folder `.agent_process/work/buzz_hc_frontend_redesign-02/iteration_01_a/`
2. Write `results.md` placeholder containing the three fixes above (verbatim, including semantic intent)
3. Update `iteration_plan.md`: latest iteration → `iteration_01_a`, decision → ITERATE, reason → "doc-drift (Gate 1)"
4. Advance scope tracking: `.agent_process/scripts/github-issues-lifecycle.sh set-iteration buzz_hc_frontend_redesign-02 iteration_01_a`
5. Hand off: `/ap_exec buzz_hc_frontend_redesign-02 iteration_01_a`

## Next Step

Coordinator reviews this decision with the human, then executes the post-decision actions above to spin up `iteration_01_a` with the three doc fixes scoped exactly to MEMORY.md and README.md.
