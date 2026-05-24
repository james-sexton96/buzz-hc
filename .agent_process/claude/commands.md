# Claude Code Commands

This framework provides slash commands that integrate with Claude Code. After installation, these commands are available in your project.

## Installation

The install script copies command files to `.claude/commands/` in your project. After installation, restart Claude Code (or reload commands) so the new shortcuts are available.

## Available Commands

### Requirements & Ideation

- **ap_brainstorm.md** – `/ap_brainstorm "idea"` – Multi-agent brainstorm that transforms a vague idea into a formal requirement.

  Spawns 3 parallel agents (Product, Architecture, Critical) to explore the idea, synthesizes output, optionally runs design review, and creates a requirement document.

- **ap_requirements.md** – `/ap_requirements <action> [details]` – Create, import, and list requirements.

  **Actions:**
  - `add "name"` – Create new requirement (offers brainstorm if metaswarm enabled)
  - `import "path" [--supersedes old_id]` – Import existing file as requirement
  - `brainstorm "idea"` – Redirects to `/ap_brainstorm`
  - `list [category]` – Show all requirements with status

### Project Management

- **ap_project.md** – `/ap_project <action> [details]` – Manages roadmap, backlog, and project status.

  **Actions:**
  - `init` – Initialize roadmap infrastructure
  - `discover` – Scan project and build/update roadmap
  - `status` – Show current project status summary
  - `add-todo "description"` – Add item to backlog
  - `set-status "req_id status reason"` – Manually set requirement status
  - `archive "req_id type reason"` – Archive a requirement
  - `archive-completed` – Bulk archive all approved work scopes
  - `sync` – Reconcile roadmap with actual work/ status
  - `report [type]` – Generate stakeholder report (executive/detailed/weekly)
  - `help` – Show detailed help

  **Deprecated:** `add-requirement` and `import-requirement` have moved to `/ap_requirements`.

### Iteration Workflow

- **ap_exec.md** – `/ap_exec <scope> <iteration>` – Executes implementation for a single iteration.

  **What it does:**
  1. Reads iteration plan and frozen criteria
  2. Selects appropriate specialized agent for the work
  3. Implements changes within scope boundaries
  4. Runs scoped validation (automatic via hook)
  5. Creates results artifacts via `/ap_iteration_results`
  6. Reports completion status

  **Examples:**
  ```
  /ap_exec user_auth iteration_01
  /ap_exec user_auth iteration_01_a
  ```

- **ap_iteration_results.md** – `/ap_iteration_results <scope> <iteration>` – Documents iteration results using `test-output.txt`.

### Release Workflow

- **ap_release.md** – `/ap_release [noscope] <mode> [version-type]` – Updates changelog, creates PR, and optionally tags a release.

  **Context Modes:**
  - Default: Reads from `.agent_process/work/` after orchestrator approval
  - `noscope`: Analyzes git diff for ad-hoc releases

  **Release Modes:**
  - `pr` – Add to [Unreleased] changelog, create PR, no version tag
  - `beta` – Move [Unreleased] to beta version, create beta tag (vX.Y.Z-beta.N), create PR
  - `release patch` – Patch release (1.0.0 → 1.0.1)
  - `release minor` – Minor release (1.0.0 → 1.1.0)
  - `release major` – Major release (1.0.0 → 2.0.0)

  **Examples:**
  ```
  /ap_release pr                    # Scope mode, PR only
  /ap_release noscope pr            # No-scope mode, PR only
  /ap_release release minor         # Scope mode, minor release
  /ap_release noscope release patch # No-scope mode, patch release
  ```

- **ap_changelog_init.md** – `/ap_changelog_init [starting-version]` – Initialize CHANGELOG.md from git history for projects not yet tracking releases.

  **What it does:**
  - Analyzes git tags and commit history
  - Creates historical summary grouped by era/milestone
  - Sets up [Unreleased] section for future `/ap_release` use
  - Links to full git history for transparency

## Command Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TYPICAL WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /ap_project init            # One-time: set up roadmap         │
│  /ap_project discover        # Optional: scan existing project  │
│                                                                 │
│  /ap_brainstorm "idea"       # Brainstorm → requirement         │
│    — or —                                                       │
│  /ap_requirements add "name" # Direct requirement creation      │
│                                                                 │
│  [Plan scope — orchestration/plan-scope.md]           │
│                                                                 │
│  /ap_exec feature iteration_01   # Execute implementation       │
│                                                                 │
│  [Review — orchestration/review-iteration.md]         │
│                                                                 │
│  bash .agent_process/scripts/evaluate-scope.sh ...  # Validate  │
│                                                                 │
│  /ap_release pr              # Create PR with changelog         │
│                                                                 │
│  /ap_project archive-completed   # Clean up approved work       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Customization

### Local Environment Instructions

For projects with unique workflow requirements (polyrepo, custom CI/CD, multi-step validation), customize command behavior in:

**File:** `.agent_process/process/local_environment_instructions.md`

Commands check this file for project-specific:
- Extended command arguments
- Multi-repository coordination
- Custom validation steps
- Environment-specific setup

This file is preserved across re-installations.

## See Also

- **README.md** – Full framework documentation
- **orchestration/context/base-context.md** – Quick onboarding for orchestration
- **process/validation-playbook.md** – Testing patterns
