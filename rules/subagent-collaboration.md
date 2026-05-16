# Subagent Collaboration Patterns

> 깊은 디자인 / 게임성 / 광범위 결정 영역에 *다수 서브 에이전트 병행 호출* + 결과 통합 패턴. 사람 팀 협업 모사.

---

## § 1 — 언제 사용

| 트리거 | 패턴 |
|--------|------|
| **광범위 + 깊은 디자인 결정** (예: 새 시스템 spec) | 다수 서브 에이전트 병행 |
| 단순 기능 / 코드 수정 / 사실 확인 | 메인 Claude 단독 |
| 외부 자료 + 내부 spec 통합 | WebSearch + 1~2 서브 에이전트 |

**Rule of thumb**: 결정 영역이 *4+ 분야* 또는 *광범위 게임성 영향* 일 때 → 서브 에이전트 호출.

---

## § 2 — 4 에이전트 병행 호출 패턴

게임 시스템 spec 의 표준 4 분야:
1. **game-designer** — 게임 메카닉 / 룰 / 옵션 비교
2. **ux-designer** — 흐름 / 인터랙션 / 게임패드+KBM 정합
3. **ui-programmer** — 구현 아키텍처 / 매니저 / widget spec
4. **gameplay-programmer** — 입력 시스템 / 인터랙트 / 씬 전환 / 백엔드

### 호출 절차

```
1. 메인 Claude 가 안건 분석 → 4 분야 spec 명시
2. 단일 message + 4 Agent tool call (병행 — 같은 message 안)
3. 각 에이전트:
   - 프로젝트 컨텍스트 + 안건 + 결정 권한 영역 명시
   - 결과 spec = ~300줄 한도 (R2 정합)
   - 옵션 A/B/C 형식 (사장님 결정 받기 위한)
4. 메인 Claude 가 4 결과 통합 → 회의록 작성
5. 결정 요청 안건 매트릭스 — 사장님 picking
```

### Parallel 호출 — 단일 message 안 다수 tool call

병행 호출 시 *N 배 빠름* (4 에이전트 × ~3분 → 동시 진행). Claude Code 가 자동 병렬 실행.

```python
# pseudo-code — 단일 응답 안 다수 Agent tool call
Agent(subagent_type="game-designer", prompt="...")
Agent(subagent_type="ux-designer",   prompt="...")
Agent(subagent_type="ui-programmer", prompt="...")
Agent(subagent_type="gameplay-programmer", prompt="...")
```

---

## § 3 — 각 에이전트 prompt 의무 항목

각 에이전트는 *자기 conversation* 만 가짐 (메인 Claude 의 컨텍스트 X). prompt 가 self-contained:

1. **프로젝트 컨텍스트** — 엔진 / 플랫폼 / Phase / 관련 메모리 link
2. **외부 조사 결과** (있다면) — WebSearch 결과 반영
3. **작성 안건** — 각 § 별 명시
4. **결정 권한 영역** — 사장님 결정 받기 위한 옵션 A/B/C
5. **응답 형식** — 마크다운 + ~300줄 한도

---

## § 4 — 결과 통합 패턴

4 에이전트 결과 받은 후 메인 Claude:

### 4.1 결정 안건 매트릭스 작성
| ID | 안건 | 권고 | 옵션 |
|----|------|------|------|
| D-1 | … | ✅ A | A 추가 / B 제외 |
| UX-1 | … | ✅ A | … |
| A-1 | … | ✅ A | … |

### 4.2 회의록 작성 — `Documents/Meetings/YYYY-MM-DD-<주제>.md`
회의록 메타 박스 (일자 / 운영자 / 안건 / 결정 채택 상태 / 통합 보고 link / **서브 에이전트 ID 보존**) + § 별 spec 통합.

### 4.3 사장님 결정 흐름 — 3 옵션
- (i) 일괄 결정 — 모든 안건 권고 채택
- (ii) 점진 결정 — 우선순위 영역만
- (iii) 권고 일괄 수용 — 가장 단순 / 가장 효율

---

## § 5 — 안티패턴

- ❌ *단순 기능* 에 다수 서브 에이전트 — 토큰 / 시간 낭비
- ❌ 에이전트 prompt 에 컨텍스트 부족 — "based on the conversation" 같은 의존 (에이전트는 새 conversation)
- ❌ 4 에이전트 결과 *복사 붙여넣기* — 메인 Claude 의 *통합 + 충돌 해소* 책임
- ❌ 직렬 호출 (1 에이전트 끝나고 다음) — 병행 호출 vs 4배 느림

---

## § 6 — 회의록 template

본 패턴의 결과물 = `Documents/Meetings/YYYY-MM-DD-<주제>-Meeting.md` — template 참조:
- `docs/templates/subagent-meeting-template.md` (이 플러그인 안)

회의록 = 사장님 결정 후 *영구 참조 문서* — 결정 권한 영역 + 옵션 비교 + 권고 + 사장님 picking 결과 모두 보존.

---

## § 7 — 메모리 등재

서브 에이전트 결과 중 *영구 가치 있는 패턴* 발견 시 메모리 등재 (다른 회의에서 재참조). 1회성 spec 은 회의록만.
