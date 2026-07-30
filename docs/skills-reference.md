# Available Skills (Slash Commands)

84 slash commands organized by phase. Type `/` in Claude Code to access any of them.

## Onboarding & Navigation

| Command | Purpose |
|---------|---------|
| `/start` | First-time onboarding — asks where you are, then guides you to the right workflow |
| `/help` | Context-aware "what do I do next?" — reads current stage and surfaces the required next step |
| `/project-stage-detect` | Full project audit — detect phase, identify existence gaps, recommend next steps |
| `/setup-engine` | Configure engine + version, detect knowledge gaps, populate version-aware reference docs |
| `/adopt` | Brownfield format audit — checks internal structure of existing GDDs/ADRs/stories, produces migration plan |

## Game Design

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Guided ideation using professional studio methods (MDA, SDT, Bartle, verb-first) |
| `/map-systems` | Decompose game concept into systems, map dependencies, prioritize design order |
| `/design-system` | Guided, section-by-section GDD authoring for a single game system |
| `/quick-design` | Lightweight design spec for small changes — tuning, tweaks, minor additions |
| `/review-all-gdds` | Cross-GDD consistency and game design holism review across all design docs |
| `/propagate-design-change` | When a GDD is revised, find affected ADRs and produce an impact report |
| `/art-bible` | Guided, section-by-section Art Bible authoring — visual identity spec that gates asset production |
| `/asset-spec` | Generate per-asset visual specs and AI generation prompts from GDDs/level docs/profiles |
| `/governance-bible-init` | Bootstrap a domain-specific governance Bible (Sound, Art, Narrative, etc.) via the Anchor + Bible pattern |

## Product Design (App/Web/Service)

| Command | Purpose |
|---------|---------|
| `/create-prd` | Guided, section-by-section PRD authoring for a single product feature — writes `product/prd/prd-<feature>.md`. Product-track counterpart of `/design-system` |

## UX & Interface Design

| Command | Purpose |
|---------|---------|
| `/ux-design` | Guided section-by-section UX spec authoring (screen/flow, HUD, or pattern library) |
| `/ux-review` | Validate UX specs for GDD alignment, accessibility, and pattern compliance |

## Architecture

| Command | Purpose |
|---------|---------|
| `/create-architecture` | Guided authoring of the master architecture document |
| `/architecture-decision` | Create an Architecture Decision Record (ADR) |
| `/architecture-review` | Validate all ADRs for completeness, dependency ordering, and GDD coverage |
| `/create-control-manifest` | Generate flat programmer rules sheet from accepted ADRs |

## Stories & Sprints

| Command | Purpose |
|---------|---------|
| `/create-epics` | Translate GDDs + ADRs into epics — one per architectural module |
| `/create-stories` | Break a single epic into implementable story files |
| `/dev-story` | Read a story and implement it — routes to the correct programmer agent |
| `/sprint-plan` | Generate or update a sprint plan; initializes sprint-status.yaml |
| `/sprint-status` | Fast 30-line sprint snapshot (reads sprint-status.yaml) |
| `/story-readiness` | Validate a story is implementation-ready before pickup (READY/NEEDS WORK/BLOCKED) |
| `/story-done` | 8-phase completion review after implementation; updates story file, surfaces next story |
| `/estimate` | Structured effort estimate with complexity, dependencies, and risk breakdown |

## Reviews & Analysis

| Command | Purpose |
|---------|---------|
| `/design-review` | Review a game design document for completeness and consistency |
| `/code-review` | Architectural code review for a file or changeset |
| `/balance-check` | Analyze game balance data, formulas, and config — flag outliers |
| `/asset-audit` | Audit assets for naming conventions, file size budgets, and pipeline compliance |
| `/content-audit` | Audit GDD-specified content counts against implemented content |
| `/scope-check` | Analyze feature or sprint scope against original plan, flag scope creep |
| `/perf-profile` | Structured performance profiling with bottleneck identification |
| `/tech-debt` | Scan, track, prioritize, and report on technical debt |
| `/gate-check` | Validate readiness to advance between development phases (PASS/CONCERNS/FAIL) |
| `/consistency-check` | Scan all GDDs against the entity registry to detect cross-document inconsistencies (stats, names, rules that contradict each other) |
| `/self-loop` | Iterate a deliverable until all pass criteria score 8+/10 — evidence-cited scoring, fix lowest first, max 5 iterations, stall detection (see `rules/self-loop.md`) |
| `/sot-audit` | Audit a Single Source of Truth for cross-witness consistency across design doc, code enum, engine asset, and runtime usage |
| `/legacy-purge` | Audit a codebase for legacy residue after a pivot/deprecation/migration — produces a categorized suspect table (never auto-deletes) |

## QA & Testing

| Command | Purpose |
|---------|---------|
| `/qa-plan` | Generate a QA test plan for a sprint or feature |
| `/smoke-check` | Run critical path smoke test gate before QA hand-off |
| `/soak-test` | Generate a soak test protocol for extended play sessions |
| `/regression-suite` | Map test coverage to GDD critical paths, identify fixed bugs without regression tests |
| `/test-setup` | Scaffold the test framework and CI/CD pipeline for the project's engine |
| `/test-helpers` | Generate engine-specific test helper libraries for the test suite |
| `/test-evidence-review` | Quality review of test files and manual evidence documents |
| `/test-flakiness` | Detect non-deterministic (flaky) tests from CI run logs |
| `/skill-test` | Validate skill files for structural compliance and behavioral correctness |
| `/skill-improve` | Improve a skill via a test-fix-retest loop — keeps or reverts based on score change |
| `/security-audit` | Audit for security vulnerabilities (save tampering, cheat vectors, network exploits, data exposure) with remediation guidance |

## Production

| Command | Purpose |
|---------|---------|
| `/milestone-review` | Review milestone progress and generate status report |
| `/retrospective` | Run a structured sprint or milestone retrospective |
| `/bug-report` | Create a structured bug report |
| `/bug-triage` | Read all open bugs, re-evaluate priority vs. severity, assign owner and label |
| `/reverse-document` | Generate design or architecture docs from existing implementation |
| `/playtest-report` | Generate a structured playtest report or analyze existing playtest notes |
| `/lesson-log` | Extract lecture-worthy lessons from recent work into `Documents/Lessons/` (standard format) and update INDEX (see `rules/lesson-capture.md`) |
| `/lesson-review` | Retrospective scan of commits/notes for missed lessons; regenerates INDEX and the curriculum map |

## Release

| Command | Purpose |
|---------|---------|
| `/release-checklist` | Generate and validate a pre-release checklist for the current build |
| `/launch-checklist` | Complete launch readiness validation across all departments |
| `/changelog` | Auto-generate changelog from git commits and sprint data |
| `/patch-notes` | Generate player-facing patch notes from git history and internal data |
| `/hotfix` | Emergency fix workflow with audit trail, bypassing normal sprint process |
| `/day-one-patch` | Scope, implement, and QA-gate a focused day-one launch patch for known post-gold-master issues |

## Creative & Content

| Command | Purpose |
|---------|---------|
| `/prototype` | Rapid throwaway prototype to validate a mechanic (relaxed standards, isolated worktree) |
| `/onboard` | Generate contextual onboarding document for a new contributor or agent |
| `/localize` | Localization workflow: string extraction, validation, translation readiness |
| `/api-cost-gate` | Pre-flight cost approval gate for any paid AI API call — forces 4-point disclosure before invocation |

## Team Orchestration

Coordinate multiple agents on a single feature area:

| Command | Coordinates |
|---------|-------------|
| `/team-combat` | game-designer + gameplay-programmer + ai-programmer + technical-artist + sound-designer + qa-tester |
| `/team-narrative` | narrative-director + writer + world-builder + level-designer |
| `/team-ui` | ux-designer + ui-programmer + art-director + accessibility-specialist |
| `/team-release` | release-manager + qa-lead + devops-engineer + producer |
| `/team-polish` | performance-analyst + technical-artist + sound-designer + qa-tester |
| `/team-audio` | audio-director + sound-designer + technical-artist + gameplay-programmer |
| `/team-level` | level-designer + narrative-director + world-builder + art-director + systems-designer + qa-tester |
| `/team-live-ops` | live-ops-designer + economy-designer + community-manager + analytics-engineer |
| `/team-qa` | qa-lead + qa-tester + gameplay-programmer + producer |

## Web + AI (Product)

| Command | Purpose |
|---------|---------|
| `/web-ai-patterns` | Field-proven reusable patterns for web+AI (SaaS) products — LLM orchestration & i18n-safe parsing (`ai`), no-loss cost/usage gating & billing & webhook idempotency (`monetization`), document-store data modeling (`data`). Source: SpecForge. |

## Writing

| Command | Purpose |
|---------|---------|
| `/humanize-korean` | Strip AI tells from Korean text — translationese, mechanical parallelism, passive overuse, emoji/bullet excess — without changing a single point of meaning. Routes to 1/2/3+ calls by measured severity; structural gates (`scripts/verify_gates.py`) decide PASS/FAIL by exit code, not self-scoring. |
| `/humanize` | Thin entry command for the above — Fast mode by default, `--strict` forces the 3-call precision path. Explicit slash invocation only. |
| `/humanize-redo` | Second pass on the most recent result — re-run by category, paragraph, or strength; rolls back from `final_prev.md`. Max 3 rounds, then hands off for human review. |
