# Iteration Plan – {{scope_name}}

## Scope Overview
- **Scope Name:** {{scope_name}}
- **Date:** {{date}}
- **Summary:** [One sentence describing what this scope achieves]

## Requirements Source
- **Path:** `.agent_process/requirements_docs/{{requirements_path}}`
- **Document:** `{{requirements_filename}}`

*Work folder name derived from requirements path per naming convention.*

## Current Status
- Latest iteration: iteration_01 (not started)
- Decision: N/A
- Next: Run `/ap_exec {{scope_name}} iteration_01`

## Acceptance Criteria (LOCKED - DO NOT MODIFY)
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]

**CRITICAL:** These criteria are FROZEN at iteration start.
New issues discovered during iteration → backlog for future scopes.

**Scope boundaries are guidance, not walls.** If meeting the acceptance criteria
correctly requires touching files outside this list, the executor may do so with:
- Documentation of what was added and why
- Validation script updated to cover new files
- Justification in results.md for reviewer assessment

## Known Patterns & Constraints

*Populated from knowledge base (`.agent_process/knowledge/`) — see `process/knowledge-base.md` for query instructions. Use `/prime` when metaswarm is available.*

**From knowledge base:**
- [List relevant entries as: **[type]** fact (confidence: X, source: provenance reference)]
- [Include provenance reference for traceability]

**No matches found for:** [list keywords that returned nothing]

*If knowledge base is empty or no relevant entries found, note: "No relevant knowledge base entries for this scope."*

## Design Review

*Populated by Step 8.5 of the planning instructions when `complexity: complex` is set and design review is enabled in `quality-config.json`.*

N/A — scope complexity is not `complex` (or design review gate disabled)

<!-- When design review runs, replace the above with:
**Gate triggered:** Yes (complexity: complex)
**Reviewers:** [list specialist domains]
**Revision cycles:** [0-2]
**Outcome:** APPROVED | ESCALATED TO HUMAN

### Reviewer Verdicts
- **[Domain]:** APPROVE/REQUEST_CHANGES — [one-line summary]
-->

## Technical Assessment (by Orchestrator)

**Code Review Findings:**
[Summary of current code state - what exists today, what patterns are used]

**Implementation Approach:**
[Recommended technical approach for implementation session]

**Known Risks:**
[Identified risks and mitigation strategies]

**Implementation Guidance:**
[Specific guidance: patterns to follow, pitfalls to avoid, best practices to apply]

**Design Decisions (made by orchestrator, not human prereqs):**

This is the home for choices the orchestrator made during planning that did NOT need to go to the human (failed the human-prereqs filter — see `orchestration/coordinators/plan-scope.md`). The reviewer reads this section and may flag any choice they disagree with at review time; the human is not paused for these.

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| [Decision summary, in user-outcome terms] | [Chosen approach] | [Rejected alternative(s)] | [Reason — must include user/operator-visible consequence] |

*If empty:* "No design decisions beyond Implementation Approach above; nothing fell into the orchestrator-decides bucket."

## Iteration Budget (ENFORCED)
- iteration_01: First attempt
- iteration_01_a: First revision (if needed)
- iteration_01_b: Second revision (if needed)
- iteration_01_c: Final attempt (if needed)

After iteration_01_c → Escalate to human for decision (ship/pivot/abort)

## Files in Scope (Expected)

These are the files expected to change. The executor may touch additional files
if necessary for correctness — see "Scope boundaries" note above.

- `path/to/file1.tsx`
- `path/to/file2.ts`
- `path/to/test1.test.tsx`

**Total:** {{count}} files (if >10, consider splitting scope)

## Documentation in Scope

**End User Documentation:**
- [List docs that need updates for application users]
- Example: `docs/how-to/using-feature-x.md` (workflow changes)
- Example: `docs/tutorials/getting-started.md` (if affects onboarding)
- Or: *None - no user-facing behavior changes*

**Developer Documentation:**
- [List docs that need updates for code users/contributors]
- Example: `docs/reference/api/endpoints.md` (API changes)
- Example: `docs/explanation/architecture/data-flow.md` (architectural decision)
- Example: `README.md` (if affects installation/setup)
- Example: `CONTRIBUTING.md` (if affects contribution workflow)
- Or: *None - internal implementation only*

**Documentation Requirements (from CLAUDE.md):**
- [ ] End user documentation updated (or N/A - explain why)
- [ ] Developer documentation updated (or N/A - explain why)
- [ ] Documentation follows Diátaxis framework organization
- [ ] Cross-references to changed code updated
- [ ] Migration guide created (if replacing systems)

**Reference:** See `process/documentation-checklist.md` for guidance

## Removed Surfaces

*Populated when this scope removes or renames a public surface. See
`process/removal-scope-checklist.md` for what counts as a public surface
and how to fill out this section.*

**Default for additive scopes:** *N/A — no public surfaces removed or renamed.*

<!-- When the scope removes a public surface, replace the default with one
entry per surface, following this shape:

### `<surface identifier>` (e.g. `POST /api/metrics/query`, `list_metric_dimensions` (MCP tool))
- **Replaced by:** `<replacement, or "no replacement — surface deleted">`
- **Grep pattern:** `<regex the validator scrub will use>`
- **Whitelist (allowed references after this scope completes):**
  - `path/to/file:line-range` — *reason this reference is allowed (historical record, guardrail test, internal name collision, explicit "is removed" note, etc.)*
- **Acceptance:** workspace grep returns only whitelisted hits.

When this section is non-empty, the validation script generated below
MUST include the stale-surface scrub block from
`process/removal-scope-checklist.md`. The review's Gate 1 inspects this
section explicitly. -->

## Validation Requirements (SCOPED)

**Hook validation (after_edit):**
- Script: `.agent_process/scripts/after_edit/validate-{{scope_name}}.sh`
- Lints only files in scope
- Tests only scope-specific patterns
- Provides immediate feedback (not enforcement)
- **If `Removed Surfaces` above is non-empty:** the script also runs the
  stale-surface scrub. See `process/removal-scope-checklist.md`.

**Important:** If scope expands during iterations (new files needed for fixes), the orchestrator must update the validation script to include new files.

**Pre-existing issues (documented, out of scope):**
- [List any pre-existing failures that will NOT block this scope]
- Example: "89 TypeScript errors in non-lexical files (documented YYYY-MM-DD)"

**Validation approach:**
- Scoped validation via hook (fast feedback)
- Document results in test-output.txt
- Orchestrator review is the quality gate (not automated enforcement)

## Scope Changes

Track any files added to scope during iterations:
- **iteration_01:** Initial scope (see Files in Scope section)
- *(Orchestrator adds entries here if scope expands during ITERATE decisions)*

## Out of Scope
- [Explicit list of what's NOT included in this scope]
- Example: "Plugin lifecycle refactoring (separate scope)"

## Technical Notes
- [Any technical constraints, patterns, or references]
- Example: "Follow docs/technology/lexical-best-practices.md"

## Time Budget
- Target: 2-4 hours implementation per iteration
- Maximum: 1-2 weeks total (3 iterations max)
- After time exceeded: Escalate to human

## Success Metrics
- All acceptance criteria checked
- Scoped validation passes
- No regressions in scope files
- Tests demonstrate new functionality
