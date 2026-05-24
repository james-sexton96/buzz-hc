# Naming Conventions

**Purpose:** Single source of truth for requirement IDs, file names, work directories, and categories.

---

## Core Principle

**One requirement = one ID = one work scope.**

- Each requirement has exactly one canonical ID
- Work directories use that ID (or a clearly mapped variant)
- No duplicate IDs across active requirements
- Superseded requirements get archived (not left as zombies)

---

## Requirement IDs

### Format

```
{category}_{descriptor}
```

**Examples:**
- `lexical_epic_06_save`
- `code_quality_scope_03_editor_ref`
- `ai_radar_scope_18_stability_rendering`
- `word_tools_scope_15_collection_actions`

### Rules

| Rule | Good | Bad |
|------|------|-----|
| Lowercase only | `lexical_save` | `Lexical_Save` |
| Underscores (no hyphens) | `word_tools` | `word-tools` |
| No redundant prefixes | `code_quality_scope_05` | `code_quality_code_quality_scope_05` |
| Concise but descriptive | `auth_system` | `the_new_authentication_system_v2` |
| No dates in ID | `save_navigation` | `2026_01_19_save_navigation` |

### Numbering (Optional)

Use `_epic_NN_` or `_scope_NN_` for sequenced work within a category:

```
lexical_epic_01_baseline
lexical_epic_02_stress_data
lexical_epic_03_rendering
```

Numbering helps with ordering but isn't required for standalone features.

---

## File Names

### Format

```
{requirement_id}.md
```

The filename **must match** the frontmatter `id:` field exactly (minus `.md` extension).

**Examples:**
- `lexical_epic_06_save.md` → `id: lexical_epic_06_save`
- `word_tools_scope_15.md` → `id: word_tools_scope_15`

### Location

Files go in `requirements_docs/` organized by category:

```
requirements_docs/
├── lexical_editor/
│   ├── lexical_epic_01_baseline.md
│   ├── lexical_epic_02_stress_data.md
│   └── lexical_save_state_navigation.md
├── code_quality/
│   ├── code_quality_scope_01_pre_commit.md
│   └── code_quality_scope_02_authform.md
├── ai_radar/
│   └── ...
└── standalone_feature.md  # No category subdirectory = uncategorized
```

---

## Categories

### Format

```
lowercase_with_underscores
```

### Standard Categories

| Category | Description |
|----------|-------------|
| `lexical_editor` | Rich text editor (Lexical.js) |
| `ai_radar` | AI feedback system |
| `word_tools` | Word collection, rhyme tools |
| `code_quality` | Linting, testing, CI/CD |
| `song_settings` | Song metadata, settings UI |
| `infrastructure` | Deployment, database, auth |

New categories can be created as needed. Keep them broad enough to group related work.

---

## Work Directories

### Format

Work directory names **must match** the requirement's frontmatter `id:` field. The orchestration planning step reads `id:` directly from frontmatter — it does not derive folder names from file paths.

```
work/
├── lexical_epic_06_save/
│   ├── iteration_01/
│   └── iteration_02/
├── code_quality_scope_03_editor_ref/
│   └── iteration_01/
```

### When Names Diverge

Legacy work directories (created before this convention) may not match requirement IDs. A common source of mismatch was the old path-based derivation, which prepended the category directory name to the filename, creating redundant prefixes like `lexical_editor_lexical_epic_06_save` instead of just `lexical_epic_06_save`.

For these cases, use `project_mappings` in `.roadmap_config.json`:

```json
{
  "project_mappings": {
    "work_to_requirement": {
      "ai_radar_based_feedback_system_scope_02_interactive_layer_19": "ai_radar_scope_19_tooltips"
    }
  }
}
```

**Goal:** Minimize mappings. New work should use matching names.

---

## Frontmatter

### Required Fields

```yaml
---
id: requirement_id_here
type: requirement
category: category_name
status: not_started | scoped | in_progress | blocked | complete | approved
priority: low | medium | high | critical
---
```

**Note:** The `type: requirement` field is mandatory. Discovery and sync will ignore files without it.

**Breakdown files** use `type: breakdown` — these are parent files that were split into multiple
smaller requirements. They preserve the original content for reference but are excluded from
roadmap discovery. See `orchestration/coordinators/plan-scope.md (coordinator) + orchestration/steps/planning/ (step files)` § "Large Requirements File Breakdown".

### Optional Fields

```yaml
---
id: lexical_save_state_navigation
type: requirement
category: lexical_editor
status: not_started
priority: high
complexity: simple | moderate | complex  # Triggers design review gate when "complex"
supersedes: lexical_epic_06_save  # If this replaces another requirement
---
```

**`complexity` field:**
- **Omitted** (default): treated as `moderate` — no design review gate
- **`simple`**: Straightforward scope, skip design review
- **`moderate`**: Standard scope, skip design review
- **`complex`**: Multi-system or architecturally significant — triggers the design review gate (if enabled in `quality-config.json`). 2-4 specialist reviewers assess the iteration plan before execution begins

---

## Superseding Requirements

When a new requirement replaces an old one:

1. **Archive the old requirement** using `/ap_project archive {old_id} superseded "Replaced by {new_id}"`
2. **Add `supersedes:` field** to new requirement's frontmatter
3. **Discovery ignores archived requirements** — no ambiguity

This maintains the "one ID = one active requirement" invariant.

---

## Quick Reference

| Element | Format | Example |
|---------|--------|---------|
| Requirement ID | `{category}_{descriptor}` | `lexical_epic_06_save` |
| File name | `{id}.md` | `lexical_epic_06_save.md` |
| Category | `lowercase_underscores` | `lexical_editor` |
| Work directory | Match requirement ID | `work/lexical_epic_06_save/` |
| Frontmatter ID | Must match filename | `id: lexical_epic_06_save` |

---

## Anti-Patterns

| Problem | Why It's Bad | Fix |
|---------|--------------|-----|
| Redundant prefix: `code_quality_code_quality_scope_05` | Confusing, breaks matching | `code_quality_scope_05` |
| Date in ID: `2026_01_19_feature` | IDs should be timeless | `feature` (date in frontmatter) |
| Hyphens: `word-tools` | Inconsistent with underscores | `word_tools` |
| Spaces: `My Feature` | Breaks shell scripts | `my_feature` |
| Multiple active requirements for same scope | Discovery ambiguity | Archive old, keep one active |
