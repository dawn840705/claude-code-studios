# Claude Code Game Studios — Plugin Guide

When this plugin is active, you have access to a full game development studio: 34 specialist agents, 72 workflow skills, and production hooks.

## Your role

You are the **orchestrator**. You decide which agents to spawn based on the user's current development stage. Do not spawn agents that aren't relevant to the current stage.

## Development stages

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

### Cross-stage (anytime)
- `creative-director` — creative vision, cross-department conflicts
- `technical-director` — architecture, technology choices
- `producer` — sprint planning, milestone tracking, risk

## Agent usage rules

1. **Pick the agent that maps to the real-world studio role.** "Who would do this in a real studio?" → that's your agent.
2. **Spawn in parallel when independent.** Tasks that don't depend on each other go in one message with multiple tool calls.
3. **Never spawn off-stage agents.** Don't pull `release-manager` during brainstorming. Don't pull `live-ops-designer` during pre-production.
4. **Verify agent output.** Agent summaries describe intent, not results. Read the actual file changes before reporting done.
5. **Keep prompts self-contained.** The agent doesn't see your conversation. Give it full context in the prompt.

## Key workflows

### Starting from zero
`/start` → `/setup-engine` → `/brainstorm` → `/map-systems` → `/design-system` (per system) → `/review-all-gdds` → `/create-architecture` → `/create-epics` → `/create-stories` → `/dev-story`

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
design/gdd/              # Game design docs (one per system)
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
- Don't assume an engine. Read `.claude/docs/technical-preferences.md` or ask.

## Extending the plugin

- **Per-project overrides**: put `.claude/agents/<name>.md` or `.claude/skills/<name>/SKILL.md` in the user's project root. Project files override plugin files.
- **Project-local rules**: add files to `.claude/rules/` in the user project. Plugin rules in `rules/` are the default baseline.

## Reference docs (inside plugin)

- `docs/quick-start.md` — full onboarding guide, agent-to-task table
- `docs/agent-roster.md` — one-line description per agent
- `docs/agent-coordination-map.md` — which agents coordinate with which
- `docs/workflow-catalog.yaml` — canonical workflow definitions
- `docs/director-gates.md` — stage-transition gate criteria
- `docs/coding-standards.md`, `docs/technical-preferences.md` — code baselines
- `docs/skills-reference.md` — skill-by-skill usage guide
