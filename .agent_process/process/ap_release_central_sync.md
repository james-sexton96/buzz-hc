# Agent Process Central Repo Sync

This file configures syncing `.agent_process` changes to a central repository after releases.

The `/ap_release` workflow reads this file to determine sync behavior (see `orchestration/steps/release/07-09-commit-tag-push.md`).

---

## Configuration

```
ENABLED: false
CENTRAL_REPO_PATH: <not_configured>
PROJECT_FOLDER: <not_configured>
```

**Values:**
- `ENABLED: true` - Central repo sync is active
- `ENABLED: false` - Central repo sync is disabled (this project does not use central sync)

---

## How It Works

### When ENABLED: true

The `/ap_release` workflow will:

1. Navigate to `CENTRAL_REPO_PATH`
2. Check for changes in `PROJECT_FOLDER/` (subdirectory of central repo)
3. Commit and push any changes to the central repo
4. Return to the project directory

**Central repo structure:**
```
CENTRAL_REPO_PATH/
  PROJECT_FOLDER/
    ├── orchestration/
    ├── process/
    ├── work/
    └── ...
```

The project's `.agent_process/` symlinks directly to `CENTRAL_REPO_PATH/PROJECT_FOLDER/`.

### When ENABLED: false

The `/ap_release` workflow will skip all sync steps.

This project manages `.agent_process/` locally within the project repository.

---

## Setup

This file is created during installation:
- **Central sync enabled:** Set `ENABLED: true` and provide paths
- **Central sync disabled:** Set `ENABLED: false` (default for most projects)

### To enable central sync manually:

1. Set `ENABLED: true`
2. Replace `<not_configured>` with your central repo path (e.g., `~/repos/agent-process-central`)
3. Replace `<not_configured>` with this project's folder name in the central repo
4. Create symlink: `ln -s $CENTRAL_REPO_PATH/$PROJECT_FOLDER .agent_process`

### To disable central sync:

1. Set `ENABLED: false`
2. The other fields will be ignored

---

See `orchestration/steps/release/07-09-commit-tag-push.md` for the implementation.
