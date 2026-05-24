# Roadmap Discovery Process

**Purpose:** Scan any `.agent_process` project to build a normalized roadmap from existing requirements and work directories.

**See also:** `naming_conventions.md` for ID formats, file naming rules, and category standards.

---

## Core Principle

**Only files with `type: requirement` in YAML frontmatter are treated as requirements.**

All other `.md` files in `requirements_docs/` (READMEs, planning docs, session logs, implementation guides, index files) are silently ignored. There is no heuristic-based fallback — the `type` field is the sole discriminator.

---

## Discovery Algorithm

### Phase 1: Requirements Discovery

**Scan:** `requirements_docs/` recursively for all `.md` files

**Use Python for reliable scanning** (shell globs and pipes break with complex paths):

```python
from pathlib import Path
import re

req_dir = Path(".agent_process/requirements_docs")
exclude = ["bugs/", "_TEMPLATE_", "artifacts/", "designs/"]

for md_file in req_dir.rglob("*.md"):
    if any(exc in str(md_file) for exc in exclude):
        continue
    # Process file...
```

**Strict filter:** Only process files with `type: requirement` in YAML frontmatter. All other files are skipped.

**Extract from each matching file:**

1. **Requirement ID** - From frontmatter `id:` field (required — skip file if missing)
2. **Display Name** - From filename or first `# heading`
3. **Priority** - From frontmatter `priority:` field (default: MEDIUM)
4. **Category** - From frontmatter `category:` field, OR from parent directory path
5. **Status** - From frontmatter `status:` field
6. **Metadata** - Date, Author (auto-populated from `git config user.name`), Timeline if present

**Frontmatter example (all required fields shown):**
```yaml
---
id: lexical_epic_06_save       # Explicit ID (matches work directory names)
type: requirement              # MANDATORY — files without this are skipped
category: lexical_editor       # Explicit category
status: not_started            # Current status
priority: HIGH                 # CRITICAL, HIGH, MEDIUM, LOW
---
# Requirements: Save Behavior
```

**Files without `type: requirement` in frontmatter are silently ignored.** This includes READMEs, planning docs, session logs, index files, breakdown parent files (`type: breakdown`), and any other non-requirement markdown. No path-based ID generation fallback exists.

To include a file in discovery, add the required frontmatter using `/ap_project import-requirement`.

**Additional exclusions (belt and suspenders):**
- Template files (`_TEMPLATE_*`) — excluded even though they contain `type: requirement` as template boilerplate
- Archived requirements (`archived: true` in frontmatter)

**Stats reporting:**
Discovery reports how many files were processed vs. skipped:
```
# Scanned: 45 requirements, 23 skipped (no type: requirement), 2 archived
```

### ID Generation Rules

**Full specification:** See `naming_conventions.md` for complete ID formatting rules.

**Requirement:** Use frontmatter `id:` field. There is no fallback.

The `id:` field gives explicit control over the requirement ID, making it easy to match work directories. Files with `type: requirement` but no `id:` field are skipped with a warning.

**Benefits of mandatory frontmatter IDs:**
- No fuzzy matching needed - IDs match work directories exactly
- No category prefix_mappings needed - category is explicit
- No priority regex parsing needed - priority is explicit
- Works with any directory structure (flat, nested, hierarchical)
- No false positives from READMEs, planning docs, or other markdown files

### Phase 2: Work Directory Discovery

**Scan:** `work/*/` for all directories

**Use Python for reliable iteration scanning** (shell `sort -V` and `while read` loops break):

```python
from pathlib import Path

work_dir = Path(".agent_process/work")
for scope_dir in work_dir.iterdir():
    if not scope_dir.is_dir():
        continue
    iterations = sorted([d for d in scope_dir.iterdir()
                        if d.is_dir() and d.name.startswith("iteration_")])
    # Process iterations...
```

**Extract from each directory:**
1. **Work Scope ID** - Directory name
2. **Parent Requirement** - Fuzzy match to requirements
3. **Status** - Parse latest `iteration_*/results.md`
4. **Iteration History** - Count iteration directories (major + sub-iterations)
   - Major iterations: `iteration_01`, `iteration_02`, `iteration_03` (criteria changes via PIVOT)
   - Sub-iterations: `iteration_01_a`, `iteration_01_b` (minor fixes via ITERATE)
   - Format: `{major}+{sub} ({latest})` e.g., `2+1 (02_a)` means 2 major + 1 sub, latest is iteration_02_a
5. **Last Activity** - Most recent results.md timestamp

**Status Detection Rules:**

Status markers are discovered during `/ap_project init` by scanning existing results.md files. The discovered patterns are stored in `.roadmap_config.json` under `status_markers`.

```python
def detect_status(work_dir, config):
    iterations = glob(f"{work_dir}/iteration_*")
    if not iterations:
        return "NOT_STARTED"

    latest = max(iterations, key=get_timestamp)
    results = f"{latest}/results.md"

    if not exists(results):
        return "IN_PROGRESS"

    content = read(results)
    markers = config.get("status_markers", {})

    # Check for APPROVED markers first (highest priority — reviewed and accepted)
    for marker in markers.get("approved", ["✅ APPROVED"]):
        if marker in content:
            return "APPROVED"

    # Check for COMPLETE markers (implementation done, awaiting review)
    for marker in markers.get("complete", ["✅ COMPLETE"]):
        if marker in content:
            return "COMPLETE"

    # Check for BLOCKED markers
    for marker in markers.get("blocked", ["BLOCKED"]):
        if marker in content:
            return "BLOCKED"

    # Check for explicit IN_PROGRESS markers (optional)
    # If no markers match, default to IN_PROGRESS anyway
    return "IN_PROGRESS"
```

**Common status marker patterns found in the wild:**

| Status | Common Patterns |
|--------|----------------|
| approved | `**Status:** APPROVED`, `✅ APPROVED` |
| complete | `**Status:** COMPLETE`, `**Status**: ✅ COMPLETED`, `✅ COMPLETE` |
| blocked | `BLOCKED`, `🚫 BLOCKED` |
| in_progress | `IN PROGRESS`, `WIP` (usually just the default) |

### Phase 3: Fuzzy Matching

**Problem:** Requirements and work directories often use different naming conventions.

**Common Patterns:**
- Requirements use hyphens, work uses underscores (or vice versa)
- Work directories add `_scope_XX_` between prefix and description
- Work directories may have different prefixes than requirements
- A single requirement may spawn multiple work scopes
- Epic/scope "explosion": One requirement spawns many work scopes as issues are discovered

**Matching Algorithm:**
```python
def match_work_to_requirement(work_name, requirement_ids):
    # Normalize both names
    normalized_work = normalize(work_name)  # underscores, lowercase

    # Direct match first
    for req_id in requirement_ids:
        if normalize(req_id) == normalized_work:
            return req_id

    # Remove common patterns and try again
    clean_work = remove_scope_pattern(normalized_work)  # removes _scope_XX_

    for req_id in requirement_ids:
        normalized_req = normalize(req_id)

        # BIDIRECTIONAL MATCHING - check both directions
        # Check if work contains requirement ID
        if normalized_req in normalized_work:
            return req_id

        # Check if requirement contains work prefix (handles _save, _followup suffixes)
        if normalized_work in normalized_req:
            return req_id

        # Check if cleaned work matches
        if clean_work.startswith(normalized_req):
            return req_id

        # Check common prefix (handles epic_XX vs epic_XX_suffix)
        if share_significant_prefix(clean_work, normalized_req):
            return req_id

    # Mark as orphan if no match
    return None

def normalize(name):
    return name.lower().replace("-", "_").replace(" ", "_")

def remove_scope_pattern(name):
    # Remove patterns like _scope_01_, _scope_02_, etc.
    import re
    return re.sub(r'_scope_\d+_', '_', name)

def share_significant_prefix(a, b):
    """Check if two names share a meaningful common prefix (e.g., 'epic_06')"""
    # Split on underscores and compare first N segments
    parts_a = a.split('_')
    parts_b = b.split('_')
    common = []
    for pa, pb in zip(parts_a, parts_b):
        if pa == pb:
            common.append(pa)
        else:
            break
    # Require at least 2 matching parts (e.g., "lexical_epic" or "epic_06")
    return len(common) >= 2
```

---

### Phase 3.5: LLM Critical Evaluation (REQUIRED)

**⚠️ CRITICAL: Do not blindly trust algorithmic matching. Think about what you're seeing.**

After running the fuzzy matching algorithm, Claude must critically evaluate the results before finalizing. The algorithm is a starting point, not the answer.

**Questions to Ask Yourself:**

1. **Do the orphan counts make sense?**
   - If there are many orphan work directories, something is probably wrong
   - Completed work that doesn't count toward any requirement is a red flag
   - Check: Could these orphans reasonably match a requirement?

2. **Are suspiciously many work dirs matched to the same requirement?**
   - Multiple scopes matched to one requirement is normal (epic explosion)
   - But 10+ unrelated scopes matched to one req is suspicious
   - Investigate: Are these truly related or a fuzzy matching false positive?

3. **Do the completion percentages seem plausible?**
   - If 5 work scopes show complete but the requirement shows 0%, matching failed
   - Cross-reference: Read a few orphan work results.md files and check their content

4. **Naming patterns to investigate manually:**
   - `requirement_name_save` vs `requirement_name` (suffix variations)
   - `category_scope_XX_name` work dirs that don't match `category_name` requirements
   - Work dirs named after the problem discovered, not the original requirement

**Investigation Protocol:**

When orphans are detected:

```
For each orphan work directory:
1. Read the latest results.md file
2. Look for clues about which requirement it relates to:
   - Does it mention a requirement name?
   - Does the work description match a requirement's scope?
   - Is there a clear parent-child relationship?
3. If a match is obvious, note it for project_mappings
4. If genuinely orphan (ad-hoc work), document it in the orphan summary
```

**Project Mappings:**

When the algorithm fails (common with hierarchical requirements), add explicit mappings to `.roadmap_config.json`:

```json
{
  "project_mappings": {
    "work_to_requirement": {
      "lexical_epic_06_scope_01_save_behavior": "lexical_epic_06_save",
      "ai_feedback_scope_03_cliche_rework": "ai_feedback_system_cliche_detection"
    }
  }
}
```

**Red Flags That Require Investigation:**

| Red Flag | What to Check |
|----------|---------------|
| Orphan work marked COMPLETE | Almost always a matching failure |
| 0% complete with many work dirs | Matching not linking work to requirements |
| Same requirement matched 10+ times | Overly aggressive fuzzy matching |
| Work dir name very different from all requirements | May need manual override or retroactive requirement |

**Remember:** The goal is an accurate roadmap. If the numbers don't look right, they probably aren't. Dig deeper before accepting the results.

### Phase 4: Aggregation

**Group work scopes by parent requirement:**

A requirement is considered:
- **NOT_STARTED**: No work directories found
- **IN_PROGRESS**: Has work directories, but not all complete
- **COMPLETE**: All associated work scopes are complete (awaiting review)
- **APPROVED**: All associated work scopes are approved (reviewed and accepted)
- **BLOCKED**: Any work scope is blocked

**Completion calculation:**
```
Requirement completion = (completed work scopes) / (total work scopes)
```

For requirements with no work scopes yet, show `0/?` to indicate unknown total.

---

## Structure Detection

The discovery process should detect and report the organizational pattern found:

| Pattern | Detection Logic | Example |
|---------|----------------|---------|
| `flat` | All requirements at root level | `requirements_docs/*.md` |
| `flat_numbered` | Root-level files with number prefixes | `epic_01_*.md`, `scope_02_*.md` |
| `categorized` | Requirements in subdirectories by category | `category_a/*.md`, `category_b/*.md` |
| `nested_numbered` | Subdirs with numbered scopes | `category/scopes/01_*.md` |
| `layered` | Subdirs organized by layers/phases | `layer_01/*.md`, `layer_02/*.md` |
| `mixed` | Multiple patterns in same project | (most real projects) |

---

## Orphan Detection

**Orphan Work:** Work directories with no matching requirement
- Flag for human review
- May indicate ad-hoc work done without formal requirements
- **If marked COMPLETE, almost always a matching failure** — investigate before accepting

**Orphan Requirements:** Requirements with no work directories
- Normal for NOT_STARTED requirements
- If expected to have work, may indicate naming mismatch

### Orphan Work Summary (in master_roadmap.md)

When orphan work directories are found, include a summary in `master_roadmap.md`:

```markdown
## Orphan Work Directories

| Work Directory | Status | Iterations | Likely Requirement | Action Needed |
|----------------|--------|------------|-------------------|---------------|
| epic_06_scope_01_save | COMPLETE | 2 (01→02) | lexical_epic_06_save | Add manual_override |
| random_bugfix_2025 | IN_PROGRESS | 1+1 (01_a) | (none - ad-hoc) | Document or create req |

**Orphan Summary:**
- Total orphan work dirs: X
- Completed orphans: Y (⚠️ investigate — likely matching failures)
- In-progress orphans: Z
```

**Why this matters:** Completed orphans represent work that's DONE but not reflected in roadmap completion stats. This distorts % Complete calculations and hides actual progress.

---

## Sub-Roadmap Migration

If the project has existing sub-roadmap files (README.md files that list scopes, index files, etc.):

1. **Extract metadata** from these files (phase groupings, dependencies, estimated timelines)
2. **Apply to discovered requirements** as category/phase information
3. **The master roadmap replaces these sub-roadmaps** as the single source of truth
4. **Keep sub-roadmap files** as documentation/context, but don't duplicate status tracking

---

## Implementation Notes

- **Cache results** in `.agent_process/roadmap/.discovery_cache.json` with timestamps
- **Incremental updates** - Only re-scan changed files/directories
- **Error handling** - Graceful failure for malformed files
- **Performance** - Limit to 1000 files, warn if exceeded

---

## File Format Support

**Requirements files must be markdown (`.md`) with:**
- YAML frontmatter containing `type: requirement` (mandatory)
- `id:` field in frontmatter (mandatory)
- First heading used as display name if no explicit title
- Any organizational structure (flat, nested, categorized)

**Work directories must follow pattern:**
- `work/{scope_name}/iteration_{NN}/results.md` for major iterations (01, 02, 03)
- `work/{scope_name}/iteration_{NN}_{x}/results.md` for sub-iterations (01_a, 01_b)
- Major iterations indicate criteria changes (via PIVOT)
- Sub-iterations indicate minor fixes (via ITERATE)
- Status markers in results.md content
- Directory name used for matching back to requirements

---

This process is designed to handle any `.agent_process` project structure without requiring specific naming conventions or folder names. The only hard requirement is `type: requirement` in YAML frontmatter.