# AX LABS 블로그 → claude-code-studios 적용 감사

> 조사 범위: `theaxlabs.com/blog` 전 카테고리. `agent-design` 67편(6p) · `methodology` 36편(3p) 전문 정독,
> `strategy`/`org-people`/`field-notes` 36편 스캔 후 8편 정독. **총 정독 111편.**
> 기준 커밋 시점: 2026-08-04. 대조 대상: `CLAUDE.md`(214줄), `rules/`(15), `docs/`, `hooks/`(16), `scripts/`(10), `skills/`(85), `agents/`(45).

---

## 0. 한 문장 요약

우리 저장소는 **"스크립트가 판정한다"는 원칙은 이미 최상급**인데, 그 원칙이 **적용되지 않은 구멍이 다섯 군데** 있다.
그리고 CLAUDE.md 214줄 중 약 100줄은 에이전트가 파일을 열어 확인할 수 있는 정보라, 정작 중요한 지시의 밀도를 떨어뜨리고 있다.

---

## 1. 기준이 되는 원문 — 「600억 토큰을 태우고 남은 8줄」

컨텍스트 파일은 **지식 저장소가 아니라 편향 교정 프롬프트**다. 판단 기준 3가지:

| # | 분류 | 처리 |
|---|---|---|
| 1 | 에이전트가 스스로 알아낼 수 있는 것 (디렉터리 구조, 설치 패키지, 코드 스타일) | **뺀다** |
| 2 | 알면서도 하지 않는 성향 (삭제, 단순화, 기존 방식 조사, 문서 확인, 임시방편 거부) | **반드시 넣는다** |
| 3 | 팀마다 답이 갈리는 지점 (하위 호환, 테스트 강도, 로깅 수준) | **우리 선택을 명시한다** |

핵심 논거: 300줄 안에 핵심 지시 3줄이 섞이면 그 3줄은 나머지 297줄에 묻힌다.
컨텍스트 창 안에서는 목차·강조 같은 장치가 작동하지 않는다. **품질은 길이가 아니라 밀도다.**

---

## 2. 우리 CLAUDE.md 214줄 감사

| 줄 | 섹션 | 분류 | 판정 |
|---|---|---|---|
| 5–8 | Your role | 3 | 유지 (4줄) |
| 9–31 | Domain packs | 3 | 유지 — 라우팅 정책은 파일에서 유추 불가 |
| 32–57 | Development stages — GAME (26줄) | 1 | **압축** — `docs/workflow-catalog.yaml`이 SoT인데 본문에 복제됨 |
| 58–90 | Development stages — PRODUCT (33줄) | 1 | **압축** — 위와 동일 |
| 91–99 | Agent usage rules | 2 | 유지 — 특히 규칙 5 "에이전트 요약은 의도지 결과가 아니다"는 최상급 유형2 |
| 100–118 | Key workflows (19줄) | 1 | **압축** — 카탈로그 중복. `/help`·`/project-stage-detect`가 이미 판정 |
| 119–131 | Self-loop quality rule | 2 | 유지하되 3줄 요약 + `rules/self-loop.md` 포인터 |
| 132–154 | Deterministic gates | 2+3 | **유지 (최우선)** — 이 저장소의 정체성 |
| 155–170 | Route hint | 2 | 유지 |
| 171–190 | File conventions (20줄) | 1 | **압축** — `ls`로 확인 가능. "빈 폴더 미리 만들지 말 것" 1줄만 유형2 |
| 191–198 | Don't do this | 2 | 유지 |
| 199–203 | Extending the plugin | 3 | 유지 |
| 204–214 | Reference docs (11줄) | 1 | **삭제** — `ls docs/`로 확인 가능 |

**감축 추정: 약 95줄 → 최종 120줄 안팎.** 삭제가 아니라 SoT 포인터로 교체하는 것이므로 정보 손실 없음.

### 가장 큰 공백 — 유형2가 통째로 비어 있다

우리 CLAUDE.md의 유형2 항목은 **전부 오케스트레이션 편향**(에이전트 남발 금지, 훅 우회 금지, 요약 신뢰 금지)이다.
**구현 편향 교정이 0줄이다.** 그런데 이 플러그인이 스폰하는 45개 에이전트는 실제로 코드를 쓴다.
원문 8줄 중 우리에게 없는 것: 기존 제품 선(先)조사 · 가장 단순한 구현 · 레이어로 성장 · 재구현 금지 · 기존 의존성 확인 · 임시방편 거부.

`rules/` 아래 코드 규칙 15종이 있지만 **path-scoped라 압축 후 사라진다**
(「맥락은 줄이고 기억은 남겨라」: 압축 후 CLAUDE.md와 auto memory는 재주입되지만 path-scoped rule은 해당 파일을 다시 읽기 전까지 복원되지 않는다).

### 우리 팀에 맞게 뒤집어야 하는 줄 — 원문 2번(하위 호환)

원문은 "하위 호환을 유지하지 말고 쓰이지 않는 경로를 삭제하라"고 한다.
**우리는 그대로 쓰면 안 된다.** 이 저장소는 사용자가 설치하는 배포물이고, 스킬 85개 · 에이전트 45개 · 훅 16개의 이름과 산출물 경로는 사실상 공개 API다.
`/dev-story`를 쓰던 사용자 프로젝트가 다음 버전에서 깨지면 안 된다.

대체 문안:

```markdown
- 스킬 이름·슬래시 명령·산출물 경로 규약의 하위 호환을 깨지 마세요.
  바꿔야 한다면 새 경로를 추가하고 기존 경로는 CHANGELOG에 deprecated로
  표시한 뒤 최소 한 마이너 버전 유지하세요. 제거는 별도 작업으로 분리합니다.
- 반면 플러그인 내부 구현(스크립트 헬퍼, 훅 lib, 템플릿 내부 구조)에는
  호환 레이어를 쌓지 말고 쓰이지 않는 경로를 삭제하세요.
```

---

## 3. 실측으로 확인된 결함 1건

**`hooks/validate-assets.sh` — 차단해야 할 에러가 차단되지 않는다.**

```
hooks/validate-assets.sh:7   # exit 1 = blocking error (build-breaking issues...)
hooks/validate-assets.sh:107 exit 1     ← "ERRORS (Blocking)" 출력 후
```

Claude Code 훅에서 **차단은 exit 2**이고, exit 1은 비차단 에러로 흘러간다.
같은 저장소의 `validate-commit.sh`·`validate-push.sh`는 올바르게 exit 2를 쓴다.
`docs/deterministic-gates.md`가 "2 = abort"를 이미 선언했으므로, 이것은 새 정책이 아니라 **기존 계약의 미준수**다.

부수 확인: `validate-skill-change.sh` · `unity-meta-check.sh` · `unity-animator-string-lint.sh`는 전부 exit 0으로만 끝난다(경고 전용).
`post-compact.sh` · `notify.sh`에는 exit 문 자체가 없다. **판정을 낸 적 없는 게이트가 통과로 읽힐 여지**가 있으므로 문서에 "경고 전용"임을 명시해야 한다.

---

## 4. 적용 후보 — 우선순위

### Tier 1 — 지금 하는 것 (기존 원칙의 미완성분 채우기)

| # | 항목 | 대상 | 근거 글 | 왜 지금인가 |
|---|---|---|---|---|
| 1 | `exit 1` → `exit 2` 수정 + 훅별 판정 능력 표 | `hooks/validate-assets.sh`, `docs/hooks-reference.md` | 품질 게이트는 hooks다 | 실측 확인된 유일한 버그. 계약 위반 상태 |
| 2 | **unsafe-success 판정 축 신설** | `scripts/verify_policy.py`(신규), `skills/story-done` | 성공도 실패로 쪼개야 한다 / 도구 호출 직전이 통제점이다 | 현 exit 0/1/2/3은 "게이트가 돌았나"만 본다. "테스트를 고쳐서 통과", "`--no-verify` 커밋", "팩 위반 스폰"은 지금 **exit 0으로 기록되어 성공률에 섞인다**. CLAUDE.md "Don't do this"가 문장으로만 존재하고 판정 주체가 없다 |
| 3 | **CLAUDE.md 밀도 감사 + 유형2 8줄 신설** | `CLAUDE.md` | 600억 토큰을 태우고 남은 8줄 | §2 참조. 구현 편향 교정이 0줄. 하위 호환은 우리 버전으로 뒤집어 쓸 것 |
| 4 | **서브에이전트 4줄 계약: 입력 / 금지 / 판정 기준 / 반환 형식** | `rules/subagent-collaboration.md` | Subagent는 context 방화벽이다 / Fan-out은 계약 없인 위험하다 | 현 §3은 "self-contained 프롬프트, 300줄 한도"까지만. **금지(무엇을 모르게 할지)와 반환 형식(main에 올리지 않을 것)이 없어** 격리 이득이 새어나간다. 반환은 요약문이 아니라 Artifact(파일 경로 + 상태) |
| 5 | **스킬 description 오선택 게이트** | `scripts/lint_skills.py` | 툴 스키마가 에이전트를 가른다 / Skill은 프롬프트가 아니다 | 현재 `description`이 **비어 있는지만** 검사(L193). 스킬 85 + 에이전트 45 = 130 선택지를 한 오케스트레이터가 고르는데, "언제 쓰지 않는가" 누락과 근접 중복 description을 아무도 안 본다. 스크립트가 판정 가능 = 우리 철학 그대로 |

### Tier 2 — 다음 마이너 (새 축을 추가)

| # | 항목 | 대상 | 근거 글 | 요지 |
|---|---|---|---|---|
| 6 | **self-loop을 증거 기반 수정 루프로 개정** | `rules/self-loop.md` | 고치기 전에 증거를 요구하라 / 출력은 약속이 아니라 계약이다 | 현행 "최저점부터 고쳐라"는 **revise 편향**을 만든다(증거 없이 멀쩡한 부분까지 재작성). 기본값을 preserve로 바꾸고 defect ticket 4필드(claim_id·defect_type·evidence·severity)를 받는다. 반복 입력은 전체 맥락이 아니라 **검증 오류·실패 필드·허용값·직전 출력만** |
| 7 | **BLOCKED(보류) 종료 + 실패 분류** | `rules/self-loop.md` | 에이전트는 끝나야 일한다 / 재시도는 신뢰성이 아니다 | 지금은 "8점 전부" 또는 "5회/2회 정체"뿐. 권한·데이터·사람 판단이 없어 더 못 도는 상태가 실패로 오분류된다. retryable만 반복, hard_error(스키마 위반·권한·정책)는 즉시 종료 |
| 8 | **검증 라우팅** | `rules/verify-route.md`(신규) 또는 route-hint 확장 | 검증도 라우팅해야 산다 | route-hint는 **생성 측만** 라우팅한다(에이전트 몇 개). 그래서 오탈자 수정에 `/team-qa` 풀세트가 붙고 되돌리기 어려운 변경이 `/smoke-check` 하나로 통과한다. 위험도 4등급 → verifier 매핑, 치명 등급은 자동 실행 금지 |
| 9 | **compaction 손실 프로브** | `hooks/post-compact.sh` | 압축 손실은 재연으로 잡는다 / 맥락은 줄이고 기억은 남겨라 | `pre-compact.sh`/`post-compact.sh`는 **판정을 내지 않는 유일한 게이트 지점**이다. 압축 직전 원장에서 결정사실·제약·근거 3종 probe를 뽑아 대조, 불일치면 exit 1. 동시에 직전 활성 `rules/*.md` 경로 재주입 |
| 10 | **스토리 티켓에 `execution_type` + Tool boundary** | `skills/create-stories`, `skills/story-readiness` | 백로그는 사람만 보지 않는다 | 45 에이전트를 굴리면서 "이 스토리를 사람이 하나, 에이전트가 하나, 하이브리드인가"를 스토리 파일이 기록하지 않는다. 필드 존재 여부라 스크립트 판정 가능 → `/story-readiness`가 **위임 가능 조건 게이트**로 승격(미충족 시 human 티켓 강등) |
| 11 | **골든 궤적 회귀** | `tests/trajectories/` + `scripts/verify_trajectory.py`(신규) | 하네스 변경은 회귀로 검증한다 / 에이전트 테스트는 재생이다 | `regression-suite`는 *사용자 제품*만 본다. CLAUDE.md 라우팅 표나 `agent-packs.yaml` 한 줄을 고치면 85개 스킬의 팬아웃이 조용히 바뀌는데 **플러그인 자신의 행동은 아무도 회귀 검증하지 않는다**. `check_phase.py`의 글롭 판정 인프라를 재사용 가능 |
| 12 | **레슨 → 회귀 승격 경로 (write path)** | `rules/lesson-capture.md`, `skills/lesson-review` | 골든셋은 테스트가 아니다 / 기억은 저장이 아니라 정책이다 / 실패 로그가 에이전트를 키운다 | 레슨은 `Documents/Lessons/`에 **쌓이기만 하고** `rules/`·`CLAUDE.md`·`regression-suite.md`로 승격되는 경로가 없다. 후보생성 → 검증(출처·소유자·유효기간) → 반영(update/supersede/**reject**). 신규 레슨이 기존과 모순될 때의 처리와 폐기 기준도 없음 |

### Tier 3 — 검토만 (가치는 있으나 현 규모 대비 과설계 위험)

| 항목 | 근거 글 | 유보 사유 |
|---|---|---|
| 게이트 출력 4필드 구조화(`status`/`reason`/`next_action`/`evidence`) | 품질 게이트는 hooks다 | 가치 높음. 다만 10개 스크립트 전체 개편이라 Tier 1 완료 후 |
| 런타임 비용 차단선(세션 누적 상한, retry 상한) | 비용 초과는 장애다 | `skills/api-cost-gate`가 건당 게이트를 이미 담당. 누적 축만 증분 |
| 에이전트 registry 4필드(owner/eval/scope) — `docs/agent-packs.yaml` | 업무 기능은 등록돼야 한다 | 45개 × 4필드 = 유지보수 부담. 리뷰 계열 에이전트 tools 축소가 더 실효적 |
| contradiction queue 4분류 | 검색 에이전트는 장부가 필요하다 | `consistency-check`/`sot-audit`에 붙일 것. 우선순위 낮음 |
| `active.md` 3평면 분할(reasoning/대화/감사) | 장기 작업은 상태를 찢어야 산다 | 9번(compaction 프로브)의 부수 효과로 자연히 따라옴 |
| PRD에 permission envelope / eval SLA | AI-Native PRD는 운영 문서다 | `+ai` 프로젝트 한정. 해당 유형이 늘어날 때 |
| 한 PR에 CLAUDE.md 라우팅 + 에이전트 + 스킬 동시 변경 경고 | 에이전트 A/B는 배포가 아니다 | `validate-skill-change.sh`에 붙일 1줄. 저비용이나 저빈도 |

---

## 5. 적용하지 않는 것 (명시적 제외)

층위가 다르거나 우리가 소유하지 않는 레이어다. 나중에 "왜 뺐지" 하지 않도록 기록해 둔다.

- **엔터프라이즈 런타임**: Agent Gateway, MCP 권한 IdP/SCIM, DLP read/sink 경계, PII 마스킹, OTel trace 전파 — 로컬 플러그인에 대응물 없음
- **API 하네스 계층**: Responses API WebSocket, reasoning span replay, tool schema late-loading, prompt cache prefix — 우리는 하네스를 만들지 않고 그 위에서 돈다
- **MCP 서버 구현**: MRTR 상태기계, MCP RC Tasks, A2A Agent Card TCK — 이 플러그인은 MCP 서버를 제공하지 않음
- **RAG/온톨로지**: agentic retrieval, RAG 3단계 평가, RDF 온톨로지 — `sot-audit`의 N-way witness 매트릭스가 이미 더 구체적
- **경영·조직 담론**: AX ROI, 좌석 수 지표, FDE 계약·양성, 챔피언 프로그램, 성인학습 6원칙 — 층위가 다름
- **배포 전략**: shadow/canary/rolling — 사용자 설치형이라 트래픽 분할 개념이 없음

---

## 6. 운영 루틴 — 컨텍스트 파일은 한 번 쓰고 끝나는 문서가 아니다

원문의 핵심 후속 조치. Marcos의 파일도 처음엔 3줄이었고, 반복 관찰된 실패 패턴이 새 줄로 승격되며 8줄이 됐다.

1. 세션이 끝날 때, 결과물을 손으로 고쳐야 했던 지점을 기록한다
2. **같은 유형의 수정이 3회 반복되면** 컨텍스트 파일에 한 줄을 추가한다
3. **분기마다 전체를 다시 읽고, 더 이상 발동되지 않는 줄을 삭제한다**

우리 저장소에는 (1)에 해당하는 `rules/lesson-capture.md`(트리거 5종, 2회 반복 기준)가 있지만 **(2)의 승격 경로와 (3)의 폐기 루틴이 없다** — Tier 2 #12가 이 구멍이다.

### 세션 끝 — 규칙 후보 뽑기

```
이번 세션에서 네가 처음 내놓은 결과물을 내가 어떤 식으로 고쳤는지 되짚어줘.
- 내가 수정한 지점을 유형별로 묶어줘 (예: 불필요한 추상화, 삭제 대신 추가, 문서 미확인)
- 각 유형에 대해, 컨텍스트 파일에 한 줄로 넣으면 다음부터 막을 수 있는 지시를 써줘
- 이미 CLAUDE.md에 있는 내용과 겹치는 건 빼줘
- 이번 작업에만 해당하는 일회성 요구는 규칙 후보에서 제외해줘
```

### 분기마다 — 안 쓰이는 줄 걷어내기

```
CLAUDE.md를 읽고, 각 줄을 다음 세 가지로 분류해줘.
A) 네가 파일을 뒤져 스스로 알아낼 수 있는 정보 → 삭제 후보
B) 지시가 없으면 네 기본 동작이 반대로 갈 항목 → 유지
C) 팀의 선택을 적어둔 항목 → 유지하되 최신인지 나에게 질문
분류 결과를 표로 주고, A로 분류한 줄은 왜 스스로 알 수 있는지 근거를 한 줄씩 적어줘.
```

→ 이 둘은 `/context-audit` 스킬로 묶을 만하다. 세 번째가 특히 중요하다: 모델이 세대를 거듭하면 예전에 필요했던 지시가 불필요해지고, 그 줄을 남겨두면 다시 밀도가 떨어진다.
**컨텍스트 파일에도 첫 번째 원칙 — 쓰이지 않는 경로는 삭제한다 — 이 적용된다.**

---

## 7. 반대 관점 (같이 읽을 것)

이 감사는 "밀도를 높여라"는 한 편의 주장을 축으로 삼았다. 반대 방향의 논거도 있다.

- **8줄은 1인 개발자의 결과물이다.** Marcos는 자기 코드베이스에서 자기 기준으로 600억 토큰을 태웠다. 팀 저장소에서는 "에이전트가 알아낼 수 있는 정보"라도 **사람 기여자가 읽을 필요**가 있어서 남기는 경우가 있다. CLAUDE.md를 줄이려면 그 내용이 `docs/`와 README에 살아 있는지 먼저 확인해야 한다.
- **오케스트레이터용 컨텍스트 파일은 성격이 다르다.** 원문이 상정한 것은 "코드를 쓰는 단일 에이전트"의 지침이다. 우리 CLAUDE.md는 **라우팅 테이블**이기도 해서, 스테이지→에이전트 매핑은 유형1처럼 보여도 실제로는 유형3(팀 선택)이다. §2에서 "삭제"가 아니라 "SoT 포인터로 교체"라고 쓴 이유다.
- **111편 중 대부분은 같은 처방의 변주다.** 계약·경계·판정 3단어로 요약되는 글이 반복된다. Tier 3을 전부 하면 규모 대비 과설계가 된다.

---

## 출처

핵심 근거 글만.

- [600억 토큰을 태우고 남은 8줄](https://theaxlabs.com/blog/context-file-eight-lines-prompt-guide) — 이 문서의 축
- [Marcos Hernanz 원문 AGENTS.md](https://x.com/MarcosHernanz/status/2083011475346510240)
- [품질 게이트는 프롬프트가 아니라 hooks다](https://theaxlabs.com/blog/품질-게이트는-프롬프트가-아니라-hooks다) — §3 결함, Tier 1 #1
- [성공도 실패로 쪼개야 한다](https://theaxlabs.com/blog/성공도-실패로-쪼개야-한다) · [도구 호출 직전이 통제점이다](https://theaxlabs.com/blog/pre-tool-call-is-the-control-point) — Tier 1 #2
- [Subagent는 context 방화벽이다](https://theaxlabs.com/blog/subagents-are-context-firewalls) · [Fan-out은 계약 없인 위험하다](https://theaxlabs.com/blog/fan-out은-계약-없인-위험하다) — Tier 1 #4
- [툴 스키마가 에이전트를 가른다](https://theaxlabs.com/blog/툴-스키마가-에이전트를-가른다) · [Skill은 프롬프트가 아니다](https://theaxlabs.com/blog/skill은-프롬프트가-아니다) — Tier 1 #5
- [고치기 전에 증거를 요구하라](https://theaxlabs.com/blog/고치기-전에-증거를-요구하라) · [출력은 약속이 아니라 계약이다](https://theaxlabs.com/blog/outputs-are-contracts-not-promises) — Tier 2 #6
- [검증도 라우팅해야 산다](https://theaxlabs.com/blog/verification-needs-routing-too) — Tier 2 #8
- [압축 손실은 재연으로 잡는다](https://theaxlabs.com/blog/압축-손실은-재연으로-잡는다) · [맥락은 줄이고 기억은 남겨라](https://theaxlabs.com/blog/맥락은-줄이고-기억은-남겨라) — Tier 2 #9
- [백로그는 사람만 보지 않는다](https://theaxlabs.com/blog/백로그는-사람만-보지-않는다) — Tier 2 #10
- [하네스 변경은 회귀로 검증한다](https://theaxlabs.com/blog/test-harness-regressions-with-replay) — Tier 2 #11
- [골든셋은 테스트가 아니다](https://theaxlabs.com/blog/골든셋은-테스트가-아니다) · [기억은 저장이 아니라 정책이다](https://theaxlabs.com/blog/기억은-저장이-아니라-정책이다) — Tier 2 #12
