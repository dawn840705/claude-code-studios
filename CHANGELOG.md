# Changelog

## Unreleased

### Added — `/spatial-audit`: 지어진 레벨을 건축 4렌즈로 감사

이 저장소에 레벨을 *만드는* 경로는 있었지만(`/team-level`, `level-designer`,
`level-design-document.md`) 이미 만든 공간을 **읽어서 판정하는** 것은 없었다.
블록아웃이 걸어다녀진다는 것과 공간이 작동한다는 것은 다른 말인데, 그 차이를
보는 도구가 없으니 플레이테스트 결과가 "재미없다"로만 돌아왔다.

- **`skills/spatial-audit/SKILL.md`** — 매싱 · 동선 · 조망-은신 · 길찾기 4렌즈.
  읽기 전용이고 **재미는 판정하지 않는다** — 재미는 `/playtest-report` 의 몫이고,
  이 스킬은 그 결과를 해석 가능하게 만드는 성질(가독성·항행성·공정성)만 본다.
  장르 인자(`sp`/`pvp`/`open`)가 장식이 아니다: 막다른 길은 pvp 에서 결함이고
  sp 에서는 대개 의도다.
- **침묵 실패 계약이 이 스킬의 핵심이다.** `hera-agent-unity exec` 는 에디터
  메인 스레드가 막히면(모달·라이선스·도메인 리로드) **아무것도 출력하지 않는다.**
  무출력과 "찾은 게 없음" 이 구별되지 않으므로, 그걸 "엄폐물이 없다" 로 읽는 것이
  이 스킬이 낼 수 있는 최악의 산출이다. 그래서 모든 스니펫은 `__SPATIAL_AUDIT_OK__`
  센티널을 찍고 끝내고, **센티널이 없으면 판정은 BLOCKED — PASS 도 "발견 없음"도
  아니다.** `docs/deterministic-gates.md` 의 "돌지 못한 게이트는 통과가 아니다" 를
  산문으로 옮긴 것이다. 단 **이 스킬은 exit code 를 내지 않는다** — 센티널은 모델
  측 확인이지 게이트가 아니고, 그렇게 부르면 stdout 파싱을 게이트 판정으로
  세탁하는 셈이 된다(같은 문서가 금지하는 것).
- **에디터가 닫힌 것과 막힌 것은 다르게 라우팅한다.** 닫힘은 정상 조건이라 채널 B
  로 내려가고, 막힘(센티널 부재)은 결함이라 BLOCKED 로 세운다. 후자를 조용히 파일
  감사로 대체하면 고장을 덮는다.
- 추출(Bash)과 판정(에이전트)을 분리했다. `level-designer` 는 `disallowedTools: Bash`
  라 hera 를 못 부른다 — 메인 Claude 가 뽑아서 숫자를 넘긴다. 병렬 스폰 시 쓰기
  소유는 `rules/subagent-collaboration.md` § 2.1 을 따른다.
- 에디터가 없어도 씬 YAML 로 동작한다. 단 NavMesh·레이캐스트·카메라 시야는 볼 수
  없으므로 해당 발견은 전부 `추정 — 파일 기반` 으로 표기한다
  (`rules/claim-confidence.md`).
- **`docs/level-design-sources.md`** (신규) — 출처 목록. The Level Design Book 은
  **CC BY-NC-SA 4.0** 이라 본문을 이 저장소에 넣지 않는다: ShareAlike 가 파생물을
  같은 라이선스로 묶어 이 플러그인의 **MIT 와 충돌**하고, NonCommercial 은 상용
  게임 개발에 쓰이는 툴킷에 그대로 걸린다. 링크와 자체 표현으로만 쓴다 —
  claude-seo 를 vendor-in 하지 않은 것과 같은 판단이다.
- **형태·색 심리학은 명시적으로 배제했다.** "둥글면 안전" 류는 근거가 없고, 원전이
  해당 페이지 제목에서 직접 그렇게 부른다. 형태 주장은 시선거리·이동비용·실루엣
  변별처럼 **측정 가능한 결과로 환원될 때만** 채택한다.
- `docs/templates/spatial-audit-report.md` (신규) — 판정 박스에 추출 채널과 센티널
  상태를 먼저 적는다. 리포트를 읽는 사람이 "빈 섹션"과 "결함 없음"을 구별해야 한다.

스킬 수 85 → 86. `tests/test_manifest_sync.py` 가 매니페스트 3곳의 광고 숫자를
잡아냈다 — 그 게이트가 의도대로 작동했다.

### Added — 상류 흡수 1차: 제품 PRD 템플릿 + 전역 룰 3건

출처는 `.upstream-scan/2026-08-05.md` — 이 플러그인을 쓰는 8개 프로젝트를 훑어
**상류에 없으면서 2개 이상 프로젝트에 반복되는** 것만 추린 리포트다. 9건 중
"신규 파일·절 추가뿐이라 기존 규약을 건드리지 않는" 4건을 먼저 넣었다. 나머지
5건(아카이브 경로 규약, 세션 진입 루틴, 커밋 규율, 계측·인수인계 템플릿)은
선행 결정이나 반복도 확인이 필요해 보류했고 사유는 리포트에 있다.

- **`docs/templates/product-requirements-document.md`** (신규) — product 트랙의
  **제품 단위** PRD. 5개 프로젝트(SpecForge · InvestLog · TossMiniApp · MindCare ·
  ReviewSupporter)가 거의 같은 절 구성으로 수렴해 있었는데, 상류 템플릿 39종은
  전부 게임 쪽이라 받을 자리가 없었다. `game-concept.md` · `pitch-document.md` 는
  발상 단계 산출물이라 기능/비기능 요구사항, 페르소나, KPI, Out of Scope 가
  통째로 없다.
  **`/create-prd` 에는 연결하지 않았다.** 그쪽은 `product/prd/prd-<feature>.md`
  에 쓰는 *기능 단위* PRD 이고 이건 제품 단위다. 두 층위를 한 스킬에 밀어넣지
  않는다 — 산출 경로도 겹치지 않게 `product/prd/product-requirements.md` 를
  권장 경로로 적어 두었다.
- **`rules/subagent-collaboration.md` § 2.1** (절 추가) — **쓰기 영역을 스폰
  전에 나눈다.** 45개 에이전트를 병렬로 부르는 플러그인에 쓰기 충돌면 분할이
  없었다. Edit 은 마지막에 쓴 쪽이 이기고 진 쪽은 "완료" 를 보고하므로, § 5 의
  안티패턴 중 유일하게 **조용히** 실패한다. 소유 표(에이전트 × 쓰기 경로 ×
  읽기 전용 × 금지)를 채우지 못하면 아직 부를 준비가 안 된 것으로 본다.
  소유가 겹치면 병렬 대신 직렬 — § 5 의 "직렬 호출 안티패턴" 은 *독립* 작업에만
  해당한다는 점을 명시했다. 근거: StarDiver · SpecForge · CorpProject_10th ·
  TossMiniApp 4개 프로젝트가 각자 같은 규칙을 재발명해 두고 있었다.
- **`rules/decision-lifecycle.md`** (신규, 전역) — 확정된 결정은 다시 열지
  않는다. 사람은 회의를 기억하지만 **새 세션의 에이전트는 기억하지 않으므로**,
  폐기된 대안이 문서에 남지 않으면 매번 신선한 아이디어로 보인다. 확정 항목은
  결정 문장 + 근거 링크 + **재검토 트리거** 3요소를 갖춘다 (트리거 없는 확정은
  교착이다). 폐기된 값은 지우지 말고 **본문에** 폐기 표시 — 판단 기준은 "이
  파일만 읽은 에이전트가 옛 값을 정본으로 착각할 수 있는가". ADR 과 겹치지
  않게 기술 결정 / 제품·운영 결정의 경계도 표로 나눴다.
- **`rules/claim-confidence.md`** (신규, 전역) — 확인한 것 · 추정한 것 · 모르는
  것을 구별해 표기한다(무표기+출처 / `(추정)`+계산식 / `[확인 필요]`). 법조항,
  과태료, 가격, 수수료율, 경쟁사 사실, API 시그니처는 기억에서 쓰지 않는다.
  정직성 이전에 **전파** 문제다 — 표시되지 않은 추정치는 문서를 건널 때마다
  확신이 올라간다. `self-loop.md` 는 *채점 근거*의 인용을 요구하고 이쪽은
  *산출물 본문*의 사실 표기라 축이 다르며, 본문의 무표기 추정치는 그 자체로
  `self-loop.md` § 2.1 의 결함 티켓 요건을 충족한다.

하위 호환: **깨는 것 없음.** 스킬 이름 · 슬래시 명령 · 산출물 경로 규약 변경이
없고, 기존 파일 수정은 `subagent-collaboration.md` 절 추가·§ 5 항목 2건과
인덱스 3곳(`docs/rules-reference.md` · `docs/quick-start.md` · `README.md`)
갱신뿐이다. 게이트: pytest 413 passed · `verify_policy` exit 0 ·
`verify_trajectory` exit 0 · `lint_skills --baseline` exit 0 ·
`check_phase --validate` exit 0.

리뷰에서 드러난, **이 변경이 만든 게 아니라 부딪힌** 기존 구멍 셋. 고치지
않았고 다음 스캔 항목으로 남긴다:

- `product/prd/product-concept.md` 를 **쓰는 스킬이 없다.** 카탈로그
  (`docs/workflow-catalog.yaml:456-458`) 는 그 단계에 `/brainstorm` 을
  걸어놨지만 `skills/brainstorm/SKILL.md` 는 `design/gdd/game-concept.md` 만
  쓴다. product 트랙 discovery 가 정상 경로로는 완료될 수 없다.
- **`/gate-check` 는 game 트랙 phase 이름만 받는다** (`SKILL.md:4`). product
  트랙(discovery → architecture → build → hardening → ship → growth) 에는
  쓸 수 없어서, 새 템플릿은 `/project-stage-detect` 로 안내한다.
- `CLAUDE.md:54` 의 product 스테이지 목록에 `architecture` 가 빠져 있다
  (카탈로그 `:444` 의 `next_phase` 와 불일치).

### Added — `claude-seo` as a companion plugin (병합 아님)

SEO 는 이 저장소가 직접 다루지 않던 공백이었다. `growth-engineer` 의 remit 에
"SEO" 라는 단어만 있고 그것을 어떻게 하는지는 없었으므로, 실제로는 매번
즉흥적으로 감사를 짜는 결과가 났다.

- **`.claude/settings.json`** (신규) — `AgriciDaniel/claude-seo` (MIT, v2.2.4)
  를 `extraKnownMarketplaces` 로 선언하고 `enabledPlugins` 로 켠다.
  `autoUpdate: false` — 서드파티 마켓플레이스의 기본값이고, 훅과 네트워크
  fetcher 를 가진 플러그인을 조용히 갱신시키지 않는다.
- **vendor-in 하지 않았다.** 25 스킬 · 18 에이전트를 이 저장소로 복사하면
  업스트림 업데이트가 전부 수동 머지가 되고, 게임 프로젝트에서도 팩 게이팅
  없이 노출된다. 별도 플러그인으로 두면 업데이트는 업스트림에서 오고 이름
  충돌도 없다 (`seo-*` 는 기존 85 스킬 · 45 에이전트 어디와도 겹치지 않는다).
- **`CLAUDE.md` → "Companion plugins"** — 라우팅 교정 한 절. SEO 작업은
  `/seo-*` 로 보내고 `growth-engineer` 는 브리핑·리뷰만 한다. 이 저장소에
  `seo-*` 스킬/에이전트를 새로 만들지 않는다.
- `.gitignore` 에 `.claude/settings.local.json` — 머신별 trust 승인 기록.

주의: 설치는 자동이 아니다. 세션 시작 시 신뢰(trust) 프롬프트가 뜨고 사용자가
승인해야 로드된다. 새 머신에서 첫 사용 시 `/seo setup` 1회 필요 (venv +
Chromium 프로비저닝). claude-seo 의 `PostToolUse` 훅은 Edit|Write 전체를
matcher 로 받지만 스크립트가 JSON-LD 포함 여부를 먼저 확인하므로 이 저장소의
`.md`/`.py` 편집에는 개입하지 않는다.

## v0.6.3 — 2026-08-04

### Added — `gate_report.py`: one machine-readable shape for every gate verdict

`docs/deterministic-gates.md` has forbidden re-deriving a verdict by parsing a
runner's output since v0.6.0 — "read the exit code, use the text only to explain
it". But every gate then printed free prose, so a caller who needed *why* had
exactly one option: parse the prose. **The rule was unfollowable, which is worse
than absent — it looked like it was holding.**

- **`scripts/gate_report.py`** — four fields, identical across gates: `status`
  (what), `reason` (why), `next_action` (what to do about it), `evidence` (the
  findings as data), plus `gate` and `exit_code`. A skill reads `status`, a human
  reads `reason`, a follow-up reads `next_action`, a report cites `evidence`, and
  nothing is left to interpret.
- **`status` is a pure function of `exit_code`** and cannot be passed in. A gate
  can no longer print ABORT while exiting 0 — which is not hypothetical:
  `validate-assets.sh` shipped printing "ERRORS (Blocking)" and exiting 1, a code
  Claude never receives. Deriving one from the other makes that state
  unrepresentable rather than merely discouraged. An off-contract exit code
  raises instead of being silently coerced.
- `--json` added to `verify_policy.py` and `verify_trajectory.py`.
- For `verify_gates.py` and `check_phase.py` the envelope is **additive** — a new
  `gate_report` key beside the existing output, whose shape is unchanged.
  `/project-stage-detect` already consumes those keys, and per `CLAUDE.md`
  작업 원칙 that is a contract, not an implementation detail. A test asserts the
  original keys survive.
- `verify_gates.py` excludes its P4 axis (sentence touch rate) from `evidence`:
  it is reporting-only and does not move the exit code. Citing a signal that did
  not contribute to the verdict invites the reader to think it did.
- Tests: `tests/test_gate_report.py`, 13 cases — including that `build()` has no
  `status` parameter (the invariant is structural, not documentary), that a
  hand-forged `status` fails validation, and that the `exit 3` path conforms too,
  since that is precisely the path most likely to be misread as a pass.

### Added — `rules/verify-route.md`: routing the checking, not the making

`route-hint.md` routes **production** — how many agents make the thing. Nothing
routed **verification**, so it ran at whatever weight each skill happened to
hardcode. That fails in both directions at once: a comment typo pulls the full
`/team-qa` fan-out because the sprint loop says so, while a data migration passes
on a single `/smoke-check` because nothing said to do more.

- **Route by reversibility, not importance.** "Important" is a feeling and it
  inflates; *"if this is wrong, what does it take to undo?"* is a property of the
  change. R1 (one edit undoes it) → the file's own gate · R2 (a revert undoes it)
  → gates + review · R3 (needs coordination or a re-release) → gates + a
  **separate** reviewing subagent + `/gate-check` · **R4 (cannot be undone, or
  costs users) → never runs unattended.**
- Only the last row takes the decision away from the agent. Escalation is "add
  this named check", not "be more careful".
- **Uncertainty escalates** — guessing high costs one extra check, guessing low
  costs whatever the change breaks. De-escalation requires a stated reason in the
  output, because an unexplained one is indistinguishable from a skipped check.
- **At R3+ the reviewer is not the author**, and receives the final state rather
  than the narrative of how it was produced. An agent asked to check its own work
  defends it — not from dishonesty, but because the same context reaches the same
  conclusions twice.
- `exit 3` at R3+ is itself an escalation trigger: you now know less than planned.
- Cross-referenced from `route-hint.md`, `subagent-collaboration.md` (new § 8),
  `CLAUDE.md` and `docs/rules-reference.md`. The two axes are explicitly
  independent — a one-line edit to a published config is the lightest production
  route and the heaviest verification route.

### Added — `verify_trajectory.py`: the plugin's own routing is now regression-tested

`/regression-suite` manages tests for the *user's product*. Nothing tested **this
plugin's own behaviour** — and that behaviour lives in no single file. It is a
join: `check_phase.py` reads `workflow-catalog.yaml` for the phase, and the
orchestrator looks that phase up in `agent-packs.yaml` for the staffing.

One line changed in either file silently re-routes every skill running in that
phase. A renamed phase, a deleted step, a support role quietly promoted to
primary — none of it failed a test, and none of it was visible in review unless
someone happened to hold both files in their head at once.

- **`scripts/verify_trajectory.py`** — records the derived routing (steps in
  order, required steps, `depends_on` edges, primary/support agents) per track
  and phase as a golden trajectory. `0` match · `2` drift · `3` cannot judge.
  **Never `1`** — a routing change is not a soft signal.
- **`tests/trajectories/routing.json`** — 2 tracks, 13 phases. A deliberate
  change is `--update` in the same commit, which turns an invisible drift into an
  explicit diff a reviewer reads.
- **Labels, descriptions and prose are excluded on purpose.** They change often
  and mean nothing to routing; including them makes the gate noisy, and a noisy
  gate gets `--update`d without being read — the same as having no gate.
- Tests: `tests/test_verify_trajectory.py`, 19 cases, both directions — every
  drift shape is detected (added/removed phase, membership change, **step
  reordering**, dependency edge change) and an unchanged tree does not false-fire.
  Also asserts the golden is current, since a stale golden passes while guarding
  nothing.
- CI: added to the `policy` job.

### Changed — `self-loop` defends a third failure mode: rewriting without evidence

The rule guarded two traps — score inflation and runaway loops — and both are
about *stopping*. It had nothing about the opposite pull. "Fix the lowest score
first" is all the licence a model needs to rewrite a section nobody found fault
with, and the 5-iteration cap does not catch it: each round dutifully changes
something while the deliverable keeps moving.

- **`rules/self-loop.md` § 2.1 — the default is preserve, not revise.** Scoring
  now emits a **defect ticket** (`claim_id` / `defect_type` / `evidence` /
  `severity`) and only what a ticket names may be touched. Default severity is
  `국소수정`; `전면재생성` is for structural defects. **No ticket → no edit.**
- **Verifier ladder: deterministic → tool → model.** If a script settled it, the
  lower rungs are not used. On the `heavy` route, scoring goes to a *separate*
  subagent — the agent that produced the work defends the work.
- **§ 2.2 — iteration input does not accumulate.** From round 2, re-inject four
  things only: previous output, this round's tickets, the violated criteria with
  allowed values, and what must be preserved. Re-feeding the whole context makes
  the model reinterpret the task and undo earlier agreements.
- **§ 4.1 — failures are classified.** `retryable` consumes a round;
  `hard_error` (schema, permission, policy `exit 2`) terminates immediately,
  because the same input yields the same result.
- **§ 4.2 — three terminal states, not two.** `완료` / `실패` / **`보류`**.
  Collapsing them recorded "cannot proceed without a permission or a decision" as
  a failure, and those need opposite responses: one is fixed, the other is
  escalated. The policy axis also gains standalone blocking power — all criteria
  at 10 with `verify_policy.py → exit 2` is not DONE.
- Exit report gains a **판정 주체** column: which script and exit code decided
  each row, or "모델". A blank means that row was never verified.
- § 1-§ 6 numbering is unchanged (new material is § 2.1/2.2, § 4.1/4.2) so
  existing citations still resolve. `skills/self-loop/SKILL.md`,
  `docs/rules-reference.md` and `CLAUDE.md` updated to match.
- `scripts/lint_baseline.json`: the `self-loop` entry loses `Check 3: no verdict
  keyword` — adding `BLOCKED` as a terminal state incidentally satisfied it. The
  remaining `Check 4` entry (Write/Edit without ask-before-write) stays
  baselined deliberately: this skill's contract is to iterate autonomously and
  it says so explicitly, so asking before each write would contradict its design.

### Changed — `CLAUDE.md` is a bias-correction file again (214 → 169 lines)

A context file is not a knowledge store; it is the set of instructions that
correct what the model would otherwise do by default. Roughly 90 of `CLAUDE.md`'s
214 lines were things an agent can find by opening a file — stage tables, the
workflow list, a directory tree, an index of `docs/`. Those lines do not merely
waste tokens: they dilute the instructions that actually change behaviour, and a
context window has no table of contents to compensate.

- **New `## 작업 원칙` (8 items).** Every prior "don't do this" in `CLAUDE.md`
  corrected *orchestration* bias — don't over-spawn, don't bypass hooks, don't
  trust an agent's summary. There was **nothing about implementation bias**, yet
  the 45 agents this file routes write code. The eight cover research-before-
  designing, simplest-sufficient implementation, growing in layers, not
  reimplementing, checking installed dependencies, and refusing stopgaps.
- **Backward compatibility is inverted from the usual advice, on purpose.** The
  common form of this rule is "delete unused paths, don't keep compatibility
  layers". This repo is an installed distributable: skill names, slash commands
  and artifact paths are effectively public API, so those must not break — while
  *internal* implementation (script helpers, hook libs) follows the delete-freely
  rule. Getting this backwards would break user projects on upgrade.
- **Stage → agent assignments moved to `docs/agent-packs.yaml` (`stages:`), not
  deleted.** The audit assumed `workflow-catalog.yaml` was their source of truth.
  It is not — the catalog carries steps and skills but essentially no agent
  information (`grep -c agent` → 2), and `agent-packs.yaml` had no stage
  information. That mapping existed *only* in `CLAUDE.md` prose and would not
  have been recoverable. It is a team decision, so it moved to the routing SoT.
- **`tests/test_agent_packs_stages.py` (6 cases) locks the join.** `CLAUDE.md` now
  says "ask `check_phase.py` for the phase, look that phase up in
  `agent-packs.yaml`". A verification pass caught that the first draft listed only
  5 stages while the catalog defines 7 game phases and 6 product phases — so
  `concept`, `systems-design`, `technical-setup` and `architecture` had no
  staffing and the lookup would have silently returned nothing. Those four are now
  staffed; game `live-ops` moved to `post_release:` because the catalog has no
  such phase; and the test fails if either side drifts again, in both directions.
- Compressed with pointers, not deletions: `## Development stages` (59 → 21, now a
  two-SoT table), `## Entry points` (19 → 14), `## File conventions` (20 → 11, now
  pointing at `docs/directory-structure.md`, which the tree had been duplicating),
  `## Reference docs` (11 → folded into `## Extending the plugin`), plus trims to
  the domain-pack member lists and the self-loop protocol, both of which restate
  files that already hold the full version.
- Untouched by design: `## Deterministic gates`, `## Route hint`, `## Agent usage
  rules`, `## Don't do this` — the bias-correction core.

**The 130-line target was dropped rather than met.** It was computed assuming the
stage tables could be deleted; once they had to be relocated instead, the pointer
section plus the new principles account for the difference. Line count is a proxy
for density, and gating on a proxy invites damaging the thing it stands for — so
the completion gate is now `test_agent_packs_stages.py`, which judges information
loss directly. Reasoning in full: `docs/design/v0.6.3-context-density-plan.md`.

### Added — `verify_policy.py`: the policy axis `/story-done` was missing

Every gate in this plugin judged the same question — *did the work get done?*
`/story-done` verifies acceptance criteria, `/smoke-check` runs the suite,
`check_phase.py` checks artifacts exist. All completion axis.

Nothing asked the second question: *was it done the way we said?* A story that
reached `Status: Complete` by adding `@pytest.mark.skip`, or by scattering
artifacts outside the documented tree, recorded exactly the same `exit 0` as one
that did the work properly. `CLAUDE.md` has a "Don't do this" section, but it is
prose — no script had ever read it, so nothing enforced it.

That failure mode is **unsafe-success**, and it is worse than a plain failure: a
plain failure is visible and gets fixed, while an unsafe success is
indistinguishable from a real one in every record we keep — and the next
session's agent reads those records as the normal way to work.

- **`scripts/verify_policy.py`** — stdlib-only, 4-code contract:
  `0` compliant · `1` warning · `2` abort · `3` cannot judge (not a git repo).
  - **P1** — story is `Complete` but its declared test evidence does not exist,
    or the evidence block still reads "Not yet created". **ABORT.**
  - **P2** — the diff *adds* a test-skip marker (pytest, unittest, jest, NUnit,
    Go, Rust). Pre-existing markers are not flagged; only additions. **ABORT.**
  - **P3** — `design/gdd/*.md` and `product/prd/*.md` both present, i.e. the
    pack mixing `CLAUDE.md` warns against. **WARNING.**
  - **P4** — new files under `design/`/`production/` outside the documented
    layout. **WARNING.**
- **P1/P2 abort, P3/P4 warn, deliberately.** P1 and P2 are mechanical and
  unambiguous. P3 and P4 have legitimate exceptions, and a gate that fires
  wrongly gets disabled wholesale — which costs more than the check ever earned.
  Promote them once the false-positive rate is known, not before.
- **Two-axis verdict in `/story-done`** (new Phase 5b). The axes never cancel
  each other: a completion PASS beside a policy FAIL is still BLOCKED, and a
  policy `exit 3` is recorded as "NOT RUN", never as "PASS".
- **P2 judges code files only.** Its first run on this repo flagged
  `skills/story-done/SKILL.md` for *explaining what P2 catches* — prose that
  names a marker is documentation, not a skipped test. P2 now checks an
  extension allowlist plus a greppable file-level opt-out
  (`policy-allow-file: skip-marker`) for the gate's own fixtures.
- CI: new `policy` job in `.github/workflows/test.yml` — runs `--self-test`
  first, then judges the repo against its own conventions.
- Tests: `tests/test_verify_policy.py`, 28 cases, including
  `test_this_repository_passes_its_own_gate` (a plugin that breaks its own
  policy has no business shipping the gate) and both directions of the P2
  opt-out, so the escape hatch cannot silently widen.

### Changed — Subagent collaboration is a contract, not just a call

`rules/subagent-collaboration.md` specified what to *send* a subagent and how to
merge results, but nothing about isolation. The point of a subagent is that it
holds its own conversation — yet with no return boundary, agents summarised their
discarded candidates and failed attempts back into main context. The thing being
isolated came straight back, so the fan-out cost was paid and the benefit lost.

- **§3 gains obligations 6 and 7** — *금지 영역* (what not to read, modify or
  spawn) and *반환 경계* (what goes back to main context and what does not).
  New §3.1 explains why, with a two-column default table.
- **Returns are Artifacts, not summaries** — an agent that wrote a file returns
  `path — status`, not 400 lines of prose the orchestrator then carries forever.
- **Read-only agents get read-only tools.** For `qa-lead`, `security-engineer`
  and `performance-analyst`, narrow `tools` to Read/Glob/Grep rather than
  relying on a sentence in the prompt — a permission is a stronger guarantee.
- **§2 is no longer game-only.** The standard four roles now come in a game set
  and a product set (`product-manager` / `ux-designer` / `frontend-engineer` /
  `backend-engineer`); the product pack shipped in v0.4.0 and this rule never
  followed. Also notes that four is a convention, not a quota.
- **§5 gains two antipatterns** — narrating the whole search back (the
  orchestrator ends up persuaded by length rather than content), and spawning
  across tracks.

### Fixed — `validate-assets.sh` printed "Blocking" and did not block

The hook detected invalid JSON, printed `=== Asset Validation: ERRORS (Blocking) ===`,
and exited **1**. In a Claude Code hook only `exit 2` feeds stderr back to Claude;
`exit 1` surfaces to the user and is otherwise ignored. Because this is a
*PostToolUse* hook the write has already landed, so exit 2 was the only path by
which Claude could learn it must fix the file it just wrote — the "blocking"
branch had never rendered a verdict at all.

`validate-commit.sh` and `validate-push.sh` were already correct at `exit 2`, and
`docs/deterministic-gates.md` had declared `2 = abort` since v0.6.0. This was a
contract violation, not a new policy.

- **`hooks/validate-assets.sh`** — `exit 1` → `exit 2` on invalid JSON. Naming
  violations stay advisory (`exit 0`), unchanged.
- **`docs/hooks-reference.md`** — rule 3 for adding a hook now names the code
  (`exit 2`, and why `exit 1` is not a verdict) instead of saying "non-zero".
- **New: "Which hooks can actually block" table** — only three of the sixteen
  hooks render a verdict. The rest exit 0 unconditionally, and a hook that has
  never judged anything must not be read as a green light. Same rule
  `deterministic-gates.md` states for gates, applied to hooks.
- Tests: `tests/test_hooks_layout.py` — the two existing invalid-JSON tests now
  assert `2`, plus `test_blocking_exit_is_2_not_1` (regression guard) and
  `test_naming_violations_never_block` (the other half of the contract).

**Upgrade note:** invalid JSON under an asset root now actually stops Claude. A
project carrying a pre-existing malformed JSON file will see this surface for the
first time.

### Added — `lint_skills.py` judges `description` as a routing rule (Checks 8-10)

`description` is not documentation. It is the text Claude reads when deciding
whether to auto-invoke a skill or spawn an agent, and this plugin ships 85 skills
+ 45 agents — 130 choices resolved from description text alone. The linter
checked only that the field was *non-empty*, so misrouting (a skill firing on the
wrong task, or the right skill never firing) had no detector.

- **Check 8** — description never says when *not* to use this. WARNING.
- **Check 9** — description is a near-duplicate of another entry's. WARNING.
- **Check 10** — description has no explicit trigger clause; it describes rather
  than routes. WARNING.
- Checks 8 and 10 recognise Korean as well as English phrasing.
- **All three are warnings, and warnings never enter `lint_baseline.json`** — so
  this landed with zero baseline churn. Current roster: 118 of 130 files warn.
  Run `--strict` to see the backlog; CI stays green and a *new* skill lands with
  the defect visible.
- **`NEAR_DUPLICATE_THRESHOLD = 0.30`**, measured not guessed. Over all 8385
  pairs in the v0.6.2 roster: max 0.438, p99.9 0.216, p99 0.121, median 0.000.
  The first value tried was 0.60 and it never fired once — a check that cannot
  fire is worse than no check, because silence reads as "no confusables exist".
  At 0.30 it selects exactly the pairs a human agrees are confusable, led by
  `create-prd` ~ `design-system` (0.44), which is the product-track/game-track
  pack mixing `CLAUDE.md` explicitly warns against.
- Tests: `tests/test_skill_lint.py` — 13 new cases including
  `test_threshold_can_actually_fire_on_the_real_roster`, which fails if the
  threshold is ever raised back out of range.

Rationale and the wider plan: `docs/design/v0.6.3-context-density-plan.md`,
sourced from `docs/design/ax-labs-blog-audit.md`.

### Added — `/remove-bg`: background removal as a deterministic, cost-gated skill

The plugin had `/api-cost-gate` (a disclosure format) and `/asset-spec` (which
produces asset rows) but nothing that actually *did* image work. Background
removal is the most common cutout task in both tracks — game sprites and product
photography — and it is billable, which makes it a useful shape to get right.

- **`scripts/removebg.py`** — stdlib-only [remove.bg](https://www.remove.bg/api)
  client with three subcommands: `account` (balance), `estimate` (plan + cost,
  **zero** billable calls), `run` (execute). Single file, folder batch,
  recursive, and `http(s)` URL inputs. Emits a JSON report whose
  `credits_charged_total` is the measured `X-Credits-Charged` sum, not the
  estimate.
- **Exit code is the verdict**, per `docs/deterministic-gates.md`: `0` all
  processed · `1` partial failure or everything skipped · `2` all failed / `402`
  insufficient credits / `403` auth failure / `--max-calls` ceiling tripped ·
  `3` cannot run (no key, bad path — nothing called, nothing charged).
  `402`/`403` abort the whole batch rather than failing per-image, because
  continuing there only spends money badly.
- **`skills/remove-bg/SKILL.md`** — embeds the `/api-cost-gate` 4-point
  disclosure (Phases 2-3) rather than delegating to it, backs point 2 with a real
  balance lookup, and writes results back to `design/assets/asset-manifest.md` at
  status `In Progress` (a cutout is a processing step, not an approval).
- **Cost discipline is structural, not advisory**: `--size preview` (≈0.25
  credits) is the default against `full` (≈1 credit); `--max-calls` aborts if the
  input set grew between estimate and run; failed images are never auto-retried.
- **Keys are never CLI arguments** — environment variable or `--api-key-file`
  only, so nothing lands in shell history or the process list.
- Docs: entries in `docs/skills-reference.md` (Art & Asset Pipeline + Creative &
  Content), a remove.bg row and a "use the dedicated skill" note in
  `skills/api-cost-gate/SKILL.md`, a third reference implementation in
  `docs/deterministic-gates.md`, and a README section.

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
