#!/usr/bin/env python3
"""Tier 1 구조 게이트 — 5축 통합 결정적 사후 검증 (LLM 콜 0).

`verify_change_rate.py`(문자율 단축 게이트)의 확장판. 문자 diff는 구조
편집에 눈이 없다 — 실측에서 change_rate 2.77% 뒤에 문장 터치율 29.7%,
ending_comma -86%, C-8 대구 -75%가 숨어 있었다. 이 스크립트는 문자율에
더해 (목표 달성 · 대구 전멸 · golden+수치 · 줄표) 4축을 결정적 코드로 판정해
문자율의 사각지대를 보완한다. 기존 verify_change_rate.py는 그대로 두고
(하위 호환), 신규 게이트는 이 파일이 담당한다.

5축 + 리포트:
    P0 문자율   — change_rate() vs WARN 30% / ABORT 50% (기존과 동일 판정)
    P1 목표달성 — before z > +2.0인 어휘 S1 지표가 after에서 z <= +1.0으로
                  내려왔는가. 미달(> +2.0)·과교정(< -1.5)은 WARN.
    P2 전멸    — C-8 대구: before >= 5 AND after == 0 이면 FAIL.
    P3 golden  — tests/golden/checks.run_checks() 실패 목록 (수치 주입 포함).
    P4 터치율  — 원문 문장 중 after에 그대로 없는 비율 + 수치 소실 관찰.
                 게이트 아님, 보고만 (수치 소실은 문장 병합·표기 통합의
                 정상 부산물일 수 있어 exit code에 기여하지 않는다).
    P5 줄표    — J-3 문장 중간 em dash. before >= 3 인데 after > 2 이면 미달,
                 after > before 이면 역방향 삽입. 둘 다 WARN.

Exit code (verify_change_rate.py와 의미 동일):
    0 — 수렴 (전 축 통과)
    1 — 경고 (문자율 30~50% / 목표 미달·과교정 / 전멸 / golden FAIL / 줄표 잔존)
    2 — 중단 (문자율 >= 50%). 윤문본 채택 금지 — 최우선.
    3 — 실행 오류 (입력 파일 없음 등). 게이트 판정 불가.

CLI:
    python3 scripts/verify_gates.py \
        --before _workspace/{run_id}/01_input.txt \
        --after  _workspace/{run_id}/final.md \
        --genre essay
    옵션: --json (구조화 출력 병기) / --ignore-markup (문자율 축만 적용)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gate_report  # noqa: E402

_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_REFS = os.path.join(_ROOT, "skills", "humanize-korean", "reference")
_GOLDEN = os.path.join(_ROOT, "tests", "golden")
for _p in (_REFS, _GOLDEN):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks as _checks  # noqa: E402  (sys.path mutation is intentional)
import metrics_v2 as _m  # noqa: E402

# final.md 본문 끝의 메타데이터 주석 블록. 여는 마커부터 파일 끝까지.
_SUMMARY_BLOCK_RE = re.compile(r"<!--\s*HUMANIZE-SUMMARY\b.*", re.DOTALL)

# P1 목표 달성 축의 어휘 S1 후보 지표. lexical_diversity는 제외 —
# 높을수록 사람 글이라 감축 대상이 아니다.
S1_CANDIDATE_METRICS = (
    "comma_inclusion_rate",
    "comma_usage_rate",
    "ending_comma_rate",
    "comma_segment_length",
    "hanja_nominalizer_density",
)

# P1 임계값
S1_SELECT_Z = 2.0      # before z가 이보다 크면 S1 대상
S1_ACHIEVED_Z = 1.0    # after z가 이하이면 달성
S1_MISSED_Z = 2.0      # after z가 이보다 크면 미달 (조용한 실패)
S1_OVERCORRECT_Z = -1.5  # after z가 미만이면 과교정

# P2 전멸 임계값 — 원래 대구가 이만큼은 있어야 "전멸"이 의미를 가진다.
ANNIHILATION_MIN_BEFORE = 5

# P5 줄표(J-3) 임계값.
# 절대치가 아니라 before/after 로 판정한다 — J-3 는 "원문에 이미 있던 대시는
# 사람 글의 증거이므로 보존" 을 예외로 두므로, 출력만 세면 흔한 보존 케이스
# (원문 1~2회)를 그대로 벌한다.
#
# 다만 이 설계가 그 예외를 **완전히** 면제하지는 않는다: 원문에 산문 삽입
# 줄표가 3회 이상이면 보존해도 미달로 걸린다. 실측상 그런 한국어 원문은
# 22.0만 자에 0건이라 드물고, 걸려도 exit 1(WARN — 고지 + finalize 승급)이지
# 채택 금지가 아니다. 반대로 없던 줄표를 넣는 것은 1회부터 잡는다.
EM_DASH_MIN_BEFORE = 3    # 이만큼은 있어야 "남발" 이라 부를 수 있다
EM_DASH_TARGET_AFTER = 2  # J-3 처방의 "1문서에 1~2회 이하"

_WS_RE = re.compile(r"\s+")


def strip_summary_block(text: str) -> str:
    """final.md에서 `<!-- HUMANIZE-SUMMARY -->` 메타 블록을 제거한다."""
    return _SUMMARY_BLOCK_RE.sub("", text).strip()


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _norm_sentence(s: str) -> str:
    return _WS_RE.sub(" ", s).strip()


def sentence_touch_rate(before: str, after: str) -> tuple[float, int, int]:
    """원문 문장 중 after에 (공백 정규화 후) 그대로 없는 비율.

    게이트가 아니라 리포트 전용 — 문자율이 낮아도 구조 편집이 넓게 퍼져
    있으면 이 수치가 드러낸다. 반환: (rate, touched, total).
    """
    before_sents = [_norm_sentence(s) for s in _m._split_sentences(before)]
    before_sents = [s for s in before_sents if s]
    if not before_sents:
        return 0.0, 0, 0
    after_set = {_norm_sentence(s) for s in _m._split_sentences(after)}
    touched = sum(1 for s in before_sents if s not in after_set)
    return touched / len(before_sents), touched, len(before_sents)


def judge_s1_targets(
    z_before: dict, z_after: dict
) -> tuple[list[dict], bool]:
    """P1 목표 달성 판정. 반환: (지표별 판정 목록, warn 여부).

    S1 대상 = S1_CANDIDATE_METRICS 중 before z > +2.0인 지표.
    각 대상: after z <= +1.0 달성 / > +2.0 미달(WARN) / < -1.5 과교정(WARN)
    / 그 사이는 부분 개선(통과). after z가 None이면 판정 불가(보고만).
    """
    results: list[dict] = []
    warn = False
    for key in S1_CANDIDATE_METRICS:
        zb = z_before.get(key)
        if zb is None or zb <= S1_SELECT_Z:
            continue
        za = z_after.get(key)
        if za is None:
            verdict = "판정불가 (after z 없음)"
        elif za <= S1_OVERCORRECT_Z:
            verdict, warn = "과교정", True
        elif za <= S1_ACHIEVED_Z:
            verdict = "달성"
        elif za > S1_MISSED_Z:
            verdict, warn = "미달", True
        else:
            verdict = "부분 개선"
        results.append({
            "metric": key,
            "z_before": round(zb, 2),
            "z_after": round(za, 2) if za is not None else None,
            "verdict": verdict,
        })
    return results, warn


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Tier 1 구조 게이트 (5축 통합)")
    p.add_argument("--before", required=True, help="원문 경로 (01_input.txt)")
    p.add_argument("--after", required=True, help="윤문본 경로 (final.md)")
    p.add_argument("--genre", default="essay", help="essay/column/report/blog/abstract")
    p.add_argument("--json", action="store_true", help="구조화 JSON 출력 병기")
    p.add_argument(
        "--ignore-markup",
        action="store_true",
        help="문자율 축에서 마크업 줄·줄머리 장식을 제외하고 본문만 비교",
    )
    args = p.parse_args(argv)

    for path in (args.before, args.after):
        if not os.path.exists(path):
            print(f"error: 파일 없음: {path}", file=sys.stderr)
            return 3

    try:
        before = strip_summary_block(_read(args.before))
        after = strip_summary_block(_read(args.after))
    except OSError as e:
        print(f"error: 파일 읽기 실패: {e}", file=sys.stderr)
        return 3

    report: dict = {"genre": args.genre}
    warn = False

    # --- P0 문자율 (기존 verify_change_rate.py와 동일 판정) ---------------
    rate = _m.change_rate(before, after, ignore_markup=args.ignore_markup)
    abort = rate >= _m.CHANGE_RATE_ABORT
    if _m.CHANGE_RATE_WARN <= rate < _m.CHANGE_RATE_ABORT:
        warn = True
    scope = "본문만 (마크업 제외)" if args.ignore_markup else "전문"
    if abort:
        p0_verdict = "ABORT — 강제 중단. 윤문본 채택 금지"
    elif rate >= _m.CHANGE_RATE_WARN:
        p0_verdict = "WARN — 과윤문 경고"
    else:
        p0_verdict = "OK"
    report["change_rate"] = {
        "rate": round(rate, 4), "scope": scope, "verdict": p0_verdict,
    }
    print(f"[P0 문자율] {rate * 100:.1f}% [{scope}] — {p0_verdict} "
          f"(경고 {_m.CHANGE_RATE_WARN * 100:.0f}% / 중단 {_m.CHANGE_RATE_ABORT * 100:.0f}%)")

    # --- P1 목표 달성 (before z > +2.0인 어휘 S1 지표) --------------------
    try:
        z_before = _m.compute_all_v2(before, genre=args.genre)["z_scores"]
        z_after = _m.compute_all_v2(after, genre=args.genre)["z_scores"]
    except Exception as e:  # graceful degrade — 이 축만 판정 불가
        z_before, z_after = {}, {}
        print(f"[P1 목표달성] 판정 불가 (metrics 오류: {e})", file=sys.stderr)
    s1_results, s1_warn = judge_s1_targets(z_before, z_after)
    warn = warn or s1_warn
    report["s1_targets"] = s1_results
    if not s1_results:
        print("[P1 목표달성] N/A — 구조 진단 (어휘 S1 앵커 없음)")
    else:
        for r in s1_results:
            za = f"{r['z_after']:+.2f}" if r["z_after"] is not None else "?"
            print(f"[P1 목표달성] {r['metric']}: z {r['z_before']:+.2f} → {za}"
                  f"  {r['verdict']}")

    # --- P2 전멸 (C-8 대구) ----------------------------------------------
    anti_before = _m.antithesis_count(before)
    anti_after = _m.antithesis_count(after)
    annihilated = anti_before >= ANNIHILATION_MIN_BEFORE and anti_after == 0
    warn = warn or annihilated
    report["antithesis"] = {
        "before": anti_before, "after": anti_after,
        "verdict": "FAIL — 전멸" if annihilated else (
            "OK" if anti_before >= ANNIHILATION_MIN_BEFORE
            else "스킵 (원문 대구 < 5)"),
    }
    print(f"[P2 전멸] C-8 대구 {anti_before} → {anti_after} — "
          f"{report['antithesis']['verdict']}")

    # --- P3 golden + 수치 -------------------------------------------------
    failures = _checks.run_checks(before, after)
    warn = warn or bool(failures)
    report["golden"] = [{"code": f.code, "message": f.message} for f in failures]
    if failures:
        print(f"[P3 golden] FAIL — {len(failures)}건:")
        for f in failures:
            print(f"    FAIL {f}")
    else:
        print("[P3 golden] PASS (수치 주입·각주·인용·register 이상 없음)")

    # --- P4 터치율 + 수치 소실 관찰 (리포트 전용 — 게이트 아님) -----------
    touch_rate, touched, total = sentence_touch_rate(before, after)
    report["sentence_touch"] = {
        "rate": round(touch_rate, 4), "touched": touched, "total": total,
    }
    print(f"[P4 터치율] {touch_rate * 100:.1f}% ({touched}/{total} 문장) — 보고 전용")
    dropped = _checks.dropped_numbers(before, after)
    report["numbers_dropped"] = dropped
    if dropped:
        print(f"[P4 수치소실] 관찰: {dropped} "
              f"(문장 병합·표기 통합이면 정상 — exit 미반영, 확인 요망)")

    # --- P5 줄표 (J-3) ----------------------------------------------------
    # 두 가지를 잡는다: (a) 남발이 그대로 남음, (b) 윤문기가 대시를 늘림.
    # (b) 는 D 카테고리의 "역방향 삽입 금지"(v2.0.1)와 같은 실패 모드다.
    dash_before = _m.em_dash_count(before)
    dash_after = _m.em_dash_count(after)
    dash_injected = dash_after > dash_before
    dash_missed = (
        dash_before >= EM_DASH_MIN_BEFORE and dash_after > EM_DASH_TARGET_AFTER
    )
    warn = warn or dash_injected or dash_missed
    if dash_injected:
        dash_verdict = "FAIL — 역방향 삽입 (원문보다 늘었다)"
    elif dash_missed:
        dash_verdict = f"FAIL — 미달 (목표 {EM_DASH_TARGET_AFTER} 이하)"
    elif dash_before >= EM_DASH_MIN_BEFORE:
        dash_verdict = "OK"
    else:
        dash_verdict = f"스킵 (원문 줄표 < {EM_DASH_MIN_BEFORE})"
    report["em_dash"] = {
        "before": dash_before, "after": dash_after, "verdict": dash_verdict,
    }
    print(f"[P5 줄표] J-3 문장중간 대시 {dash_before} → {dash_after} — "
          f"{dash_verdict}")

    # --- 통합 판정 --------------------------------------------------------
    if abort:
        verdict, code = "ABORT — 강제 중단. 윤문본 채택 금지", 2
    elif warn:
        verdict, code = "WARN — 경고. 사용자 고지 + finalize 승급", 1
    else:
        verdict, code = "OK — 수렴", 0
    report["gate"] = {"verdict": verdict, "exit_code": code}
    # 공통 4필드 봉투를 **추가**한다 — 기존 키는 그대로 둔다.
    # `--json` 출력은 이미 소비자가 있는 계약이라 형태를 바꾸지 않는다
    # (CLAUDE.md 작업 원칙: 새 경로를 더하고 기존 경로는 유지).
    # P4(sentence_touch)는 보고 전용이라 exit code 에 영향을 주지 않는다 —
    # 증거에도 넣지 않는다. 판정에 쓰이지 않은 신호를 근거로 제시하면
    # 읽는 쪽이 그것이 판정에 기여했다고 오해한다.
    _AXES = ("change_rate", "s1_targets", "antithesis", "golden",
             "em_dash", "numbers_dropped")
    report["gate_report"] = gate_report.build(
        "verify_gates", code, reason=verdict,
        evidence=[{"id": axis, "detail": report[axis]}
                  for axis in _AXES if axis in report],
    )
    print(f"gate: {verdict}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
