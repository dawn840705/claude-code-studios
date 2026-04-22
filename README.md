# Claude Code Game Studios

A complete game development studio, as a Claude Code plugin.

**34 specialist agents** · **72 workflow skills** · **production hooks** · covers pre-production → production → QA → release → live-ops.

Mirrors a real game studio structure: directors (creative, technical, producer) coordinate department leads (design, programming, art, audio, narrative, QA), who coordinate specialists (gameplay programmers, level designers, economy designers, etc.). All design agents and templates are grounded in established game design theory (MDA, Self-Determination Theory, Flow State, Bartle Player Types).

Engine-agnostic. Works with Godot, Unity, Unreal, GameMaker, or custom engines.

## What's inside

### Agents (34)

Directors · Department leads · Specialists:

- **Directors (Opus-tier)**: `creative-director`, `technical-director`, `producer`
- **Design**: `game-designer`, `systems-designer`, `economy-designer`, `level-designer`, `narrative-director`, `world-builder`, `writer`, `live-ops-designer`
- **Programming**: `lead-programmer`, `gameplay-programmer`, `ui-programmer`, `ai-programmer`, `engine-programmer`, `network-programmer`, `tools-programmer`, `prototyper`
- **Art/Audio**: `art-director`, `technical-artist`, `audio-director`, `sound-designer`
- **QA/Ops**: `qa-lead`, `qa-tester`, `performance-analyst`, `security-engineer`, `accessibility-specialist`, `localization-lead`, `release-manager`, `devops-engineer`
- **UX/Community/Analytics**: `ux-designer`, `community-manager`, `analytics-engineer`

### Skills (72)

Organized by development phase:

- **Pre-production**: `/start`, `/brainstorm`, `/map-systems`, `/design-system`, `/review-all-gdds`, `/consistency-check`, `/create-architecture`, `/architecture-decision`, `/architecture-review`, `/create-control-manifest`, `/art-bible`, `/ux-design`, `/ux-review`, `/setup-engine`, `/adopt`, `/gate-check`
- **Sprint/Production**: `/create-epics`, `/create-stories`, `/story-readiness`, `/dev-story`, `/story-done`, `/quick-design`, `/sprint-plan`, `/sprint-status`, `/scope-check`, `/estimate`, `/propagate-design-change`, `/reverse-document`, `/asset-spec`, `/asset-audit`
- **Code quality**: `/code-review`, `/tech-debt`, `/design-review`
- **QA**: `/qa-plan`, `/test-setup`, `/test-helpers`, `/test-evidence-review`, `/test-flakiness`, `/regression-suite`, `/smoke-check`, `/soak-test`, `/bug-report`, `/bug-triage`, `/balance-check`, `/playtest-report`, `/content-audit`
- **Orchestration (team skills)**: `/team-audio`, `/team-combat`, `/team-level`, `/team-live-ops`, `/team-narrative`, `/team-polish`, `/team-qa`, `/team-release`, `/team-ui`
- **Release/Ops**: `/release-checklist`, `/launch-checklist`, `/day-one-patch`, `/hotfix`, `/patch-notes`, `/changelog`, `/milestone-review`, `/retrospective`, `/security-audit`, `/perf-profile`, `/localize`, `/onboard`, `/project-stage-detect`, `/help`, `/prototype`, `/skill-test`, `/skill-improve`

### Hooks

- `SessionStart`: loads project context + detects missing documentation
- `PreToolUse` (Bash): validates git commit/push (Korean convention by default — override in your project)
- `PostToolUse` (Write/Edit): validates asset naming, detects skill file changes
- `Notification/PreCompact/PostCompact/Stop`: context compaction and session logging
- `SubagentStart/Stop`: agent activity logging

## Install

### Option 1 — Install from local marketplace (recommended for now)

```bash
# In Claude Code, add this repo as a local marketplace:
/plugin marketplace add /path/to/claude-code-game-studios

# Then install:
/plugin install claude-code-game-studios@game-studios
```

### Option 2 — Install from Git

Once pushed to GitHub:

```bash
/plugin marketplace add <github-user>/claude-code-game-studios
/plugin install claude-code-game-studios@game-studios
```

### Option 3 — Manual (symlink into a project)

```bash
cd /your/game/project
ln -s /path/to/claude-code-game-studios/agents .claude/agents
ln -s /path/to/claude-code-game-studios/skills .claude/skills
ln -s /path/to/claude-code-game-studios/hooks  .claude/hooks
ln -s /path/to/claude-code-game-studios/rules  .claude/rules
ln -s /path/to/claude-code-game-studios/docs   .claude/docs
```

(Note: Option 3 bypasses the plugin system — hooks won't auto-register. Copy the `hooks` block from `.claude-plugin/plugin.json` into your project's `.claude/settings.json` manually if you go this route.)

## Quick start

Once installed, in any new game project:

1. `/start` — first-time onboarding, asks where you are and guides you to the right workflow
2. `/setup-engine` — pin your engine (Unity, Unreal, Godot, GameMaker, custom) and version
3. `/brainstorm` — guided ideation from zero concept to structured game concept doc
4. `/map-systems` — decompose concept into systems and priorities
5. `/design-system <system>` — authoring for each system's GDD
6. `/create-architecture` → `/create-epics` → `/create-stories` → `/dev-story`

Or for a mid-flight project: `/adopt` audits what exists and produces a migration plan.

## Recommended directory structure

The agents and skills assume this in your project root:

```
design/gdd/          # Game design docs
production/sprints/  # Sprint plans
production/bugs/     # Bug reports
src/                 # Source code (engine-dependent)
tests/               # Test files
.claude/             # Project-local overrides (optional)
  └── docs/
      └── technical-preferences.md  # Pin engine + version
```

Skills will create these as you go.

## Customization

- **Per-project overrides**: create `.claude/agents/<name>.md` or `.claude/skills/<name>/SKILL.md` in your project. Project files override plugin files.
- **Personal preferences**: copy `docs/CLAUDE-local-template.md` to your project root as `CLAUDE.local.md` (gitignored).
- **Rules**: `rules/` contains per-system coding standards (gameplay-code, shader-code, ui-code, etc.). Referenced by agents during code review.

## Status & stage

- Pre-production · Production · Polish & QA · Release · Live-ops — every stage covered.
- The orchestrator spawns only agents relevant to your current stage. See `docs/agent-coordination-map.md` for full agent-to-stage mapping.

## Acknowledgments

Built and battle-tested on the Cannon Kingdom project. Extracted as a standalone plugin for portability across game projects.

## License

MIT
