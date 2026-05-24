# Step 01: Config Check

**Model tier:** cheap
**Tools needed:** Read
**Input:** none (reads quality-config.json)
**Output:** `<project_root>/.agent_process/brainstorms/.run/01-config.md`

---

## Your Task

Read `.agent_process/quality-config.json` and check brainstorm-related config.

## Check

- `metaswarm.enabled` — master switch
- `metaswarm.features.brainstorm` — brainstorm feature flag
- `metaswarm.features.design_review` — whether design review is available

This command works without metaswarm — all features are built in.

## Output Format

```markdown
# Config

**Metaswarm:** enabled/disabled
**Brainstorm feature:** enabled/disabled
**Design review available:** YES/NO
```
