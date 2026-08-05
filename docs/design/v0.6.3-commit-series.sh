#!/bin/bash
# v0.6.3 커밋 시리즈 — 로컬에서 실행하세요.
#
# 왜 스크립트인가: 이 저장소는 샌드박스에 FUSE 로 마운트돼 있고, 그 마운트는
# 파일 생성은 허용하지만 삭제를 막습니다. `.git/index.lock` (8/3 11:37 자 0바이트
# 잔존물) 을 지울 수 없어 샌드박스에서 커밋이 불가능했습니다.
#
# 실행 전 확인:
#   1. 아래 락이 정말 잔존물인지 — 다른 git 프로세스가 없어야 합니다
#   2. 최종 상태는 이미 전부 녹색입니다 (pytest 413 passed, 게이트 7종 exit 0)
#
# 실행:
#   bash docs/design/v0.6.3-commit-series.sh
#
# 커밋을 나눈 기준은 "되돌리는 단위" 입니다. 각 커밋이 하나의 결정에 대응하므로
# 어느 하나가 틀렸다고 판명되면 그것만 revert 할 수 있습니다.

set -e
cd "$(git rev-parse --show-toplevel)"

# --- 0. 잔존 락 제거 -----------------------------------------------------------
if [ -f .git/index.lock ]; then
    echo "==> .git/index.lock 제거 (잔존물)"
    rm -f .git/index.lock
fi

# 샌드박스가 남긴 탐침 파일 — 삭제 권한이 없어 지우지 못했습니다.
[ -f .git/_probe ] && rm -f .git/_probe && echo "==> .git/_probe 제거"

# --- 1. remove-bg (이번 작업 이전부터 미커밋 상태였던 것) -----------------------
git add scripts/removebg.py skills/remove-bg/ tests/test_removebg.py \
        skills/api-cost-gate/SKILL.md
git commit -m 'feat(remove-bg): 배경 제거를 결정적·비용 게이트 스킬로

/api-cost-gate 는 고지 형식이고 /asset-spec 은 행을 만들 뿐, 실제로 이미지
작업을 하는 것이 없었다. 배경 제거는 양 트랙(게임 스프라이트·제품 사진)에서
가장 흔한 컷아웃 작업이고 과금 대상이라 계약을 제대로 잡기 좋은 모양이다.

- exit code 가 판정: 0 전체 처리 / 1 부분 실패·전량 스킵 / 2 전량 실패·402·
  403·--max-calls 초과 / 3 실행 불가(키 없음·경로 오류 — 호출도 과금도 없음)
- estimate 는 과금 호출 0회. 비용 고지 자체에 비용이 들지 않는다
- 402/403 은 이미지별 실패가 아니라 배치 전체 중단 — 거기서 계속하면 돈만 나간다
- 키는 CLI 인자로 받지 않는다 (셸 히스토리·프로세스 목록 유출 방지)'

# --- 2. A-1 훅 exit 계약 정합 --------------------------------------------------
git add hooks/validate-assets.sh docs/hooks-reference.md tests/test_hooks_layout.py
git commit -m 'fix(hooks): validate-assets 가 "Blocking" 을 출력하며 차단하지 않았다

깨진 JSON 을 감지해 "ERRORS (Blocking)" 을 출력하고 exit 1 로 끝났다.
Claude Code 훅에서 stderr 를 Claude 에게 되돌리는 것은 exit 2 뿐이고, exit 1 은
사용자에게만 보인 뒤 흘러간다. PostToolUse 훅이라 쓰기는 이미 끝난 뒤이므로
exit 2 는 Claude 가 방금 쓴 파일을 고쳐야 한다는 걸 아는 유일한 경로였다 —
즉 그 "차단" 분기는 판정을 낸 적이 없다.

validate-commit.sh 와 validate-push.sh 는 이미 exit 2 로 올바르고,
docs/deterministic-gates.md 는 v0.6.0 부터 2 = abort 를 선언해 왔다.
새 정책이 아니라 계약 미준수다.

- hooks-reference 규칙 3 이 "non-zero" 대신 코드를 명시 (왜 1 이 판정이 아닌지)
- "차단 가능한 훅" 표 신설 — 16개 중 판정을 내는 것은 셋뿐이다. 판정을 낸 적
  없는 훅을 통과로 읽지 않기 위한 표
- 기존 invalid-JSON 테스트 2건이 == 1 을 단언하고 있었다. 감사 문서의 "기존
  테스트는 안 깨진다" 는 틀렸다 — 2 로 고치고 회귀 가드를 따로 추가'

# --- 3. A-2 스킬 description 린트 ----------------------------------------------
git add scripts/lint_skills.py scripts/lint_baseline.json tests/test_skill_lint.py
git commit -m 'feat(lint): description 을 라우팅 지시문으로 판정 (Check 8~10)

description 은 문서가 아니라 Claude 가 스킬 자동 발동을 결정할 때 읽는 라우팅
지시문이다. 이 플러그인은 스킬 85 + 에이전트 45 = 130개 선택지를 그 텍스트만으로
가른다. 린터는 필드가 비어 있는지만 봤으므로 오라우팅(엉뚱한 작업에 발동하거나
맞는 스킬이 안 뜨거나)에는 탐지 수단이 아예 없었다.

- Check 8 언제 쓰지 않는지 부재 / Check 9 근접 중복 / Check 10 트리거 절 부재
- 셋 다 WARNING. 경고는 baseline 에 들어가지 않으므로 baseline 변동 0
- NEAR_DUPLICATE_THRESHOLD = 0.30 은 추측이 아니라 측정값이다. 8385쌍 전수:
  max 0.438 · p99.9 0.216 · median 0.000. 처음 넣은 0.60 은 한 번도 발동하지
  않았다 — 발동 못 하는 검사는 없느니만 못하다 (침묵이 "혼동 없음" 으로 읽힌다).
  0.30 에서 걸리는 최상위 쌍이 create-prd ~ design-system(0.44), 즉 CLAUDE.md 가
  경고하는 트랙 혼용이다
- test_threshold_can_actually_fire_on_the_real_roster 로 임계값이 다시 범위 밖으로
  올라가면 실패하게 잠금'

# --- 4. B-1 정책 축 -------------------------------------------------------------
git add scripts/verify_policy.py tests/test_verify_policy.py skills/story-done/SKILL.md
git commit -m 'feat(gates): verify_policy.py — 완료 축이 못 보던 정책 축

모든 게이트가 "일이 끝났나" 만 판정했다. 테스트를 skip 처리해 통과시킨 스토리,
--no-verify 로 넘긴 커밋, 규약 밖 경로에 흩뿌린 산출물은 정상 완료와 똑같이
exit 0 으로 기록됐다. CLAUDE.md 의 금지 목록은 산문이라 읽는 스크립트가 없었고,
따라서 강제하는 것도 없었다.

이 실패 유형이 unsafe-success 다. 평범한 실패보다 나쁘다 — 평범한 실패는 보이고
고쳐지지만, unsafe-success 는 우리가 남기는 모든 기록에서 진짜 성공과 구별되지
않고 다음 세션의 에이전트가 그 경로를 정상으로 학습한다.

- P1 증거 누락 / P2 skip 마커 추가 = exit 2, P3 트랙 혼용 / P4 경로 규약 = exit 1
- P3·P4 를 경고로 둔 것은 의도다. 정당한 예외가 있는 검사가 잘못 발동하면
  게이트가 통째로 꺼지고, 그 비용이 검사가 버는 것보다 크다
- /story-done Phase 5b 로 2축 판정. 두 축은 서로를 상쇄하지 않는다 —
  완료 PASS 옆의 정책 FAIL 은 여전히 BLOCKED 이고, exit 3 은 "미실행" 이지
  "통과" 가 아니다
- P2 는 코드 파일만 판정한다. 첫 실행에서 story-done/SKILL.md 가 "P2 가 무엇을
  잡는지 설명" 했다는 이유로 걸렸다 — 마커를 언급한 산문은 건너뛴 테스트가 아니다.
  확장자 허용목록 + grep 가능한 파일 단위 면제(policy-allow-file)로 처리'

# --- 5. B-2 서브에이전트 계약 ---------------------------------------------------
git add rules/subagent-collaboration.md
git commit -m 'docs(rules): 서브에이전트 호출을 계약으로 — 금지·반환 경계

무엇을 보낼지와 결과를 어떻게 합칠지는 있었지만 격리에 대한 규정이 없었다.
서브에이전트를 부르는 이유는 별도 conversation 을 갖는 것인데, 반환 경계가
없으니 에이전트가 폐기한 후보와 실패한 시도까지 요약해 메인으로 돌려보냈다.
격리하려던 것이 그대로 돌아오면 팬아웃 비용만 치르고 이득은 잃는다.

- § 3 에 의무 6(금지 영역)·7(반환 경계) 추가, § 3.1 에 근거와 기본값 표
- 반환은 요약문이 아니라 Artifact(경로 + 상태)
- 리뷰·감사 에이전트는 프롬프트가 아니라 tools 를 Read/Glob/Grep 으로 좁혀서
  부른다 — 읽기 전용은 문장보다 권한으로 보장하는 편이 확실하다
- § 2 를 트랙 중립화. 표준 4분야가 game 전용으로 고정돼 있었다. product 팩은
  v0.4.0 에 들어왔는데 이 규칙만 따라오지 않았다
- § 5 안티패턴 2줄 추가 (탐색 과정 서술 반환, 트랙 혼용 스폰)'

# --- 6. C CLAUDE.md 밀도 개편 (+ stage 이관) -------------------------------------
git add CLAUDE.md docs/agent-packs.yaml tests/test_agent_packs_stages.py
git commit -m 'refactor(claude-md): 편향 교정 파일로 되돌리기 (214 → 169줄)

컨텍스트 파일은 지식 저장소가 아니라 기본 동작을 교정하는 지시의 집합이다.
214줄 중 약 90줄은 에이전트가 파일을 열면 알 수 있는 것이었고, 그 줄들은 토큰만
쓰는 게 아니라 정작 행동을 바꾸는 지시의 밀도를 떨어뜨린다 — 컨텍스트 창에는
목차도 강조도 없다.

- "작업 원칙" 8줄 신설. 기존의 "하지 마라" 는 전부 오케스트레이션 편향이었고
  구현 편향 교정이 0줄이었다. 이 파일이 라우팅하는 45개 에이전트는 코드를 쓴다
- 하위 호환 항목은 통상과 반대로 적었다. 이 저장소는 사용자가 설치하는 배포물이라
  스킬 이름·슬래시 명령·산출물 경로가 사실상 공개 API다. 내부 구현에만
  "쓰이지 않는 경로는 삭제" 를 적용한다
- 스테이지별 에이전트 배정은 삭제가 아니라 agent-packs.yaml 로 이관.
  카탈로그에는 에이전트 정보가 사실상 없고(grep -c agent → 2) agent-packs 에는
  스테이지 정보가 없었다 — 그 매핑은 CLAUDE.md 본문에만 있었고 지웠으면 복원되지
  않는다. 유형1(스스로 알 수 있음)이 아니라 유형3(팀의 선택)이었다
- test_agent_packs_stages.py 로 조인을 잠금. 검증 과정에서 초안이 5개 스테이지만
  적어 concept·systems-design·technical-setup·architecture 가 비어 있는 것을
  발견했다 — check_phase 가 그 phase 를 반환하면 조회가 조용히 실패한다.
  압축이 만든 결함이라 압축과 함께 잠근다

줄 수 목표 130 은 맞추지 못했고 목표 쪽이 틀렸다고 판단했다. 근거는
docs/design/v0.6.3-context-density-plan.md "Phase C 후기" 에 적었다.'

# --- 7. T2-6 self-loop 증거 기반 개정 -------------------------------------------
git add rules/self-loop.md skills/self-loop/SKILL.md
git commit -m 'feat(self-loop): 세 번째 함정 방어 — 증거 없는 재작성

기존 방어 둘(점수 인플레·무한 루프)은 전부 멈추는 이야기였다. 반대편 당김에 대한
방어가 없었다. "최저 점수부터 고쳐라" 는 아무도 결함을 지적하지 않은 부분까지 다시
쓰게 만드는 면허가 되고, 5회 상한은 이걸 못 잡는다 — 회차마다 착실히 뭔가를
고치면서 산출물이 계속 흔들리기 때문이다.

- § 2.1 기본값을 보존으로. 결함 티켓 4필드(claim_id/defect_type/evidence/severity)
  가 지목한 것만 건드린다. 티켓 없으면 수정 없음
- 채점자 우선순위: 결정적 → 도구 → 모델. heavy 라우트에서는 별도 서브에이전트
- § 2.2 회차 입력은 누적하지 않는다 — 재주입은 넷뿐
- § 4.1 실패 분류 (retryable / hard_error), § 4.2 종료 유형 셋 (완료/실패/보류).
  "권한·데이터·결정이 없어 못 간다" 가 실패로 기록되면 후속 조치가 틀린다 —
  하나는 고칠 것이고 다른 하나는 받아올 것이다
- 정책 축은 점수와 무관하게 단독 차단권
- § 1~§ 6 번호는 그대로 두고 하위 절로 끼워 넣었다 (작업 원칙 2번을 우리 문서에도)'

# --- 8. T2-11 골든 궤적 (6 이후여야 골든이 최신) ---------------------------------
git add scripts/verify_trajectory.py tests/trajectories/ tests/test_verify_trajectory.py
git commit -m 'feat(gates): verify_trajectory.py — 플러그인 자신의 라우팅 회귀 검증

/regression-suite 는 사용자 제품의 테스트를 관리할 뿐, 이 플러그인 자신의 행동은
아무도 회귀 검증하지 않았다. 그 행동은 어느 한 파일에 있지도 않다 — 카탈로그(무엇을
어떤 순서로) × agent-packs(누가) 의 조인이다.

어느 한쪽 한 줄이 바뀌면 그 phase 에서 도는 모든 스킬이 조용히 다르게 라우팅된다.
phase 개명, 스텝 삭제, support 가 primary 로 슬며시 승격 — 어느 것도 테스트를
깨지 않았고, 두 파일을 동시에 머리에 담고 있지 않으면 리뷰에도 안 보였다.

- 0 일치 / 2 드리프트 / 3 판정불가. 1 은 쓰지 않는다 — 라우팅 변경은 약한 신호가
  아니다
- 라벨·설명·산문은 일부러 제외. 자주 바뀌고 라우팅에 무의미해서, 넣으면 게이트가
  시끄러워지고 시끄러운 게이트는 읽지 않고 --update 당한다 (게이트가 없는 것과 같다)
- 19 케이스 양방향. 골든이 최신인지도 단언한다 — 낡은 골든은 통과하면서 아무것도
  지키지 않는다'

# --- 9. T2-A 게이트 공통 봉투 ---------------------------------------------------
git add scripts/gate_report.py tests/test_gate_report.py \
        scripts/verify_gates.py scripts/check_phase.py
git commit -m 'feat(gates): gate_report.py — 모든 게이트에 하나의 기계 판독 형태

v0.6.0 부터 "출력을 파싱해 판정을 재도출하지 말라" 고 금지해 왔지만, 게이트들이
자연어만 뱉는 동안에는 왜 를 알아야 하는 호출자에게 파싱 말고 다른 방법이 없었다.
지킬 수 없는 규칙은 없는 규칙보다 나쁘다 — 지켜지는 것처럼 보이기 때문이다.

- 4필드 공통: status(무엇) / reason(왜) / next_action(무엇을 할 것) / evidence
- status 는 exit_code 의 순수 함수이고 인자로 받지 않는다. "ABORT 를 출력하면서
  0 으로 종료" 가 표현 불가능해진다 — 가설이 아니라 이번에 고친
  validate-assets.sh 가 정확히 그 상태였다
- verify_gates / check_phase 에는 추가지 교체가 아니다. /project-stage-detect 가
  이미 그 키들을 읽고 있어서 구현 세부가 아니라 계약이다. 기존 키 생존을 테스트로 단언
- verify_gates 의 P4(문장 터치율)는 evidence 에서 제외 — 보고 전용이라 exit code 에
  영향이 없다. 판정에 기여하지 않은 신호를 근거로 제시하면 기여했다고 오해한다'

# --- 10. T2-B 검증 라우팅 -------------------------------------------------------
git add rules/verify-route.md rules/route-hint.md
git commit -m 'feat(rules): verify-route.md — 만드는 쪽이 아니라 검사하는 쪽을 라우팅

route-hint 는 생산만 라우팅했다. 검증은 라우팅이 없어서 각 스킬이 하드코딩한
무게로 돌았고, 그 결과 양방향으로 틀린다 — 주석 오탈자에 /team-qa 풀세트가 붙고,
데이터 마이그레이션이 /smoke-check 하나로 통과한다.

- 축은 중요도가 아니라 되돌릴 수 있는가다. "중요하다" 는 느낌이고 부풀지만
  "틀리면 되돌리는 데 뭐가 드나" 는 변경의 속성이다
- R1 파일의 게이트 / R2 게이트+리뷰 / R3 게이트+별도 리뷰 서브에이전트+gate-check /
  R4 무인 실행 금지. 마지막 한 줄만 에이전트에게서 결정권을 가져간다
- 불확실하면 승급. 높게 잡으면 검사 하나 더, 낮게 잡으면 깨지는 것 전부
- 강등은 사유를 출력에 남긴다 — 사유 없는 강등은 검사를 건너뛴 것과 구별되지 않는다
- 두 축은 독립이다. 배포된 config 한 줄 수정은 생산 라우트로 가장 가볍고 검증
  라우트로 가장 무겁다'

# --- 11. 문서·CI·릴리스 ---------------------------------------------------------
git add docs/deterministic-gates.md docs/rules-reference.md docs/skills-reference.md \
        docs/design/ README.md .github/workflows/test.yml \
        .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -m 'release: v0.6.3 — 컨텍스트 밀도 + 결정적 게이트 계약의 구멍 넷

- deterministic-gates.md 에 verify_policy · verify_trajectory · gate_report 등재.
  "출력을 파싱하지 말라" 항목에 공통 봉투를 연결 — 그 금지를 처음으로 실행 가능하게
- rules-reference 에 verify-route 등재, self-loop 요약 갱신
- CI: policy 잡에 verify_policy(--self-test 먼저) 와 verify_trajectory 추가
- docs/design/ax-labs-blog-audit.md — 블로그 111편 감사. 이번 변경의 출처이며,
  틀렸던 부분(스테이지 표가 카탈로그에 있다고 본 것)도 그대로 남겨 뒀다
- docs/design/v0.6.3-context-density-plan.md — 계획과 그 후기(줄 수 목표를 왜
  폐기했는가)

최종 상태: pytest 413 passed, 게이트 7종 exit 0'

echo
echo "=== 완료 ==="
git log --oneline -11
