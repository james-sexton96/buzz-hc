# Metaswarm Integration

> **Type:** Reference (Diataxis)
> **Audience:** AP users and contributors

## What Is Metaswarm?

[Metaswarm](https://github.com/dsifry/metaswarm) is a separate agent framework that provides tactical capabilities AP leverages as optional enhancements:

- **Brainstorming** — structured ideation with multi-agent design review
- **Design Review** — 5-agent parallel review (Product, Architect, Designer, Security, CTO)
- **Knowledge Priming** — loads relevant context before work starts
- **PR Shepherd** — monitors PRs through CI and review cycles
- **Self-Reflect** — extracts learnings from PR feedback

AP wraps these features under the `/ap_*` command umbrella. Metaswarm is never required — every AP command works without it.

## Configuration

Metaswarm integration is controlled via `quality-config.json`:

```json
{
  "metaswarm": {
    "enabled": false,
    "_user_configured": true,
    "features": {
      "brainstorm": true,
      "design_review": true,
      "prime": true,
      "pr_shepherd": true,
      "self_reflect": true
    }
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Master switch for all metaswarm features |
| `_user_configured` | boolean | `false` | Set by install.sh — prevents re-prompting on reinstall |
| `features.brainstorm` | boolean | `true` | Enable brainstorm in `/ap_requirements` |
| `features.design_review` | boolean | `true` | Enable design review offers after brainstorm/import |
| `features.prime` | boolean | `true` | Enable knowledge priming in `/ap_exec` (Phase 2) |
| `features.pr_shepherd` | boolean | `true` | Enable PR shepherd in `/ap_release` (Phase 3) |
| `features.self_reflect` | boolean | `true` | Enable self-reflection after APPROVE (Phase 3) |

Individual feature flags allow granular control even when the master switch is on.

## Feature Mapping

| AP Command | Without Metaswarm | With Metaswarm |
|---|---|---|
| `/ap_brainstorm` | Built-in 3-agent brainstorm (Product, Arch, Critical) | Enhanced with metaswarm agents if available |
| `/ap_requirements add` | Direct creation only | Offers to route through `/ap_brainstorm` |
| `/ap_requirements import` | Standard import | Offers design review after import |
| `/ap_exec` | Pre-flight checks: session recovery, working tree, branch, git context (Step 0.7) | Same (metaswarm `/prime` inspired the design) |
| `/ap_release` | Works as-is | `/pr-shepherd` monitors PR (Phase 3) |
| Post-decision | Knowledge deposit (APPROVE: code learnings, BLOCK/PIVOT: process observations) | `/self-reflect` extracts learnings (Phase 3) |

**Key:** `/ap_brainstorm` always works — it uses built-in multi-agent brainstorming via the Agent tool. Metaswarm enhances it when available but is never required.

## Installation

### During AP Install

`install.sh` prompts for metaswarm during installation:

```
Enable Metaswarm integration? [y/N]
```

Choosing "y" sets `metaswarm.enabled: true` in quality-config.json and provides install instructions for the metaswarm plugin itself.

### Manual Enable/Disable

Edit `.agent_process/quality-config.json` directly:

```json
"metaswarm": { "enabled": true, "_user_configured": true }
```

### Installing Metaswarm

```bash
# Via Claude Code plugin marketplace
claude plugin marketplace add dsifry/metaswarm-marketplace
claude plugin install metaswarm

# Or follow instructions at https://github.com/dsifry/metaswarm
```

## Detection Logic

AP commands check metaswarm availability in this order:

1. Read `quality-config.json` → `metaswarm.enabled`
2. If enabled, check for installed commands:
   - `~/.claude/commands/brainstorm.md` (global install)
   - `.claude/commands/brainstorm.md` (project install)
3. Three possible states:
   - **Available** — enabled + installed → offer metaswarm features
   - **Install needed** — enabled but not installed → warn once, continue without
   - **Disabled** — not enabled → don't mention metaswarm at all

## How Brainstorming Works

`/ap_brainstorm` uses the Agent tool to spawn 3 parallel brainstorm subagents (Product Strategist, Software Architect, Devil's Advocate). This is the same pattern used by adversarial review in `ap_exec` Step 4.5 — no nested slash commands needed.

The agents return structured analyses, which `/ap_brainstorm` synthesizes into a brainstorm document, then transforms into a formal AP requirement.

When metaswarm is installed, `/ap_brainstorm` can optionally use metaswarm's agent definitions for enhanced brainstorming. Without metaswarm, the built-in agents work just fine.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `/ap_brainstorm` output seems thin | Metaswarm agents not available, using built-in | Install metaswarm for enhanced brainstorming, or the built-in approach is fine |
| Metaswarm enabled but "not detected" | Plugin installed in wrong location | Check `~/.claude/commands/brainstorm.md` exists |
| Brainstorm output not found | Design doc written to unexpected path | Check `docs/plans/` for recent `.md` files |
| Design review not offered | `features.design_review` set to `false` | Check quality-config.json feature flags |
