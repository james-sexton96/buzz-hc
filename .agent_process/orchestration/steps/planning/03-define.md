# Step 03: Define Scope

**Input:** Requirement file, assessment output
**Output:** `<project_root>/.agent_process/work/{scope}/.run/planning/03-define.md`

---

## 1. Files in Scope (Expected)

Create the expected list of files to create, modify, or delete.

**Note:** This is guidance, not a hard boundary. The executor may touch additional
files if necessary for correctness, with justification and validation updates.

**Target:** 4-10 files. If >15, flag for potential split.

For each file:
- Path
- Action (New / Modified / Deleted)
- Purpose (brief)

**Contract Check:** If API/payload changes affect other clients, note:
- Which consumers
- Contract definition file

---

## 2. Frozen Acceptance Criteria

Transform requirement success criteria into specific, testable criteria.

**Good criteria (specific, testable):**
- `Function X returns Y when given Z`
- `12/12 unit tests pass`
- `API returns 200 with valid payload`

**Bad criteria (vague):**
- ~~Code quality improved~~ (how measured?)
- ~~Works better~~ (what does "better" mean?)

**Target:** 3-7 criteria. If >10, scope likely too large.

**LOCKED:** These criteria cannot change during iteration. New issues → backlog.

---

## 3. Documentation Impact

Based on the changes:

**End User Docs:**
- Updated needed? (behavior change → yes)
- Which docs?

**Developer Docs:**
- Update needed? (API/architecture change → yes)
- Which docs?

If internal refactor only: "N/A — no external impact"

---

## Output

```markdown
# Scope Definition

**Scope:** {scope}

## Files in Scope

| Path | Action | Purpose |
|------|--------|---------|
| `path/to/file.ts` | Modified | {what changes} |
| `path/to/new.ts` | New | {purpose} |

**Total:** {N} files
**Contract consumers:** {list or N/A}

## Acceptance Criteria (LOCKED)

**DO NOT MODIFY during iteration. New issues → backlog.**

- [ ] {Specific, testable criterion 1}
- [ ] {Specific, testable criterion 2}
- [ ] {Specific, testable criterion 3}

**Count:** {N} (target: 3-7)

## Documentation

- End user docs: {Updated: X.md / N/A — reason}
- Developer docs: {Updated: Y.md / N/A — reason}
```
