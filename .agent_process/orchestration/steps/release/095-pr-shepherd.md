# Step 9.5: PR Shepherd (CONDITIONAL)

**Model tier:** capable (Agent tool — spawns a single-pass sub-agent)
**Tools needed:** Agent/Task
**Input:** PR URL from `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/07-09-git-ops.md`
**Output:** `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/095-shepherd.md`

---

## Your Task

Launch a shepherd agent to do **one bounded pass** over the PR — check current CI status, check current review state, attempt simple fixes (lint/type) if applicable, then report. This step is conditional — check the launch criteria before spawning.

**The shepherd is not a long-lived watcher.** A sub-agent has a single bounded execution; it cannot wait hours for CI to finish or for reviewers to respond. If continuous monitoring is needed, the recommendation is to run this step on a `/loop` interval or as a `/schedule` routine — each invocation is its own bounded pass.

## Launch Criteria

1. Read `quality-config.json` → `pr_shepherd.enabled`
2. Check CLI flags:
   - `--no-shepherd` → skip regardless of config
   - `--shepherd` → run regardless of config
   - Neither → follow config setting

## Shepherd Agent (single bounded pass)

Spawn with Agent/Task tool:

```
Agent({
  subagent_type: "general-purpose",
  description: "PR shepherd: single bounded pass",
  prompt: "You are a PR shepherd doing ONE BOUNDED PASS over PR {URL}.

    You are NOT a long-lived watcher. Sub-agents run once and return —
    they cannot wait for CI to finish or for reviewers to respond. Do
    the work that's actionable RIGHT NOW given the PR's current state,
    then report and exit.

    Single-pass workflow:
    1. Snapshot CI: gh pr checks {NUMBER}
       - All passing now → record MERGE-READY (CI side)
       - Some failing now → if lint/type/format and within PR diff,
         fix in one commit; if test/build failure or out of diff,
         record diagnosis and stop (do not retry beyond 1 attempt
         per issue this pass)
       - Still running → record IN PROGRESS, do not block waiting
    2. Snapshot reviews: gh pr view {NUMBER} --comments
       - For each thread you can resolve in this pass (a question
         with a short answer, a change request strictly within the
         PR's existing files), respond/implement and resolve
       - For threads needing scope expansion, design discussion, or
         extended context, record them and skip — do not force a
         resolution
    3. Decide bounded outcome:
       - MERGE-READY: CI green + no unresolved review threads + no
         changes requested
       - NEEDS-FOLLOWUP: actionable work remains that the human or a
         later pass should handle (CI still running, review pending,
         out-of-scope thread)
       - BLOCKED: PR cannot progress without human intervention
         (build error needing scope decision, design pushback, etc.)
    4. Report. Recommend next action explicitly:
       - If NEEDS-FOLLOWUP and the only thing pending is CI/reviewer
         response: suggest the user run `/loop 5m` invoking this
         step, or `/schedule` for less frequent checks
       - If BLOCKED: surface the human decision needed
       - If MERGE-READY: tell the human to merge

    Boundaries: only modify files already in the PR diff (no new
    files without explicit user approval); no force-push; no merge;
    no rebase; one fix attempt per issue this pass; no waiting,
    polling, sleeping, or retrying — return when the snapshot is
    captured and any one-shot fixes are committed."
})
```

## Output Format

Write to `<project_root>/.agent_process/work/{scope_or_noscope}/.run/release/095-shepherd.md`:

```markdown
# PR Shepherd

**Launched:** YES / SKIPPED
**Reason:** {config enabled / flag override / config disabled / --no-shepherd}
**Pass type:** single bounded pass (not a watcher)

## Report (if launched)
**PR:** {URL}
**Status:** MERGE-READY / NEEDS-FOLLOWUP / BLOCKED
**CI snapshot:** {all passing / N failing / still running}
**Reviews snapshot:** {approved / changes requested / none / pending}
**Actions taken this pass:** {list fixes committed, threads resolved, or "none — snapshot only"}
**Recommended next action:** {merge | run `/loop 5m /ap_release ... --shepherd` for ongoing CI watch | run `/schedule` for periodic check | human action: <description>}
```

---

## Long-Running Monitoring (recommended pattern)

When the shepherd reports `NEEDS-FOLLOWUP` and the only remaining work is "wait for CI/reviews," **do not try to make the sub-agent itself wait.** Instead, the user (or a parent loop in the main conversation) re-runs this step on an interval:

- **`/loop 5m /ap_release shepherd-pass {PR}`** — short interval (5–10 min) when actively waiting for CI.
- **`/schedule "every 1 hour" /ap_release shepherd-pass {PR}`** — longer interval when waiting for human review.
- **Single re-run** when the user wants to check status manually.

Each invocation is its own bounded pass — the framework's coordination primitive, not the sub-agent itself, is what provides "until merge-ready." If you find yourself wanting the sub-agent to sleep, poll, or retry across long windows, you're using the wrong primitive — use `/loop` or `/schedule`.
