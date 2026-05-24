# GitHub Issue Body Template
#
# This template is used when creating GitHub issues for scopes, work units, and splits.
# Projects can override this by creating templates/overrides/github-issue-body.md
#
# Available variables (set by render_issue_body):
#   ${DESCRIPTION}         - Required. What this issue is about.
#   ${PARENT_SECTION}      - Optional. Parent issue reference and relationship.
#   ${REQUIREMENT_SECTION} - Optional. Link to requirement doc if available.
#
# The script builds PARENT_SECTION and REQUIREMENT_SECTION as complete markdown blocks
# (or empty strings if not applicable), so no conditionals needed here.

## Description

${DESCRIPTION}
${PARENT_SECTION}
${REQUIREMENT_SECTION}
