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

# <animator-ish receiver>.<Setter|Getter>("...") — first arg a literal string.
#
# 판단 축은 원래 수신자의 **타입**이 Animator 인가인데, bash 정규식은 타입을 모른다.
# 그래서 이름 휴리스틱을 쓴다 — 식별자에 `anim` 이 들어가면 Animator 로 본다.
# 이전 패턴은 수신자를 `animator` 로 못박아 뒀고 앞의 `\b` 때문에 밑줄·접두사가
# 붙은 이름에는 경계가 생기지 않아, 실제 프로젝트가 쓰는 5변형 중 1개만 잡았다
# (`_anim` · `_animator` · `playerAnimator` · `playerAnim` 이 전부 통과했다).
#
# 넓히면 오탐이 따라오므로 두 가지로 막는다:
#   - 첫 인자가 `"_` 로 시작하면 제외 = 셰이더 프로퍼티 관례.
#     `animMaterial.SetFloat("_BaseColor")` 같은 Material 호출을 살려준다.
#   - 수신자에 `anim` 이 없으면 애초에 안 잡힌다.
#     `EditorPrefs.SetBool(...)`, `serializedObject.SetBool("m_...")` 가 여기 해당.
#
# `GetComponent<Animator>()` 는 이름이 아니라 타입이 그 자리에 드러난 형태라
# 오탐 여지가 없어 함께 잡는다. 해시 접근(`SetBool(hash, ...)`)과 권장 해법인
# `Animator.StringToHash("...")` 는 따옴표·메서드가 달라 걸리지 않는다.
ANIM_STR_PAT='(\b[A-Za-z0-9_]*[Aa]nim[A-Za-z0-9_]*|GetComponent<Animator>\(\))\.(SetBool|SetInteger|SetFloat|SetTrigger|ResetTrigger|GetBool|GetInteger|GetFloat)\("[^_"]'
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
