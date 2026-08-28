#!/usr/bin/env bash
# Claude Code PostToolUse hook — Unity .meta missing detection (advisory)
#
# After Edit/Write/MultiEdit on Unity asset files (.cs/.shader/.asset/.prefab/.mat/.controller),
# warns to stderr if the paired .meta file is missing.
#
# Why: Unity auto-generates .meta (GUID mapping) for new assets, but only when the
# Editor has window focus. If Claude creates a .cs while Unity is backgrounded, the
# .meta is generated *later*. A commit in that window pushes the asset without its
# .meta → GUID corruption on other machines.
#
# This hook is *advisory only* — does not auto-generate. Focus Unity Editor once
# to trigger .meta generation.
#
# Auto-opt-in: only runs in Unity projects (detected via Assets/ + ProjectSettings/).

set -e

# Auto-opt-in: skip if not a Unity project
if [ ! -d "Assets" ] || [ ! -d "ProjectSettings" ]; then
    exit 0
fi

# Read hook event JSON from stdin
input=$(cat)

# Extract tool_input.file_path (jq with grep fallback)
if command -v jq >/dev/null 2>&1; then
    file=$(echo "$input" | jq -r '.tool_input.file_path // empty')
else
    file=$(echo "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
fi

# Empty file_path = non-file tool, skip
[ -z "$file" ] && exit 0

# Only check Unity asset extensions
case "$file" in
    *.cs|*.shader|*.asset|*.prefab|*.mat|*.controller)
        meta="${file}.meta"
        if [ ! -f "$meta" ]; then
            base=$(basename "$file")
            echo "⚠️  Missing .meta: $base.meta" >&2
            echo "   → Focus Unity Editor → auto-generates. Verify 'git add ${file}.meta' before commit." >&2
        fi
        ;;
esac

exit 0
