# Step 02: Quality Gates

**Input:** `<project_root>/.agent_process/work/{scope}/.run/review/01-verify.md`
**Output:** `<project_root>/.agent_process/work/{scope}/.run/review/02-gates.md`

---

## Fast-Track Check

If ALL true, most gates can be fast-tracked:
- Internal refactor only (no API/UI/behavior changes)
- Test-only or doc-only changes
- results.md notes "No external impact"

Fast-tracked gates still need quick verification, not full analysis.

---

## Gate 1: Documentation

**Check:** Docs updated in same commit as code changes (Zero Documentation Drift).

- End user docs updated? (if behavior changed)
- Developer docs updated? (if API/architecture changed)
- Orphaned references to removed code?

### When the iteration plan declares `Removed Surfaces`

If the plan's **Removed Surfaces** section is non-empty (i.e. this scope
removes or renames a public surface), the "orphaned references" check is
no longer a yes/no judgment. The reviewer MUST:

1. Read the **Removed-Surface Scrub** section of the iteration's
   `results.md`. If it is missing, **FAIL Gate 1**.
2. For at least one declared surface, run the validator's stale-surface
   scrub block manually — do not trust the implementer's count alone.
3. Inspect each whitelist addition the executor made beyond the planner's
   initial whitelist. Each addition must have an inline justification
   (historical record, guardrail test, internal name collision, explicit
   "is removed" note). **FAIL Gate 1** if any of these are true:
   - A whitelist entry has no justification.
   - The justification is *"out of scope"* / *"deferred to follow-up scope"* — those are valid reasons to defer entire AC, not to whitelist a specific stale reference while still claiming the AC is met.
   - An operator-facing surface (smoke scripts, READMEs, runbooks, observability docs) is whitelisted as "historical" when it is in fact still serving as live operator guidance.

When **Removed Surfaces** is empty (additive scope), this gate falls back
to its existing yes/no check on orphaned references.

See `process/removal-scope-checklist.md` for the full contract.

### When `results.md` declares `Spec Concerns`

If `results.md` contains a `## Spec Concerns` section, the reviewer
MUST read it before applying any other gate logic. A surfaced concern
is not by itself a FAIL — but it changes how the gates are weighted:

- **Concern raised AND local fix applied:** Gate 1 verifies the fix
  is correct AND that the iteration plan / prepare doc are updated to
  reflect the corrected understanding (otherwise the next iteration
  inherits the same gap).
- **Concern raised WITHOUT a fix:** the iteration's overall decision
  becomes ITERATE — revise the prepare doc to address the concern —
  regardless of whether other gates pass. The reviewer MUST NOT mark
  the iteration APPROVE while a Spec Concern is unresolved.

A passing iteration that silently bypasses a known soundness concern
is the failure mode this clause prevents. It encodes the lesson from
sub-iterations where the implementer noticed a soundness issue,
classified it as future-improvement, and shipped — leaving the next
iteration to inherit the bug.

**FAIL Gate 1** if a Spec Concern was raised, no fix was applied, and
the decision is APPROVE. (The proper outcome for that combination is
ITERATE.)

**Weakened-Assertion FAIL.** If `results.md` acknowledges removing,
relaxing, commenting-out, or rephrasing-around a failing test
assertion, validator check, or guard — especially under Spec Concerns
or as a "future scope" note — AND the underlying production fix did
NOT land in the same iteration, **FAIL Gate 1** regardless of other
gate signals. Signature phrases to watch for in `results.md`:

- "dropped the X assertion" / "removed the assertion since..."
- "rephrased the comment to avoid the validator check"
- "future scope can extend the loader / fix the gap"
- "weakened to match current behavior"

The reviewer MUST spot-check the test diff against the previous
iteration to verify whether an assertion was actually weakened. A
weakened assertion is a *contract reduction*, even when the edit is
mechanically simple — and contract reductions cannot be silently
shipped. The proper response when this is found:

- **ITERATE** with a fix that either (a) restores the assertion AND
  adds the production fix in the same iteration, or (b) preserves
  the weakening only if the coordinator has explicitly accepted the
  contract reduction in writing, with the iteration plan updated to
  reflect the reduced contract.

This rule encodes the lesson from scopes where an executor classified
a contract-erosion as a "safe local fix" under §1.4 and shipped the
iteration with the contract surface silently reduced. The §1.4
channel's third-option prohibition is mirrored here on the reviewer
side: weakening is not a valid resolution path.

**PASS:** Docs appropriately updated OR clear justification why N/A;
AND no unresolved Spec Concerns
**FAIL:** External behavior changed with no doc update; OR
removed-surface scrub missing/incomplete; OR a whitelist entry is
unjustified; OR an unresolved Spec Concern is paired with an APPROVE
decision

---

## Gate 2: Integration

**Check:** Changes don't break integration points outside scope.

For files with changed interfaces:
```bash
grep -r "functionName\|ComponentName\|api/endpoint" src/
```

**PASS:** All integration points verified compatible OR internal-only changes
**FAIL:** Interface changed but call sites not updated

---

## Gate 3: Adversarial Review

**Check:** Independent verification of criteria compliance.

If `adversarial-review.md` exists from execution:
- Read the verdicts
- Note agreements/disagreements with your assessment

If not, perform rubric self-review:
- For each criterion, find file:line evidence
- Assign PASS/FAIL with no hedging

**The verdict is advisory** — informs but doesn't make the decision.

---

## Gate 4: Scoped Validation

**Check:** Validation was scoped to this work, not entire codebase.

Read `test-output.txt`:
- Did scoped validation run?
- Pre-existing issues excluded?

---

## Output

```markdown
# Quality Gates

## Gate Summary

| Gate | Status | Notes |
|------|--------|-------|
| Documentation | PASS/FAIL/N/A | {brief reason} |
| Integration | PASS/FAIL/FAST-TRACKED | {brief reason} |
| Adversarial | {X}/{Y} PASS | {method used} |
| Scoped Validation | PASS/FAIL | {from test-output.txt} |

## Overall Signal

- Toward APPROVE: {N} gates
- Toward ITERATE: {N} gates  
- Toward BLOCK: {N} gates

## Details

{Only include if gates failed — don't pad with "everything passed" text}
```
