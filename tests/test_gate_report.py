"""scripts/gate_report.py + 네 게이트의 공통 봉투 준수 검사.

`docs/deterministic-gates.md` 는 "러너 출력을 파싱해 판정을 재도출하지 말라"고
금지해 왔지만, 게이트들이 자연어만 뱉는 동안에는 *왜* 를 알아야 하는 호출자에게
파싱 말고 다른 방법이 없었다. 지킬 수 없는 규칙은 없는 규칙보다 나쁘다 —
지켜지고 있는 것처럼 보이기 때문이다. 이 봉투가 그 나머지 반쪽이다.

핵심 불변식은 하나다: **status 는 exit_code 의 함수다.** 둘을 따로 두면
"ABORT 를 출력하면서 0 으로 종료" 가 표현 가능해지고, 그게 정확히
validate-assets.sh 에서 났던 버그다. 여기서는 그 상태를 만들 수 없어야 한다.

`python3 -m unittest` 와 pytest 양쪽에서 동작.
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import gate_report as gr  # noqa: E402
import verify_policy  # noqa: E402
import verify_trajectory  # noqa: E402


class TestSchema(unittest.TestCase):
    def test_status_is_derived_from_exit_code(self):
        for code, status in gr.STATUS_BY_EXIT.items():
            with self.subTest(code=code):
                r = gr.build("g", code, reason="r")
                self.assertEqual(r["status"], status)

    def test_status_cannot_be_passed_in(self):
        """호출자가 status 를 직접 지정할 수 있으면 불변식이 깨진다."""
        import inspect
        params = inspect.signature(gr.build).parameters
        self.assertNotIn("status", params)

    def test_off_contract_exit_code_is_rejected(self):
        for bad in (-1, 4, 127):
            with self.subTest(code=bad):
                with self.assertRaises(gr.UnknownExitCode):
                    gr.build("g", bad, reason="r")

    def test_exit_3_next_action_forbids_reading_as_pass(self):
        r = gr.build("g", 3, reason="git missing")
        self.assertIn("not", r["next_action"].lower())
        self.assertIn("pass", r["next_action"].lower())

    def test_every_field_is_present_and_non_empty(self):
        r = gr.build("g", 0, reason="fine")
        for k in gr.SCHEMA_KEYS:
            self.assertIn(k, r)
        self.assertTrue(gr.is_valid(r))

    def test_is_valid_rejects_a_forged_status(self):
        r = gr.build("g", 2, reason="bad")
        r["status"] = "PASS"          # 손으로 뒤집으면
        self.assertFalse(gr.is_valid(r))   # 검사에 걸려야 한다

    def test_is_valid_rejects_missing_fields(self):
        r = gr.build("g", 0, reason="fine")
        del r["evidence"]
        self.assertFalse(gr.is_valid(r))

    def test_emit_writes_parseable_json(self):
        buf = io.StringIO()
        gr.emit(gr.build("g", 1, reason="warn"), stream=buf)
        self.assertTrue(gr.is_valid(json.loads(buf.getvalue())))


def _run_json(main, argv) -> tuple[int, dict]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    text = buf.getvalue()
    start = text.find("{")
    return code, json.loads(text[start:])


class TestGatesConform(unittest.TestCase):
    """네 게이트가 같은 봉투를 내는지 — 하나라도 어긋나면 공통 소비가 불가능하다."""

    def test_verify_policy_json_conforms(self):
        code, report = _run_json(verify_policy.main, ["--project-root", _ROOT, "--json"])
        self.assertTrue(gr.is_valid(report))
        self.assertEqual(report["exit_code"], code)
        self.assertEqual(report["gate"], "verify_policy")

    def test_verify_trajectory_json_conforms(self):
        code, report = _run_json(verify_trajectory.main, ["--json"])
        self.assertTrue(gr.is_valid(report))
        self.assertEqual(report["exit_code"], code)
        self.assertEqual(report["gate"], "verify_trajectory")

    def test_check_phase_json_carries_the_envelope(self):
        import check_phase
        code, payload = _run_json(check_phase.main, ["--root", _ROOT, "--json"])
        self.assertIn("gate_report", payload)
        self.assertTrue(gr.is_valid(payload["gate_report"]))
        self.assertEqual(payload["gate_report"]["exit_code"], code)

    def test_cannot_judge_paths_also_conform(self):
        """exit 3 이야말로 구조화가 필요한 경로다 — 통과로 오독되는 지점이므로."""
        import tempfile
        with tempfile.TemporaryDirectory() as plain:
            code, report = _run_json(verify_policy.main, ["--project-root", plain, "--json"])
        self.assertEqual(code, 3)
        self.assertEqual(report["status"], "CANNOT_JUDGE")
        self.assertTrue(gr.is_valid(report))


class TestBackwardCompatibility(unittest.TestCase):
    """기존 --json 소비자를 깨지 않았는지 — 봉투는 추가지 교체가 아니다."""

    def test_check_phase_keeps_its_original_keys(self):
        import check_phase
        _, payload = _run_json(check_phase.main, ["--root", _ROOT, "--json"])
        for key in ("track", "phase", "verdict", "exit_code", "steps"):
            self.assertIn(key, payload, f"기존 키 {key} 가 사라졌다 — "
                                        "/project-stage-detect 가 이 출력을 읽는다")


if __name__ == "__main__":
    unittest.main()
