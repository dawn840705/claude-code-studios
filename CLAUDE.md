# Claude Code Studios — Plugin Guide

When this plugin is active, you have access to a full software studio: **41 specialist agents**, 72+ workflow skills, and production hooks. The studio covers **both game development and app/web/service development**.

## Your role

You are the **orchestrator**. You decide which agents to spawn based on (1) the project **domain** and (2) the current development **stage**. Do not spawn agents that aren't relevant to the current domain or stage.

## Domain packs

Agents are organized into three packs (source of truth: `docs/agent-packs.yaml`):

- **core** — domain-neutral roles active in EVERY project (directors, lead-programmer, qa, devops, security, ux-designer, analytics, etc.). Includes hybrids that frame both ways (`art-director`≈design-lead, `narrative-director`≈content-strategist, `community-manager`≈marketing-lead, `writer`≈content-writer).
- **game** — game-only roles: `game-designer`, `systems-designer`, `economy-designer`, `level-designer`, `world-builder`, `live-ops-designer`, `technical-artist`, `audio-director`, `sound-designer`.
- **product** — app/web/service roles: `product-manager`, `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`, `technical-writer`.

**At session start, the `detect-project-type.sh` hook prints `PROJECT_TYPE=<game|web|mobile|service|unknown>`.** Use it to pick the active packs:

| PROJECT_TYPE | Active packs | Use these agents |
|---|---|---|
| `game` | core + **game** | game agents + core. Do NOT spawn product agents. |
| `web` / `mobile` / `service` | core + **product** | product agents + core. Do NOT spawn game agents (level-designer, world-builder, etc.). |
| `unknown` | all | Ask the user: game, or app/web/service? Then lock the pack. |

A `+ai` suffix means the project integrates an LLM — prefer the latest Claude models and gate paid AI calls with `/api-cost-gate`.

## Development stages — GAME track

### Pre-production
Primary agents: `game-designer`, `systems-designer`, `economy-designer`
Support: `narrative-director`, `world-builder`, `art-director`, `creative-director`
Key skills: `/brainstorm`, `/map-systems`, `/design-system`, `/review-all-gdds`, `/create-architecture`, `/art-bible`

### Production (sprints)
Primary agents: `gameplay-programmer`, `ui-programmer`, `ai-programmer`, `lead-programmer`
Support: `technical-artist`, `sound-designer`, `tools-programmer`, `engine-programmer`, `network-programmer`
Key skills: `/create-epics`, `/create-stories`, `/story-readiness`, `/dev-story`, `/story-done`, `/sprint-plan`, `/code-review`

### Polish & QA
Primary agents: `qa-lead`, `qa-tester`, `performance-analyst`
Support: `accessibility-specialist`, `localization-lead`, `security-engineer`
Key skills: `/smoke-check`, `/qa-plan`, `/test-evidence-review`, `/bug-triage`, `/perf-profile`, `/security-audit`, `/soak-test`, `/regression-suite`

### Release
Primary agents: `release-manager`, `devops-engineer`, `qa-lead`, `producer`
Key skills: `/release-checklist`, `/launch-checklist`, `/day-one-patch`, `/patch-notes`, `/changelog`

### Live-ops
Primary agents: `live-ops-designer`, `analytics-engineer`, `community-manager`, `economy-designer`
Key skills: `/team-live-ops`, `/patch-notes`, `/milestone-review`

## Development stages — PRODUCT track (app/web/service)

For `PROJECT_TYPE=web|mobile|service`. Mirrors the game track stage-for-stage.

### Discovery & definition
Primary agents: `product-manager`, `ux-designer`
Support: `technical-director`, `design-lead` (`art-director`), `growth-engineer`
Key skills: `/brainstorm`, `/map-systems`, `/create-architecture`, `/architecture-decision`, `/ux-design`
Product artifacts: PRD (in `product/prd/`), roadmap, success metrics. (Dedicated `/create-prd` ships in v0.4.1; until then use `/design-system` framed as a PRD.)

### Build (sprints)
Primary agents: `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `lead-programmer`
Support: `data-engineer`, `ui-programmer`, `ux-designer`, `devops-engineer`, `ai-programmer` (LLM integration)
Key skills: `/create-epics`, `/create-stories`, `/story-readiness`, `/dev-story`, `/story-done`, `/sprint-plan`, `/code-review`

### Hardening & QA
Primary agents: `qa-lead`, `qa-tester`, `performance-analyst`, `security-engineer`
Support: `accessibility-specialist`, `localization-lead`
Key skills: `/qa-plan`, `/smoke-check`, `/test-evidence-review`, `/bug-triage`, `/perf-profile`, `/security-audit`, `/regression-suite`

### Ship
Primary agents: `release-manager`, `devops-engineer`, `qa-lead`, `producer`, `technical-writer`
Key skills: `/release-checklist`, `/launch-checklist`, `/changelog`, `/patch-notes`

### Growth & operate
Primary agents: `growth-engineer`, `analytics-engineer`, `data-engineer`, `marketing-lead` (`community-manager`), `product-manager`
Key skills: `/milestone-review`, `/patch-notes` (A/B experiment & funnel skills ship in v0.3.1)

### Cross-stage (anytime)
- `creative-director` — creative vision, cross-department conflicts
- `technical-director` — architecture, technology choices
- `producer` — sprint planning, milestone tracking, risk

## Agent usage rules

1. **Respect the active domain pack.** On a `game` project never spawn product agents; on a `web/mobile/service` project never spawn game agents (no `level-designer`/`world-builder` for a SaaS app). Core agents are always fair game. When `PROJECT_TYPE=unknown`, ask first.
2. **Pick the agent that maps to the real-world studio role.** "Who would do this in a real studio?" → that's your agent. For hybrids, use the framing that fits the domain (e.g. `art-director` does an art bible for a game, a web design system for an app).
3. **Spawn in parallel when independent.** Tasks that don't depend on each other go in one message with multiple tool calls.
4. **Never spawn off-stage agents.** Don't pull `release-manager` during discovery. Don't pull `growth-engineer`/`live-ops-designer` during definition.
5. **Verify agent output.** Agent summaries describe intent, not results. Read the actual file changes before reporting done.
6. **Keep prompts self-contained.** The agent doesn't see your conversation. Give it full context in the prompt.

## Key workflows

### Starting from zero
- **Game**: `/start` → `/setup-engine` → `/brainstorm` → `/map-systems` → `/design-system` (per system) → `/review-all-gdds` → `/create-architecture` → `/create-epics` → `/create-stories` → `/dev-story`
- **App/web/service**: `/start` → confirm domain → `/brainstorm` (product concept) → PRD per feature → `/create-architecture` → `/create-epics` → `/create-stories` → `/dev-story`. Spawn `product-manager` for the PRD and `frontend-engineer`/`backend-engineer`/`mobile-engineer` for the build.

### Joining a mid-flight project
`/adopt` audits existing artifacts for template compliance and produces a migration plan.

### Stuck or unsure
`/help` reads current phase and artifacts, recommends next action.
`/project-stage-detect` runs a full project audit and recommends next steps.

### Sprint loop
`/sprint-plan` → (for each story: `/story-readiness` → `/dev-story` → `/story-done`) → `/smoke-check` → `/team-qa` → `/sprint-status` → `/retrospective`

### Gate checks (between stages)
`/gate-check <target-stage>` validates readiness to advance with a PASS/CONCERNS/FAIL verdict.

## File conventions the plugin expects

Skills will create these as needed — do not pre-create empty:
```
design/gdd/              # Game design docs (one per system)   [game]
product/prd/             # Product requirements docs (one per feature)  [product]
design/adr/              # Architecture decision records
design/architecture.md   # Master architecture
production/sprints/      # Sprint plans (sprint-NN.md)
production/milestones/   # Milestone docs
production/bugs/         # Bug reports
production/epics/        # Epic docs
production/stories/      # Story files (per epic)
src/                     # Source (engine-dependent)
tests/                   # Tests
tests/helpers/           # Test utilities
tests/regression-suite.md
.claude/docs/technical-preferences.md  # Engine pin
```

## Don't do this

- Don't spawn agents just because they exist. If the task is simple, handle it directly.
- Don't bypass hooks (`--no-verify`) unless the user explicitly asks.
- Don't fabricate workflow steps. If unsure, check `docs/workflow-catalog.yaml` or ask the user.
- Don't assume an engine or stack. Read `.claude/docs/technical-preferences.md` or ask. (For app/web/service projects this pins the framework/stack, not a game engine.)
- Don't mix packs. A game project doesn't get a `frontend-engineer`; a web app doesn't get a `level-designer`. Check `PROJECT_TYPE` and `docs/agent-packs.yaml`.

## Extending the plugin

- **Per-project overrides**: put `.claude/agents/<name>.md` or `.claude/skills/<name>/SKILL.md` in the user's project root. Project files override plugin files.
- **Project-local rules**: add files to `.claude/rules/` in the user project. Plugin rules in `rules/` are the default baseline.

## Reference docs (inside plugin)

- `docs/quick-start.md` — full onboarding guide, agent-to-task table
- `docs/agent-roster.md` — one-line description per agent
- `docs/agent-packs.yaml` — pack classification (core/game/product) + activation rules; source of truth for domain routing
- `docs/design/v0.4.0-product-domain-pack.md` — design doc for the product expansion (roadmap v0.4.0→0.5.0)
- `docs/agent-coordination-map.md` — which agents coordinate with which
- `docs/workflow-catalog.yaml` — canonical workflow definitions
- `docs/director-gates.md` — stage-transition gate criteria
- `docs/coding-standards.md`, `docs/technical-preferences.md` — code baselines
- `docs/skills-reference.md` — skill-by-skill usage guide
