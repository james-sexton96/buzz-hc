# Scope Sizing Rules

**Purpose:** Configurable thresholds for the scope check gate (Step 01 of planning).
Edit this file to adjust what passes the gate. The step file reads these values — no other files need to change.

---

## 5-Second Check (all must be YES to pass)

1. **One sentence?** Can the objective be explained in one sentence?
2. **Done definition?** Do I know what "done" looks like (specific, testable)?
3. **Timeframe?** Can this be done within the target duration below?
4. **Specific name?** Is the name specific (not "cleanup", "improve", or "refactor" without qualifiers)?

## Size Thresholds

| Metric | Target | Warning | Fail |
|--------|--------|---------|------|
| Acceptance criteria count | 3–7 | 8–10 | >10 |
| Files expected to change | 4–10 | 11–15 | >15 |
| Distinct subsystems touched | 1–3 | 4 | >4 |

**Warning** means: flag it in the output but still PASS. The planner should note the risk.
**Fail** means: VERDICT: FAIL. The scope must be split before planning continues.

## Duration Target

```
Duration: 1–2 weeks (5–10 work sessions)
Iterations: 1–5 numbered iterations
Sub-iterations: 0–3 per numbered iteration
Outcome: Shippable feature or measurable improvement
```

## Override: Allowing Larger Scopes

To temporarily allow a larger scope, add a frontmatter field to the requirement:

```yaml
---
id: my_large_requirement
scope_override: true
scope_override_reason: "Cross-cutting migration that can't be split without creating integration risk"
---
```

When `scope_override: true` is present in the requirement:
- The 5-second check still runs (informational)
- Size thresholds shift to Warning levels only (no Fail)
- The scope check output notes the override and reason
- The planner must still document the risk of the larger scope

## Red Flags (always fail regardless of override)

These indicate a scope that will fail during execution, not just planning:

- Objective needs multiple paragraphs to explain
- Uses vague verbs without specifics: "cleanup", "improve", "refactor"
- Has dependencies on other in-progress work
- Touches files owned by multiple active scopes
