# Changelog

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
