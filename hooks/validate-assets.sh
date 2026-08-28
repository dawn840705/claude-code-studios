#!/usr/bin/env bash
# Codex PostToolUse hook: validate changed asset files after apply_patch/edit tools.

set +e

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/lib/hook-io.sh" ]; then
    # shellcheck source=lib/hook-io.sh
    . "$SCRIPT_DIR/lib/hook-io.sh"
else
    exit 0
fi

if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
    # shellcheck source=lib/detect-layout.sh
    . "$SCRIPT_DIR/lib/detect-layout.sh"
else
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

PATHS=$(studio_extract_changed_paths "$INPUT")
[ -n "$PATHS" ] || exit 0

ASSET_RE=$(studio_asset_root_regex)
WARNINGS=""
ERRORS=""

while IFS= read -r FILE_PATH; do
    [ -n "$FILE_PATH" ] || continue
    printf '%s' "$FILE_PATH" | grep -qE "$ASSET_RE" || continue

    case "$FILE_PATH" in
        *.meta) continue ;;
    esac

    FILENAME=$(basename "$FILE_PATH")
    NAMING_REASON=$(studio_naming_violation "$FILENAME")
    if [ -n "$NAMING_REASON" ]; then
        WARNINGS="$WARNINGS
NAMING [$STUDIO_ASSET_NAMING]: $FILE_PATH $NAMING_REASON (got: $FILENAME)"
    fi

    if printf '%s' "$FILE_PATH" | grep -qE '(((^|/)assets/data/)|'"$ASSET_RE"').*\.json$' \
        && [ -f "$FILE_PATH" ]; then
        PYTHON_CMD=""
        for cmd in python3 python py; do
            if command -v "$cmd" >/dev/null 2>&1; then
                PYTHON_CMD="$cmd"
                break
            fi
        done
        if [ -n "$PYTHON_CMD" ] && ! "$PYTHON_CMD" -m json.tool "$FILE_PATH" >/dev/null 2>&1; then
            ERRORS="$ERRORS
FORMAT: $FILE_PATH is not valid JSON — fix syntax errors before continuing"
        fi
    fi
done <<< "$PATHS"

if [ -n "$ERRORS" ]; then
    printf 'Asset validation failed:%s\n' "$ERRORS" >&2
    exit 2
fi

if [ -n "$WARNINGS" ]; then
    studio_emit_additional_context "Asset validation warnings:$WARNINGS
These are advisory; fix them before the final commit."
fi

exit 0
