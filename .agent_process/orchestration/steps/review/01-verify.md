# Step 01: Verify Implementation

**Output:** `<project_root>/.agent_process/work/{scope}/.run/review/01-verify.md`

---

## Guiding Principle

Verify the executor understood the INTENT, not just made changes. A mechanical fix that misses the semantic requirement should fail even if it technically matches the checklist.

---

## 1. Load Context

Read these files:
- `.agent_process/work/{scope}/iteration_plan.md` — frozen criteria
- `.agent_process/work/{scope}/{iteration}/results.md` — claimed work
- `.agent_process/work/{scope}/{iteration}/test-output.txt` — validation output

Determine iteration state:

| Iteration | Attempt | Can ITERATE? |
|-----------|---------|--------------|
| `_01` | 1 of 4 | Yes |
| `_01_a` | 2 of 4 | Yes |
| `_01_b` | 3 of 4 | Yes |
| `_01_c` | 4 of 4 | **No — APPROVE or BLOCK only** |

---

## 2. Evaluate Criteria

For each frozen criterion:
1. What does results.md claim?
2. What does the code actually show?
3. **Did the executor understand WHY**, not just make the change?

Assign: **MET** / **PARTIAL** / **NOT MET**

For sub-iterations: verify each fix addressed the semantic intent, not just the mechanical change.

---

## 3. Code Verification

Open each claimed changed file. Check:
- Does the code match the claim?
- Is the implementation complete or partial?
- For sub-iteration fixes: does the fix actually solve the underlying problem?

**Red flag:** If executor made the literal change but missed the semantic requirement (e.g., added checkout step but git diff still queries wrong repo), mark as PARTIAL.

## 4. Scope Expansion Assessment

If the executor touched files outside the planned scope:
- Was the expansion necessary for correctness?
- Was it documented with justification in results.md?
- Was the validation script updated to cover new files?
- **This is expected behavior** — executors have agency to solve the problem correctly.
- Only flag as issue if expansion was unjustified or undocumented.

---

## Output

```markdown
# Verification Results

**Scope:** {scope}
**Iteration:** {iteration}
**Attempt:** {N} of 4 | Can ITERATE: {YES/NO}

## Criteria Evaluation

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | {text} | MET/PARTIAL/NOT MET | {file:line or gap} |

**Summary:** {N} MET, {N} PARTIAL, {N} NOT MET

## Code Verification

| Claim | Actual | Match? |
|-------|--------|--------|
| {from results.md} | {from code} | YES/NO |

**Semantic Understanding:** {Did executor demonstrate understanding of WHY, or just mechanical changes?}

## Scope Expansion
- **Files outside plan:** {N files, or "none"}
- **Justified:** {YES — needed for correctness / NO — unjustified / N/A}
- **Documented:** {YES — in results.md / NO / N/A}
- **Validation updated:** {YES / NO / N/A}

## Key Findings
- {finding 1}
- {finding 2}
```
