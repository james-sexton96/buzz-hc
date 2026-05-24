# Step 03: Get Current Version

**Model tier:** cheap
**Tools needed:** Read, Bash
**Input:** structure output (`<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/02-structure.md`), mode, version type
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/03-version.md`

---

## Your Task

Read current version from the detected version files and calculate the next version.

## Read Current Version

```bash
# pyproject.toml
grep -E '^version\s*=' pyproject.toml 2>/dev/null

# package.json
grep '"version"' package.json 2>/dev/null | head -1

# setup.py
grep -E "version\s*=" setup.py 2>/dev/null
```

## Calculate Next Version

| Current | Mode | Next |
|---------|------|------|
| 1.2.3 | `release patch` | 1.2.4 |
| 1.2.3 | `release minor` | 1.3.0 |
| 1.2.3 | `release major` | 2.0.0 |
| 1.2.3 | `beta` | v1.2.4-beta.{N} |
| 1.2.3 | `pr` | (no version change) |

For beta, check existing beta tags:
```bash
git tag -l "v*-beta.*" | sort -V | tail -1
```

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/03-version.md`:

```markdown
# Version

**Current:** {X.Y.Z}
**Mode:** {pr/beta/release}
**Next version:** {calculated or "no change"}
**Beta number:** {N, if beta mode}
```
