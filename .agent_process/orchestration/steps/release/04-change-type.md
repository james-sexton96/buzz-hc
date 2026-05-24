# Step 04: Determine Change Type

**Model tier:** capable
**Tools needed:** Read
**Input:** context output (`<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/01-context.md`), mode
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/04-change-type.md`

---

## Your Task

Classify the changes and draft a changelog entry.

## Categories

| Category | When to Use | Example |
|----------|-------------|---------|
| **Added** | New feature or capability | "Dark mode toggle in settings" |
| **Changed** | Modified existing behavior | "Improved loading performance" |
| **Fixed** | Bug fix | "Session timeout now extends properly" |
| **Removed** | Removed feature | "Deprecated legacy export removed" |
| **Security** | Security fix | "Fixed XSS vulnerability in comments" |
| **Breaking Changes** | API/behavior breaking change | "Config format changed to YAML" |

## Draft Changelog Entry

Write user-facing summaries (1-2 sentences max per item):
- Focus on WHAT changed from user perspective
- Don't mention internal implementation details
- Reference issue/PR number if applicable

**Good:** "Added dark mode toggle in Settings → Appearance"
**Bad:** "Refactored ThemeProvider to use React context"

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/04-change-type.md`:

```markdown
# Change Classification

**Primary category:** Added / Changed / Fixed / Removed / Security
**User-facing:** YES / NO
**Breaking:** YES / NO

## Drafted Changelog Entry

### {Category}
- {user-facing description}
- {user-facing description}
```
