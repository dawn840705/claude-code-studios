# Changelog

## v0.6.2 — 2026-07-31

### Fixed — Hooks stopped assuming a lowercase web layout

Three of the four path-sensitive hooks hardcoded `src/`, `assets/` and
`design/gdd/`. Unity forces `Assets/` + `ProjectSettings/` and keeps code under
`Assets/**/*.cs`, so on a real Unity project they either never fired or fired on
nothing. Shipping `unity-meta-check.sh` and `unity-animator-string-lint.sh` said
Unity was a first-class target; the rest of the hook set said otherwise.
Measured on a live Unity 6 project (60+ scripts, 80+ design docs, six observed
commits):

- **`detect-gaps.sh` called a mature project a fresh start.** All three
  freshness tests looked at non-Unity paths, and the branch `exit 0`s — so
  checks 1-5, the actual purpose of the hook, had never run on a Unity project.
  Freshness now also clears on an engine scaffold, on 3+ design docs under any
  detected design root, and on a non-empty `production/` tree (which is why this
  very repo, having no `src/` at all, was also reporting `NEW PROJECT`). Checks
  1-5 resolve `core`/`gameplay` directories by **name** rather than by a fixed
  `src/gameplay` path, so Unity's `Assets/02.Scripts/Gameplay/Combat/` resolves.
- **`validate-commit.sh` passed silently on every commit.** Its four staged-file
  filters were all `^src/…`-shaped. Code checks now select files by
  **extension**, which is portable across engines; document and JSON checks use
  the detected design and asset roots. Per-file findings collapse into one
  summary line (5 files named, then a count) so a large Unity commit cannot bury
  the warning, and the scan is capped at 200 files to stay inside the 15s
  PreToolUse budget. Also fixed: matched lines used to leak onto stdout because
  the `grep` guards were missing `-q`.
- **`validate-assets.sh` had two bugs hiding each other.** The path filter
  matched lowercase `assets/` only, so Unity files never reached the naming
  rule — which hardcoded lowercase-with-underscores and would have rejected
  `PlayerController.cs`, `CARD_MaxHP.asset` and `Monster_Base.prefab`, all of
  them correct Unity names (a C# file name must match its class name). Fixing
  the path alone would have warned on essentially every Unity file. The
  convention is now per-engine: `pascal` for Unity/Unreal flags only whitespace
  and hyphens, `snake` for web/Godot is unchanged, and `any` disables the check.
- **`plugin.json`** — the PostToolUse matcher was `Write|Edit`, so `.meta`
  checks and the Animator lint were skipped wherever MultiEdit is active. Now
  `Write|Edit|MultiEdit`.

`unity-meta-check.sh`, `unity-animator-string-lint.sh`, `validate-push.sh` and
`detect-project-type.sh` were already correct and are untouched; regression
tests pin the first three.

### Added — `hooks/lib/detect-layout.sh`

One place decides the layout, because copy-pasting the same engine test per hook
is how they diverged. Exports `STUDIO_ENGINE` (unity/godot/unreal/gamemaker/
generic), source roots and extensions, design roots, asset roots and the naming
convention, plus helpers (`studio_count_sources`, `studio_find_subdir`,
`studio_naming_violation`, …). Generated trees (`Library/`, `Temp/`,
`node_modules/`, `Intermediate/`, …) are pruned from every walk — Unity's
`Library/` alone would blow the SessionStart timeout.

- **Backward compatible by construction.** `generic` reproduces the old web
  layout; `lib`/`app`/`packages` are additive and only apply when they exist.
- **Overridable** via environment, `.claude/studio-layout.json`, or a
  `studio.layout` block in `.claude/settings.json` — a project whose docs live
  somewhere unusual (`Documents/Specs/`) can say so. Unreadable config falls
  through to detection, never to an empty layout.
- **Degrades, never dies.** Every consumer guards the `source` with `-f` and
  keeps a legacy fallback; a missing helper cannot fail a session or a commit.
- `docs/hooks-reference.md` — layout contract, the override schema, and five
  rules for adding a hook (source the helper; select by extension; stay
  advisory; `grep -E` only; test both directions).

### Added — `tests/test_hooks_layout.py`

69 tests, the repo's first coverage of hook behaviour: engine detection for four
engines, layout resolution and override precedence (including the jq-less grep
fallback), the `NEW PROJECT` misfire in both directions, Unity vs. web naming,
JSON blocking on both layouts, and a guard proving the source globs are not
shell-expanded before `find` sees them. Suite: 226 → 295 passed.

### Fixed — the marketplace manifest had been advertising v0.6.0

`.claude-plugin/marketplace.json` — the file the marketplace actually reads —
still said `0.6.0` and "83 workflow skills". Both the v0.6.1 and v0.6.2 release
commits updated `plugin.json` and forgot its twin, so users were being offered a
two-release-old build. Now `0.6.2` / 84 skills, matching the filesystem.

`tests/test_manifest_sync.py` (9 tests) makes the next omission unmergeable:
the two manifests must agree on version, license and author; the advertised
skill and agent counts are checked against the filesystem rather than against
each other (so adding a skill without touching the description also fails); and
the CHANGELOG's top section must name the current version or be `Unreleased`.

## v0.6.1 — 2026-07-30

### Changed — The deterministic flow now covers both tracks

The workflow catalog claimed to serve the whole studio but only encoded the game track — on a `web`/`mobile`/`service` project, `/help` walked users through art bibles and playtests. The premise of a deterministic flow (every project passes the same steps, produces the same artifacts, in the same order) held for exactly one of the two domains this plugin supports. Prompted by [a pattern analysis of large skill plugins](https://thakicloud.com/tech-blog/ko/dev/agentops/agent-plugin-158-skills-deterministic-flow/): the flow, not the model, owns format/order/dependencies — so the flow has to exist for every domain.

- `docs/workflow-catalog.yaml` — **schema v2, dual-track**. `tracks: game` (the v1 flow, unchanged step-for-step) and `tracks: product` (discovery → architecture → build → hardening → ship → growth, mirroring the CLAUDE.md product stages with real artifact globs: `product/prd/prd-*.md`, ADR minimums, `tests/regression-suite.md`, …). Track selection follows `PROJECT_TYPE`.
- **Explicit step dependencies** — steps now declare `depends_on` (qualified as `phase:step` where ids repeat). Order is no longer implied by list position alone; a skipped step is now *detectable* rather than inferable.

### Added — `scripts/check_phase.py`: phase completion is script-decided

`/help` used to decide step completion by having the model glob for artifacts and count matches — exactly the kind of judgment `docs/deterministic-gates.md` says a script must own (globs + `min_count` + text pattern are 100% mechanical). New gate, same contract:

- Exit codes: `0` phase complete · `1` in progress · `2` **dependency violation** (a completed step's required dependency is missing — a step was skipped) · `3` cannot judge (catalog unreadable, or both game and product markers present with no `--track`). Code 3 is never a pass.
- Resolves track (marker-based, mirroring `detect-project-type.sh`), phase (`production/stage.txt` first, artifact inference second), then evaluates every step. `--json` for machine consumption, `--validate` for CI schema checking (broken globs, dangling `depends_on` → unmergeable).
- Standard library only, including the catalog parser — a purpose-built YAML-subset reader rather than a PyYAML dependency, keeping the vendored runtime at zero third-party deps.
- `skills/help/SKILL.md` — runs the gate in its context block; the model now narrates the script's verdicts instead of producing its own. Model-side globbing survives only as the documented exit-3 fallback, labeled as such. `skills/project-stage-detect/SKILL.md` — same, as its new first step.
- `tests/test_check_phase.py` — 21 tests: the real catalog parses and validates, v1 game flow survived the restructure intact, artifact/pattern/min_count semantics, all four exit codes exercised via the CLI.

### Added — `/create-prd`

Promised for v0.4.1 ("until then use `/design-system` framed as a PRD"), never shipped. Now real: guided section-by-section PRD authoring to `product/prd/prd-<feature>.md` — 8 required sections with a self-check that success metrics carry numbers + measurement sources, acceptance criteria map to FRs, and the MoSCoW *Won't* list is non-empty (an empty Won't list means scope was not decided). Retrofit mode mirrors `/design-system` (fills gaps, never touches existing content). The catalog's `discovery:create-prd` step points at it; the CLAUDE.md workaround note is gone. Skill count: 83 → 84.

## v0.6.0 — 2026-07-30

### Changed — Gates stopped grading themselves

Every quality gate in this plugin used to end with an LLM declaring PASS or FAIL. `/self-loop` already defended against that (8+ requires quoted evidence, 5-iteration cap, stall detection) — but every one of those defenses was the same kind: asking the model to doubt itself. This release moves the verdict out of the model.

- `docs/deterministic-gates.md` — exit-code contract as a repo standard: `0` converged / `1` warning / `2` abort / `3` **could not judge**. A gate that did not run has produced no verdict, and "no verdict" is never "pass". Reference implementation is `scripts/verify_gates.py`. Four caller rules (the exit code overrides the model; never re-derive a verdict from stdout; keep PASS/FAIL/NOT RUN distinct; name the deciding gate) plus how to add a gate.
- `skills/self-loop/SKILL.md` — scoring now asks **"can a script decide this?"** first. If yes, the exit code sets the score and model judgment does not override it. Self-scoring is the fallback for the irreducibly qualitative (readability, tone, whether an argument holds), not the default.
- `skills/smoke-check/SKILL.md` — reads the runner's **exit code** instead of parsing its output. Non-zero is FAIL even if the log looks harmless; zero is PASS even if it contains scary warnings. The NOT RUN → PASS WITH WARNINGS policy stays (deliberate, for environments with no engine binary) but the three states are never collapsed.
- `/gate-check` is deliberately untouched — it judges whether artifacts say something *meaningful*, which is irreducibly qualitative, and its verdict is documented as advisory.

### Added — Korean humanize (`writing` pack)

Strips AI tells from Korean prose — translationese, mechanical parallelism, passive overuse, emoji/bullet excess — without changing a single point of meaning. Vendored from [`epoko77-ai/im-not-ai`](https://github.com/epoko77-ai/im-not-ai) @ `53e24e8` (MIT; full notice in `NOTICE.md`).

- **3 skills** — `/humanize-korean` (orchestrator; routes to 1/2/3+ calls by measured severity), `/humanize` (Fast entry, `--strict` forces the precision path), `/humanize-redo` (second pass by category/paragraph/strength, rollback via `final_prev.md`).
- **4 agents** — `humanize-monolith`, `humanize-diagnostician`, `humanize-finalizer`, `korean-ai-tell-taxonomist`. `tools` is declared narrowly on purpose: upstream enforces its tool-call cap by prompt instruction; narrowing the schema makes the same limit structural.
- **New `writing` pack, active on every `PROJECT_TYPE`** — patch notes and GDDs need this as much as release notes and landing copy. Kept out of `core` only because it is Korean-specific, so dropping it later means one line in `activation`.
- `humanize-redo` shipped upstream referencing agents retired in v2.1 (`korean-style-rewriter`, `content-fidelity-auditor`) and reading artifacts that do not exist. Repaired here against the real call path — a candidate to send back upstream.

### Added — Call-count routing (`rules/route-hint.md`)

`CLAUDE.md` already said "don't spawn agents just because they exist", with no way to act on it. Upstream measurement prices that instinct: the same 10,000-character text cost **610K tokens as 7 chunks vs. 134K as a single call, at equal quality** — the waste was reloading shared context per chunk, not the model tier. With 45 agents that structure is easy to reproduce by accident.

- Three routes — **light** (orchestrator handles it, 0 agents) / **standard** (1 specialist) / **heavy** (fan-out + gates), with a tiebreaker: when torn, take the lighter one.
- Two principles carried over verbatim: **savings come from fewer calls, not a cheaper model** (never silently downgrade a tier — that is the user's choice) and **splitting is the last resort**.

### Added — First tests and CI in this repo

- `tests/` — 27 files: 12 `test_*.py`, golden fixtures (2 sets), `checks.py`. The ported suite reproduces the upstream baseline exactly (**185 passed, 1 skipped, 12 subtests**); with the linter's own tests the repo now runs **205 passed**.
- `scripts/` — 6 deterministic gate/build scripts. Standard library only; **zero third-party dependencies**.
- `scripts/lint_skills.py` — the 7 static checks from `skills/skill-test/SKILL.md` as runnable code. That skill is a linter an LLM reads and performs, so it could never run in CI. It found 11 real pre-existing violations; those are pinned in `scripts/lint_baseline.json` so CI blocks *new* violations without demanding the backlog be cleared first. `tests/test_skill_lint.py` covers it in both directions — a baselined failure stays tolerated, a new one fails the build — including a regression test for the stale-entry guard.
- `.github/workflows/test.yml` — pytest × Python 3.11/3.12/3.13, SSOT drift checks (`quick-rules.md` and `diagnosis-rules.md` are *built* from the taxonomy — hand-editing them is now unmergeable), and the skill/agent structure lint.
- `LICENSE` — the repo declared MIT in `plugin.json` without ever shipping the text. Fixed.

### Added — Self-loop quality rule (all projects)

- `rules/self-loop.md` — global, path-independent rule: deliverables with clear quality criteria are never one-shot. Protocol per iteration: plan → execute → score each criterion 1-10 → judge (all ≥ 8 → done, else fix lowest first). Includes defenses for the two classic traps of self-scoring loops: **score inflation** (criteria must be objectively verifiable; scores of 8+ require quoted evidence; every score names a remaining weakness) and **runaway loops** (max 5 iterations by default; stop + report after 2 consecutive stalled rounds). Ends with a verifiable exit report so the user can check the result without trusting the scores.
- `skills/self-loop/SKILL.md` — `/self-loop [target] [--criteria "..."] [--max N]`, the executable form of the rule. Default entry point when reworking after a FAIL from `/smoke-check`, `/gate-check`, or `/story-done`, or when the user asks to "loop until it passes" / "될 때까지 반복".
- `hooks/session-start.sh` — now prints a compact Self-Loop Rule reminder at every session start, so the rule reaches every project using the plugin.
- `CLAUDE.md` — new "Self-loop quality rule" section in the orchestrator guide; `docs/rules-reference.md` gained a Global Rules section; `docs/skills-reference.md` updated (skill count corrected to match the repo — previously undocumented skills are now listed).

## v0.5.0 — 2026-07-15

### Added — Lesson Ledger (교육용 노하우 원장)

Every studio project doubles as **teaching material** for a game-designer vibe-coding course. This release makes knowledge capture a first-class, auto-propagating workflow: update the plugin once, every project gets it.

- `skills/lesson-log` — `/lesson-log [topic]` extracts lecture-worthy lessons from recent work into `Documents/Lessons/LES-YYYYMMDD-NN-<slug>.md` (standard format) and updates `INDEX.md`. The "what we tried and why it failed" section is mandatory — failure narratives are the teaching asset.
- `skills/lesson-review` — `/lesson-review [period]` retrospective-scans commits/meeting-notes for missed lessons, regenerates INDEX + curriculum map (category counts, difficulty distribution, lecture-module suggestions).
- `templates/lesson.md` — lesson format: frontmatter (id/category/difficulty/teachable-moment) + 6 sections (Context → Problem → What we tried → Resolution → Lesson → Teaching notes).
- `rules/lesson-capture.md` — 5 standing capture triggers: repeated trap ×2 / design hole exposed by user feedback / assumption overturned by verification / tooling pitfall / design-decision pattern locked by data.
- `hooks/session-start.sh` — Lesson Ledger status line at every session start (count + latest, or initialization nudge). This is the auto-propagation mechanism: no per-project setup needed.

Categories (curriculum axes): `vibe-coding` / `game-design` / `engine-tech` / `test-balancing` / `production-ops`. Seed ledger lives in the StarDiver repo (`Documents/Lessons/`).

## v0.4.0 — 2026-06-19

### Added — Product pack (app / web / service expansion)

The studio is no longer game-only. A **domain-pack architecture** splits agents into `core` (always active), `game`, and `product`, so only the relevant pack activates per project. Routing source of truth: `docs/agent-packs.yaml`.

- **7 new product-pack agents** — `product-manager`, `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`, `technical-writer`. (Total agents: 34 → 41.)
- `hooks/detect-project-type.sh` (SessionStart) — auto-detects `PROJECT_TYPE=game|web|mobile|service|unknown` (+`ai` flag) from engine/framework signals, handling monorepos (scans `apps/*`, `packages/*`). The orchestrator uses it to activate `core+game` or `core+product` and avoid spawning off-domain agents. Verified against the owner's real projects (Unity / Next.js / React Native / Firebase).
- `docs/agent-packs.yaml` — pack classification + activation rules + neutral-name mapping for hybrid agents (`art-director`→design-lead, `narrative-director`→content-strategist, `community-manager`→marketing-lead, `writer`→content-writer).
- `docs/design/v0.4.0-product-domain-pack.md` — design doc: portfolio analysis, decisions, roadmap, pre-implementation checks.

### Changed

- `CLAUDE.md` — orchestrator guide restructured around **two stage tracks** (GAME and PRODUCT) plus a Domain packs section and a pack-routing table. Agent usage rules now lead with "respect the active domain pack."
- `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` — version `0.3.0` → `0.4.0`; description and keywords broadened to game + app/web/service.

### Roadmap (next)

- v0.4.1 — product workflow skills (`/create-prd`, `/usability-test`, `/ab-experiment`, `/data-model`, `/user-flow`) + stack scaffolds (`/scaffold-nextjs`, `/firebase-setup`, `/stripe-integration`, `/llm-integration`) + stack presets.
- v0.5.0 — plugin/marketplace rename to "Claude Code Studios", full doc rebrand, `customer-support` agent, web/RN opt-in hooks.

---

## v0.3.0 — 2026-05-17

### Added — Unity UI/UX guidelines (5 permanent rules)

- `docs/engine/unity-ui-guidelines.md` — uGUI + Input System 1.x 의 UI/UX 5 영구 룰 통합 spec. 게임패드 + KBM 동시 대응 시 *반드시* 적용:
  1. **UI 활성 시 첫 selectable 자동 select** — Coroutine 1프레임 지연 + `Selectable.Select()` (직접 `EventSystem.SetSelectedGameObject` 호출은 1프레임 늦은 refresh 로 무시됨)
  2. **O 버튼 / Escape = popup 닫기** — `InputSystemUIInputModule.cancel.action.performed` 구독
  3. **게임패드 + KBM 동시 대응** — UI action 의 양쪽 binding + EventSystem actionsAsset + 4 action ref
  4. **UI 생성 default** — TMP Text placeholder 자동 채우기 + 중앙 정렬 (`TextAlignmentOptions.Center`)
  5. **Device-aware auto-select (최종 spec)** — 마지막 *실제* 입력 장치 추적 (`InputSystem.onEvent` + significant input deadzone). `InputDevice.lastUpdateTime` 단독 비교는 stick drift 로 false positive
- `templates/unity/UIAutoSelectGuardian.cs` — Rule 5 helper class. panel root 부착 + fallback Selectable 지정. 양방향 전환 (게임패드 ↔ 마우스) 자동 처리

### Added — Unity scene-loading patterns

- `docs/engine/unity-scene-loading-patterns.md` — `SceneManager.sceneLoaded` 이벤트가 *이미 로드된 씬* 에는 발화 X 함정. 단독 Play 시 FadeManager 검은 화면 사고 + `Start()` fallback 패턴. Boot 씬 진입 시 skip 룰 (중복 fade 깜빡임 회피)

### Added — Unity MCP workflow patterns

- `docs/engine/unity-mcp-workflow.md` — Claude Code + CoplayDev/unity-mcp 통한 Unity Editor 자동화 패턴:
  - 도구 선택 기준 (manage_scene / manage_gameobject / manage_components / manage_prefabs / execute_code / batch_execute)
  - **batch_execute** — N 명령 1회 호출로 latency 10~100x 향상 (UI widget 일괄 생성 시 필수)
  - **execute_code** — reflection / sub-asset 매핑 / nested SerializedField array set (`manage_components.set_property` 가 못 하는 영역)
  - 회귀 사고 cluster (nested array set 실패 / Component 매핑 자동 reset / Play mode 중 EditorSceneManager / MCP session stale)

### Added — Subagent parallel collaboration rules

- `rules/subagent-collaboration.md` — *광범위 + 깊은 디자인 결정* 영역에 다수 서브 에이전트 병행 호출 패턴. 사람 팀 협업 모사:
  - 단일 message 안 4 Agent tool call → N 배 빠른 병행
  - 표준 4 분야 — game-designer / ux-designer / ui-programmer / gameplay-programmer
  - 각 에이전트 prompt 의무 항목 (self-contained 컨텍스트)
  - 결과 통합 패턴 (결정 안건 매트릭스 + 회의록 + agentId 보존)
- `docs/templates/subagent-meeting-template.md` — 4 에이전트 결과 통합 회의록 template (메타 박스 + 결정 안건 § + 작업 계획 § + agentId 보존)

### Changed

- `.claude-plugin/plugin.json` — version `0.2.0` → `0.3.0`. description 갱신
- `README.md` — v0.3.0 자산 link 추가

### Compatibility

- Unity UI guidelines: Unity 6 / 2022 LTS + Input System 1.x + uGUI 검증. UI Toolkit (UXML/USS) 별도 (본 가이드 X)
- Scene loading patterns: Unity 일반
- MCP workflow: CoplayDev/unity-mcp v9.6+ 정합. Other Unity MCP 호환 가능
- Subagent collaboration: Claude Code 일반 (모든 프로젝트)

### Origin

Distilled from StarDiver Unity 6 PC/콘솔 게임 프로젝트 (5-15~5-17, 17 commit cluster). 5 회귀 사고 + UI/UX 영구 룰 cluster 채택 과정에서 surfaced 패턴들. 모든 자산이 *engine / genre / platform agnostic* (Unity UI 룰만 Unity 특정).

---

## v0.2.0 — 2026-05-04

### Added — Opt-in Unity safeguards

- `hooks/unity-meta-check.sh` (PostToolUse, Write/Edit) — advisory warning when a Unity asset (`.cs`/`.shader`/`.asset`/`.prefab`/`.mat`/`.controller`) is written without its paired `.meta`. Auto-detects Unity projects via `Assets/` + `ProjectSettings/`; exits silently elsewhere.
- `hooks/unity-animator-string-lint.sh` (PostToolUse, Write/Edit) — advisory warning when `.cs` files use `Animator.SetBool("name", ...)` style string lookups. Recommends `Animator.StringToHash` caching.
- `templates/githooks/unity-pre-commit` — manual opt-in git pre-commit template that *blocks* commits with missing `.meta` (zero-tolerance enforcement for shared repos / CI).
- `docs/engine/unity-setup.md` — activation guide, troubleshooting, disable instructions.

### Added — Engine-agnostic meta-audit skills

- `skills/sot-audit` — N-witness consistency audit for any multi-witness specification (FSM, input bindings, save schemas, localization, audio mixer, shader uniforms, network messages). Produces severity-classified mismatch matrix; advisory only.
- `skills/legacy-purge` — categorized residue audit after a pivot or migration (genre change, API deprecation, platform swap, architecture rewrite). Cross-references policy docs to filter intentional retention; advisory only.

### Added — Governance & workflow assets (engine/genre/platform agnostic)

- `skills/governance-bible-init` — bootstraps a domain Bible (Sound / Art / Narrative / UI / etc.) with the **Anchor + Bible** pattern: text spec + reference assets + decision protocol. Designed for solo devs and small teams managing AI-generated assets at scale.
- `skills/api-cost-gate` — pre-flight 4-point disclosure (call type / cost / purpose / use plan) gate for paid AI APIs (Suno, ElevenLabs, Midjourney, Tripo, OpenAI, etc.). Auto-mode does not bypass.
- `docs/templates/meeting-template.md` — meeting note template with mandatory header metadata table, D-table for decisions, and memorialization protocol.
- `docs/templates/api-cli-template.py` — reusable Python CLI scaffold for wrapping a new pay-as-you-go AI service (env loading, auth headers, async polling, sync binary, file downloads, subcommand argparse).
- `docs/rules/token-efficiency.md` — six rules (R1 commit length / R2 meeting length / R3 bulk operation reporting / R4 parallel reads / R5 memory-write discipline / R6 acknowledgement length) for keeping agent collaboration efficient on multi-month projects.
- `docs/rules/artifact-organization.md` — three-zone discipline (Workshop / Curated / Engine import), prefix naming convention, companion `.prompt.txt` rule. The structural layer underneath governance Bibles.

### Changed

- `.claude-plugin/plugin.json` — version bumped `0.1.0` → `0.2.0`. PostToolUse Write|Edit chain extended with the two new Unity advisory hooks.
- `README.md` — Hooks section documents Unity auto-opt-in + manual pre-commit template.

### Compatibility

- Unity safeguards: tested on Unity 2022 LTS / Unity 6 (6000.x). Zero impact on Godot/Unreal/GameMaker/non-Unity projects (auto-opt-in via filesystem detection).
- Meta-audit skills + governance assets + workflow rules: engine, genre, and platform agnostic. Apply equally to 2D / 3D / mobile / PC / console / web projects, across solo and team workflows.
- No new dependencies (`jq` optional, falls back to `grep`).

### Origin

Distilled from production use on a multi-month Unity 6 PC/console game project. Patterns surfaced after repeated incidents — `.meta`-corruption near-misses, asset tone drift across sessions, surprise paid-API spend, mid-batch verification gaps. Promoted to plugin tier when the patterns proved reusable across domains (sound vs art vs narrative) and across services (Suno vs ElevenLabs vs Midjourney vs Tripo).

## v0.1.0 — 2026-04-22

Initial release. 34 specialist agents, 72 workflow skills, production hooks (SessionStart/PreToolUse/PostToolUse/Notification/PreCompact/PostCompact/Stop/SubagentStart/SubagentStop). Engine-agnostic.
