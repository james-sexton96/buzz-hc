# Execution Coordinator (Lean)

Execute an iteration in 2 preparation steps + implementation.

## Model Tiers

| Tier | Use For | Claude Code | Codex |
|------|---------|-------------|-------|
| **cheap** | Preflight checks | haiku | gpt-5.4-mini |
| **capable** | Preparation, context extraction | sonnet | gpt-5.4 |
| **synthesis** | Implementation — code quality demands best model | opus | gpt-5.4 |

## Prohibitions

- Do NOT commit during execution — validation runs, then results documented
- Do NOT push to remote
- The user reviews and commits after successful iteration
- Do NOT proceed if GitHub integration is enabled and `github-issues-lifecycle.sh` fails — that's a blocking error, not a "non-blocking" inconvenience
- Do NOT run `.agent_process/` commands from the wrong directory — verify `pwd` is at project root before any bash command. "Script not found" usually means you're in the wrong directory, not that the script is missing.
- Do NOT silently skip `human-prereqs.md`. If the file exists, the coordinator (this workflow, in the main conversation with the user) is responsible for surfacing its contents to the human — sub-agents cannot hold interactive gates.

---

## Step 0: Resolve Input

```bash
bash .agent_process/scripts/github-issues-lifecycle.sh resolve-input "{{scope}}"
```

Use `scope` and `iteration` from result.

---

## Step 0.5: Human Prerequisites Gate — BEFORE work

**This gate runs in the main conversation, not in a sub-agent.** Sub-agents cannot pause and wait for human input; only the coordinator can.

```bash
test -f .agent_process/work/{scope}/human-prereqs.md && echo "EXISTS" || echo "NONE"
```

If `NONE`, skip this step. If `EXISTS`:

1. Read `.agent_process/work/{scope}/human-prereqs.md` in full.
2. Identify which items must be handled **before** work starts (environment setup, credentials, policy decisions, scope confirmations). When a file doesn't explicitly label pre-work vs post-work, treat any "Required Decisions" / "Blocking Assumptions" / "Operator Actions" as pre-work by default — better to ask early than silently skip.
3. **For each item, present it in human-readable form.** If the file follows the structured template (`Plain-language question` / `What this means` / `Recommended answer` / `If yes / If no` / `Override required because`), pass those fields through verbatim. If the file is in a legacy / looser format, do the translation yourself before showing it to the user — strip codebase jargon, internal step numbers, internal table or contract identifiers, and planning artifacts. State the user-visible consequence in one sentence. Add a recommended answer if the file's context makes one obvious.

   **Translation rule for legacy items:** if you cannot translate an item into a one-sentence user-outcome question with a recommended answer, the item is wrong-shaped. Surface it to the user with a flag: "this prereq item is written in planning vocabulary I can't translate cleanly — please re-read the source file or revise the planning step."

4. **Stop and present to the user directly in the main conversation**, using this format:

   ```markdown
   ## Questions for you — {scope}/{iteration}

   The planning step flagged the following for your call before execution starts:

   1. **{Plain-language question}**
      - **What this means:** {1–2 sentences in user-outcome terms}
      - **Recommended:** {YES / NO + one-line reason}
      - **If you say YES:** {user-outcome consequence}
      - **If you say NO:** {user-outcome consequence}

   2. **{Plain-language question}**
      - ...

   **How do you want to proceed?**
   - `proceed` — items resolved (tell me what was decided / what was done)
   - `blocked` — cannot move forward, stop here
   - `local-only` — defer live/external items, run local work only and note limitation
   ```

   Do NOT show the human raw planning vocabulary. If the structured template fields are present, present them. If not, translate as best you can; if you cannot translate, say so explicitly rather than dumping the raw text.

4. **Wait for the user's response in the main conversation.** Do not spawn any further sub-agents until the human replies.
5. Record the decision — it will be carried into the prepare step and the results doc.

If the user responds `blocked`, stop the workflow and report. Otherwise continue with the decision recorded.

---

## Step 1: Preflight

Spawn **cheap** agent:

```
Agent({
  description: "Preflight {scope}/{iteration}",
  prompt: "Read orchestration/steps/execution/01-preflight.md and execute.
    Scope: {scope}
    Iteration: {iteration}
    
    Check branch, working state, git context.
    Output: <project_root>/.agent_process/work/{scope}/.run/execution/01-preflight.md"
})
```

**Gate:** If `PREFLIGHT: BLOCKED`, stop and present options to user.

---

## Step 2: Prepare

Spawn **capable** agent:

```
Agent({
  description: "Prepare {scope}/{iteration}",
  prompt: "Read orchestration/steps/execution/02-prepare.md and execute.
    Scope: {scope}
    Iteration: {iteration}
    
    Load context, assess decomposition, select agent.
    For sub-iterations: extract semantic intent from each fix.
    Output: <project_root>/.agent_process/work/{scope}/.run/execution/02-prepare.md"
})
```

---

## Step 3: Implement

Read `<project_root>/.agent_process/work/{scope}/.run/execution/02-prepare.md` for agent selection and context.

**Sub-agents cannot interactively wait for a human.** If the preparation artifact flags a mid-execution checkpoint (e.g. "before live validation"), the sub-agent must STOP at that point, report what's pending, and return — the coordinator (main conversation) will surface the question to the human and resume on the user's reply.

Pass the recorded response from Step 0.5 (`proceed` / `local-only`) into the implementer so it skips live/external steps if `local-only` was chosen.

### First Iteration

```
Agent({
  model: "{synthesis}",  // Claude Code: "opus" | Codex: use best available
  subagent_type: "{selected_agent}",
  description: "Implement {scope}/{iteration}",
  prompt: "Implement {scope}/{iteration}:
    1. Read iteration_plan.md for criteria and guidance
    2. Implement changes to meet acceptance criteria
    3. Add/update tests
    4. Update docs per plan

    **Scope boundaries are guidance, not walls.** If solving the problem
    correctly requires touching files outside the plan:
    - Do it if necessary for correctness
    - Document what you added and why in results.md
    - Update the validation script to cover new files
    - The reviewer will assess whether the expansion was justified

    **Human mode from coordinator:** {proceed | local-only}
    - If local-only: skip any step that requires live/external systems,
      note the skipped items in results.md.

    **Mid-execution checkpoint:** If <project_root>/.agent_process/work/{scope}/.run/execution/02-prepare.md declares
    a pause point you hit (e.g. before a destructive/external action),
    STOP immediately, write what you need confirmed into results.md under
    'PENDING HUMAN', and return. Do NOT try to wait interactively — you
    cannot. The coordinator will ask the human and resume.

    You are the problem-solver. Meet the criteria correctly.
    Report completion status."
})
```

### Sub-iteration (semantic comprehension required)

```
Agent({
  model: "{synthesis}",  // Claude Code: "opus" | Codex: use best available
  subagent_type: "{selected_agent}",
  description: "Fix {scope}/{iteration}",
  prompt: "Fix issues for {scope}/{iteration}:

    BEFORE implementing, explain for EACH fix:
    - What is the underlying problem?
    - Why does this fix solve it?
    - What would fail if you made only the mechanical change?

    If you can't explain the semantic intent, STOP and ask.

    Then implement, and verify each fix's acceptance test passes.

    **Human mode from coordinator:** {proceed | local-only}
    - If local-only: skip any step that requires live/external systems.

    **Mid-execution checkpoint:** If <project_root>/.agent_process/work/{scope}/.run/execution/02-prepare.md declares
    a pause point you hit, STOP, write 'PENDING HUMAN' items into results,
    and return. You cannot wait interactively — the coordinator will.

    Report: comprehension summary, changes made, test results."
})
```

**After the sub-agent returns:** check results.md / the returned summary for a `PENDING HUMAN` section. If present, surface those items to the user in the main conversation (same format as Step 0.5), wait for the reply, then re-spawn the implementer with the resolution to continue.

---

## Step 4: Validate

**If the Step 0.5 response was `local-only`** (or the human flagged that live systems aren't available): skip validation commands that touch external systems and note the skipped items in results.md. Do not silently run them anyway.

Hook fires automatically after edits. If fails, fix and retry (max 3 attempts).

Then run full validation:
```bash
bash .agent_process/scripts/after_edit/validate-{scope}.sh {scope} {iteration} \
  | tee .agent_process/work/{scope}/{iteration}/test-output.txt
```

---

## Step 5: Document Results

```
/ap_iteration_results {scope} {iteration}
```

Update GitHub issue status:
```bash
bash .agent_process/scripts/github-issues-lifecycle.sh set-status {scope} status:awaiting_review
```

---

## Step 6: Human Prerequisites Gate — AFTER work

If `.agent_process/work/{scope}/human-prereqs.md` exists, re-read it and surface any items that:
- Were not resolved in Step 0.5 (e.g. deferred under `local-only`)
- Are explicitly post-work (cutover, rotation, notifying users, prod follow-up)
- Are follow-up actions the human committed to during Step 0.5

Present to the user in the main conversation:

```markdown
## Questions for you — {scope}/{iteration} (post-work)

Work is complete. `human-prereqs.md` still has these items pending your action:

1. {item}
   - {what the human needs to do or confirm}

2. {item}
   - ...

**How would you like to handle these?**
- Mark resolved (tell me what was done so I can note it in results.md)
- Defer to a follow-up scope (I'll add a backlog entry)
- Keep open — they stay in human-prereqs.md for the next iteration
```

Wait for the user's response. Update `results.md` and `human-prereqs.md` accordingly (e.g. strike through resolved items, keep open ones).

This step is mandatory if the file exists — do not skip it, even if work validated cleanly.

---

## Completion

```markdown
## Iteration Complete: {scope}/{iteration}

**Criteria:** {N}/{total} addressed
**Validation:** {PASS/FAIL}
**Files Changed:** {count}

**Next:** Review with `orchestration/review-iteration.md`
```
