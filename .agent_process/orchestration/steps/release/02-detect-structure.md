# Step 02: Detect Project Structure

**Model tier:** cheap
**Tools needed:** Bash
**Input:** none (reads filesystem)
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/02-structure.md`

---

## Your Task

Determine project type and version file locations.

```bash
ls -la package.json pyproject.toml setup.py VERSION 2>/dev/null
ls -la frontend/package.json backend/pyproject.toml 2>/dev/null
```

## Detection Rules

| Structure Found | Project Type | Version Files |
|-----------------|-------------|---------------|
| `pyproject.toml` only | Python library | `pyproject.toml` |
| `setup.py` only | Python legacy | `setup.py` |
| `package.json` only | TypeScript/Node | `package.json` |
| `frontend/package.json` | Full-stack | `frontend/package.json` + backend |
| `frontend/` + `backend/pyproject.toml` | TS + Python | Both |

**Changelog:** Always `CHANGELOG.md` at project root.

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/02-structure.md`:

```markdown
# Project Structure

**Type:** {project type}

## Version Files
- `{path/to/version/file}`

## Changelog
- `CHANGELOG.md`

## User-facing
{YES if frontend exists or library has end users, NO otherwise}
```
