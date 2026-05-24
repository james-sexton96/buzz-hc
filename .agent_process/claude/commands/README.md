# Claude Code Commands

**The actual command files are located in your project's `.claude/commands/` directory (note the dot prefix).**

This directory serves as a reference placeholder in the template structure.

## Quick Start

```bash
# Brainstorm an idea into a formal requirement
/ap_brainstorm "improve the login experience"

# Execute the planned iteration
/ap_exec user_auth iteration_01

# Ship it
/ap_release pr
```

## Available Commands

| Command | Invocation | Purpose |
|---------|------------|---------|
| `ap_brainstorm.md` | `/ap_brainstorm "idea"` | Multi-agent brainstorm → formal requirement |
| `ap_requirements.md` | `/ap_requirements <action>` | Create, import, and list requirements |
| `ap_project.md` | `/ap_project <action>` | Roadmap, backlog, and project management |
| `ap_exec.md` | `/ap_exec <scope> <iteration>` | Execute implementation iterations |
| `ap_release.md` | `/ap_release <mode>` | Changelog, PR creation, release tagging |
| `ap_iteration_results.md` | `/ap_iteration_results <scope> <iteration>` | Document iteration results |
| `ap_changelog_init.md` | `/ap_changelog_init` | Initialize CHANGELOG from git history |

## Command Reference

### Project Management

```bash
/ap_project init                    # Initialize roadmap
/ap_project discover                # Scan project and build roadmap
/ap_project status                  # Check project status
/ap_project add-todo "description"  # Add backlog item
/ap_project archive-completed       # Bulk archive approved work
/ap_project sync                    # Reconcile roadmap with work/
/ap_project report                  # Generate stakeholder report
```

### Requirements Management

```bash
/ap_brainstorm "idea"                # Multi-agent brainstorm → requirement
/ap_requirements add "name"          # Create requirement (offers brainstorm)
/ap_requirements import "file.md"    # Import existing file as requirement
/ap_requirements list                # Show all requirements
/ap_requirements list "category"     # Filter by category
```

### Iteration Workflow

```bash
/ap_exec scope_name iteration_01    # Execute iteration
/ap_exec scope_name iteration_01_a  # Execute sub-iteration (after ITERATE decision)
```

### Release Workflow

```bash
/ap_release pr                      # Create PR only
/ap_release pr --shepherd           # Create PR + monitor CI and reviews
/ap_release beta                    # Beta tag + PR
/ap_release release patch           # Patch release (1.0.0 → 1.0.1)
/ap_release release minor           # Minor release (1.0.0 → 1.1.0)
/ap_release release major           # Major release (1.0.0 → 2.0.0)
/ap_release noscope pr              # PR without scope context (git diff mode)
```

### Utilities

```bash
/ap_iteration_results scope iter    # Document iteration results manually
/ap_changelog_init                  # Initialize CHANGELOG from git history
```

## Dependencies

These commands require **Claude Code** as the execution environment and **GitHub CLI (`gh`)** for PR and issue tracking operations. Optional features like GitHub Issues tracking, metaswarm, and design review gates are controlled via `quality-config.json`.

## Documentation

For detailed usage of each command, see:
- Each `.md` file in `.claude/commands/` for the full command specification
- The project [README.md](../../README.md) for framework overview
- `process/quality-configuration.md` for feature toggle reference

## Customization

For projects with unique workflow requirements (polyrepo, custom CI/CD, etc.):

**File:** `.agent_process/process/local_environment_instructions.md`

Commands automatically check this file for:
- Extended command arguments
- Multi-repository coordination
- Custom validation steps
- Environment-specific setup

This file is preserved across re-installations.
