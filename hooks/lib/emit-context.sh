#!/usr/bin/env bash
# Hand a PostToolUse hook's advisory to the model, not just the terminal.
#
# WHY THIS FILE EXISTS
#   On exit 0 a PostToolUse hook's stdout goes to the debug log and its stderr
#   goes nowhere the model can see (code.claude.com/docs/en/hooks). The
#   advisory hooks here used to print to stderr and exit 0, so in a session no
#   one was watching, the model never learned that a .meta was missing or that
#   an Animator call used a string — it went straight on to the next edit.
#   Exit 2 would reach the model but reads as a failure for what is only
#   advice. The documented channel for advice is
#   {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}.
#
# USAGE
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   [ -f "$SCRIPT_DIR/lib/emit-context.sh" ] && . "$SCRIPT_DIR/lib/emit-context.sh"
#   studio_emit_context "unity-meta-check: Foo.cs.meta missing — focus Unity before commit"
#
# CONTRACT
#   Keep the message to one short line. It is injected on every matching edit,
#   so a full report costs tokens on every write; name the file and the fix and
#   stop. Call at most once per hook run — two JSON objects on stdout are not a
#   valid hook response. The full human-readable report can still go to stderr.
#
# Fallback when the helper is missing: callers define nothing and the advice
# goes to stderr only, as it did before.

# studio__json_escape <text> — JSON string body (no surrounding quotes).
studio__json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/\r//g' \
        | awk 'NR > 1 { printf "\\n" } { printf "%s", $0 }'
}

# studio_emit_context <one-line message>
studio_emit_context() {
    [ -n "$1" ] || return 0
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' \
        "$(studio__json_escape "$1")"
}
