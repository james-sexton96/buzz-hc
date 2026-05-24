# Removal Scope Checklist

**When this applies:** any scope where the answer to "does this scope remove
or rename a public surface?" is yes. A "public surface" is anything an
external caller, operator, agent, or downstream doc treats as live:

- HTTP routes (added, removed, or moved — `POST /api/foo`, `GET /api/x/{id}`)
- MCP tool names (`list_metric_dimensions`, `query_metric`)
- CLI subcommands, env-var names, config keys, feature flags
- Exported function/class/module names that other repos import
- Container/queue/topic names, BigQuery dataset/table names

If a scope only adds or modifies private internals, this checklist does not
apply. If you are unsure, populate the checklist anyway — the cost of
listing a surface that turns out to be internal is low; the cost of missing
a removed public surface is what produced this document.

---

## Why this checklist exists

The framework's scoped-validation pattern works well for additive changes:
list the files you change, validate them, ship. For removals it has a
known failure mode — the validator only inspects the files in scope, but
the *callers* of the removed surface live outside scope by definition.
Stale references to the removed surface get laundered through the "known
issues, out of scope" channel and survive into the next iteration.

The lesson is documented in the user's global `CLAUDE.md` under
**"System Migration and Refactoring Lessons"** (Iterations 3-4 of the
harmonic-analysis redesign), with a "Comprehensive Migration Checklist."
This file is the framework-level encoding of that lesson — what the
planner, executor, and reviewer must do so the lesson does not have to be
re-learned per scope.

---

## Planner responsibilities (during `04-plan.md`)

For each removed/renamed surface, populate a **Removed Surfaces** section
in `iteration_plan.md` with one entry per surface:

```markdown
## Removed Surfaces

The following public surfaces are removed or renamed in this scope.
After implementation, no live operator/agent/doc reference to these
surfaces may remain outside the explicit whitelist below.

### `POST /api/metrics/query`
- **Replaced by:** `POST /api/metrics/{metric_name}/query`
- **Grep pattern:** `/api/metrics/query`
- **Whitelist (allowed references):**
  - `CHANGELOG.md` — historical record
  - `docs/reference/api-metrics.md:24,330` — explicitly notes "is gone"
  - `routers/metrics.py:23,69,359` — comments explaining the removal
  - `tests/dashboard_api/test_metrics.py:882-887` — guardrail test
    asserting absence
- **Acceptance:** workspace grep returns only whitelisted hits.

### `list_metric_dimensions` (MCP tool)
- **Replaced by:** `describe_metric` (subsumes dimensions)
- **Grep pattern:** `list_metric_dimensions`
- **Whitelist:**
  - `*/CHANGELOG.md`
  - `dbt_cloud_client.py`, `metricflow_engine.py` — internal helper
    method with the same name (name collision; not the MCP tool)
  - `ai-lab/CLAUDE.md`, `core/mcp/tools/metrics.py` docstrings —
    explicitly note "subsumes the legacy"
  - `tests/core/mcp/tools/test_metrics.py` — guardrail asserting absence
- **Acceptance:** workspace grep returns only whitelisted hits.
```

**Rules for the whitelist:**

1. Prefer **paths and reasons**, not blanket "all docs" patterns.
2. Comments and docstrings that say *"is removed" / "is gone" / "subsumes the legacy"* are OK — they are the migration note, not a stale reference.
3. Internal name collisions (the dbt-cloud client's `list_metric_dimensions` helper vs. the removed MCP tool) must be called out explicitly with a justification, not silently included.
4. README files and operator scripts are **not** automatically whitelisted. If they reference the removed surface as if live, they must be updated by this scope.

---

## Validator responsibilities (during `04-plan.md`)

When `Removed Surfaces` is non-empty, the generated
`validate-{scope}.sh` script must include a **stale-surface scrub** block
after the existing ruff/pytest checks. Pseudo-shape:

```bash
printf "[%s-validation] Stale-surface scrub...\n" "$SCOPE"
SURFACE_VIOLATIONS=0
for SURFACE in <surface-keys>; do
  PATTERN="$(<grep pattern for $SURFACE>)"
  WHITELIST_FILE="$ROOT_DIR/.agent_process/work/$SCOPE/.removal-whitelist/$SURFACE.txt"
  HITS="$(grep -rEn "$PATTERN" \
    --include='*.md' --include='*.sh' --include='*.py' \
    --include='*.ts' --include='*.tsx' --include='*.yml' --include='*.yaml' \
    --exclude-dir=.agent_process --exclude-dir=.git --exclude-dir=node_modules \
    "$ROOT_DIR" 2>/dev/null || true)"
  # Filter out whitelisted file:line entries.
  UNEXPECTED="$(echo "$HITS" | grep -vFf "$WHITELIST_FILE" || true)"
  if [[ -n "$UNEXPECTED" ]]; then
    printf "[%s-validation] STALE REFERENCES TO %s:\n%s\n" "$SCOPE" "$SURFACE" "$UNEXPECTED" >&2
    SURFACE_VIOLATIONS=$((SURFACE_VIOLATIONS+1))
  fi
done
[[ "$SURFACE_VIOLATIONS" -eq 0 ]] || exit 1
```

The whitelist file format is one `path:line-range` per line, exactly as
grep emits. The planner generates the initial whitelist from the
iteration plan's whitelist section. The executor extends it (with
justification in `results.md`) when an additional reference is genuinely
historical and should remain.

The scrub deliberately **excludes `.agent_process/`** because that
directory is intentionally a historical record of every prior iteration's
language; it would always trip on its own work artifacts. The cost is
that prior-iteration historical references in `.agent_process/` cannot
themselves be a tripwire — that is acceptable; the planning/review
artifacts are not consumed by clients.

---

## Executor responsibilities (during `02-prepare.md` / implementation)

Surface the Removed Surfaces section to the implementer in the prepare
doc, with the explicit instruction:

> Before declaring this iteration complete, run the stale-surface scrub
> locally (the validator will run it too). If the scrub flags a reference
> outside the whitelist, the implementer must either (a) update that
> reference to remove or replace the removed surface, or (b) extend the
> whitelist with a justification in `results.md` for the reviewer to
> assess. Pasting an entry into the whitelist without a justification is
> not acceptable.

The implementer's report in `results.md` must include a section:

```markdown
## Removed-Surface Scrub

| Surface | Hits Found | Hits Resolved | Hits Whitelisted (with justification) |
|---------|-----------:|--------------:|---------------------------------------:|
| `POST /api/metrics/query` | 7 | 4 | 3 |
| `list_metric_dimensions` (MCP) | 12 | 3 | 9 |

See `.agent_process/work/{scope}/.removal-whitelist/` for the per-surface
whitelist files and inline justifications.
```

---

## Reviewer responsibilities (during `02-gates.md`)

When `Removed Surfaces` is non-empty in `iteration_plan.md`, **Gate 1
(Documentation)** is no longer a yes/no on "Orphaned references to
removed code?" The reviewer must:

1. Read the `Removed-Surface Scrub` section of `results.md`.
2. Spot-check at least one surface by running the validator's scrub block
   manually.
3. Inspect each whitelist addition against its justification.
4. **FAIL Gate 1** if any of the following are true:
   - The scrub section is missing.
   - A whitelist entry has no justification, or the justification is
     "out of scope" / "deferred to follow-up scope" — those are valid
     reasons to defer entire AC, not to whitelist a specific reference
     while claiming the AC is met.
   - An operator-facing surface (smoke scripts, README, runbooks) is
     whitelisted as historical when it is in fact still serving as
     live operator guidance.

When `Removed Surfaces` is empty (additive scope), Gate 1 falls back to
its existing yes/no check.

---

## Anti-patterns this prevents

- **"Stale references; not in scope" punt.** Without this checklist,
  an executor can correctly apply the "stay in scope" rule, list stale
  references in `results.md` known-issues, and ship a half-removed
  surface. The reviewer accepts the punt because no AC explicitly
  blocks it. The next iteration's prepare doc inherits the gap. By the
  time a human notices, two iterations have shipped with broken
  operator scripts and misleading READMEs.

- **Generic AC7 ("Documentation captures...") marked MET on the basis
  of the *named* doc files.** Without an explicit Removed Surfaces
  contract, the AC can be satisfied by updating the docs in the plan
  while leaving the docs that aren't in the plan referring to the
  removed surface as if live. This checklist forces the question
  "documentation captures... and what about *every* doc that mentions
  the surface?"

- **Validator scope == file list.** The existing scoped-validator
  pattern is right for additive changes but cannot, on its own, catch
  references that live in files outside the plan. The stale-surface
  scrub is the minimal extension that handles this without abandoning
  the file-scoped pattern (which is still what runs ruff/pytest).

- **Append-instead-of-update on canonical records.** A scope renames
  or replaces a surface, then *appends* a "Phase X Implementation
  Index" or a "see new section below" pointer to the canonical record
  (catalog entry, README owner table, decision log, registry doc) —
  while leaving the original entry intact and describing the old
  state. Result: two sources of truth for the same fact — one
  current, one stale — and the stale one is the one a reader hits
  first. The fix is not "add an index"; it is "update the entry in
  place." The stale-surface scrub catches body-text references like
  `mace_metrics.yml`, but it cannot catch a structured catalog entry
  whose *fields* still describe the old reality. Planner
  responsibility: when the iteration plan's documentation-in-scope
  list includes a canonical record (catalog, owner table, decision
  log), the entries describing the renamed/replaced surface are
  updated in place, not supplemented with a forward-pointer index.

---

## When this checklist is overkill

For a scope that removes a single internal function used in two places
within the same module, this checklist is overkill — the existing
file-scoped validator already covers it. A useful heuristic: if the
removed identifier appears in any of `README*`, `docs/`, `scripts/`,
`*.md` files outside the implementation module, populate the checklist.
Otherwise skip.

The planner makes this call during `04-plan.md` and records the
decision (one line in `iteration_plan.md` is fine: *"Removed Surfaces:
N/A — internal removal only, no public surface affected."*).
