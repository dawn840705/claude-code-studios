# Claude Code Studios -- Quick Start Guide

## What Is This?

This is a complete Claude Code studio for **both game development and
app/web/service development**. It organizes **41 specialized AI agents** and
**76 workflow skills** into a studio hierarchy that mirrors real product teams,
with defined responsibilities, delegation rules, and coordination protocols.

Agents are grouped into three **domain packs** (source of truth:
`docs/agent-packs.yaml`):

- **core** — domain-neutral roles active in EVERY project (directors,
  programming, QA/Ops, plus hybrids that frame both ways).
- **game** — game-only roles (`game-designer`, `systems-designer`,
  `economy-designer`, `level-designer`, `world-builder`, `live-ops-designer`,
  `technical-artist`, `audio-director`, `sound-designer`).
- **product** — app/web/service roles (`product-manager`, `frontend-engineer`,
  `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`,
  `technical-writer`).

At session start the `detect-project-type.sh` hook prints
`PROJECT_TYPE=<game|web|mobile|service|unknown>` and only the relevant packs
activate (core + game for games; core + product for app/web/service). There are
**no engine-specific agents** — engine guidance comes from `/setup-engine` and
version-aware reference docs. Design agents and templates are grounded in
established game design theory (MDA Framework, Self-Determination Theory, Flow
State, Bartle Player Types).

> For the full agent list see `docs/agent-roster.md`; for orchestration and
> stage routing see the root `CLAUDE.md`.

## How to Use

### 1. Understand the Hierarchy

There are three tiers of agents:

- **Tier 1 (Opus)**: Directors who make high-level decisions
  - `creative-director` -- vision and creative conflict resolution
  - `technical-director` -- architecture and technology decisions
  - `producer` -- scheduling, coordination, and risk management
  - (product track adds `product-manager` for PRD/roadmap/prioritization)

- **Tier 2 (Sonnet)**: Department leads who own their domain
  - Game: `game-designer`, `lead-programmer`, `art-director`, `audio-director`,
    `narrative-director`, `qa-lead`, `release-manager`, `localization-lead`
  - Product: `frontend-engineer`, `backend-engineer`, `mobile-engineer`,
    `data-engineer`, `growth-engineer`, `technical-writer`

- **Tier 3 (Sonnet/Haiku)**: Specialists who execute within their domain
  - Designers, programmers, artists, writers, testers, engineers

### 2. Pick the Right Agent for the Job

Ask yourself: "What department would handle this in a real studio?" Respect the
active domain pack — never spawn product agents on a game project (or vice
versa). Core agents are always fair game.

| I need to... | Use this agent |
|-------------|---------------|
| Design a new mechanic (game) | `game-designer` |
| Write combat code (game) | `gameplay-programmer` |
| Create a shader / VFX (game) | `technical-artist` |
| Write dialogue / lore (game) | `writer` |
| Design a level (game) | `level-designer` |
| Design a loot table / economy (game) | `economy-designer` |
| Plan live events and seasons (game) | `live-ops-designer` |
| Build a web UI (product) | `frontend-engineer` |
| Build a server API / DB schema (product) | `backend-engineer` |
| Build a mobile app (product) | `mobile-engineer` |
| Define a PRD / roadmap (product) | `product-manager` |
| Build event/ETL pipelines (product) | `data-engineer` |
| Improve acquisition/retention funnels (product) | `growth-engineer` |
| Write API docs / runbooks (product) | `technical-writer` |
| Implement UI screens / HUDs | `ui-programmer` |
| Plan the next sprint | `producer` |
| Review code quality | `lead-programmer` |
| Write test cases | `qa-tester` |
| Fix a performance problem | `performance-analyst` |
| Set up CI/CD | `devops-engineer` |
| Resolve a creative conflict | `creative-director` |
| Make an architecture decision | `technical-director` |
| Manage a release | `release-manager` |
| Prepare strings for translation | `localization-lead` |
| Test an idea quickly | `prototyper` |
| Review code for security issues | `security-engineer` |
| Check accessibility compliance | `accessibility-specialist` |
| Design UX flows / interactions | `ux-designer` |
| Set up telemetry / A/B tests | `analytics-engineer` |
| Write patch notes for players | `community-manager` |
| Get engine-specific setup advice | Run `/setup-engine` (not an agent) |
| Brainstorm a new concept | Use `/brainstorm` skill |

### 3. Use Slash Commands for Common Tasks

A selection of the most common commands is below. For the complete list of all
**76 skills** (with one-line purposes, grouped by phase), see
`docs/skills-reference.md`.

| Command | What it does |
|---------|-------------|
| `/start` | First-time onboarding — asks where you are, guides you to the right workflow |
| `/help` | Context-aware "what do I do next?" — reads your current phase and artifacts |
| `/project-stage-detect` | Analyze project state, detect stage, identify gaps |
| `/setup-engine` | Configure engine + version, populate reference docs |
| `/adopt` | Brownfield audit and migration plan for existing projects |
| `/brainstorm` | Guided game concept ideation from scratch |
| `/map-systems` | Decompose concept into systems, map dependencies, guide per-system GDDs |
| `/design-system` | Guided, section-by-section GDD authoring for a single game system |
| `/quick-design` | Lightweight spec for small changes — tuning, tweaks, minor additions |
| `/review-all-gdds` | Cross-GDD consistency and game design theory review |
| `/propagate-design-change` | Find ADRs and stories affected by a GDD change |
| `/ux-design` | Author UX specs (screen/flow, HUD, interaction patterns) |
| `/ux-review` | Validate UX specs for accessibility and GDD alignment |
| `/create-architecture` | Master architecture document for the game |
| `/architecture-decision` | Creates an ADR |
| `/architecture-review` | Validate all ADRs, dependency ordering, GDD traceability |
| `/create-control-manifest` | Flat programmer rules sheet from Accepted ADRs |
| `/create-epics` | Translate GDDs + ADRs into epics (one per architectural module) |
| `/create-stories` | Break a single epic into implementable story files |
| `/dev-story` | Read a story and implement it — routes to the correct programmer agent |
| `/sprint-plan` | Creates or updates sprint plans |
| `/sprint-status` | Quick 30-line sprint snapshot |
| `/story-readiness` | Validate a story is implementation-ready before pickup |
| `/story-done` | End-of-story completion review — verifies acceptance criteria |
| `/estimate` | Produces structured effort estimates |
| `/design-review` | Reviews a design document |
| `/code-review` | Reviews code for quality and architecture |
| `/balance-check` | Analyzes game balance data |
| `/asset-audit` | Audits assets for compliance |
| `/content-audit` | GDD-specified content vs. implemented — find gaps |
| `/scope-check` | Detect scope creep against plan |
| `/perf-profile` | Performance profiling and bottleneck ID |
| `/tech-debt` | Scan, track, and prioritize tech debt |
| `/gate-check` | Validate phase readiness (PASS/CONCERNS/FAIL) |
| `/consistency-check` | Scan all GDDs for cross-document inconsistencies (conflicting stats, names, rules) |
| `/reverse-document` | Generate design/architecture docs from existing code |
| `/milestone-review` | Reviews milestone progress |
| `/retrospective` | Runs sprint/milestone retrospective |
| `/bug-report` | Structured bug report creation |
| `/playtest-report` | Creates or analyzes playtest feedback |
| `/onboard` | Generates onboarding docs for a role |
| `/release-checklist` | Validates pre-release checklist |
| `/launch-checklist` | Complete launch readiness validation |
| `/changelog` | Generates changelog from git history |
| `/patch-notes` | Generate player-facing patch notes |
| `/hotfix` | Emergency fix with audit trail |
| `/prototype` | Scaffolds a throwaway prototype |
| `/localize` | Localization scan, extract, validate |
| `/team-combat` | Orchestrate full combat team pipeline |
| `/team-narrative` | Orchestrate full narrative team pipeline |
| `/team-ui` | Orchestrate full UI team pipeline |
| `/team-release` | Orchestrate full release team pipeline |
| `/team-polish` | Orchestrate full polish team pipeline |
| `/team-audio` | Orchestrate full audio team pipeline |
| `/team-level` | Orchestrate full level creation pipeline |
| `/team-live-ops` | Orchestrate live-ops team for seasons, events, and post-launch content |
| `/team-qa` | Orchestrate full QA team cycle — test plan, test cases, smoke check, sign-off |
| `/qa-plan` | Generate a QA test plan for a sprint or feature |
| `/bug-triage` | Re-prioritize open bugs, assign to sprints, surface systemic trends |
| `/smoke-check` | Run critical path smoke test gate before QA hand-off (PASS/FAIL) |
| `/soak-test` | Generate a soak test protocol for extended play sessions |
| `/regression-suite` | Map coverage to GDD critical paths, flag gaps, maintain regression suite |
| `/test-setup` | Scaffold test framework + CI pipeline for the project's engine (run once) |
| `/test-helpers` | Generate engine-specific test helper libraries and factory functions |
| `/test-flakiness` | Detect flaky tests from CI history, flag for quarantine or fix |
| `/test-evidence-review` | Quality review of test files and manual evidence — ADEQUATE/INCOMPLETE/MISSING |
| `/skill-test` | Validate skill files for compliance and correctness (static / spec / audit) |

### 4. Use Templates for New Documents

Templates are in `.claude/docs/templates/`:

- `game-design-document.md` -- for new mechanics and systems
- `architecture-decision-record.md` -- for technical decisions
- `architecture-traceability.md` -- maps GDD requirements to ADRs to story IDs
- `risk-register-entry.md` -- for new risks
- `narrative-character-sheet.md` -- for new characters
- `test-plan.md` -- for feature test plans
- `sprint-plan.md` -- for sprint planning
- `milestone-definition.md` -- for new milestones
- `level-design-document.md` -- for new levels
- `game-pillars.md` -- for core design pillars
- `art-bible.md` -- for visual style reference
- `technical-design-document.md` -- for per-system technical designs
- `post-mortem.md` -- for project/milestone retrospectives
- `sound-bible.md` -- for audio style reference
- `release-checklist-template.md` -- for platform release checklists
- `changelog-template.md` -- for player-facing patch notes
- `release-notes.md` -- for player-facing release notes
- `incident-response.md` -- for live incident response playbooks
- `game-concept.md` -- for initial game concepts (MDA, SDT, Flow, Bartle)
- `pitch-document.md` -- for pitching the game to stakeholders
- `economy-model.md` -- for virtual economy design (sink/faucet model)
- `faction-design.md` -- for faction identity, lore, and gameplay role
- `systems-index.md` -- for systems decomposition and dependency mapping
- `project-stage-report.md` -- for project stage detection output
- `design-doc-from-implementation.md` -- for reverse-documenting existing code into GDDs
- `architecture-doc-from-code.md` -- for reverse-documenting code into architecture docs
- `concept-doc-from-prototype.md` -- for reverse-documenting prototypes into concept docs
- `ux-spec.md` -- for per-screen UX specifications (layout zones, states, events)
- `hud-design.md` -- for whole-game HUD philosophy, zones, and element specs
- `accessibility-requirements.md` -- for project-wide accessibility tier and feature matrix
- `interaction-pattern-library.md` -- for standard UI controls and game-specific patterns
- `player-journey.md` -- for 6-phase emotional arc and retention hooks by time scale
- `difficulty-curve.md` -- for difficulty axes, onboarding ramp, and cross-system interactions
- `test-evidence.md` -- template for recording manual test evidence (screenshots, walkthrough notes)

Also in `.claude/docs/templates/collaborative-protocols/` (used by agents, not typically edited directly):

- `design-agent-protocol.md` -- question-options-draft-approval cycle for design agents
- `implementation-agent-protocol.md` -- story pickup through /story-done cycle for programming agents
- `leadership-agent-protocol.md` -- cross-department delegation and escalation for director-tier agents

### 5. Follow the Coordination Rules

1. Work flows down the hierarchy: Directors -> Leads -> Specialists
2. Conflicts escalate up the hierarchy
3. Cross-department work is coordinated by the `producer`
4. Agents do not modify files outside their domain without delegation
5. All decisions are documented

## First Steps for a New Project

**Don't know where to begin?** Run `/start`. It asks where you are and routes
you to the right workflow. No assumptions about your game, engine, or experience level.

If you already know what you need, jump directly to the relevant path:

### Path A: "I have no idea what to build"

1. **Run `/start`** (or `/brainstorm open`) — guided creative exploration:
   what excites you, what you've played, your constraints
   - Generates 3 concepts, helps you pick one, defines core loop and pillars
   - Produces a game concept document and recommends an engine
2. **Set up the engine** — Run `/setup-engine` (uses the brainstorm recommendation)
   - Configures CLAUDE.md, detects knowledge gaps, populates reference docs
   - Creates `.claude/docs/technical-preferences.md` with naming conventions,
     performance budgets, and engine-specific defaults
   - If the engine version is newer than the LLM's training data, it fetches
     current docs from the web so agents suggest correct APIs
3. **Validate the concept** — Run `/design-review design/gdd/game-concept.md`
4. **Decompose into systems** — Run `/map-systems` to map all systems and dependencies
5. **Design each system** — Run `/design-system [system-name]` (or `/map-systems next`)
   to write GDDs in dependency order
6. **Test the core loop** — Run `/prototype [core-mechanic]`
7. **Playtest it** — Run `/playtest-report` to validate the hypothesis
8. **Plan the first sprint** — Run `/sprint-plan new`
9. Start building

### Path B: "I know what I want to build"

If you already have a game concept and engine choice:

1. **Set up the engine** — Run `/setup-engine [engine] [version]`
   (e.g., `/setup-engine godot 4.6`) — also creates technical preferences
2. **Write the Game Pillars** — delegate to `creative-director`
3. **Decompose into systems** — Run `/map-systems` to enumerate systems and dependencies
4. **Design each system** — Run `/design-system [system-name]` for GDDs in dependency order
5. **Create the initial ADR** — Run `/architecture-decision`
6. **Create the first milestone** in `production/milestones/`
7. **Plan the first sprint** — Run `/sprint-plan new`
8. Start building

### Path C: "I know the game but not the engine"

If you have a concept but don't know which engine fits:

1. **Run `/setup-engine`** with no arguments — it will ask about your game's
   needs (2D/3D, platforms, team size, language preferences) and recommend
   an engine based on your answers
2. Follow Path B from step 2 onward

### Path D: "I have an existing project"

If you have design docs, prototypes, or code already:

1. **Run `/start`** (or `/project-stage-detect`) — analyzes what exists,
   identifies gaps, and recommends next steps
2. **Run `/adopt`** if you have existing GDDs, ADRs, or stories — audits
   internal format compliance and builds a numbered migration plan to fill gaps
   without overwriting your existing work
3. **Configure engine if needed** — Run `/setup-engine` if not yet configured
4. **Validate phase readiness** — Run `/gate-check` to see where you stand
5. **Plan the next sprint** — Run `/sprint-plan new`

## File Structure Reference

Plugin repo layout:

```
CLAUDE.md                          -- Orchestrator guide (read this first)
.claude-plugin/
  plugin.json                      -- Plugin manifest + hook wiring
  marketplace.json                 -- Marketplace entry
agents/                            -- 41 agent definitions (YAML frontmatter)
skills/                            -- 76 slash command definitions (one folder per skill, each with SKILL.md)
hooks/                             -- 15 hook scripts (.sh) wired by plugin.json
rules/                             -- 12 path-specific rule files
docs/
  quick-start.md                   -- This file
  agent-roster.md                  -- One-line description per agent
  agent-packs.yaml                 -- Pack classification + activation rules (domain routing)
  skills-reference.md              -- Skill-by-skill usage guide
  agent-coordination-map.md        -- Which agents coordinate with which
  workflow-catalog.yaml            -- Canonical workflow definitions
  director-gates.md                -- Stage-transition gate criteria
  coding-standards.md              -- Coding and design doc standards
  templates/                       -- 37 document templates
```

> When the plugin is installed, Claude Code surfaces these as agents and `/`
> slash commands. Per-project overrides live in the consumer project's
> `.claude/agents/`, `.claude/skills/`, and `.claude/rules/`.
