# Knowledge Base

**Type:** How-To Guide (Diátaxis)
**Purpose:** Query, deposit, and curate project knowledge across iterations

---

## Overview

The knowledge base is a set of JSONL files that accumulate project wisdom over time. Each APPROVE deposits 0-3 code learnings; each BLOCK or PIVOT may deposit 0-2 process observations; each planning phase queries for relevant entries. The system starts empty and gets smarter with every scope — even blocked ones.

### Storage Location

Knowledge lives in **`.agent_process/knowledge/`** — the single canonical location for all project knowledge. This directory is shared with metaswarm's `/prime` command when available.

```bash
KB_DIR=".agent_process/knowledge"
```

---

## Knowledge Files

| File | What goes here | Example |
|------|---------------|---------|
| `patterns.jsonl` | Recommended approaches that worked | "Auth uses middleware pattern, not decorators" |
| `gotchas.jsonl` | Things that bit us, non-obvious pitfalls | "Session tokens in localStorage breaks compliance" |
| `decisions.jsonl` | Architectural choices with rationale | "Chose JWT refresh over sliding window (latency)" |
| `anti-patterns.jsonl` | Approaches that failed or should be avoided | "Don't cache decoded tokens — invalidation nightmare" |
| `codebase-facts.jsonl` | Facts about how code works | "Thread model stores drafts only, not threads" |
| `api-behaviors.jsonl` | External API quirks and behaviors | "API returns 429 after ~100 req/min" |

All six files use the same schema. The last two (`codebase-facts`, `api-behaviors`) are metaswarm-compatible extensions — use them when the distinction is helpful.

---

## Entry Schema

All entries use the metaswarm-compatible schema, ensuring knowledge is shared between AP orchestration and metaswarm.

```json
{
  "id": "unique_snake_case_id",
  "type": "pattern|gotcha|decision|anti_pattern|api_behavior|code_quirk|performance|security",
  "fact": "Clear description of the knowledge",
  "recommendation": "What to do about it",
  "confidence": "high|medium|low",
  "provenance": [
    {
      "source": "agent|human|documentation|test|production",
      "reference": "scope_name/iteration_XX",
      "date": "YYYY-MM-DD"
    }
  ],
  "tags": ["auth", "middleware"],
  "affectedFiles": ["src/middleware/auth.ts"],
  "createdAt": "YYYY-MM-DDTHH:MM:SSZ",
  "updatedAt": "YYYY-MM-DDTHH:MM:SSZ"
}
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique snake_case identifier within the file |
| `type` | Yes | Knowledge category (must match the file it's in) |
| `fact` | Yes | Clear description — scannable in under 5 seconds |
| `recommendation` | Yes | Actionable guidance — what to do with this knowledge |
| `confidence` | Recommended | `high` (verified multiple times), `medium` (observed once), `low` (suspected) |
| `provenance` | Yes | Source chain: who discovered it, where, when |
| `tags` | Recommended | Search keywords for filtered queries |
| `affectedFiles` | Recommended | Glob patterns for files this applies to |

**Rules:**
- `id` must be unique within its file
- `fact` should be scannable in under 5 seconds
- `recommendation` should be actionable — "Use X because Y", not just "X exists"
- Entries are append-only in normal operation

---

## How to Query (Planning Phase)

The orchestrator queries the knowledge base before creating `iteration_plan.md`.

### grep (primary query method)

```bash
KB_DIR=".agent_process/knowledge"

# Search by keyword across all files
grep -i "auth\|session\|jwt" "$KB_DIR"/*.jsonl

# Search by affected files
grep -i "middleware\|auth.ts" "$KB_DIR"/*.jsonl
```

**Note:** Metaswarm's `/metaswarm:prime` skill can also query knowledge with keyword/file filtering when available, but grep is the universal method that always works.

### Include Findings in Plan

Add matches to `## Known Patterns & Constraints`:

```markdown
## Known Patterns & Constraints

**From knowledge base:**
- **[pattern]** Auth uses middleware pattern, not route decorators (confidence: high)
- **[gotcha]** Session tokens must not use localStorage — compliance requirement
- **[decision]** JWT refresh tokens over sliding window (latency trade-off)
- **[anti_pattern]** Don't cache decoded tokens — invalidation creates subtle bugs

**No matches found for:** [list keywords that returned nothing]
```

If no entries exist (common early on), note it — the knowledge base grows with each APPROVE (code learnings), BLOCK/PIVOT (process observations), ITERATE (conditional process observations), and ad-hoc deposits.

---

## How to Deposit (Review Phase)

The knowledge base accepts deposits at several decision points:

| Decision | What to deposit | Why it's safe |
|----------|----------------|---------------|
| **APPROVE** | Code patterns, gotchas, decisions, anti-patterns (0-3 entries) | Code is verified — learnings are grounded in working implementation |
| **BLOCK/PIVOT** | Process observations only (0-2 entries) | Process patterns don't depend on code correctness |
| **ITERATE** | Process observations only (0-2 entries, conditional) | Only when the reviewer spots a generalizable lesson about process, scope structure, or agent behavior — not code patterns |
| **Ad-hoc** | Any type (user-initiated, requires consent) | Human judgment gates the deposit — user decides what's worth preserving |

### Code Knowledge Deposit (APPROVE)

After an APPROVE decision, the orchestrator extracts 0-3 learnings.

### Step 1: Find the Knowledge Directory

```bash
KB_DIR=".agent_process/knowledge"
```

### Step 2: Reflect on the Iteration

Ask these questions about the completed work:
1. Did we discover a pattern worth reusing? → `patterns.jsonl`
2. Did something non-obvious bite us? → `gotchas.jsonl`
3. Did we make an architectural choice with trade-offs? → `decisions.jsonl`
4. Did we try something that failed? → `anti-patterns.jsonl`

### Step 3: Write Entries

**Good entry (specific, reusable, metaswarm-compatible):**
```json
{"id": "auth_middleware_pattern", "type": "pattern", "fact": "Auth checks use Express middleware, not route-level decorators", "recommendation": "Apply auth middleware in app.ts before route registration. Don't use decorators — they cause route ordering issues in Express 5.", "confidence": "high", "provenance": [{"source": "agent", "reference": "auth_scope_01/iteration_02", "date": "2025-03-15"}], "tags": ["auth", "middleware", "express"], "affectedFiles": ["src/app.ts", "src/middleware/auth.ts"], "createdAt": "2025-03-15T00:00:00Z", "updatedAt": "2025-03-15T00:00:00Z"}
```

**Bad entry (too vague to be useful):**
```json
{"id": "auth_stuff", "type": "pattern", "fact": "Auth is tricky", "recommendation": "Be careful.", "confidence": "low", "tags": [], "createdAt": "2025-03-15T00:00:00Z", "updatedAt": "2025-03-15T00:00:00Z"}
```

### Step 4: Append to the Right File

```bash
echo '{"id": "auth_middleware_pattern", ...}' >> "$KB_DIR/patterns.jsonl"
```

### Step 5: Deposit 0 Entries When Appropriate

Not every scope produces learnings. If the work was straightforward and nothing surprising happened, deposit nothing. Don't force entries just to fill the knowledge base.

### Process Knowledge Deposit (BLOCK or PIVOT)

After a BLOCK or PIVOT decision, the orchestrator may extract 0-2 *process observations*. These are things about scope structure, agent behavior, or review patterns — valid regardless of whether the code shipped.

#### What Qualifies

- Implementation agents consistently miss something (e.g., stale doc references)
- A type of acceptance criterion always blocks (e.g., operational gates)
- Scope structure caused predictable problems
- Review caught a systemic pattern worth flagging for future planners

#### What Does NOT Qualify

- Code patterns or architectural decisions → wait for APPROVE
- Library-specific gotchas → wait for APPROVE (approach might change on retry)
- One-off blockers (missing API key, broken CI) → not systemic, not worth preserving

#### Example

```json
{"id": "impl_agents_miss_stale_doc_refs", "type": "gotcha", "fact": "Implementation agents claim docs need no update while stale references remain", "recommendation": "When removing code, always grep docs/ for references. Agents skip this — review must catch it.", "confidence": "high", "provenance": [{"source": "agent", "reference": "gemini_hybrid_06_hard_cutover/iteration_01", "date": "2026-03-21"}], "tags": ["documentation", "refactoring", "agent-behavior"], "affectedFiles": ["docs/**/*.md"], "createdAt": "2026-03-21T00:00:00Z", "updatedAt": "2026-03-21T00:00:00Z"}
```

Most BLOCKs and PIVOTs won't produce process learnings — that's fine. Only deposit when you see something likely to repeat.

### Process Knowledge Deposit (ITERATE)

ITERATE deposits are **conditional** — most ITERATEs won't produce learnings. The reviewer deposits 0-2 process observations only when they spot a generalizable lesson:

#### What Qualifies
- Scope structure that predictably led to iteration (e.g., missing integration test in criteria)
- Agent behavior pattern that future planners should anticipate
- Review process insight (e.g., certain criteria types always need clarification)

#### What Does NOT Qualify
- Code patterns or architectural decisions → wait for APPROVE
- The specific fixes requested in this ITERATE → those belong in the sub-iteration plan
- One-off issues unlikely to recur

### Ad-Hoc Knowledge Deposit

Users can request knowledge deposits at any time outside the formal review cycle. The agent assists with formatting and appending, but the user gates the decision.

**Workflow:**
1. User identifies something worth preserving (pattern, gotcha, decision)
2. Agent drafts the entry using the standard schema
3. User reviews and approves the entry
4. Agent appends to the appropriate `.jsonl` file in `.agent_process/knowledge/`

---

## Ad-Hoc Knowledge Evaluation Criteria

Before depositing ad-hoc knowledge, evaluate the candidate entry against these criteria:

1. **Is this specific to this scope or generalizable?** — Knowledge should help future scopes, not just document the current one. If it only applies here, it belongs in `results.md`, not the knowledge base.
2. **Would a future agent benefit from knowing this?** — If the answer is "only if they're working on exactly this feature," it's too narrow. Good entries inform decisions across the project.
3. **Is there a concrete recommendation (not just "be careful")?** — Every entry needs an actionable `recommendation` field. "Auth is tricky" doesn't cut it; "Apply auth middleware in app.ts before route registration" does.
4. **Does this duplicate existing knowledge? (Check before adding)** — Search the knowledge base first. If a similar entry exists, update it rather than creating a duplicate.

---

## How to Curate (Manual Maintenance)

Over time, the knowledge base may need cleanup. This is a manual process — do it when entries become stale or the files get large.

### When to Curate

- **File exceeds ~100 entries**: Some entries may be obsolete
- **Contradictory entries exist**: A newer decision may supersede an older one
- **Entries reference deleted code**: Clean up after major refactors
- **Planning queries return too many results**: Tighten scope tags

### How to Curate

1. **Review entries**: Read through the file, identify stale or redundant entries
2. **Remove obsolete entries**: Delete lines for patterns/decisions that no longer apply
3. **Consolidate duplicates**: Merge similar entries into one comprehensive entry
4. **Update scope tags**: Ensure scope values match current category names
5. **Preserve the schema line**: Always keep the first `_schema` line intact

### Curation Tips

- **Don't over-curate**: Some "old" entries are still valuable context
- **Preserve the why**: Even if a pattern was abandoned, knowing *why* it was abandoned helps
- **Date helps**: Entries with old dates are candidates for review, not automatic deletion
- **Anti-patterns are permanent**: Something that failed once will likely fail again — keep these

---

## Integration Points

| Phase | Action | File |
|-------|--------|------|
| Planning (Step 2.5) | Query knowledge via grep | `orchestration/steps/planning/025-knowledge-query.md` |
| Planning output | Include findings in `## Known Patterns & Constraints` | `templates/iteration-plan.md` |
| Review (APPROVE, Step 9.5) | Extract 0-3 code learnings → `.agent_process/knowledge/*.jsonl` | `orchestration/steps/review/07-10-post-decision.md` |
| Review (BLOCK/PIVOT, Step 9.6) | Extract 0-2 process observations → `.agent_process/knowledge/*.jsonl` | `orchestration/steps/review/07-10-post-decision.md` |
| Review (ITERATE, Step 9.7) | Extract 0-2 process observations (conditional) → `.agent_process/knowledge/*.jsonl` | `orchestration/steps/review/07-10-post-decision.md` |
| Ad-hoc | User-initiated deposit (requires consent) → `.agent_process/knowledge/*.jsonl` | `process/knowledge-base.md` (this file) |
| Metaswarm `/metaswarm:prime` | Keyword/file-filtered knowledge queries | Reads `.agent_process/knowledge/*.jsonl` |
| Metaswarm `/metaswarm:self-reflect` | Mines PR comments + conversation history → knowledge | Writes `.agent_process/knowledge/*.jsonl` |

---

## Troubleshooting

**Q: Knowledge base is empty, should I pre-populate it?**
A: No. Let it grow organically through APPROVE deposits. Pre-populated entries lack the context that comes from actually experiencing the issue.

**Q: Queries return too many results, overwhelming the iteration plan.**
A: Filter more aggressively by scope/category. Include only entries directly relevant to the files you're changing, not the entire category.

**Q: An entry is wrong — the pattern it recommends caused problems.**
A: Move it to `anti-patterns.jsonl` with updated detail explaining what went wrong. Don't just delete it — future planners need to know what *not* to do.

**Q: Two entries contradict each other.**
A: The newer entry wins. Update the older entry's detail to note it was superseded, or remove it entirely. Add the superseding entry's ID to the detail for traceability.
