# Personality Adaptation Process

**Purpose:** Describes how the agent personality system works — the static default profile, the adaptive user profile, and how they blend together.

---

## Architecture

```
orchestration/context/personality/
├── default-profile.md        # Baseline personality (ships with framework)
├── adaptation-schema.json    # Trackable dimensions and adaptation rules
└── user-profile.md           # Per-user calibration (gitignored, process-created)
```

### Layer 1: Default Profile (Static)
`default-profile.md` defines the factory personality. It ships with the framework and establishes a baseline that is engaging, technically sharp, and collaborative. All agents inherit this personality through the context loading chain.

### Layer 2: User Profile (Adaptive)
`user-profile.md` is a per-user calibration file that evolves over time. Key properties:

- **Not created by the installer** — created by the process on first interaction
- **Gitignored** — personal data stays local, not committed to the project
- **Blended with default** — never fully replaces the baseline personality

---

## How Personality Gets Loaded

### Every Session (via CLAUDE.md)
The installer adds an `## Agent Personality` section to the project's `.claude/CLAUDE.md`. Because Claude Code loads CLAUDE.md at the start of every session, the personality profile is always in context — not just during orchestrated workflows.

This means personality shapes:
- Casual coding sessions
- Debugging and Q&A
- Code reviews
- Orchestrated workflows (planning, execution, review)

### Orchestrated Workflows (via base-context.md)
Coordinators that load `base-context.md` also get a pointer to the personality files. This is redundant with the CLAUDE.md path but ensures personality is loaded even if CLAUDE.md is missing.

---

## User Profile Lifecycle

### Creation (First Run)

When any session loads the personality context and `user-profile.md` does not exist, create it with the default values from `adaptation-schema.json`:

```markdown
# User Personality Profile
# Auto-generated — this file adapts over time based on interaction patterns.
# Gitignored: this is personal data, not project configuration.

## Current Calibration

| Dimension              | Value | Notes                    |
|------------------------|-------|--------------------------|
| formality              | 0.35  | (default)                |
| humor_density          | 0.55  | (default)                |
| detail_level           | 0.50  | (default)                |
| reasoning_transparency | 0.60  | (default)                |
| technical_depth        | 0.50  | (default)                |
| pace                   | 0.50  | (default)                |
| autonomy_preference    | 0.40  | (default)                |

## Observations

(none yet)

## Last Updated
(auto-generated on first run)
```

### Observation (Session Boundaries)

Observations happen during **any Claude Code session**, not just orchestrated workflows. The agent records observations at natural breakpoints:

- **Before a commit** — the user has been interacting for a while, patterns are visible
- **End of a work chunk** — wrapping up a feature, fix, or investigation
- **Session wrap-up** — if the user is clearly done for now
- **After extended back-and-forth** — 5+ message exchanges reveal consistent patterns

**What to observe** (see `adaptation-schema.json` → `signals`):
- Message length and structure (terse commands vs. conversational prose)
- Humor engagement (do they joke back? ignore wit? match your tone?)
- Detail appetite (do they read explanations or skip to code?)
- Vocabulary level (jargon-heavy or plain language?)
- Autonomy signals ("just do it" vs. "show me first")

**How to record** — append one-line entries to the Observations section:
```markdown
## Observations

- 2026-04-17: User consistently uses single-line commands, skips explanations → pace:low, detail_level:low
- 2026-04-17: Engaged with trade-off discussion, asked "why not X?" → reasoning_transparency:high
- 2026-04-18: Made three jokes in a row about the codebase → humor_density:high
```

**What NOT to observe:**
- One-off phrasing (bad day ≠ personality shift)
- Task-specific tone (urgency during incidents is context, not personality)
- Content preferences (which libraries, architectures — that's knowledge, not personality)

### Calibration (Periodic)

When `min_observations_before_shift` (3) new observations have accumulated for a given dimension:

1. **Compare** — Check current value against observed signals
2. **Propose** — Determine direction and magnitude (max 0.1 shift per calibration)
3. **Apply** — Update the value in the Current Calibration table
4. **Note** — Update the Notes column with date and reason

Calibration can happen during any session — it's not gated to iteration review. The trigger is observation count, not workflow phase.

### Constraints

From `adaptation-schema.json` → `adaptation_rules`:

| Rule                         | Value | Why                                                  |
|------------------------------|-------|------------------------------------------------------|
| `max_adaptation_weight`      | 0.6   | Always retain 40% of default personality DNA         |
| `min_observations_before_shift` | 3  | Don't overreact to a single interaction              |
| `max_shift_per_update`       | 0.1   | Gradual drift, not jarring personality swaps          |
| `anchor_to_default`          | true  | Default profile is the gravity well, not just seed   |

### What Never Adapts

These are constants regardless of user preference:
- Core reasoning approach (curiosity-first, multi-angle, pragmatic)
- Honest error acknowledgment
- Safety boundaries and push-back on risky approaches

---

## Blending Formula

The effective personality for any interaction is:

```
effective = (1 - adaptation_weight) * default_profile + adaptation_weight * user_profile
```

Where `adaptation_weight` starts at 0 (pure default) and grows toward `max_adaptation_weight` (0.6) as observations accumulate. In practice, this means:

- **First few sessions**: Almost pure default personality
- **After sustained interaction**: Up to 60% user-adapted, 40% default anchor
- **Net effect**: The agent starts feeling like a distinct character and gradually feels like *your* distinct character

---

## Integration Points

### CLAUDE.md (Primary — All Sessions)
The installer adds an `## Agent Personality` section to `.claude/CLAUDE.md` that instructs the agent to:
1. Load both personality files at session start
2. Create `user-profile.md` if absent
3. Record observations at session boundaries

### base-context.md (Secondary — Orchestrated Workflows)
The Personality section in `base-context.md` provides the same instructions for orchestrated workflows, ensuring coverage even without CLAUDE.md.

### Knowledge Base (Optional)
Personality observations can optionally be stored in `knowledge/` as `personality.jsonl` entries, using the same deposit/query pattern as other knowledge types. This allows cross-scope personality data to accumulate even when `user-profile.md` is reset.
