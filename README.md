# Claude Code Game Studios

Claude Code 플러그인 형태로 패키징된 *완전한* 게임 개발 스튜디오.

**전문 에이전트 34종** · **워크플로우 skill 76종** · **production hooks** · **거버넌스/워크플로우 자산 (v0.2.0+)** — 프리프로덕션 → 프로덕션 → QA → 릴리스 → 라이브 옵스 전 단계 커버.

실제 게임 스튜디오 구조를 그대로 모사: 디렉터(creative / technical / producer)가 부서장(design / programming / art / audio / narrative / QA)을 조율하고, 부서장이 다시 스페셜리스트(gameplay programmer / level designer / economy designer 등)를 조율합니다. 모든 디자인 에이전트와 템플릿은 검증된 게임 디자인 이론(MDA, Self-Determination Theory, Flow State, Bartle Player Types)에 기반합니다.

엔진 무관(Engine-agnostic). Godot, Unity, Unreal, GameMaker, 또는 커스텀 엔진 모두에서 동작합니다.

## 목차

- [무엇이 들어있나](#무엇이-들어있나)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [v0.2.0 신규 — 거버넌스/워크플로우 자산 사용 가이드](#v020-신규--거버넌스워크플로우-자산-사용-가이드)
- [권장 디렉터리 구조](#권장-디렉터리-구조)
- [커스터마이징](#커스터마이징)
- [라이선스](#라이선스)

---

## 무엇이 들어있나

### 에이전트 (34종)

디렉터 · 부서장 · 스페셜리스트 — 실제 게임 스튜디오 조직도 그대로:

- **디렉터 (Opus급)**: `creative-director`, `technical-director`, `producer`
- **디자인**: `game-designer`, `systems-designer`, `economy-designer`, `level-designer`, `narrative-director`, `world-builder`, `writer`, `live-ops-designer`
- **프로그래밍**: `lead-programmer`, `gameplay-programmer`, `ui-programmer`, `ai-programmer`, `engine-programmer`, `network-programmer`, `tools-programmer`, `prototyper`
- **아트/오디오**: `art-director`, `technical-artist`, `audio-director`, `sound-designer`
- **QA/Ops**: `qa-lead`, `qa-tester`, `performance-analyst`, `security-engineer`, `accessibility-specialist`, `localization-lead`, `release-manager`, `devops-engineer`
- **UX/커뮤니티/분석**: `ux-designer`, `community-manager`, `analytics-engineer`

### Skill (76종)

개발 단계별로 정리:

- **프리프로덕션**: `/start`, `/brainstorm`, `/map-systems`, `/design-system`, `/review-all-gdds`, `/consistency-check`, `/create-architecture`, `/architecture-decision`, `/architecture-review`, `/create-control-manifest`, `/art-bible`, `/ux-design`, `/ux-review`, `/setup-engine`, `/adopt`, `/gate-check`
- **스프린트/프로덕션**: `/create-epics`, `/create-stories`, `/story-readiness`, `/dev-story`, `/story-done`, `/quick-design`, `/sprint-plan`, `/sprint-status`, `/scope-check`, `/estimate`, `/propagate-design-change`, `/reverse-document`, `/asset-spec`, `/asset-audit`
- **코드 품질**: `/code-review`, `/tech-debt`, `/design-review`
- **QA**: `/qa-plan`, `/test-setup`, `/test-helpers`, `/test-evidence-review`, `/test-flakiness`, `/regression-suite`, `/smoke-check`, `/soak-test`, `/bug-report`, `/bug-triage`, `/balance-check`, `/playtest-report`, `/content-audit`
- **팀 오케스트레이션**: `/team-audio`, `/team-combat`, `/team-level`, `/team-live-ops`, `/team-narrative`, `/team-polish`, `/team-qa`, `/team-release`, `/team-ui`
- **릴리스/Ops**: `/release-checklist`, `/launch-checklist`, `/day-one-patch`, `/hotfix`, `/patch-notes`, `/changelog`, `/milestone-review`, `/retrospective`, `/security-audit`, `/perf-profile`, `/localize`, `/onboard`, `/project-stage-detect`, `/help`, `/prototype`, `/skill-test`, `/skill-improve`
- **메타 감사 (v0.2.0 신규)**: `/sot-audit` (다중 source-of-truth 정합성 감사), `/legacy-purge` (피봇/마이그레이션 잔재 청소)
- **거버넌스 (v0.2.0 신규)**: `/governance-bible-init` (사운드/아트/내러티브 등 도메인 Bible 부트스트랩), `/api-cost-gate` (유료 AI API 호출 전 4건 명시 승인 게이트)

### Hooks

- `SessionStart`: 프로젝트 컨텍스트 로드 + 누락 문서 감지
- `PreToolUse` (Bash): git 커밋/푸시 검증 (한국어 컨벤션 기본 — 프로젝트별 오버라이드 가능)
- `PostToolUse` (Write/Edit): 자산 명명 검증, skill 파일 변경 감지, **Unity 전용 안전장치 (자동 opt-in, v0.2.0+)**
- `Notification/PreCompact/PostCompact/Stop`: 컨텍스트 압축 및 세션 로깅
- `SubagentStart/Stop`: 에이전트 활동 로깅

#### Unity opt-in (v0.2.0+)

플러그인이 Unity 프로젝트(`Assets/` + `ProjectSettings/` 존재)를 자동 감지하면 두 advisory hook 이 활성화됩니다:

- `unity-meta-check.sh` — `.cs`/`.shader`/`.prefab` 등을 짝 `.meta` 없이 작성한 경우 경고 (다른 머신에서 GUID 깨짐 방지)
- `unity-animator-string-lint.sh` — `Animator.SetBool("name", ...)` 같은 문자열 lookup 패턴 감지 시 경고 (`StringToHash` 캐싱 권고)

추가로 수동 opt-in git pre-commit 템플릿(`templates/githooks/unity-pre-commit`)이 있어 `.meta` 누락 커밋을 *차단*. 활성화는 [docs/engine/unity-setup.md](docs/engine/unity-setup.md) 참고.

비-Unity 프로젝트에서는 모두 즉시 종료(silent exit) — 영향 없음.

### 템플릿 & 룰 (v0.2.0 신규)

엔진/장르/플랫폼 무관하게 적용되는 워크플로우 자산:

| 자산 | 위치 | 용도 |
|---|---|---|
| 회의록 템플릿 | [docs/templates/meeting-template.md](docs/templates/meeting-template.md) | 헤더 메타박스 + D-table 결정 + 메모리화 프로토콜 |
| API CLI 템플릿 | [docs/templates/api-cli-template.py](docs/templates/api-cli-template.py) | pay-as-you-go 외부 AI API wrapper 스캐폴드 (env 로드 / 인증 / 비동기 폴링 / 동기 binary / 다운로드) |
| 토큰 효율 룰 | [docs/rules/token-efficiency.md](docs/rules/token-efficiency.md) | R1~R6 (커밋 5~15줄 / 회의록 80줄 / 일괄 작업 보고 / 병렬 read / 메모리 규율 / 응답 길이) |
| 자산 정리 룰 | [docs/rules/artifact-organization.md](docs/rules/artifact-organization.md) | 3-zone 규율 (Workshop / Curated / Engine) + prefix 명명 규칙 + .prompt.txt 동반 룰 |

---

## 설치

### 옵션 1 — GitHub 마켓플레이스에서 설치 (권장)

```bash
# Claude Code 안에서:
/plugin marketplace add dawn840705/claude-code-game-studios
/plugin install claude-code-game-studios@game-studios
```

이미 0.1.0 이 설치되어 있는 프로젝트는 업데이트만:

```bash
/plugin update claude-code-game-studios@game-studios
```

### 옵션 2 — 로컬 마켓플레이스 (개발 / 포크 시)

```bash
git clone https://github.com/dawn840705/claude-code-game-studios.git /path/to/local
# Claude Code 안에서:
/plugin marketplace add /path/to/local
/plugin install claude-code-game-studios@game-studios
```

### 옵션 3 — 수동 (프로젝트 안에 symlink)

```bash
cd /your/game/project
ln -s /path/to/claude-code-game-studios/agents .claude/agents
ln -s /path/to/claude-code-game-studios/skills .claude/skills
ln -s /path/to/claude-code-game-studios/hooks  .claude/hooks
ln -s /path/to/claude-code-game-studios/rules  .claude/rules
ln -s /path/to/claude-code-game-studios/docs   .claude/docs
```

(주의: 옵션 3 은 플러그인 시스템을 우회 — hook 이 자동 등록되지 않습니다. `.claude-plugin/plugin.json` 의 `hooks` 블록을 프로젝트의 `.claude/settings.json` 에 직접 복사해야 합니다.)

---

## 빠른 시작

설치 후 신규 게임 프로젝트에서:

1. `/start` — 첫 사용 onboarding. 현 위치 파악 후 적합한 워크플로우로 안내
2. `/setup-engine` — 엔진(Unity / Unreal / Godot / GameMaker / 커스텀) + 버전 핀
3. `/brainstorm` — 컨셉 0 에서 구조화된 게임 컨셉 문서까지 가이드
4. `/map-systems` — 컨셉을 시스템 단위로 분해, 우선순위 도출
5. `/design-system <system>` — 각 시스템의 GDD 작성
6. `/create-architecture` → `/create-epics` → `/create-stories` → `/dev-story`

진행 중인 프로젝트라면: `/adopt` 가 기존 자산을 감사하고 마이그레이션 계획을 만들어줍니다.

---

## v0.2.0 신규 — 거버넌스/워크플로우 자산 사용 가이드

v0.2.0 부터 추가된 자산은 *AI 생성 자산을 다루는 1인/소규모 개발 워크플로우*에 특히 유용합니다.

### 도메인 Bible 부트스트랩 (`/governance-bible-init`)

사운드 / 아트 / 내러티브 등 *창작 도메인* 마다 Anchor + Bible 패턴을 자동 부트스트랩:

```bash
/governance-bible-init sound chapter-1
/governance-bible-init art chapter-1
/governance-bible-init narrative chapter-1
```

→ `Documents/<도메인>Design/Anchors/` 폴더 + Bible README.md(톤 필터 + 명명 규칙 + 카테고리 표) 자동 생성. 첫 anchor 자산은 `Anchors/` 안에 `mus_*.mp3` / `char_*.png` 등 prefix 명명으로 저장 + 동명 `.prompt.txt` (재현 가능한 호출 명령) 동반.

이후 모든 신규 자산은 *Anchor 와 5~10초 A/B 비교 → 채택/재시도(1회)/기각* 의사결정 워크플로우 적용. 드리프트 방지의 핵심 메커니즘.

### 유료 API 호출 게이트 (`/api-cost-gate`)

Suno / ElevenLabs / Midjourney / Tripo / OpenAI 등 모든 pay-as-you-go AI 호출 *전*에 4건 disclosure 강제:

```bash
/api-cost-gate suno combat-bgm-30s
```

표시 항목:
1. 호출 종류 (정확한 endpoint / model / mode)
2. 비용 추정 (credits / characters / 달러 + 현재 잔액)
3. 목적 (무엇을 / 왜)
4. 활용 (어디에 저장 / 어떻게 평가 / 채택 기준)

→ 사용자 명시 OK 후에만 호출 실행. **Auto mode 도 우회 X.**

### 다중 source-of-truth 감사 (`/sot-audit`)

FSM / 입력 바인딩 / 세이브 스키마 / 로컬라이제이션 / 오디오 mixer / 셰이더 uniform / 네트워크 메시지 등 *여러 곳에 정의가 흩어진* 시스템의 정합성을 N-witness 매트릭스로 감사:

```bash
/sot-audit player-fsm \
  doc=design/specs/player-fsm.md \
  enum=src/PlayerStateType.cs \
  asset=assets/animator/PlayerAnim.controller \
  callsites=src/PlayerController.cs
```

→ 심각도(🚨 High / ⚠️ Medium / ℹ️ Low) 분류된 mismatch 보고서. silent-fail 위험을 *런타임 사고 전*에 검출.

### 마이그레이션 잔재 청소 (`/legacy-purge`)

장르 피봇 / API deprecation / 플랫폼 변경 / 아키텍처 재작성 후 잔존하는 레거시 코드/문서/자산을 카테고리별 grep 으로 감사:

```bash
/legacy-purge mobile-vertical pc-horizontal "Assets/02.Scripts/**"
```

→ 카테고리별 발견 표 + 정책 문서 cross-reference. **자동 삭제 X** — 인간 검토 필수.

### 회의록 / API CLI 템플릿

새 회의 작성 / 새 외부 API wrapper 작성 시 즉시 사용 가능한 스캐폴드:

- `cp <plugin>/docs/templates/meeting-template.md Documents/Meetings/YYYY-MM-DD-<주제>.md`
- `cp <plugin>/docs/templates/api-cli-template.py Tools/<NewService>API/<service>.py`

각 템플릿 내부의 `⚠️ FIXME` 항목만 채우면 됩니다.

### 워크플로우 룰 핀

새 프로젝트의 `CLAUDE.md` 최상단에 추가하면 모든 세션이 자동으로 룰 적용:

```markdown
## 워크플로우 룰

- 토큰 효율: docs/rules/token-efficiency.md (R1~R6)
- 자산 정리: docs/rules/artifact-organization.md (Workshop / Curated / Engine 3-zone + prefix 명명)
- 회의록: docs/templates/meeting-template.md 포맷 사용
```

---

## 권장 디렉터리 구조

에이전트와 skill 은 프로젝트 루트에 다음 구조를 가정합니다:

```
design/gdd/                # GDD 문서
production/sprints/        # 스프린트 계획
production/bugs/           # 버그 리포트
src/                       # 소스 코드 (엔진별)
tests/                     # 테스트 파일
.claude/                   # 프로젝트 단위 오버라이드 (선택)
  └── docs/
      └── technical-preferences.md   # 엔진 + 버전 핀

# v0.2.0 자산 정리 룰 적용 시 (artifact-organization.md):
Tools/<Service>API/output/        # 작업장 (gitignore)
Documents/<Domain>Design/Anchors/ # 도메인별 Bible + anchor 자산
Documents/Meetings/               # 회의록
Documents/api-cost-log.md         # 유료 API 호출 누적 기록
```

skill 들이 진행에 따라 자동으로 폴더를 생성합니다.

---

## 커스터마이징

- **프로젝트별 오버라이드**: 프로젝트의 `.claude/agents/<name>.md` 또는 `.claude/skills/<name>/SKILL.md` 작성. 프로젝트 파일이 플러그인 파일을 덮어씁니다.
- **개인 환경설정**: `docs/CLAUDE-local-template.md` 를 프로젝트 루트에 `CLAUDE.local.md` 로 복사 (gitignore 처리됨).
- **룰**: `rules/` 폴더에 시스템별 코딩 표준(gameplay-code, shader-code, ui-code 등). 코드 리뷰 에이전트가 참조.

---

## 상태 & 단계

- 프리프로덕션 · 프로덕션 · 폴리시 & QA · 릴리스 · 라이브옵스 — 모든 단계 커버.
- 오케스트레이터는 *현재 단계* 와 관련된 에이전트만 spawn 합니다. 전체 매핑은 `docs/agent-coordination-map.md` 참고.

---

## 변경 이력

자세한 버전별 변경 사항은 [CHANGELOG.md](CHANGELOG.md) 참고.

- **v0.3.0** (2026-05-17) — Unity UI/UX 영구 룰 5건 + `UIAutoSelectGuardian.cs` helper (`docs/engine/unity-ui-guidelines.md`, `templates/unity/`) + Unity scene-loading anti-pattern (`docs/engine/unity-scene-loading-patterns.md`) + Unity MCP workflow 패턴 (`docs/engine/unity-mcp-workflow.md`) + 서브 에이전트 병행 호출 룰 (`rules/subagent-collaboration.md`, `docs/templates/subagent-meeting-template.md`)
- **v0.2.0** (2026-05-04) — Unity opt-in 안전장치 + 메타 감사 skill (sot-audit, legacy-purge) + 거버넌스/워크플로우 자산 (governance-bible-init, api-cost-gate, 회의록/API CLI 템플릿, token-efficiency/artifact-organization 룰)
- **v0.1.0** (2026-04-22) — 초기 릴리스. 34 에이전트 + 72 skill + production hooks.

---

## 감사

Cannon Kingdom 프로젝트에서 만들어 검증한 후, 게임 프로젝트 간 이식성을 위해 독립 플러그인으로 추출. v0.2.0 의 거버넌스/워크플로우 자산은 StarDiver(Unity 6 PC/콘솔 로그라이트 커버 슈터) 프로덕션에서 누적된 노하우의 1차 회수.

---

## 라이선스

MIT
