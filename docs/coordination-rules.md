# Agent Coordination Rules

1. **Vertical Delegation**: Leadership agents delegate to department leads, who
   delegate to specialists. Never skip a tier for complex decisions.
2. **Horizontal Consultation**: Agents at the same tier may consult each other
   but must not make binding decisions outside their domain.
3. **Conflict Resolution**: When two agents disagree, escalate to the shared
   parent. If no shared parent, escalate to `creative-director` for design
   conflicts or `technical-director` for technical conflicts.
4. **Change Propagation**: When a design change affects multiple domains, the
   `producer` agent coordinates the propagation.
5. **No Unilateral Cross-Domain Changes**: An agent must never modify files
   outside its designated directories without explicit delegation.

## Producer 행동 프로세스

`producer` 에이전트가 작업을 받았을 때 따르는 5단계:

| 단계 | 행동 | 설명 |
|------|------|------|
| **1. 분석** | 요청 파악 | 어떤 에이전트가 필요한지, 어떤 문서를 참조할지 판단 |
| **2. 분해** | 작업 분리 | 에이전트별 독립 단위로 분해. 의존성 없으면 병렬 가능 표시 |
| **3. 위임** | 에이전트 스폰 | 각 서브에이전트에 목표, 파일 경로, 완료 조건을 전달 |
| **4. 통합** | 결과 검토 | 충돌/누락 확인, 크로스 도메인 영향 체크 |
| **5. 보고** | 사용자에게 요약 | 완료 내용 + 변경 파일 + 확인 필요 사항 (코드 상세 생략) |

## 팀 간 협의 순서

크로스 도메인 작업 시 반드시 협의 순서를 따른다:

| 상황 | 협의 순서 |
|------|----------|
| 밸런스 공식 변경 | `systems-designer` → `gameplay-programmer` 구현 |
| GDD 변경 후 구현 | `game-designer` → 해당 도메인 에이전트 |
| AI 행동 변경 | `ai-programmer` 초안 → `systems-designer` 밸런스 검토 |
| UI 플로우 변경 | `ui-programmer` → `game-designer` 승인 |
| 아키텍처 리팩토링 | `lead-programmer` → `technical-director` 승인 → 실행 |
| 성능 최적화 | `performance-analyst` 프로파일링 → `gameplay-programmer` 수정 |
| 스테이지 난이도 조정 | `level-designer` → `systems-designer` 공식 검토 |
| 경제 밸런스 변경 | `economy-designer` → `systems-designer` → `gameplay-programmer` |

### 협의 결과 전달 형식

2차 에이전트 스폰 시, 1차 에이전트의 결론을 아래 형식으로 전달한다:

```
[{에이전트명} 협의 결과]
{핵심 결론 요약}
---
위 내용을 바탕으로 {구체적 작업 지시}
```

## 보고 형식

에이전트 작업 완료 시 아래 형식을 따른다:

```
## 완료 보고
- 완료된 작업 요약 (bullet)
- 변경된 파일 목록
- 확인이 필요한 사항 (있을 경우)
```

구현 상세, 코드 블록, 긴 설명은 보고서에 포함하지 않는다.
세션 로그(`production/session-logs/`)에도 이 형식을 따른다.

## 신규 에이전트 채용 규칙

`docs/team-staging-plan.md`에 정의되지 않은 에이전트가 필요할 경우,
직접 스폰하지 않고 **사용자에게 먼저 보고한다**.

보고 형식:
```
## 신규 에이전트 채용 요청
- 필요한 이유: [기존 에이전트로 커버 안 되는 이유]
- 담당 영역: [어떤 작업을 맡길지]
- 제안 에이전트명: [예: vfx-artist, narrative-designer]
- 추가할 프로젝트 단계: [어느 Stage에 배치할지]

승인하시겠습니까?
```

사용자 승인 후:
1. `docs/team-staging-plan.md`에 해당 에이전트 추가
2. 필요시 `.claude/agents/` 하위에 에이전트 정의 파일 생성
3. 이후부터 정식 사용

## 작업 후 문서 업데이트 규칙

모든 에이전트는 작업 완료 시 아래를 체크한다:

1. **GDD 영향 체크**: 구현이 `design/gdd/` 문서의 내용을 변경했는가?
   → 변경 시 해당 GDD 문서 업데이트
2. **아키텍처 영향 체크**: 새 시스템/매니저를 추가했는가?
   → 변경 시 `docs/architecture/` 문서 업데이트
3. **데이터 스키마 변경 체크**: CSV/ScriptableObject 구조가 바뀌었는가?
   → 변경 시 관련 데이터 문서 업데이트
4. **세션 상태 업데이트**: `production/session-state/active.md` 반영

문서 업데이트 없이 구현만 완료하는 것은 "미완료"로 간주한다.

## Model Tier Assignment

Skills and agents are assigned to model tiers based on task complexity:

| Tier | Model | When to use |
|------|-------|-------------|
| **Haiku** | `claude-haiku-4-5-20251001` | Read-only status checks, formatting, simple lookups — no creative judgment needed |
| **Sonnet** | `claude-sonnet-4-6` | Implementation, design authoring, analysis of individual systems — default for most work |
| **Opus** | `claude-opus-4-6` | Multi-document synthesis, high-stakes phase gate verdicts, cross-system holistic review |

Skills with `model: haiku`: `/help`, `/sprint-status`, `/story-readiness`, `/scope-check`,
`/project-stage-detect`, `/changelog`, `/patch-notes`, `/onboard`

Skills with `model: opus`: `/review-all-gdds`, `/architecture-review`, `/gate-check`

All other skills default to Sonnet. When creating new skills, assign Haiku if the
skill only reads and formats; assign Opus if it must synthesize 5+ documents with
high-stakes output; otherwise leave unset (Sonnet).

## Subagents vs Agent Teams

This project uses two distinct multi-agent patterns:

### Subagents (current, always active)
Spawned via `Task` within a single Claude Code session. Used by all `team-*` skills
and orchestration skills. Subagents share the session's permission context, run
sequentially or in parallel within the session, and return results to the parent.

**When to spawn in parallel**: If two subagents' inputs are independent (neither
needs the other's output to begin), spawn both Task calls simultaneously rather
than waiting. Example: `/review-all-gdds` Phase 1 (consistency) and Phase 2
(design theory) are independent — spawn both at the same time.

### Agent Teams (experimental — opt-in)
Multiple independent Claude Code *sessions* running simultaneously, coordinated
via a shared task list. Each session has its own context window and token budget.
Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable.

**Use agent teams when**:
- Work spans multiple subsystems that will not touch the same files
- Each workstream would take >30 minutes and benefits from true parallelism
- A senior agent (technical-director, producer) needs to coordinate 3+ specialist
  sessions working on different epics simultaneously

**Do not use agent teams when**:
- One session's output is required as input for another (use sequential subagents)
- The task fits in a single session's context (use subagents instead)
- Cost is a concern — each team member burns tokens independently

**Current status**: Not yet used in this project. Document usage here when first adopted.

## Parallel Task Protocol

When an orchestration skill spawns multiple independent agents:

1. Issue all independent Task calls before waiting for any result
2. Collect all results before proceeding to dependent phases
3. If any agent is BLOCKED, surface it immediately — do not silently skip
4. Always produce a partial report if some agents complete and others block
