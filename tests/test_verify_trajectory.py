"""scripts/verify_trajectory.py 단위 테스트.

이 게이트가 지키는 것은 파일 하나가 아니라 **조인**이다 —
workflow-catalog.yaml(무엇을 어떤 순서로) × agent-packs.yaml(누가). 어느 한쪽의
한 줄이 바뀌면 그 phase 에서 도는 모든 스킬의 팬아웃이 달라지는데, 오늘까지는
어떤 테스트도 그걸 잡지 못했다.

회귀 게이트 자신이 회귀하면 아무도 모르므로, 드리프트를 **감지하는지**와
멀쩡한 상태를 **오탐하지 않는지**를 양방향으로 단언한다.

`python3 -m unittest` 와 pytest 양쪽에서 동작.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import verify_trajectory as vt  # noqa: E402


class TestExtraction(unittest.TestCase):
    def test_catalog_yields_both_tracks(self):
        cat = vt.extract_catalog()
        self.assertIn("game", cat)
        self.assertIn("product", cat)

    def test_catalog_phases_have_ordered_steps(self):
        cat = vt.extract_catalog()
        concept = cat["game"]["concept"]["steps"]
        self.assertIn("game-concept", concept)
        # 순서는 라우팅의 일부다 — 집합이 아니라 리스트로 잡아야 한다.
        self.assertIsInstance(concept, list)
        self.assertEqual(len(concept), len(set(concept)), "중복 step id")

    def test_required_is_a_subset_of_steps(self):
        for track, phases in vt.extract_catalog().items():
            for phase, data in phases.items():
                extra = set(data["required"]) - set(data["steps"])
                self.assertEqual(extra, set(), f"{track}.{phase}: steps 에 없는 required")

    def test_staffing_yields_both_tracks(self):
        staff = vt.extract_staffing()
        self.assertTrue(staff["game"])
        self.assertTrue(staff["product"])

    def test_every_catalog_phase_is_staffed_in_the_trajectory(self):
        """조인이 성립하지 않으면 이 게이트가 지킬 대상 자체가 없다."""
        traj = vt.build_trajectory()
        unstaffed = [
            f"{t}.{p}" for t, phases in traj.items()
            for p, d in phases.items() if not d["primary"]
        ]
        self.assertEqual(unstaffed, [], f"담당자 없는 phase: {unstaffed}")


class TestDiff(unittest.TestCase):
    def setUp(self) -> None:
        self.base = vt.build_trajectory()

    def test_identical_trajectories_do_not_diff(self):
        self.assertEqual(vt.diff(self.base, copy.deepcopy(self.base)), [])

    def test_removed_support_agent_is_detected(self):
        cur = copy.deepcopy(self.base)
        cur["game"]["concept"]["support"].pop()
        drift = vt.diff(self.base, cur)
        self.assertTrue(any("game.concept.support" in d for d in drift), drift)

    def test_added_primary_agent_is_detected(self):
        cur = copy.deepcopy(self.base)
        cur["product"]["build"]["primary"].append("growth-engineer")
        self.assertTrue(any("product.build.primary" in d for d in vt.diff(self.base, cur)))

    def test_reordered_steps_are_detected(self):
        """순서가 곧 워크플로다 — 같은 멤버라도 순서가 바뀌면 드리프트."""
        cur = copy.deepcopy(self.base)
        steps = cur["game"]["concept"]["steps"]
        steps[0], steps[1] = steps[1], steps[0]
        drift = vt.diff(self.base, cur)
        self.assertTrue(any("reordered" in d for d in drift), drift)

    def test_removed_phase_is_detected(self):
        cur = copy.deepcopy(self.base)
        del cur["game"]["polish"]
        self.assertIn("game.polish: PHASE REMOVED", vt.diff(self.base, cur))

    def test_added_phase_is_detected(self):
        cur = copy.deepcopy(self.base)
        cur["game"]["playtest"] = {"steps": [], "required": [], "depends_on": {},
                                   "primary": [], "support": []}
        self.assertIn("game.playtest: PHASE ADDED", vt.diff(self.base, cur))

    def test_changed_dependency_edge_is_detected(self):
        cur = copy.deepcopy(self.base)
        cur["game"]["concept"]["depends_on"]["brainstorm"] = ["game-concept"]
        self.assertTrue(any("depends_on" in d for d in vt.diff(self.base, cur)))


class TestGoldenIsCurrent(unittest.TestCase):
    def test_recorded_trajectory_matches_the_sources(self):
        """골든이 낡으면 게이트는 통과하면서 아무것도 지키지 않는다."""
        self.assertEqual(vt.main(["--quiet"]), vt.EXIT_OK,
                         "라우팅이 골든과 다르다. 의도한 변경이면 "
                         "`python3 scripts/verify_trajectory.py --update` 후 diff 를 리뷰할 것")

    def test_golden_file_is_valid_json_with_tracks(self):
        with open(vt.GOLDEN, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertIn("tracks", payload)
        self.assertIn("_comment", payload, "재생성 방법이 파일 안에 있어야 한다")

    def test_golden_covers_every_catalog_phase(self):
        golden = vt.load_golden()
        catalog = vt.extract_catalog()
        for track in vt.TRACKS:
            self.assertEqual(sorted(golden[track]), sorted(catalog[track]),
                             f"{track}: 골든과 카탈로그의 phase 목록 불일치")


class TestContract(unittest.TestCase):
    """docs/deterministic-gates.md 4코드 계약."""

    def test_missing_source_cannot_judge(self):
        original = vt.CATALOG
        try:
            vt.CATALOG = os.path.join(_ROOT, "docs", "does-not-exist.yaml")
            self.assertEqual(vt.main(["--quiet"]), vt.EXIT_CANNOT_JUDGE)
        finally:
            vt.CATALOG = original

    def test_missing_golden_cannot_judge_rather_than_pass(self):
        original = vt.GOLDEN
        try:
            vt.GOLDEN = os.path.join(_ROOT, "tests", "trajectories", "nope.json")
            self.assertEqual(vt.main(["--quiet"]), vt.EXIT_CANNOT_JUDGE)
        finally:
            vt.GOLDEN = original

    def test_drift_is_exit_2_not_1(self):
        """라우팅 드리프트는 '경고' 가 아니다 — 리뷰 없이 지나가면 안 된다."""
        self.assertEqual(vt.EXIT_DRIFT, 2)

    def test_print_mode_does_not_judge(self):
        self.assertEqual(vt.main(["--print"]), vt.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
