#!/usr/bin/env bash
# Codex PostToolUse hook: advise when changed Unity assets lack .meta sidecars.

set +e
[ -d "Assets" ] && [ -d "ProjectSettings" ] || exit 0

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/hook-io.sh" ] || exit 0
# shellcheck source=lib/hook-io.sh
. "$SCRIPT_DIR/lib/hook-io.sh"

PATHS=$(studio_extract_changed_paths "$INPUT")
WARNINGS=""

while IFS= read -r FILE_PATH; do
    case "$FILE_PATH" in
        *.cs|*.shader|*.asset|*.prefab|*.mat|*.controller)
            if [ -f "$FILE_PATH" ] && [ ! -f "${FILE_PATH}.meta" ]; then
                WARNINGS="$WARNINGS
Missing Unity sidecar: ${FILE_PATH}.meta — focus Unity Editor to generate it, then include it in the commit."
            fi
            ;;
    esac
done <<< "$PATHS"

[ -n "$WARNINGS" ] && studio_emit_additional_context "$WARNINGS"
exit 0
