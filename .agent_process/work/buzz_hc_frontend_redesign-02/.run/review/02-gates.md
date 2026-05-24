# Quality Gates

**Scope:** buzz_hc_frontend_redesign-02
**Iteration:** iteration_01

## Gate Summary

| Gate | Status | Notes |
|------|--------|-------|
| Documentation | FAIL | MEMORY.md "Run screen architecture" subsection (planned doc update) not added; existing MEMORY.md entry for `useRunSession.ts` ("SSE state machine hook") and README.md line 131 ("useRunSession (SSE state machine)") are now factually wrong — the hook is start-only. No Spec Concerns section. |
| Integration | PASS | `useRunSession` public surface `{ state, run, reset }` preserved (file inspection confirms). Grep shows ZERO non-test callers (`web/app/query/page.tsx` uses `startRun` directly, not the hook), so no call sites needed updating. `useLiveSession` is unmodified per scope. `/sessions/[id]` and `/run` (bare) continue to respond — repurposed as redirects, not removed. |
| Adversarial | 10/10 PASS | Rubric self-review across all 10 locked criteria (method: file:line evidence, no hedging). See Details. |
| Scoped Validation | PASS | test-output.txt: scoped script 8/8 OK; `pnpm tsc` clean; Jest 4/4 (incl. new `useRunSession.test.ts`); `pnpm build` SUCCESS; pytest 53/53. Scoped to the 9 in-scope files — no codebase-wide noise included. |

## Overall Signal

- Toward APPROVE: 3 gates (Integration, Adversarial, Scoped Validation)
- Toward ITERATE: 1 gate (Documentation — MEMORY.md drift)
- Toward BLOCK: 0 gates

## Details

### Gate 1 — Documentation (FAIL)

**Removed Surfaces:** iteration plan declares **N/A — no public surfaces removed or renamed** (lines 169–173). Gate 1 therefore falls back to the additive yes/no orphaned-references check. No Removed-Surface Scrub required.

**Spec Concerns:** `results.md` contains no `## Spec Concerns` section. No weakened-assertion or rephrase-around language detected (no "dropped the assertion", "rephrased to avoid", "future scope can extend", or "weakened to match"). Confirmed clean.

**Doc updates — what landed vs. what the plan committed to:**

- **End user docs:** N/A per plan — no user-visible behavior change beyond URL stability. PASS.
- **Developer docs (planned):** plan line 159 commits to updating `MEMORY.md` with a "Run screen architecture" subsection covering (a) `/run/[id]` is the live observation route, (b) `useRunSession` is start-only, (c) `useLiveSession` is the refresh-safe watch hook, (d) stages are events-derived (no `progress` field), (e) `SwarmTopology` uses mutable SVG refs in RAF.

  This update **did not land**. Inspection of `/Users/james/.claude/projects/-Users-james-Documents-CodeProjects-buzz-hc/memory/MEMORY.md` shows:
  - No new "Run screen architecture" subsection.
  - Line 21 still describes `web/hooks/useRunSession.ts` as "SSE state machine hook" — that description is now factually wrong; the hook no longer owns SSE.
  - No mention of `useLiveSession`, `/run/[id]`, or the events-derived stage model.

- **Orphaned references to refactored code:** README.md line 131 reads `hooks/ # useRunSession (SSE state machine)`. Same drift — the hook is no longer the SSE state machine after this iteration. README is checked into the repo and was not updated alongside the code.

These are orphaned/stale references to the refactored API surface introduced in this iteration. Per the gate spec ("External behavior changed with no doc update; OR orphaned references"), this fails Gate 1.

**Severity assessment:** the drift is documentation-only — it does not affect runtime correctness, test results, or the 10 acceptance criteria (all of which are MET). Fix is a one-paragraph MEMORY.md update + a one-line README.md correction. Recommend ITERATE (not BLOCK) to add the planned MEMORY.md subsection and correct the stale "SSE state machine" descriptions in README.md and MEMORY.md.

### Gate 2 — Integration (PASS)

**`useRunSession` public signature:** preserved. `web/hooks/useRunSession.ts:48` returns `{ state, run, reset }` — identical to pre-refactor shape. The `run(query, tavilyApiKey?)` argument list is unchanged.

**Non-test callers of `useRunSession`:** zero. `grep -rn "useRunSession" web --include="*.tsx" --include="*.ts"` returns only the definition (`web/hooks/useRunSession.ts:16`) and the new test (`web/__tests__/useRunSession.test.ts:2,10,25`). The `/query` page (`web/app/query/page.tsx:8,50`) calls `startRun` directly from `@/lib/api`, not the hook. So even the new `router.push('/run/<id>')` behavior added inside `run()` cannot break a downstream consumer because there are no downstream consumers in this repo.

**Redirected routes still respond:**
- `/sessions/[id]` — now a 25-line thin redirect with `router.replace` to `/run/<id>` or `/report/<id>`. Existing inbound link from `web/app/sessions/page.tsx:97` (`router.push("/run/" + s.session_id)`) was already pointing at `/run/<id>` directly, so the redirect adds no new traversal hop for the sessions-list page.
- `/run` (bare) — now a 10-line `router.replace('/query')` redirect. No site-internal callers found.

**`useLiveSession` unchanged:** confirmed by plan (line 55) and not touched in this iteration.

### Gate 3 — Adversarial Review (10/10 PASS)

No `adversarial-review.md` from execution — performed rubric self-review.

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | `/run/<id>` for `status=complete` renders historical without `EventSource` | PASS | `web/app/run/[id]/page.tsx` consumes `useLiveSession(id)` only; `useLiveSession` (unmodified per plan) gates `new EventSource` on `status === "running"`. Direct EventSource construction in the page: none. |
| 2 | Refresh of running session — historical from DB + single live EventSource, no dupes | PASS | Same pattern as the prior `/sessions/[id]` reference impl (plan line 55, 230). `useLiveSession` is the single SSE owner; page line 62 merges `session.events` + `liveEvents`. |
| 3 | `/sessions/<id>` uses `router.replace` for ALL redirect branches | PASS | `web/app/sessions/[id]/page.tsx:15,17` both use `router.replace`. Zero `router.push` in the file. |
| 4 | `/run` (no id) `router.replace('/query')`; no query form | PASS | `web/app/run/page.tsx:7` `router.replace("/query")` inside `useEffect`; file is 10 lines, single `<div>` body, zero form markup. |
| 5 | Jest test asserts `EventSource` never called + `router.push` once with `/run/<id>` | PASS | `web/__tests__/useRunSession.test.ts:29` `expect(global.EventSource).not.toHaveBeenCalled()`; `:30` `toHaveBeenCalledTimes(1)`; `:31` `toHaveBeenCalledWith('/run/test-session-001')`. EventSource stub at lines 14-17 (defined as `jest.fn()` if missing on `global`, then spied) is a valid jsdom workaround — preserves assertion intent. |
| 6 | `PipelineStrip` derives complete/running/queued states from events | PASS | `web/components/buzz/PipelineStrip.tsx:14-32` derives from `agent_start`/`agent_end`; STATE_STYLES (48-54) maps green/✓, cyan/↻, border/·. 5 cells (Lead, Researcher, Analyst, Reporter, Synthesis) per plan's 5-stage requirement. |
| 7 | Error banner with error_msg + failed-agent label + Retry → retrySession → `/run/<new>` | PASS | `web/app/run/[id]/page.tsx:21-28` `deriveFailedAgent` walks events in reverse for unterminated `agent_start`; lines 103-112 render banner with `error_msg` + uppercase agent label + retry button; `handleRetry` (66-71) calls `retrySession(sessionId)` then `router.push("/run/" + session_id)`. |
| 8 | `SwarmTopology` RAF has no `setState` calls (only `setAttribute`) | PASS | `web/components/buzz/SwarmTopology.tsx`: grep finds zero `setState`/`useState`. RAF body (47-65) uses only `outer.setAttribute(...)`; state via `useRef` (36-38), pause via `statusRef.current` avoiding stale closure. |
| 9 | Center-column placeholder text `"← Reporter streaming added in Part 4"` | PASS | `web/app/run/[id]/page.tsx:134` renders exactly that string. |
| 10 | `pnpm build` zero TS errors + zero new `any` types; pytest green | PASS | test-output.txt: build SUCCESS, TS clean, 53/53 pytest. Single typed structural cast `(session.usage as { total_tokens?: number })` (run/[id]/page.tsx:64) is not `any`. |

**Independent verdict: APPROVE on criteria-compliance grounds.** The verifier's "10 MET, 0 PARTIAL, 0 NOT MET" reading holds up under independent re-rubric.

Minor agreement on the verifier's noted deviations (none of which block):
- 5th "Synthesis" stage in `PipelineStrip.tsx` — required by criterion 6's "all 5 stages" language; minor undocumented design decision (`PIPELINE_STAGES` duplicated rather than re-exported from `web/app/query/page.tsx`). Acceptable per plan's scope-boundary guidance.

### Gate 4 — Scoped Validation (PASS)

`test-output.txt` shows the scoped validator script executed all 8 checks tied to this scope's files (TS, Jest≥4, file-existence for 3 in-scope files, `useRunSession` no-EventSource grep, `sessions/[id]` `router.replace` grep, `lucide-react` ban). All passed. The four RUN-list commands (`pnpm tsc`, `pnpm test`, `pnpm build`, `uv run pytest tests/ -v`) all green. No pre-existing issues swept in — the script's grep checks are file-scoped, not codebase-wide.

---

## Recommendation

**ITERATE (documentation-only fix).** The 10 locked acceptance criteria all PASS and integration is clean. The only failing gate is Gate 1: the planned `MEMORY.md` "Run screen architecture" subsection did not land, and `README.md:131` + `MEMORY.md:21` both still describe `useRunSession` as the "SSE state machine hook" — which is no longer true after this iteration's refactor. The fix is a single follow-up commit adding the planned MEMORY.md subsection and correcting the two stale one-liners.

If the orchestrator considers the doc-drift fix in-flight (already on the planned list), the alternative call is APPROVE-with-doc-followup — but per the gate spec a same-commit doc update is the standard, and the plan explicitly committed to landing the MEMORY.md update in this iteration.
