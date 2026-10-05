#!/bin/bash
# Claude Code SessionStart hook: Load project context at session start
# Outputs context information that Claude sees when a session begins
#
# Input schema (SessionStart): No stdin input

echo "=== Claude Code Game Studios — Session Context ==="

# Current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -n "$BRANCH" ]; then
    echo "Branch: $BRANCH"

    # Recent commits
    echo ""
    echo "Recent commits:"
    git log --oneline -5 2>/dev/null | while read -r line; do
        echo "  $line"
    done
fi

# Current sprint (find most recent sprint file)
LATEST_SPRINT=$(ls -t production/sprints/sprint-*.md 2>/dev/null | head -1)
if [ -n "$LATEST_SPRINT" ]; then
    echo ""
    echo "Active sprint: $(basename "$LATEST_SPRINT" .md)"
fi

# Current milestone
LATEST_MILESTONE=$(ls -t production/milestones/*.md 2>/dev/null | head -1)
if [ -n "$LATEST_MILESTONE" ]; then
    echo "Active milestone: $(basename "$LATEST_MILESTONE" .md)"
fi

# Open bug count
BUG_COUNT=0
for dir in tests/playtest production; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "BUG-*.md" 2>/dev/null | wc -l)
        BUG_COUNT=$((BUG_COUNT + count))
    fi
done
if [ "$BUG_COUNT" -gt 0 ]; then
    echo "Open bugs: $BUG_COUNT"
fi

# Code health quick check
if [ -d "src" ]; then
    TODO_COUNT=$(grep -r "TODO" src/ 2>/dev/null | wc -l)
    FIXME_COUNT=$(grep -r "FIXME" src/ 2>/dev/null | wc -l)
    if [ "$TODO_COUNT" -gt 0 ] || [ "$FIXME_COUNT" -gt 0 ]; then
        echo ""
        echo "Code health: ${TODO_COUNT} TODOs, ${FIXME_COUNT} FIXMEs in src/"
    fi
fi

# --- Human action queue (things only a person can do) ---
# Announce existence only. The file is a round-trip: a person may have written a
# result into it since the last session, and that result is usually the first
# task of this one. Silent when the file does not exist.
HUMAN_ACTIONS="production/human-actions.md"
if [ -f "$HUMAN_ACTIONS" ]; then
    echo ""
    echo "=== HUMAN ACTION QUEUE PRESENT ==="
    echo "File: $HUMAN_ACTIONS"
    echo "Read it before starting work. If a person has answered an item since the"
    echo "last session, that answer is this session's first task. Do not re-ask for"
    echo "something already recorded as done."
    echo "Rule: rules/work-records.md section 2"
fi

# --- Active session state recovery ---
STATE_FILE="production/session-state/active.md"
if [ -f "$STATE_FILE" ]; then
    echo ""
    echo "=== ACTIVE SESSION STATE DETECTED ==="
    echo "A previous session left state at: $STATE_FILE"
    echo "Read this file to recover context and continue where you left off."
    echo ""
    echo "Quick summary:"
    head -20 "$STATE_FILE" 2>/dev/null
    TOTAL_LINES=$(wc -l < "$STATE_FILE" 2>/dev/null)
    if [ "$TOTAL_LINES" -gt 20 ]; then
        echo "  ... ($TOTAL_LINES total lines — read the full file to continue)"
    fi
    echo "=== END SESSION STATE PREVIEW ==="
fi


# --- Self-loop quality rule (applies to every project using this plugin) ---
echo ""
echo "=== Self-Loop Rule (always active) ==="
echo "Deliverables with clear quality criteria are NOT one-shot. Iterate:"
echo "  plan -> execute -> score each criterion 1-10 (strict, evidence-cited) -> all >=8 ? done : fix lowest first"
echo "Guards: scores of 8+ require quoted evidence | max 5 iterations | stop+report after 2 stalled rounds."
echo "Full protocol: rules/self-loop.md in this plugin. Explicit run: /self-loop"
echo "Scoring order: if a script can decide a criterion, its EXIT CODE sets the score — not your judgment."

# --- Route hint (call-count routing; applies to every project) ---
echo ""
echo "=== Route Hint (always active) ==="
echo "Pick a route BEFORE spawning: light = handle it yourself (0 agents) | standard = 1 specialist | heavy = fan-out + gates"
echo "Savings come from FEWER CALLS, not a cheaper model. Splitting is the last resort — measured: 7 chunks 610K tok vs 134K single call, equal quality."
echo "Tied between two routes? Take the lighter one. Full rule: rules/route-hint.md"

# --- The other global rules, one line each ---
# Plugin rules/ files are not loaded by the host; only what this hook prints
# reaches the model. Until 2026-10 these five were listed as "always active" in
# docs/rules-reference.md while no session ever saw them (inbox 2026-09-19).
# Each line is "when, then what" — the file holds the why. Keep them short:
# this output is paid for on every session.
echo ""
echo "=== Global Rules (always active — read the file when the trigger fires) ==="
echo "verify-route: route CHECKING by reversibility — R1 file gate | R2 gates+review | R3 + separate reviewing subagent | R4 irreversible = never unattended. rules/verify-route.md"
echo "decision-lifecycle: a pinned decision in CLAUDE.md is not reopened — report contrary evidence and stop; pins need evidence + revisit trigger. A '## 결정 권한' section in the project CLAUDE.md delegates other calls to agents (opt-in, § 4.1). rules/decision-lifecycle.md"
echo "claim-confidence: mark numbers/statutes/prices/competitor facts as sourced, (추정) + basis, or [확인 필요]; never write them from memory. rules/claim-confidence.md"
echo "subagent-collaboration: fan out only for 4+ disciplines; assign file ownership before spawning — two agents never get the same file. rules/subagent-collaboration.md"
echo "work-records: one fact, one home (commit / session state / minutes / lesson / ADR); things only a person can do go to production/human-actions.md. rules/work-records.md"

# --- Skill listing budget ---
# The host lists skill names + descriptions under a budget. Reported default:
# 1% of context (StarDiver, 2026-09-19 — not in the host docs as of 2026-10).
# At ~24K characters this plugin's 90 descriptions overflow it, and the skills
# past the cut-off lose their description and stop auto-triggering, with no
# warning anywhere. That cut hit every team-* orchestrator for a month.
if ! grep -qs '"skillListingBudgetFraction"' .claude/settings.json .claude/settings.local.json \
        "$HOME/.claude/settings.json" 2>/dev/null; then
    PLUGIN_SKILLS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/skills"
    DESC_CHARS=$(awk '/^description:/ { n += length($0) - 13 } END { print n + 0 }' \
                     "$PLUGIN_SKILLS"/*/SKILL.md 2>/dev/null)
    echo ""
    echo "=== Skill listing budget ==="
    echo "WARNING: no skillListingBudgetFraction set; this plugin's skill descriptions total ~${DESC_CHARS} chars."
    echo "At the default budget, skills late in the alphabet (team-*, start, sprint-*, story-*) have been seen listed by name only — they will not auto-trigger."
    echo "Fix: add \"skillListingBudgetFraction\": 0.05 to .claude/settings.json (README § Install). Tell the user once; do not edit settings yourself."
fi

# --- Lesson Ledger (교육용 노하우 원장) ---
LESSON_DIR="Documents/Lessons"
if [ -d "$LESSON_DIR" ]; then
    LESSON_COUNT=$(find "$LESSON_DIR" -name "LES-*.md" 2>/dev/null | wc -l)
    LATEST_LESSON=$(ls -t "$LESSON_DIR"/LES-*.md 2>/dev/null | head -1)
    echo ""
    echo "Lesson Ledger: $LESSON_COUNT lessons recorded$([ -n "$LATEST_LESSON" ] && echo ", latest: $(basename "$LATEST_LESSON" .md)")"
    echo "  (교육 자료 원칙: 함정 반복/설계 구멍/뒤집힌 가정/도구 함정/기획 패턴 발생 시 /lesson-log 로 기록)"
else
    echo ""
    echo "Lesson Ledger: not initialized — this studio treats every project as teaching material."
    echo "  First lesson-worthy moment: run /lesson-log to create Documents/Lessons/ (rules/lesson-capture.md)"
fi

echo "==================================="
exit 0
