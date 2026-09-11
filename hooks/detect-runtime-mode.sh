#!/bin/bash
# Hook: detect-runtime-mode.sh
# Event: SessionStart
# Purpose: Report which runtime is working this project, so the orchestrator knows
#          whether to run the full studio, stand down, or work a partition.
#          This studio ships twice — claude-code-studios (Claude Code, /skill-name)
#          and codex-code-studios (Codex, $skill-name) — and a project may be worked
#          by one alone or by both at once.
# Cross-platform: Windows Git Bash compatible.
#
# Output: prints a single RUNTIME_MODE line the orchestrator reads.
#         Format: RUNTIME_MODE=<claude|codex|split|invalid>
# Never fails the session.
#
# Source of truth: production/runtime.txt — line 1 is the mode; any further lines
# are the split-mode path partition and are echoed verbatim.
# Full rule: rules/runtime-modes.md
set +e

FILE="production/runtime.txt"
MODE=""
RAW=""

if [ -f "$FILE" ]; then
  # Line 1 only, stripped of whitespace and a UTF-8 BOM. Comparison is
  # case-insensitive so `Claude` does not read as a typo and stall the session.
  RAW="$(head -n 1 "$FILE" 2>/dev/null | tr -d '\r' | sed 's/^\xEF\xBB\xBF//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
  case "$RAW" in
    claude|codex|split) MODE="$RAW" ;;
    "")                 MODE="" ;;          # empty file — treat as absent
    *)                  MODE="invalid" ;;
  esac
fi

# Absent or empty means `claude`: this package IS the Claude Code studio, and a
# project that never declared a runtime is one this runtime is working alone.
[ -z "$MODE" ] && MODE="claude"

echo "=== Runtime Mode ==="
echo "RUNTIME_MODE=${MODE}"

case "$MODE" in
  claude)
    echo "→ Full studio. Orchestrate agents, run gates, own artifacts — unchanged behaviour." ;;
  codex)
    echo "→ STAND DOWN. codex-code-studios owns this project. Do NOT spawn studio agents, write studio artifacts, or run phase gates."
    echo "→ Still allowed: answering questions, and one-off edits the user explicitly asks for." ;;
  split)
    echo "→ PARTITIONED. Work only the paths this runtime owns; never write a path the other runtime owns."
    echo "→ Re-read every file before editing — the other runtime shares no session, context or tool log, so an overwrite is invisible to both."
    PARTITION="$(tail -n +2 "$FILE" 2>/dev/null | sed '/^[[:space:]]*$/d')"
    if [ -n "$PARTITION" ]; then
      echo "→ Declared partition:"
      printf '%s\n' "$PARTITION" | sed 's/^/     /'
    else
      echo "→ NO PARTITION DECLARED. Ask the user which paths this runtime owns and write them into ${FILE} before editing anything."
    fi ;;
  invalid)
    echo "→ ${FILE} line 1 reads '${RAW}', which is not one of: claude | codex | split."
    echo "→ Do NOT assume full-studio behaviour. Ask the user which runtime is working this project, then correct the file." ;;
esac

echo "→ Rule: rules/runtime-modes.md  ·  Independent of production/track.txt (what is being built vs. who is building it)"
echo "===================="

exit 0
