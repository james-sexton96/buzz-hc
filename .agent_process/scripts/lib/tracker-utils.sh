#!/usr/bin/env bash
# tracker-utils.sh — Scope state management for AI Agent Process
#
# Source this from any script that needs to manage scope state:
#   source "$(dirname "$0")/lib/tracker-utils.sh"
#
# Low-level functions:
#   tracker_read_scope  <scope>          → prints the JSON line for <scope>
#   tracker_write_scope <scope> <json>   → atomic upsert of <scope> in tracker
#   tracker_get_field   <scope> <field>  → prints a single field value
#   events_log          <scope> <type> [key=val ...]  → appends to scope-events.log
#
# High-level scope operations (GitHub-independent):
#   scope_start         <scope>          → initialize/adopt scope, set as current
#   scope_set_status    <scope> <status> → update status in tracker
#   scope_set_iteration <scope> <iter>   → update iteration, set as current
#   scope_close         <scope> <decision> → mark scope closed
#   set_current_scope   <scope> <iter>   → update current_iteration.conf
#   get_current_scope                    → read current scope/iteration
#
# Designed for bash 3.2+ (macOS) and bash 5+.
# jq is preferred but we degrade gracefully to grep+sed when it's missing.

# --- Configuration ---

# Where the tracker lives — override TRACKER_FILE to test against a temp path
TRACKER_FILE="${TRACKER_FILE:-.agent_process/work/scope-tracker.jsonl}"

# Where scope event logs live — override EVENTS_DIR for testing
EVENTS_DIR="${EVENTS_DIR:-.agent_process/work}"

# --- Internal helpers ---

_has_jq() {
  command -v jq &>/dev/null
}

# ISO-8601 timestamp, UTC. Works on both GNU date and BSD date (macOS).
_timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "1970-01-01T00:00:00Z"; }

# --- Public API ---

# tracker_read_scope <scope>
#   Prints the JSON line for the given scope, or nothing if not found.
tracker_read_scope() {
  local scope="$1"
  if [[ -z "$scope" ]]; then
    echo "tracker_read_scope: scope argument required" >&2
    return 1
  fi
  if [[ ! -f "$TRACKER_FILE" ]]; then
    return 0  # no file, no scope — not an error
  fi

  if _has_jq; then
    # Note: jq processes line-by-line so select can match multiple lines
    # if the file has duplicates. head -1 ensures we return only one.
    jq -c --arg s "$scope" 'select(.scope==$s)' "$TRACKER_FILE" 2>/dev/null | head -1
  else
    # Fallback: grep for the scope name, anchored to prevent prefix collisions
    grep "\"scope\":\"${scope}\"[,}]" "$TRACKER_FILE" 2>/dev/null | head -1
  fi
}

# tracker_write_scope <scope> <json>
#   Atomic upsert: replaces the line for <scope> or appends if new.
#   Uses temp-file + mv to prevent corruption.
tracker_write_scope() {
  local scope="$1"
  local json="$2"
  if [[ -z "$scope" || -z "$json" ]]; then
    echo "tracker_write_scope: scope and json arguments required" >&2
    return 1
  fi

  local dir
  dir="$(dirname "$TRACKER_FILE")"
  mkdir -p "$dir"

  # Use unique tmp file per process to prevent race conditions when
  # multiple subagents call tracker_write_scope concurrently.
  # The old shared .tmp path caused massive duplication when agents ran in parallel.
  local tmp_file="${TRACKER_FILE}.tmp.$$"
  local found=false

  # If the tracker file exists, copy all lines except the one we're replacing
  if [[ -f "$TRACKER_FILE" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      # Check if this line is for our scope
      local line_scope=""
      if _has_jq; then
        line_scope=$(echo "$line" | jq -r '.scope' 2>/dev/null)
      else
        # sed to extract scope value — handles the common JSON shape
        line_scope=$(echo "$line" | sed -n 's/.*"scope":"\([^"]*\)".*/\1/p')
      fi

      if [[ "$line_scope" == "$scope" ]]; then
        echo "$json" >> "$tmp_file"
        found=true
      else
        echo "$line" >> "$tmp_file"
      fi
    done < "$TRACKER_FILE"
  fi

  # New scope — append
  if [[ "$found" == false ]]; then
    echo "$json" >> "$tmp_file"
  fi

  # Atomic rename — the whole point of this dance
  # If mv fails, clean up tmp file
  if ! mv "$tmp_file" "$TRACKER_FILE"; then
    rm -f "$tmp_file"
    return 1
  fi
}

# tracker_get_field <scope> <field>
#   Convenience: prints a single top-level field value from the scope's JSON.
tracker_get_field() {
  local scope="$1"
  local field="$2"
  if [[ -z "$scope" || -z "$field" ]]; then
    echo "tracker_get_field: scope and field arguments required" >&2
    return 1
  fi

  local line
  line=$(tracker_read_scope "$scope")
  [[ -z "$line" ]] && return 0

  if _has_jq; then
    echo "$line" | jq -r --arg f "$field" '.[$f] // empty' 2>/dev/null
  else
    # Best-effort extraction for simple string fields.
    # Nested objects? You really want jq for that.
    echo "$line" | sed -n "s/.*\"${field}\":\"\([^\"]*\)\".*/\1/p"
  fi
}

# set_current_scope <scope> <iteration>
#   Updates .agent_process/work/current_iteration.conf with the active scope.
#   This file is read by hooks and other scripts to know what's being worked on.
set_current_scope() {
  local scope="$1"
  local iteration="${2:-iteration_01}"

  if [[ -z "$scope" ]]; then
    echo "set_current_scope: scope argument required" >&2
    return 1
  fi

  local conf_file="${EVENTS_DIR}/current_iteration.conf"
  mkdir -p "$(dirname "$conf_file")"

  cat > "$conf_file" << EOF
SCOPE=$scope
ITERATION=$iteration
EOF
}

# get_current_scope
#   Reads current scope from current_iteration.conf. Returns "scope iteration" or empty.
get_current_scope() {
  local conf_file="${EVENTS_DIR}/current_iteration.conf"
  if [[ -f "$conf_file" ]]; then
    local scope iteration
    scope=$(grep "^SCOPE=" "$conf_file" 2>/dev/null | cut -d'=' -f2)
    iteration=$(grep "^ITERATION=" "$conf_file" 2>/dev/null | cut -d'=' -f2)
    echo "$scope $iteration"
  fi
}

# --- High-level scope operations ---
# These functions manage scope state in the tracker, independent of GitHub.

# scope_start <scope>
#   Initializes or adopts a scope in the tracker. Sets it as current.
#   Returns the current iteration for this scope.
scope_start() {
  local scope="$1"
  if [[ -z "$scope" ]]; then
    echo "scope_start: scope argument required" >&2
    return 1
  fi

  local ts
  ts=$(_timestamp)

  local existing
  existing=$(tracker_read_scope "$scope")

  local iteration="iteration_01"
  if [[ -z "$existing" ]]; then
    # New scope — create tracker entry
    if _has_jq; then
      tracker_write_scope "$scope" "$(jq -n -c \
        --arg s "$scope" \
        --arg t "$ts" \
        --arg st "active" \
        '{scope: $s, status: $st, created: $t, iteration: "iteration_01"}')"
    else
      tracker_write_scope "$scope" "{\"scope\":\"$scope\",\"status\":\"active\",\"created\":\"$ts\",\"iteration\":\"iteration_01\"}"
    fi
    events_log "$scope" "SCOPE_START" "action=start"
  else
    # Existing scope — get current iteration
    iteration=$(tracker_get_field "$scope" "iteration")
    iteration="${iteration:-iteration_01}"
    events_log "$scope" "SCOPE_ADOPT" "action=adopt"
  fi

  # Set as current working scope
  set_current_scope "$scope" "$iteration"

  echo "$iteration"
}

# scope_set_status <scope> <status>
#   Updates the status field in the tracker.
#   Status should be the short name (e.g., "executing" not "status:executing").
scope_set_status() {
  local scope="$1"
  local status="$2"
  if [[ -z "$scope" || -z "$status" ]]; then
    echo "scope_set_status: scope and status arguments required" >&2
    return 1
  fi

  # Strip "status:" prefix if present
  status="${status#status:}"

  local current
  current=$(tracker_read_scope "$scope")
  if [[ -z "$current" ]]; then
    echo "scope_set_status: scope '$scope' not found in tracker" >&2
    return 1
  fi

  if _has_jq; then
    tracker_write_scope "$scope" "$(echo "$current" | jq -c --arg st "$status" '. + {status: $st}')"
  else
    # sed fallback
    local updated
    updated=$(echo "$current" | sed "s/\"status\":\"[^\"]*\"/\"status\":\"$status\"/")
    tracker_write_scope "$scope" "$updated"
  fi

  events_log "$scope" "COMMENT" "message=status-change:status:$status"
}

# scope_set_iteration <scope> <iteration>
#   Updates the iteration field in the tracker and current_iteration.conf.
scope_set_iteration() {
  local scope="$1"
  local iteration="$2"
  if [[ -z "$scope" || -z "$iteration" ]]; then
    echo "scope_set_iteration: scope and iteration arguments required" >&2
    return 1
  fi

  local current
  current=$(tracker_read_scope "$scope")
  if [[ -z "$current" ]]; then
    echo "scope_set_iteration: scope '$scope' not found in tracker" >&2
    return 1
  fi

  if _has_jq; then
    tracker_write_scope "$scope" "$(echo "$current" | jq -c --arg i "$iteration" '. + {iteration: $i}')"
  else
    local updated
    updated=$(echo "$current" | sed "s/\"iteration\":\"[^\"]*\"/\"iteration\":\"$iteration\"/")
    tracker_write_scope "$scope" "$updated"
  fi

  set_current_scope "$scope" "$iteration"
  events_log "$scope" "ITERATION_START" "iteration=$iteration"
}

# scope_close <scope> <decision>
#   Marks a scope as closed with a decision (approved, blocked, etc.)
#   Sets status to "closed" and records the decision.
scope_close() {
  local scope="$1"
  local decision="${2:-approved}"
  if [[ -z "$scope" ]]; then
    echo "scope_close: scope argument required" >&2
    return 1
  fi

  local current
  current=$(tracker_read_scope "$scope")
  if [[ -z "$current" ]]; then
    echo "scope_close: scope '$scope' not found in tracker" >&2
    return 1
  fi

  if _has_jq; then
    tracker_write_scope "$scope" "$(echo "$current" | jq -c --arg d "$decision" '. + {status: "closed", decision: $d}')"
  else
    # sed fallback - just update status
    local updated
    updated=$(echo "$current" | sed "s/\"status\":\"[^\"]*\"/\"status\":\"closed\"/")
    tracker_write_scope "$scope" "$updated"
  fi

  events_log "$scope" "SCOPE_CLOSE" "decision=$decision"
}

# events_log <scope> <event_type> [key=value ...]
#   Appends one event line to the scope's scope-events.log.
#
#   Example:
#     events_log auth_middleware_01 SCOPE_START iteration=iteration_01
#
#   Produces:
#     2026-04-01T10:00:00Z SCOPE_START scope=auth_middleware_01 iteration=iteration_01
events_log() {
  local scope="$1"
  local event_type="$2"
  shift 2

  if [[ -z "$scope" || -z "$event_type" ]]; then
    echo "events_log: scope and event_type arguments required" >&2
    return 1
  fi

  # Validate event type — reject typos early
  local valid_types="SCOPE_START SCOPE_ADOPT SCOPE_ASSOCIATE SCOPE_SPLIT ITERATION_START ITERATION_CLOSE WU_CREATE WU_UPDATE SCOPE_CLOSE COMMENT ERROR"
  local type_ok=false
  for vt in $valid_types; do
    if [[ "$event_type" == "$vt" ]]; then
      type_ok=true
      break
    fi
  done
  if [[ "$type_ok" == false ]]; then
    echo "events_log: invalid event type '${event_type}'" >&2
    echo "  valid types: ${valid_types}" >&2
    return 1
  fi

  local scope_dir="${EVENTS_DIR}/${scope}"
  mkdir -p "$scope_dir"

  local log_file="${scope_dir}/scope-events.log"
  local ts
  ts=$(_timestamp)

  # Build the event line: timestamp + type + scope=X + any extra k=v pairs
  local event_line="${ts} ${event_type} scope=${scope}"
  for kv in "$@"; do
    event_line="${event_line} ${kv}"
  done

  echo "$event_line" >> "$log_file"
}
