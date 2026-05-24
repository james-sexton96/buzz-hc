# Step 10: Report Completion

**Model tier:** cheap
**Tools needed:** Read
**Input:** ALL `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/*` files
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/10-report.md`

---

## Your Task

Read all release step outputs and produce a final summary for the user.

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/10-report.md`:

```markdown
# Release Complete: {mode}

**Context:** {scope mode / no-scope mode}
**Scope:** {name or "N/A"}
**Build:** {BUILD_NUM}

## Actions Taken
- ✅ Changelog updated: {[Unreleased] / [X.Y.Z]}
- ✅ USER_CHANGELOG.md: {Updated / Created / Skipped / N/A}
- ✅ Version files: {updated list / "N/A (not release mode)"}
- ✅ Committed: {sha}
- ✅ Build tagged: build/{N}
- ✅ Release tagged: {tag / "N/A"}
- ✅ Pushed to: origin/{branch}
- ✅ PR created: {URL}
- ✅ PR shepherd: {launched / skipped}
- ✅ Central sync: {committed / skipped / N/A}

## Changelog Entry
{The entry added to CHANGELOG.md}

## Next Steps
- `pr` mode: Merge PR when ready, run `/ap_release release <type>` to ship
- `beta` mode: Share beta tag for testing, run more betas or release when stable
- `release` mode: Merge PR, release is complete
```
