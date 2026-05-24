# Scope Setup

**Requirement:** `.agent_process/requirements_docs/ui_redesign/buzz_hc_frontend_redesign-02.md`  
**Scope name:** `buzz_hc_frontend_redesign-02`  
**Work folder:** `.agent_process/work/buzz_hc_frontend_redesign-02/`

---

## 5-Second Check

1. **One sentence?** ✓ "Implement the live run observation screen at `/run/[id]` using `useLiveSession` so streaming output persists on page refresh."
2. **Done definition?** ✓ 10 specific success criteria with testable outcomes (navigation, refresh safety, pipeline strip rendering, RAF animation, etc.)
3. **Timeframe?** ✓ Complex scope but well-scoped to one feature (run screen); realistic for 1–2 weeks with 5 sub-iterations
4. **Specific name?** ✓ "Bloomberg-Terminal UI Redesign — Part 2: Run Screen + Persistence" — clear, specific

---

## Size Check

- **Criteria count:** 10 (target: 3–7) — **WARNING**
  - Scope is at the high end but justifiable: 10 acceptance criteria span 4 major components (dynamic route, hooks refactor, three UI panels, SSE reconnection logic).
  
- **Expected files:** 9 (target: 4–10) — **PASS**
  - New: 5 files (SwarmTopology, AgentCard, EventLog, PipelineStrip, /run/[id] page)
  - Modified: 3 files (run/page.tsx refactor, sessions/[id] redirect, useRunSession)
  - Test: 1 file (useRunSession.test.ts)
  
- **Distinct subsystems:** 3 (target: 1–3) — **PASS**
  - Frontend routing (`/run/[id]`, `/sessions/[id]` redirects)
  - Hooks layer (`useRunSession` refactor, `useLiveSession` integration)
  - UI components (AgentCard, EventLog, PipelineStrip, SwarmTopology)

---

## Risks Noted

1. **Warning: Criteria count at high end** — 10 criteria is above the 3–7 target but offset by clear sub-components (header, progress strip, banners, three columns). Each maps to 1–2 success criteria. Risk is manageable.

2. **Known execution risks** (from requirement):
   - `useRunSession` refactor larger than synthesis estimated — SSE code entanglement requires careful removal
   - Double EventSource risk if refactor incomplete — mitigated by Jest test assertion
   - Back-button trap on redirect — critical to use `router.replace` not `router.push`
   - SwarmTopology RAF isolation — must not trigger React re-renders; similar risk as Part 1

3. **Dependency:** `buzz_hc_frontend_redesign-01` (design tokens, atoms, components/buzz/) must be complete. Assumed done per requirement statement.

---

## Breakdown

**Not needed.** Scope passes thresholds with noted warning on criteria count. The requirement is already split (Part 2 of 4), so further breakdown would over-segment the work. Proceed as single scope.

---

## Ready

Work folder created at:
```
.agent_process/work/buzz_hc_frontend_redesign-02/
```

**Next step:** Proceed to assessment (02-assess.md).
