#!/bin/bash
# Hook: detect-project-type.sh
# Event: SessionStart
# Purpose: Detect project domain (game / web / mobile / service) so the orchestrator
#          activates only the relevant agent pack (core + game OR core + product).
#          Reduces context pollution and improves routing accuracy.
# Cross-platform: Windows Git Bash compatible (uses grep -E, not -P).
#          Handles monorepos by scanning one level into apps/* and packages/*.
#
# Output: prints a single PROJECT_TYPE line the orchestrator reads.
#         Format: PROJECT_TYPE=<type>[+ai]   types: game | web | mobile | service | unknown
#         Routing only distinguishes game vs product (web/mobile/service all → product pack).
# Never fails the session.

set +e

TYPE=""
AI_FLAG=""

has() { grep -qiE "$1" "$2" 2>/dev/null; }

# Candidate roots: current dir + monorepo workspaces (one level deep)
ROOTS="."
for sub in apps packages app; do
  if [ -d "$sub" ]; then
    for d in "$sub"/*/ "$sub"; do
      [ -d "$d" ] && ROOTS="$ROOTS $d"
    done
  fi
done

AI_RE='@anthropic-ai|anthropic|@google/genai|@google/generative-ai|google-generativeai|generative-ai|gemini|openai|langchain|@mistralai'

# --- 1. GAME (engine signals win first — strongest, root-only) ---
if { [ -d "Assets" ] && [ -d "ProjectSettings" ]; } || [ -f "project.godot" ] \
   || ls ./*.uproject >/dev/null 2>&1 || ls ./*.yyp >/dev/null 2>&1; then
  TYPE="game"
fi

# --- 2..4. PRODUCT signals — scan every candidate root ---
if [ -z "$TYPE" ]; then
  for r in $ROOTS; do
    pkg="${r%/}/package.json"

    # MOBILE
    if [ -f "${r%/}/pubspec.yaml" ]; then TYPE="mobile"; fi
    if [ -z "$TYPE" ] && [ -f "${r%/}/app.json" ] && [ -f "$pkg" ] && has '"?expo"?|react-native' "$pkg"; then TYPE="mobile"; fi
    if [ -z "$TYPE" ] && [ -f "$pkg" ] && has 'react-native|"expo"' "$pkg"; then TYPE="mobile"; fi

    # WEB
    if [ -z "$TYPE" ] && ls "${r%/}"/next.config.* >/dev/null 2>&1; then TYPE="web"; fi
    if [ -z "$TYPE" ] && [ -f "$pkg" ] && has '"(react|vue|svelte)"|@angular/core|"next"' "$pkg"; then TYPE="web"; fi

    # SERVICE
    if [ -z "$TYPE" ] && [ -f "${r%/}/requirements.txt" ] && has 'fastapi|flask|django|uvicorn' "${r%/}/requirements.txt"; then TYPE="service"; fi
    if [ -z "$TYPE" ] && [ -f "${r%/}/pyproject.toml" ] && has 'fastapi|flask|django' "${r%/}/pyproject.toml"; then TYPE="service"; fi
    if [ -z "$TYPE" ] && { [ -f "${r%/}/go.mod" ] || [ -f "${r%/}/Cargo.toml" ]; }; then TYPE="service"; fi
    if [ -z "$TYPE" ] && [ -f "$pkg" ] && has 'express|fastify|@nestjs' "$pkg"; then TYPE="service"; fi

    [ -n "$TYPE" ] && break
  done
fi

# --- Weak fallback: backend-as-a-service config implies a product (web/mobile) ---
if [ -z "$TYPE" ]; then
  if [ -f "firebase.json" ] || [ -f "firestore.rules" ] || [ -f "vercel.json" ] || [ -f "netlify.toml" ]; then
    TYPE="web"
  fi
fi

# --- AI flag (orthogonal — scan all roots) ---
for r in $ROOTS; do
  for f in package.json requirements.txt pyproject.toml; do
    if [ -f "${r%/}/$f" ] && has "$AI_RE" "${r%/}/$f"; then AI_FLAG="+ai"; break 2; fi
  done
done

[ -z "$TYPE" ] && TYPE="unknown"

echo "=== Project Type Detection ==="
echo "PROJECT_TYPE=${TYPE}${AI_FLAG}"

case "$TYPE" in
  game)
    echo "→ Active packs: core + game. Orchestrator: use game agents (game-designer, level-designer, etc.). Skip product-pack." ;;
  web|mobile|service)
    echo "→ Active packs: core + product. Orchestrator: use product agents (product-manager, frontend/backend/mobile/data/growth-engineer, technical-writer). Skip game-pack." ;;
  unknown)
    echo "→ Could not auto-detect domain. All packs available — ask the user whether this is a game or an app/web/service project." ;;
esac

if [ -n "$AI_FLAG" ]; then
  echo "→ AI integration detected: prefer the latest Claude models; gate paid AI calls with /api-cost-gate."
fi

echo "→ Pack classification source of truth: docs/agent-packs.yaml"
echo "=============================="

exit 0
