# Changelog

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
