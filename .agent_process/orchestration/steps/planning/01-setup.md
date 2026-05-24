# Step 01: Scope Setup

**Input:** Requirement file path
**Output:** `<project_root>/.agent_process/work/{scope}/.run/planning/01-setup.md`

---

## 1. Scope Size Check (HARD GATE)

Read thresholds from `orchestration/scope-sizing-rules.md`.

Evaluate the requirement:
- Count acceptance criteria (target: 3-7)
- Count expected files (target: 4-10)
- Estimate complexity

**PASS:** Within thresholds → continue
**WARN:** Near limits → note risk, continue
**FAIL:** Exceeds limits → offer breakdown or override

---

## 2. Breakdown (if needed)

If scope too large, offer to split into child requirements:
- Each child gets `-01`, `-02` suffix
- Parent marked as `split`
- Create breakdown coverage map

---

## 3. Derive Names

From the requirement file path, derive:
- **Scope name:** folder name under `.agent_process/work/`
- **Work folder:** `.agent_process/work/{scope}/`

Create the run directory:
```bash
mkdir -p <project_root>/.agent_process/work/{scope}/.run/planning
```

---

## Output

```markdown
# Scope Setup

**Requirement:** {path}
**Scope name:** {derived_name}
**Work folder:** `.agent_process/work/{scope}/`

## Size Check
- Criteria count: {N} (target: 3-7)
- Expected files: {N} (target: 4-10)
- **Verdict:** PASS / WARN / FAIL

## Breakdown
{If FAIL: breakdown options offered}
{If PASS/WARN: "Not needed"}

## Ready
Work folder created. Proceed to assessment.
```
