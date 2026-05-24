## GitHub Issue Context
- Issue: #10
- Repo: james-sexton96/buzz-hc
- Current Status: status:reviewing
- Scope: agent_pipeline_tdd_error_handling
- Iteration: iteration_01
- Suggested Branch: issue/10-agent_pipeline_tdd_error_handling

## Available Actions
- Update status: `bash .agent_process/scripts/github-issues-lifecycle.sh set-status agent_pipeline_tdd_error_handling <label>`
- Retitle issue: `bash .agent_process/scripts/github-issues-lifecycle.sh retitle agent_pipeline_tdd_error_handling "new title"`
- Sync issue body: `bash .agent_process/scripts/github-issues-lifecycle.sh sync-body agent_pipeline_tdd_error_handling`
- Set iteration: `bash .agent_process/scripts/github-issues-lifecycle.sh set-iteration agent_pipeline_tdd_error_handling iteration_01`
- Add note: `bash .agent_process/scripts/github-issues-lifecycle.sh comment agent_pipeline_tdd_error_handling "your message"`
- Create work unit: `bash .agent_process/scripts/github-issues-lifecycle.sh task-create agent_pipeline_tdd_error_handling WU-001 "description"`

## Rules
See process/github-issues-handling.md
