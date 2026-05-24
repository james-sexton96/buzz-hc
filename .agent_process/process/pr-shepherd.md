# PR Shepherd

**Type:** How-To Guide (Diátaxis)
**Purpose:** Snapshot a PR's CI/review state, attempt one bounded pass of simple fixes, and report — repeatedly via `/loop` if ongoing monitoring is needed.

---

## Overview

The PR shepherd is an optional post-PR agent that does **one bounded pass** over a PR: it snapshots CI status, snapshots review state, attempts simple in-diff fixes if applicable, and reports. It extends the workflow from "PR created" to "PR ready to merge" — but the shepherd itself is a single-pass primitive, not a long-lived watcher.

**Activation:** Pass `--shepherd` to `/ap_release`, or request a shepherd pass when creating a release.

**Philosophy:** The shepherd is a CI/review snapshotter with commenting privileges — not an autonomous decision-maker, and not a watcher that waits for things to happen. It reports the current state and the next concrete action; the human clicks merge (or runs `/loop` to re-snapshot until things change).

**Why bounded?** A sub-agent has a single bounded execution window. It cannot wait hours for CI to finish or for a human reviewer to respond. Trying to make a sub-agent "monitor until merge-ready" produces the failure mode where the agent complains that "long-running watch isn't supported for a sub-agent." The fix is to split the responsibility: each invocation does one pass and returns; ongoing monitoring is supplied by `/loop` or `/schedule` re-invoking the shepherd on an interval.

---

## When to Use

| Situation | Use Shepherd? | Why |
|-----------|--------------|-----|
| Simple PR, fast CI, single reviewer | No | Overhead exceeds benefit |
| Multi-file PR with lint/type CI checks | Yes | Auto-fixes save round-trips |
| PR needs to sit open for review | Yes | Monitors and responds while you move on |
| Hotfix that must merge ASAP | Yes | Actively watches for blockers |
| Draft PR / WIP | No | Not ready for monitoring |

---

## How It Works

### Activation

```bash
# During release — runs one bounded shepherd pass after PR creation
/ap_release pr --shepherd
/ap_release release minor --shepherd

# Ongoing monitoring — re-invoke the shepherd pass on an interval
/loop 5m /ap_release shepherd-pass {PR}      # tight loop while CI runs
/schedule "every 1 hour" ...                 # slower loop while waiting on review
```

### What One Shepherd Pass Does

A single pass takes a snapshot of the PR's *current* state and acts only on what's actionable right now. It does NOT wait, poll, sleep, or retry across time.

#### 1. Snapshot CI Pipeline

The shepherd checks CI status using `gh pr checks`:

- **All passing right now** → records MERGE-READY (CI side)
- **Lint/formatting failure** → fixes in one commit (one attempt per issue per pass), or records diagnosis and stops if the fix needs context outside the PR diff
- **Type errors** → same: one-shot fix if within diff, otherwise record and stop
- **Test failures** → diagnoses; fixes if strictly within PR diff and obvious; reports if not
- **Build failures** → reports with specific failure context for human action
- **Still running** → records IN PROGRESS, **does not wait** (re-run the shepherd later via `/loop` to re-check)

#### 2. Snapshot Review Comments

The shepherd reads review comments via `gh pr view --comments`:

- **Questions with short answers** → drafts and posts a response in this pass
- **Change requests strictly within the PR's existing files** → implements and commits in this pass
- **Out-of-scope requests** → records them for the user with explanation, does not act
- **Pending reviews** → records "review pending" and exits — does not nag, does not wait

#### 3. Report Bounded Outcome

The shepherd produces a status report classified as one of:

- **MERGE-READY** — CI green this snapshot, no unresolved review threads, no changes requested. Human can merge.
- **NEEDS-FOLLOWUP** — actionable work remains, but it's not actionable in this pass (CI still running, review pending, an out-of-scope thread to triage). The shepherd's recommendation: run `/loop` or `/schedule` to re-invoke the pass when the state may have changed.
- **BLOCKED** — PR cannot progress without explicit human action (build error needing scope decision, reviewer pushback, etc.).

When all conditions are met, the shepherd produces a status report:

```markdown
## PR Shepherd Report

**PR:** https://github.com/org/repo/pull/123
**Status:** 🟢 MERGE-READY | 🟡 IN PROGRESS | 🔴 BLOCKED

**CI Checks:** all passing / N failing
**Review Status:** approved / changes requested / no reviews
**Unresolved Threads:** 0 / N

**Actions Taken:**
- Fixed ESLint warning in profile.tsx (commit abc123)
- Responded to question about error handling approach

**Blockers (if any):**
- Waiting for review from @teammate
```

---

## Boundaries

The shepherd has strict operating limits:

| Allowed | Not Allowed |
|---------|-------------|
| Modify files already changed in the PR | Create new files (without user approval) |
| Push fix commits to the PR branch | Force-push or rebase |
| Respond to review comments | Merge the PR |
| Diagnose CI failures | Dismiss reviews |
| Report status | Make scope decisions |

**Bounded-pass rule:** One fix attempt per issue per pass. If the same issue is flagged on the next pass, the shepherd may try a different approach, but it never retries the same approach against the same failure within a single sub-agent invocation. No sleep loops, no polling, no waiting on async events.

**Scope constraint:** The shepherd only touches files already in the PR's diff. This prevents the common failure mode where an agent "fixes" an unrelated lint warning and introduces a regression in code it doesn't understand.

---

## Session Recovery & Ongoing Monitoring

The shepherd is **stateless by design** — it reads the PR's current state from GitHub on each invocation. No local state file needed, no resumption logic, no "is the watcher still running?" check.

If you want continuous monitoring after a single pass returns NEEDS-FOLLOWUP, re-invoke the shepherd on an interval:

```bash
# Tight loop while CI is finishing (every 5 min)
/loop 5m /ap_release shepherd-pass <PR>

# Slower loop while waiting on a human reviewer (hourly)
/schedule "every 1 hour" /ap_release shepherd-pass <PR>

# One-off check when the user wants a fresh snapshot
gh pr checks <PR_NUMBER>
gh pr view <PR_NUMBER> --comments
# ...then re-run the shepherd step manually
```

**Key principle:** the LOOP provides "monitor until merge-ready." The shepherd PASS provides "snapshot the current state and do what's actionable now." Each is a separate primitive; mixing them (asking the sub-agent to be both the loop AND the pass) is what produces the "long-running watch isn't supported" failure mode.

---

## Integration Points

| Component | How it interacts with the shepherd |
|-----------|------------------------------------|
| `/ap_release` Step 9.5 | Launches the shepherd after PR creation |
| `gh` CLI | Primary interface for PR status and comments |
| Scope branch | All shepherd commits go to the PR branch |
| CI pipeline | Shepherd reads check results, fixes failures |
| Human reviewer | Shepherd responds to comments, human merges |

---

## Troubleshooting

**Q: The agent says "long-running watch isn't supported for a sub-agent."**
A: That's the failure mode the bounded-pass design exists to prevent. The shepherd is a single bounded pass, not a watcher. If the pass returned NEEDS-FOLLOWUP because CI is still running or a reviewer hasn't responded, re-invoke the pass on a `/loop` interval — don't try to make the sub-agent itself wait.

**Q: The shepherd keeps failing on the same lint issue across passes.**
A: One fix attempt per issue per pass. If three consecutive passes fail on the same issue, that's a strong signal the issue needs context outside the PR's changed files. Fix it manually or surface as BLOCKED.

**Q: A reviewer requested changes outside the PR scope.**
A: The shepherd flags these as "out of scope" and doesn't act. Add them to the backlog or address in a follow-up scope.

**Q: CI passes but reviewer hasn't approved yet.**
A: The shepherd reports NEEDS-FOLLOWUP with "review pending" as the recommended next action. It doesn't nag reviewers and doesn't wait — re-run the pass via `/schedule` for a periodic check, or wait for the human to ping you.

**Q: The shepherd made a fix I don't agree with.**
A: Revert the commit on the branch. The shepherd pushes normal commits — they're easy to revert. Consider this feedback for the PR shepherd's prompt tuning.

**Q: Can the shepherd handle multiple PRs?**
A: One pass per PR per invocation. If you have multiple PRs, run a pass for each (or set up `/loop` for each).

---

## Relationship to Other Components

The shepherd is downstream of everything else in the agent process:

```
Plan → Execute → Review → APPROVE → /ap_release → PR Created → Shepherd
                                                                    │
                                                          ┌─────────┴──────────┐
                                                          │ Monitor CI         │
                                                          │ Respond to reviews │
                                                          │ Fix lint/types     │
                                                          │ Report readiness   │
                                                          └─────────┬──────────┘
                                                                    │
                                                              Human merges
```

The orchestrator never interacts with the shepherd. The shepherd runs after the orchestrator's APPROVE decision and operates entirely in the PR/CI domain.
