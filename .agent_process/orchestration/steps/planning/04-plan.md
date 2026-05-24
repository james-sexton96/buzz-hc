# Step 04: Create Plan

**Input:** All `<project_root>/.agent_process/work/{scope}/.run/planning/` outputs, requirement file
**Output:** `.agent_process/work/{scope}/iteration_plan.md`

---

## 1. Document Pre-existing Issues

Run validation commands and identify failures OUTSIDE this scope:

```bash
npm run typecheck 2>&1 | tail -5
npm run lint 2>&1 | tail -5
ruff check . 2>&1 | tail -5
```

For each failure: is it in a scope file? If not, it's pre-existing debt.

Document:
- **SKIP:** Commands that fail on pre-existing issues
- **RUN:** Commands that must pass for this scope

---

## 2. Identify Removed Surfaces

**Before writing the validation script, ask:** does this scope remove or
rename any public surface — HTTP route, MCP tool, CLI command, env var,
config key, exported function used by another repo, etc.?

- **If no:** record `Removed Surfaces: N/A — no public surfaces removed or renamed.` in the iteration plan and proceed to step 3.
- **If yes:** populate the iteration plan's **Removed Surfaces** section per `.agent_process/process/removal-scope-checklist.md`. For each surface, list the grep pattern and the initial whitelist (paths + reason — historical, guardrail, name-collision, etc.). Generate the per-surface whitelist files at `.agent_process/work/{scope}/.removal-whitelist/{surface}.txt` (one `path:line-range` per line).

Heuristic for the call: if the removed identifier appears in any of
`README*`, `docs/`, `scripts/`, or `*.md` files outside the implementation
module, populate the section. Otherwise skip.

---

## 3. Create Validation Script

Write to `.agent_process/scripts/after_edit/validate-{scope}.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCOPE="$1"
ITERATION="$2"

# Scope-specific validation
{commands from RUN list}

# Stale-surface scrub — INCLUDE THIS BLOCK ONLY IF "Removed Surfaces" is
# non-empty in the iteration plan. See process/removal-scope-checklist.md
# for the full template. Removed scopes without it cannot satisfy Gate 1
# during review.
#
# printf "[%s-validation] Stale-surface scrub...\n" "$SCOPE"
# SURFACE_VIOLATIONS=0
# for SURFACE in <surface-keys>; do
#   ...grep workspace, filter against per-surface whitelist...
# done
# [[ "$SURFACE_VIOLATIONS" -eq 0 ]] || exit 1

echo "✅ Scoped validation passed"
```

Make executable: `chmod +x`

### Bash 3.2 Portability (REQUIRED)

The validator script MUST run under macOS default `/bin/bash` (version
3.2.57), not just modern bash 4+/5. The shebang `#!/usr/bin/env bash`
resolves to whatever `bash` is first on PATH, which on macOS is
`/bin/bash` = 3.2 unless the operator has Homebrew bash earlier on
PATH. Validators that use bash-4-only features fail silently or with
opaque errors on a clean macOS checkout — and "the recorded validator
pass is not reproducible" is a Gate 4 (Scoped Validation) FAIL.

**Forbidden bash-4+ features** (each has bitten this framework before):

| Forbidden | Use instead |
|---|---|
| `declare -A NAME=(...)` (associative array) | `case "$KEY" in foo) echo bar;; ...; esac` (function returning value), OR parallel arrays + index loop |
| `${var^^}`, `${var,,}` (case conversion) | `echo "$var" \| tr '[:lower:]' '[:upper:]'` |
| `&>>` redirect (combined stdout+stderr append) | `>> file 2>&1` |
| `mapfile` / `readarray` builtin | `while IFS= read -r line; do ...; done < <(cmd)` |
| `[[ -v VAR ]]` (variable existence check) | `[[ -n "${VAR-}" ]]` (also works under `set -u`) |

**Pattern for surface→pattern lookups (recurring need in the
stale-surface scrub):**

```bash
# DO THIS (bash 3.2 compatible):
surface_pattern() {
  case "$1" in
    route_api_metadata_entities) printf '%s' '/api/metadata/entities' ;;
    legacy_metric_names) printf '%s' '(prevail_subject_count|...)' ;;
    *) printf '[%s-validation] unknown surface: %s\n' "$SCOPE" "$1" >&2; return 1 ;;
  esac
}

for SURFACE in route_api_metadata_entities legacy_metric_names; do
  PATTERN="$(surface_pattern "$SURFACE")"
  # ...grep workspace, filter against per-surface whitelist...
done

# DON'T DO THIS (bash 4+ only — fails on macOS /bin/bash 3.2):
declare -A PATTERNS=(
  [route_api_metadata_entities]='/api/metadata/entities'
  [legacy_metric_names]='(prevail_subject_count|...)'
)
for SURFACE in "${!PATTERNS[@]}"; do
  PATTERN="${PATTERNS[$SURFACE]}"
  ...
done
```

The `case`-statement function gives the same name→pattern lookup, the
same `set -u` safety against typos (the `*)` arm errors loudly), and
runs unmodified from bash 3.2 through bash 5+. The associative-array
form is shorter but has produced an unreproducible-validator
Gate 4 FAIL three times across two scopes — do not reach for it.

**Smoke-test before handoff.** When the validator is generated, sanity-
check it under the documented shell:

```bash
bash --version  # confirm 3.2.x if running on macOS default
bash -n .agent_process/scripts/after_edit/validate-{scope}.sh  # syntax check
```

A failed `bash -n` under 3.2 is a planning-step bug, not an executor
problem. Fix the validator template before handoff.

---

## 4. Design Review Gate (if complex)

If requirement has `complexity: complex`:
- Trigger design review
- Document architectural decisions
- Get approval before proceeding

If simple/moderate: skip this gate.

---

## 5. Write Iteration Plan

Synthesize ALL `<project_root>/.agent_process/work/{scope}/.run/planning/` outputs into the final plan.

Use template structure from `.agent_process/templates/iteration-plan.md`.

**Required sections:**
1. Scope Overview
2. Current Status (`iteration_01 - not started`)
3. Acceptance Criteria (LOCKED) — copy verbatim from define step
4. Technical Assessment — include Design Decisions table
5. Known Patterns & Constraints
6. Files in Scope
7. Documentation in Scope
8. **Removed Surfaces** — populated per step 2 above (default `N/A` for additive scopes)
9. Validation Requirements (SKIP vs RUN)
10. Out of Scope
11. Time Budget (2-4 hours/iteration)

---

## 6. Finalize

Create infrastructure:

```bash
mkdir -p .agent_process/work/{scope}/iteration_01
```

Write placeholder results:
```markdown
# Iteration Results — {scope}/iteration_01
**Status:** TODO - Awaiting execution
Run: /ap_exec {scope} iteration_01
```

Update requirement status to `scoped`.

Update roadmap if exists.

---

## Output

The iteration plan at `.agent_process/work/{scope}/iteration_plan.md`.

Report to coordinator:

```markdown
# Planning Complete

**Scope:** {scope}
**Plan:** `.agent_process/work/{scope}/iteration_plan.md`

## Summary
- Files: {N}
- Criteria: {N}
- Pre-existing issues: {N} documented (will SKIP)
- Design review: {Triggered / Not needed}

## Handoff
Ready for execution: `/ap_exec {scope} iteration_01`
```
