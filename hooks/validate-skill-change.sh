#!/usr/bin/env bash
# Codex PostToolUse hook: remind the agent to validate changed plugin skills.

set +e
INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

PATHS=$(studio_extract_changed_paths "$INPUT")
[ -n "$PATHS" ] || exit 0

SKILLS=$(printf '%s\n' "$PATHS" \
    | sed -nE 's#(^|.*/)skills/([^/]+)/SKILL\.md$#\2#p' \
    | awk 'NF && !seen[$0]++')

[ -n "$SKILLS" ] || exit 0

NAMES=$(printf '%s' "$SKILLS" | tr '\n' ' ' | sed 's/[[:space:]]*$//')
studio_emit_additional_context "Code Studios skill modified: $NAMES. Run \\$skill-test static for each changed skill and validate its SKILL.md with the Codex skill validator."

exit 0
