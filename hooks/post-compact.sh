#!/usr/bin/env bash
# Codex PostCompact hook: restore file-backed session context with valid JSON.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

ACTIVE="production/session-state/active.md"

build_message() {
  echo "=== Context Restored After Compaction ==="

  if [ -f "$ACTIVE" ]; then
    SIZE=$(wc -l < "$ACTIVE" 2>/dev/null || echo "?")
    echo "Session state file exists: $ACTIVE ($SIZE lines)"
    echo "IMPORTANT: Read this file now to restore your working context."
    echo "It contains: current task, decisions made, files in progress, open questions."
  else
    echo "No session state file found at $ACTIVE"
    echo "If you were mid-task, check production/session-logs/ for the last session audit."
  fi

  echo "========================================="
}

MESSAGE=$(build_message)
studio_emit_system_message "$MESSAGE"
