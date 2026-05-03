#!/usr/bin/env bash
# Claude Code PostToolUse hook — Unity Animator string-access lint (advisory)
#
# After Edit/Write/MultiEdit on .cs files, scans for direct string access to
# Animator parameters (SetBool/SetFloat/SetTrigger/etc with "literal-string" first arg).
#
# Why: Animator string lookups perform a per-frame string-to-hash search internally.
# Best practice — cache via Animator.StringToHash in Start/Awake, then pass the
# cached int to SetBool/SetFloat/etc.
#
# Reference: Unity Manual — Animation Best Practices
# https://docs.unity3d.com/Manual/AnimationBestPractices.html
#
# This hook is *advisory only* (exit 0). Findings printed to stderr.
#
# Auto-opt-in: only runs in Unity projects (Assets/ + ProjectSettings/ detected).

set -e

# Auto-opt-in: skip if not a Unity project
if [ ! -d "Assets" ] || [ ! -d "ProjectSettings" ]; then
    exit 0
fi

input=$(cat)

if command -v jq >/dev/null 2>&1; then
    file=$(echo "$input" | jq -r '.tool_input.file_path // empty')
else
    file=$(echo "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
fi

[ -z "$file" ] && exit 0

# .cs only
case "$file" in
    *.cs) ;;
    *) exit 0 ;;
esac

# File missing (deleted / Editor closed) — skip
[ ! -f "$file" ] && exit 0

# grep tool
if command -v rg >/dev/null 2>&1; then
    GREPCMD="rg -n --no-heading"
else
    GREPCMD="grep -nE"
fi

# Animator.<Setter|Getter>("...") — first arg literal string
ANIM_STR_PAT='\b[Aa]nimator\.(SetBool|SetInteger|SetFloat|SetTrigger|ResetTrigger|GetBool|GetInteger|GetFloat)\("'
findings=$($GREPCMD "$ANIM_STR_PAT" "$file" 2>/dev/null || true)

if [ -n "$findings" ]; then
    base=$(basename "$file")
    echo "" >&2
    echo "─── unity-animator-string-lint: $base ───" >&2
    echo "⚠️  Animator string-access detected:" >&2
    echo "$findings" | sed 's/^/   /' >&2
    echo "   → Cache hash via Animator.StringToHash in Start/Awake." >&2
    echo "" >&2
fi

exit 0
