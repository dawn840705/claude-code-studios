#!/bin/bash
# Claude Code PostToolUse hook: Validates asset files after Write/Edit/MultiEdit
# Checks naming conventions for files under the project's asset root(s)
#
# Exit behavior:
#   exit 0 = success or advisory warnings only (non-blocking)
#   exit 1 = blocking error (build-breaking issues: invalid JSON, missing required fields)
#
# Input schema (PostToolUse for Write/Edit/MultiEdit):
# { "tool_name": "Write", "tool_input": { "file_path": "assets/data/foo.json", "content": "..." } }
#
# Layout-aware since v0.6.2. Two bugs were hiding each other here: the path
# filter only matched lowercase assets/, so Unity's Assets/ never reached the
# checks — and the naming rule hardcoded lowercase_with_underscores, which
# Unity cannot satisfy (a C# file name must match its class name, so
# PlayerController.cs is correct, not a violation). Fixing the path alone would
# have fired a naming warning on essentially every Unity file. The convention
# is now per-engine: pascal for Unity/Unreal, snake elsewhere.

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
    # shellcheck source=lib/detect-layout.sh
    . "$SCRIPT_DIR/lib/detect-layout.sh"
else
    # Degraded fallback: the pre-v0.6.2 hardcoded web layout.
    STUDIO_ENGINE="generic"
    STUDIO_ASSET_NAMING="snake"
    studio_asset_root_regex() { printf '(^|/)(assets)/'; }
    studio_naming_violation() {
        if printf '%s' "$1" | grep -qE '[A-Z[:space:]-]'; then
            printf 'must be lowercase with underscores'
            return 0
        fi
        return 1
    }
fi

# Parse file path -- use jq if available, fall back to grep
if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
else
    FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# Empty file_path = non-file tool, skip
[ -z "$FILE_PATH" ] && exit 0

# Normalize path separators (Windows backslash to forward slash)
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Only check files under an asset root (Assets/ on Unity, Content/ on Unreal,
# assets/ on web). Case-sensitive: the case IS the convention signal.
ASSET_RE=$(studio_asset_root_regex)
if ! echo "$FILE_PATH" | grep -qE "$ASSET_RE"; then
    exit 0
fi

FILENAME=$(basename "$FILE_PATH")
WARNINGS=""   # Style/convention issues -- exit 0 with advisory message
ERRORS=""     # Build-breaking issues -- exit 1 to block the operation

# Unity generates .meta sidecars itself; their names mirror the asset they
# describe, so judging them separately would double every warning.
case "$FILE_PATH" in
    *.meta) exit 0 ;;
esac

# ADVISORY: Check naming convention for the detected engine.
# Naming issues are style violations -- warn but do not block.
# Uses grep -E (POSIX) not grep -P (Perl) for Windows Git Bash compatibility.
NAMING_REASON=$(studio_naming_violation "$FILENAME")
if [ -n "$NAMING_REASON" ]; then
    WARNINGS="$WARNINGS\n  NAMING [$STUDIO_ASSET_NAMING]: $FILE_PATH $NAMING_REASON (got: $FILENAME)"
fi

# BLOCKING: Check JSON validity for data files
# Invalid JSON will break runtime loading -- this is a build-breaking error
if echo "$FILE_PATH" | grep -qE '(((^|/)assets/data/)|'"$ASSET_RE"').*\.json$'; then
    if [ -f "$FILE_PATH" ]; then
        # Find a working Python command
        PYTHON_CMD=""
        for cmd in python python3 py; do
            if command -v "$cmd" >/dev/null 2>&1; then
                PYTHON_CMD="$cmd"
                break
            fi
        done

        if [ -n "$PYTHON_CMD" ]; then
            if ! "$PYTHON_CMD" -m json.tool "$FILE_PATH" > /dev/null 2>&1; then
                ERRORS="$ERRORS\n  FORMAT: $FILE_PATH is not valid JSON — fix syntax errors before continuing"
            fi
        fi
    fi
fi

# Report warnings (advisory -- non-blocking)
if [ -n "$WARNINGS" ]; then
    echo -e "=== Asset Validation: Warnings ===$WARNINGS\n==================================\n(Warnings are advisory. Fix before final commit.)" >&2
fi

# Report errors and block if any build-breaking issues found
if [ -n "$ERRORS" ]; then
    echo -e "=== Asset Validation: ERRORS (Blocking) ===$ERRORS\n===========================================\nFix these errors before proceeding." >&2
    exit 1
fi

exit 0
