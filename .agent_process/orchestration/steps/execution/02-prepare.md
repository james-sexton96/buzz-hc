# Step 02: Prepare Execution

**Input:** Preflight results
**Output:** `<project_root>/.agent_process/work/{scope}/.run/execution/02-prepare.md`

---

## Guiding Principle

For sub-iterations: the executor must understand the SEMANTIC INTENT of each fix, not just make mechanical changes. Extract and surface the WHY.

---

## 1. Load Context

Read:
- `.agent_process/work/{scope}/iteration_plan.md` — criteria, guidance, files
- `.agent_process/work/{scope}/{iteration}/results.md` — for sub-iterations, the fixes required
- `.agent_process/work/{scope}/human-prereqs.md` — optional human checkpoint (if exists)

Extract:
- **Acceptance Criteria** (LOCKED)
- **Files in Scope**
- **Removed Surfaces** (if non-empty in the plan — see step §1.1 below)
- **Validation Commands** (RUN vs SKIP)
- **Technical Guidance**
- **Human checkpoint requirements** (if `human-prereqs.md` exists)

### 1.1 Removed Surfaces (if non-empty)

If `iteration_plan.md` declares any **Removed Surfaces**, surface them in
the prepare doc verbatim and add the following instruction for the
implementer:

> Before declaring this iteration complete, run the stale-surface scrub
> block from the validator. If the scrub flags a reference outside the
> whitelist, the implementer must either (a) update that reference to
> remove or replace the removed surface, or (b) extend the per-surface
> whitelist file at
> `.agent_process/work/{scope}/.removal-whitelist/{surface}.txt` with
> the new entry AND record a justification in `results.md`. Pasting an
> entry into the whitelist without a justification is not acceptable —
> the reviewer's Gate 1 will fail it.

The implementer's `results.md` must include a **Removed-Surface Scrub**
section per `process/removal-scope-checklist.md`. The reviewer reads it
during Gate 1; missing or incomplete sections fail the gate.

If the plan declares `Removed Surfaces: N/A`, skip this sub-step.

### 1.2 Quality-Gate Artifact Check

If any file in the iteration's **Files in Scope** is a **quality-gate
artifact** — a validator script, audit hook, scrub block, gate test,
lint or type-check config, adversarial-review prompt, or similar code
whose job is to *judge* whether other code is correct — the prepare
doc MUST include a **negative-case acceptance test** for every fix
that touches one.

A quality-gate artifact has a failure mode the scoped validator cannot
catch on its own: the artifact can be silently broken in a way that
always exits 0. "The validator runs and exits 0" proves the artifact
is callable; it does not prove the artifact catches what it's meant
to catch.

**For every fix in Sub-iteration Fixes that modifies a quality-gate
artifact, write two acceptance tests:**

- **Operational:** the artifact runs and exits 0 on the current repo
  state, **under the documented invocation shell/runtime**. For shell
  validators, "the documented invocation" is the shebang the script
  uses (`#!/usr/bin/env bash` on macOS resolves to `/bin/bash` =
  3.2.57 unless the operator has Homebrew bash earlier on PATH).
  Confirm with `bash --version` in the recorded transcript. Recording
  exit 0 from a Homebrew-bash-5 invocation when the documented
  invocation is `bash <script>` does not satisfy the operational
  check — the script must run under the same shell a fresh checkout
  produces. Necessary, never sufficient.
- **Negative case:** introduce a synthetic violation the artifact is
  meant to catch and prove it gets caught (the artifact reports the
  violation and exits non-zero). Examples:
  - Stale-surface scrub → seed a fake file with a tagged stale hit
    like `stale /api/foo (#999)` and prove the scrub flags it under
    `STALE REFERENCES` and exits non-zero.
  - Type-checker config change → add a deliberately mistyped fixture
    and prove the checker fails on it.
  - Lint rule update → add a fixture that violates the new rule and
    prove lint exits non-zero.
  - Adversarial-review prompt update → seed a known-faulty result and
    prove the prompt produces a FAIL verdict.

**If you, as the prepare-step author, cannot construct a credible
negative-case test for a fix, treat that as a signal the fix spec is
incomplete.** Surface the gap under `## Spec Concerns` in the prepare
doc (see §1.4) and flag it to the coordinator before handoff —
shipping a quality-gate change with only operational acceptance tests
is the failure mode this rule prevents.

### 1.3 Scope Boundary Flexibility (mirror of iteration-plan rule)

When the prepare doc's `Files in Scope` list is narrower than the
parent `iteration_plan.md` (typical for sub-iterations focused on a
named fix), include this verbatim clause in the prepare doc just
under the Files in Scope table:

> **Boundary flexibility (mirrors the iteration-plan rule):** This
> list is the *expected* touch surface, not a *forbidden* boundary.
> If meeting the acceptance criteria correctly — including any
> negative-case tests for quality-gate artifacts (§1.2) or
> stale-surface whitelist updates for removed surfaces (§1.1) —
> requires touching files outside this list, the implementer may do
> so. Document the expansion in `results.md` under "Implementation
> Notes" with what was added and why. The narrower list keeps
> sub-iterations focused; it does not wall off soundness fixes.

**Why this is required:** in practice, sub-iteration prepare docs
that omit this clause have been read by implementers as a hard
prohibition, even when soundness required expansion. The
iteration-plan template already states the rule; the prepare doc must
not silently revoke it for sub-iterations.

### 1.4 Spec Concerns Channel

Include this verbatim clause in the prepare doc, near the implementer
summary:

> **Spec Concerns channel:** Pause and write a `## Spec Concerns`
> section at the top of `results.md` if any of these fire:
>
> - **Prepare-doc gap.** A missing acceptance test, an instruction
>   that conflicts with the iteration plan or framework rules, a
>   soundness question about a quality-gate artifact you're
>   modifying, or a fix spec that names a symptom rather than a root
>   cause.
> - **About to weaken a failing check.** You're about to remove an
>   assertion, relax a test, comment-out a guard, document a known
>   regression as "future work," or rephrase a doc/comment to dodge
>   a string match. This is the failure mode the channel exists to
>   catch. Treat the weakening as a Spec Concern, not a local fix.
> - **Test failure points at production code, not the test.** If the
>   assertion encodes the contract correctly and the production code
>   doesn't honor it, the production code is the bug — even if it
>   lives outside your file list. §1.3 (boundary flexibility) lets
>   you fix it.
>
> Then choose ONE:
>
> - **Local fix is safe and obviously correct:** apply it, document
>   it under Spec Concerns AND in Implementation Notes, including
>   what changed and why.
> - **Local fix is uncertain or expands scope significantly:** stop
>   without applying it, leave the concern in `results.md`, and
>   surface it to the coordinator so the prepare doc can be revised.
>
> **There is no third option that weakens the check to make the
> failure go away.** Modifying or removing a failing test assertion
> is a *contract change*, not a local fix — even when the edit is
> mechanically simple. A test assertion is a piece of contract
> surface area; removing it silently reduces the contract. Contract
> changes always require coordinator escalation. The path forward is
> fix-the-issue (in scope, even when §1.3 boundary flexibility is
> needed to extend to a file outside your list) or stop-and-surface
> (out of scope). Weakening the check is the anti-pattern.
>
> Concerns raised in good faith are never a failure mode; silently
> shipping work the implementer suspects is incomplete is.

The reviewer's Gate 1 reads this section explicitly and applies a
**Weakened-Assertion FAIL** rule when the implementer chooses the
weakening path. See `steps/review/02-gates.md`.

### 1.5 AC Enumeration & Concrete Scenario Coverage

The framework's experience: ACs that read like clean behavior
assertions get compressed during AC-to-test translation into a single
operational check, leaving coverage gaps that no validator catches.
Three failure shapes have recurred (these examples span backend APIs,
MCP tools, and frontend UIs — the same compression happens in every
domain):

- **Universal quantifier compressed.** AC says "every X" → test
  asserts on one X "for the family." The other N−1 cells are unproven.
  *Backend example:* "every public endpoint returns the full v2
  response schema" → one endpoint tested. *Frontend example:* "every
  list-item type opens the matching detail view" → only one item
  type tested.
- **Alternative-with-divergent-semantics compressed.** AC names
  alternatives joined by "or" → executor reads them as symmetric,
  missing that one alternative has a different shape. *Backend
  example:* "auth via API key, OAuth token, or session cookie" →
  executor handles all three the same way, missing that OAuth tokens
  refresh and session cookies have CSRF semantics. *Frontend
  example:* "trigger characters `@`, `#`, or `[[`" → executor reads
  three trigger types symmetrically, missing that `[[ ]]` is a phrase
  wrapper (multi-word) while `@` and `#` are token triggers
  (whitespace-delimited).
- **State dependency compressed.** AC names a behavior whose outcome
  depends on ambient state, but only one state value gets tested.
  *Backend example:* "rate-limit returns 429 on excessive requests"
  → tested with 0 prior failures, not the cliff-edge case of 5 prior
  failures within the window. *Frontend example:* "selecting a list
  item opens the detail view" → tested with the list populated, not
  with the list empty (where a different fallback resolution path
  must run).

The rule fires **whenever any of these triggers are present:**

1. **Universal quantifiers** — "every", "each", "all", "for every X".
2. **Multiple subjects joined by "and"** — "X and Y", "GET /api/foo
   and GET /api/foo/{id}", "service A and worker B".
3. **Alternatives joined by "or" when the alternatives may have
   divergent semantics.** Examples that span domains:
   - Auth methods: "API key, OAuth token, or session cookie"
     (different lifetime / refresh / revocation rules).
   - HTTP methods: "GET, HEAD, or OPTIONS" (different response-body
     and idempotency semantics).
   - Input formats: "JSON, form-encoded, or multipart" (different
     parsing and streaming).
   - Outcome types: "succeed, validate-only, or fail-fast" (different
     response shapes).
   - Trigger characters: "`@`, `#`, or `[[`" (token vs phrase wrapper).

   When in doubt whether alternatives diverge, treat them as
   divergent — the cost of an extra scenario row is small; the cost
   of compressing divergent semantics is what produced this rule.
4. **State-dependent behavior** — the AC describes behavior that
   varies by ambient state. Each named state value is a separate
   scenario. Examples:
   - List populated vs empty.
   - Authenticated vs anonymous vs expired-token.
   - Cache hit vs miss vs revalidating.
   - Rate-limit window: under threshold vs at threshold vs locked.
   - Save / write-back: in flight vs persisted vs failed.
   - Service: cold start vs warm.

**For every AC that fires any trigger above:**

1. **Build a scenario table, not just a code-surface matrix.** Each
   row is a **concrete behavior scenario** with three cells filled in:
   - **Input** — the literal request body / URL / event / user input
     that arrives. Not "client sends a request"; rather
     `POST /api/v1/users {email: "alice@example.com"}`. Not "user
     submits the form"; rather "user types `alice@example.com` into
     the email field, then clicks Sign In".
   - **State context** — what's true about the system when the input
     arrives. Named state values (cache populated / empty;
     authenticated / anonymous; rate-limit window position;
     persistence in flight / complete). Not "API endpoint"; rather
     "API endpoint, account active, no recent failures".
   - **Observable outcome** — what an external observer sees: HTTP
     status + body, log line, queue message, UI state, side-effect
     in another store. Not "endpoint returns success"; rather
     "200 OK, response body contains `access_token` claim with
     `iss=api.example.com`, account's `last_login` updated".
2. **Code-surface cells supplement, never replace, scenario cells.**
   "Layer A vs layer B," "compose vs read surface," or "service A vs
   service B" is useful framing, but a matrix made only of surface
   labels lets the implementer prove the *code path exists* without
   proving the *external outcome*. Every code-surface row needs at
   least one concrete-scenario row inside it.
3. **Bind each scenario to a test.** Per-scenario parametrize
   fixture, per-scenario test name, or per-scenario assertion block.
   The transcript should show one entry per scenario row. A single
   "happy path" test covering N scenarios is not sufficient.
4. **Combine with §1.2.** If a scenario exercises a quality-gate
   artifact, it gains operational + negative-case dimensions per §1.2.

**Bad scenario table (code surfaces only):**

| Endpoint | Method | Fix |
|---|---|---|
| `/api/v1/auth/login` | POST | Fix 1 |
| `/api/v1/auth/logout` | POST | Fix 2 |

This proves the endpoints exist. It does not prove that bad
credentials trigger the rate limiter, that a locked account
returns the right status, or that a logged-out token is actually
revoked at the session store. Code paths can be present and still
not honor the contract under the states that matter.

**Good scenario table (concrete behavior scenarios — backend API
example):**

| Endpoint | Input | State | Observable outcome |
|---|---|---|---|
| `POST /login` | valid creds | account active, no recent failures | 200; body contains `access_token`; `last_login` updated in DB |
| `POST /login` | wrong password | account active, no recent failures | 401; no token; `failure_count` incremented |
| `POST /login` | wrong password | account active, 5 failures in last 60s | 429; `Retry-After` header set; account locked for 5min |
| `POST /login` | valid creds | account locked | 423; "account locked" error code |
| `POST /login` | valid creds | account exists, password hash uses legacy algorithm | 200; token issued; `password_hash` rotated to current algorithm in DB |
| `POST /logout` | valid token | session active | 204; subsequent call with same token returns 401 |
| `POST /logout` | expired token | session already expired | 204 (idempotent); no DB write |

The same shape applies to MCP tool ACs (input = tool call args,
state = workspace/auth context, outcome = tool response + side
effects), to message-queue handler ACs (input = message body, state
= consumer-group offset / dedup state, outcome = downstream effect),
and to frontend UI ACs (input = literal user action, state = client
state context, outcome = visible UI change + URL/route effect).
Every row is a test the implementer must pass and the reviewer can
re-run. Each cell is concrete enough that a human reading it knows
exactly what to send, what state to set up, and what to assert on.

**Why this rule exists:** AC prose is the contract; tests are the
proof. The translation from prose to tests has historically lost
information when ACs use universal quantifiers, when ACs join
alternatives with semantic divergence, or when ACs imply state
dependencies. Each compression has produced a shipped iteration with
a real outcome gap. The Concrete Scenarios requirement reverses the
loss: the prepare doc enumerates the scenarios *before* the executor
implements anything, so coverage gaps are visible at planning time,
not after the next sub-iteration's review finds them.

When no AC fires any trigger, this rule is silent. Single-subject
single-state ACs are unaffected.

When no AC quantifies universally and no AC names multiple subjects,
this rule is silent. Additive scopes with single-subject ACs are
unaffected.

### Sub-iteration Context

For `_a`/`_b`/`_c` iterations, also extract from the placeholder results.md:
- Each fix's **mechanical change** (file:line, before/after)
- Each fix's **semantic intent** (WHY this solves the problem)
- Each fix's **acceptance test** (outcome-based verification)

Read previous iteration's results to understand what worked/didn't.

### Human Checkpoint Context

If `.agent_process/work/{scope}/human-prereqs.md` exists:
- Treat it as a required execution checkpoint, not optional context
- Extract the concrete actions the human must complete
- Surface exactly when execution must pause (e.g., before live validation, before deploy)
- Carry forward the allowed human responses (e.g., proceed, blocked, local-only)

**Format is not fixed.** Real files may use the strict template (Pause Point / Human Actions / Allowed Responses) OR a looser structure (e.g. "Required Decisions and Actions" with numbered items, "Blocking Assumptions", "Operator Actions"). Do not require the strict template — extract what's there and classify it yourself:

- **pre_execution** — decisions, confirmations, credentials, environment setup needed before any code runs. Default bucket when the file doesn't say otherwise.
- **mid_execution** — things that must be done before live validation / before touching external systems / before deploy.
- **post_execution** — cutover, user notifications, follow-up work, prod parity confirmation.

If a file only lists items without classifying them, put them in `pre_execution` — the coordinator will surface them to the human before spawning the implementer. Better to ask up front than silently skip.

The coordinator (main conversation) is what holds the actual gate — this step just extracts and classifies. Do not try to pause inside this sub-agent.

This file is created during plan-scope and may be modified during review if checkpoint needs change between iterations.

---

## 2. Decomposition Assessment

**Skip if:**
- `quality-config.json` has `work_unit_decomposition.enabled: false`
- This is a sub-iteration (execute directly against fixes)
- Files < 3 or layers < 2

**If triggered:**
- Group files by layer (backend, frontend, tests, etc.)
- Create work units with dependencies
- Each unit independently validatable

---

## 3. Agent Selection

Match file patterns to specialized agents:

| Files | Agent |
|-------|-------|
| Backend API, routes | `backend-security:backend-expert` |
| React, `.tsx` | `frontend-excellence:react-specialist` |
| Tests | `dev-accelerator:test-automator` |
| CI/CD, Docker | `infra-pipeline:cicd-engineer` |
| General/mixed | `general-purpose` |

For work units: one agent per unit.

---

## Output

```markdown
# Execution Preparation

**Scope:** {scope}
**Iteration:** {iteration}
**Type:** first_iteration / sub_iteration

## Criteria (LOCKED)
- [ ] {criterion 1}
- [ ] {criterion 2}

## Files in Scope
{list}

## Validation
- **RUN:** {commands}
- **SKIP:** {commands with reasons}

## Human Checkpoint
- **Required:** YES / NO
- **Source file:** `.agent_process/work/{scope}/human-prereqs.md` (present YES/NO)
- **Pre-execution items:** {list, or "none"}
- **Mid-execution items:** {list with trigger, or "none"}
- **Post-execution items:** {list, or "none"}
- **Allowed Responses:** {proceed / blocked / local-only / etc. — default set if file didn't specify}

**Note for coordinator:** the actual gate runs in the main conversation (Steps 0.5 and 6 of `execute.md`). This section is input for that gate, not a place to claim the gate already ran.

## Sub-iteration Fixes (if applicable)

### Fix 1: {Title}
- **Change:** {file:line, before/after}
- **Semantic Intent:** {WHY — executor must understand this}
- **Acceptance Test:** {outcome-based verification}

## Decomposition
DECOMPOSE: skip / yes
{If yes: work unit DAG}

## Agent Selection
- **Mode:** single / multi-agent
- **Agent(s):** {agent_type}
- **Reasoning:** {why this agent}
```
