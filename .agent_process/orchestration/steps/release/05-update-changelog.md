# Step 05: Update Changelog

**Model tier:** capable
**Tools needed:** Read, Write
**Input:** mode, version info (`<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/03-version.md`), change type (`<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/04-change-type.md`)
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/05-changelog.md`

---

## Your Task

Update CHANGELOG.md (and USER_CHANGELOG.md for beta/release modes).

## Ensure CHANGELOG.md Exists

If it doesn't exist, create with Keep a Changelog format header.

## Update Rules by Mode

### `pr` mode
Append entry to `[Unreleased]` section under appropriate category. Do NOT move [Unreleased] to a version.

### `beta` mode
Move `[Unreleased]` contents to new version header: `## [{version}-beta.{N}] - {date}`. Create empty `[Unreleased]` section above.

### `release` mode
Move `[Unreleased]` contents to new version header: `## [{version}] - {date}`. Create empty `[Unreleased]` section above.

## USER_CHANGELOG.md (beta and release only)

For `beta` and `release` modes, check if `USER_CHANGELOG.md` exists:
- If NOT: create it with user-friendly transformation (emojis, "You can now..." language)
- If EXISTS: show preview to user, wait for confirmation before prepending new entry

**Transformation:** "Added dark mode" → "✨ **Dark Mode**: Switch to dark mode in Settings → Appearance"

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/05-changelog.md`:

```markdown
# Changelog Update

**CHANGELOG.md:** Updated (entry added to {section})
**USER_CHANGELOG.md:** {Updated / Created / Skipped / N/A}

## Entry Added
{The exact text that was added to CHANGELOG.md}
```
