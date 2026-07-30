"""scripts/lint_skills.py 단위 테스트.

린터가 CI 게이트인 이상 린터 자신도 검증돼야 한다. 특히 baseline 로직은
"기존 부채는 통과시키되 신규 위반은 막는다"는 비대칭 동작이라, 어느 쪽이
깨져도 조용하다 — 신규를 못 막으면 게이트가 무의미해지고, 기존을 막으면
CI가 상시 빨간불이 된다. 양방향을 모두 단언한다.

`python3 -m unittest` 와 pytest 양쪽에서 동작.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import lint_skills as ls  # noqa: E402


GOOD_SKILL = """---
name: good-skill
description: A well-formed skill
argument-hint: "[target]"
user-invocable: true
allowed-tools: Read, Glob
---

# Good Skill

## Phase 1: Do the thing

Body.

## Phase 2: Report

Emit PASS or FAIL.

## Recommended next

Run `/other-skill`.
"""


def _write_skill(root: str, name: str, text: str) -> str:
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "SKILL.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class TestFrontmatter(unittest.TestCase):
    def test_parses_top_level_scalars(self):
        fm = ls.parse_frontmatter(GOOD_SKILL)
        self.assertEqual(fm["name"], "good-skill")
        self.assertEqual(fm["user-invocable"], "true")
        self.assertEqual(fm["allowed-tools"], "Read, Glob")

    def test_missing_block_returns_none(self):
        self.assertIsNone(ls.parse_frontmatter("# No frontmatter\n\nbody"))

    def test_indented_keys_are_ignored(self):
        # 중첩 키를 최상위로 잘못 읽으면 필수 필드 검사가 통과해 버린다.
        text = "---\nname: x\nnested:\n  name: should-not-leak\n---\nbody"
        fm = ls.parse_frontmatter(text)
        self.assertEqual(fm["name"], "x")
        self.assertNotIn("should-not-leak", fm.values())


class TestChecks(unittest.TestCase):
    def test_well_formed_skill_has_no_failures(self):
        # read-only 스킬이라 Check 4 는 WARN 이 남는다(설계된 동작). failures 만 0.
        r = ls.lint_skill("good/SKILL.md", GOOD_SKILL)
        self.assertEqual(r.failures, [], f"unexpected failures: {r.failures}")
        self.assertEqual(r.verdict, "WARNINGS")

    def test_fully_compliant_skill(self):
        text = GOOD_SKILL.replace("allowed-tools: Read, Glob", "allowed-tools: Read, Write")
        text = text.replace("Body.", "Body. May I write the result to the file?")
        r = ls.lint_skill("good/SKILL.md", text)
        self.assertEqual(r.failures, [])
        self.assertEqual(r.warnings, [])
        self.assertEqual(r.verdict, "COMPLIANT")

    def test_check1_missing_fields(self):
        text = "---\nname: x\ndescription: y\n---\n\n## Phase 1\n\n## Phase 2\n\nPASS\n"
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 1" in f for f in r.failures))

    def test_check2_needs_two_phases(self):
        text = GOOD_SKILL.replace("## Phase 2: Report", "").replace("## Recommended next", "")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 2" in f for f in r.failures))

    def test_check3_needs_verdict_keyword(self):
        text = GOOD_SKILL.replace("Emit PASS or FAIL.", "Emit something.")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 3" in f for f in r.failures))

    def test_check4_write_tools_require_ask_language(self):
        """Write/Edit 권한이 있는데 승인 문구가 없으면 WARN 이 아니라 FAIL 이다."""
        text = GOOD_SKILL.replace("allowed-tools: Read, Glob", "allowed-tools: Read, Write")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 4" in f for f in r.failures))

    def test_check4_readonly_skill_only_warns(self):
        r = ls.lint_skill("x/SKILL.md", GOOD_SKILL)
        self.assertTrue(any("Check 4" in w for w in r.warnings))
        self.assertFalse(any("Check 4" in f for f in r.failures))

    def test_check4_ask_language_satisfies_write_tools(self):
        text = GOOD_SKILL.replace("allowed-tools: Read, Glob", "allowed-tools: Read, Write")
        text = text.replace("Body.", "Body. May I write this to the file?")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertFalse(any("Check 4" in f for f in r.failures))

    def test_check5_missing_handoff_warns(self):
        text = GOOD_SKILL.replace("## Recommended next\n\nRun `/other-skill`.\n", "")
        r = ls.lint_skill("x/SKILL.md", text)
        self.assertTrue(any("Check 5" in w for w in r.warnings))


class TestAgentChecks(unittest.TestCase):
    def test_agent_requires_five_fields(self):
        text = "---\nname: a\ndescription: d\nmodel: opus\n---\nbody"
        r = ls.lint_agent("agents/a.md", text)
        self.assertTrue(any("tools" in f and "maxTurns" in f for f in r.failures))

    def test_complete_agent_passes(self):
        text = "---\nname: a\ndescription: d\ntools: Read\nmodel: opus\nmaxTurns: 8\n---\nbody"
        r = ls.lint_agent("agents/a.md", text)
        self.assertEqual(r.failures, [])


class TestBaseline(unittest.TestCase):
    """비대칭 동작 양방향 — 기존 부채는 통과, 신규 위반은 차단."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.skills = os.path.join(self.root, "skills")
        os.makedirs(self.skills)
        self.baseline = os.path.join(self.root, "baseline.json")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args) -> int:
        return ls.main(list(args))

    def test_known_failure_is_tolerated_but_new_one_is_not(self):
        broken = "---\nname: broken\ndescription: d\n---\n\nbody with no phases\n"
        _write_skill(self.skills, "broken", broken)

        # baseline 없이는 실패
        self.assertEqual(self._run(self.skills, "--quiet"), 1)

        # baseline 을 뜨면 통과
        self.assertEqual(self._run(self.skills, "--write-baseline", self.baseline), 0)
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 0)

        # 새 위반이 추가되면 다시 차단
        _write_skill(self.skills, "broken2", broken.replace("broken", "broken2"))
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 1)

    def test_baselined_entry_that_gets_worse_is_blocked(self):
        """failure 목록이 달라지면 baseline 과 불일치 → 차단."""
        text = "---\nname: drift\ndescription: d\nargument-hint: \"[x]\"\nuser-invocable: true\nallowed-tools: Read\n---\n\n## Phase 1\n\n## Phase 2\n\nbody\n"
        _write_skill(self.skills, "drift", text)
        self.assertEqual(self._run(self.skills, "--write-baseline", self.baseline), 0)
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 0)

        # 필수 필드를 하나 더 깨면 failure 목록이 늘어난다
        _write_skill(self.skills, "drift", text.replace("user-invocable: true\n", ""))
        self.assertEqual(self._run(self.skills, "--quiet", "--baseline", self.baseline), 1)

    def test_partial_run_does_not_report_unlinted_entries_as_stale(self):
        """회귀 테스트 — stale 판정이 `in seen` 가드를 잃으면 부분 린트에서 오보고한다."""
        broken = "---\nname: broken\ndescription: d\n---\n\nbody\n"
        _write_skill(self.skills, "broken", broken)
        _write_skill(self.skills, "other", broken.replace("broken", "other"))
        self._run(self.skills, "--write-baseline", self.baseline)

        with open(self.baseline, encoding="utf-8") as f:
            known = json.load(f)["known_failures"]
        self.assertEqual(set(known), {"broken", "other"})

        # 'broken' 하나만 린트 — 'other' 는 검사하지 않았을 뿐 고쳐진 게 아니다
        one = os.path.join(self.skills, "broken")
        buf, sys.stdout = sys.stdout, open(os.devnull, "w")
        try:
            code = self._run(one, "--baseline", self.baseline)
        finally:
            sys.stdout.close()
            sys.stdout = buf
        self.assertEqual(code, 0)

    def test_missing_baseline_file_is_not_an_error(self):
        _write_skill(self.skills, "good", GOOD_SKILL)
        code = self._run(self.skills, "--quiet", "--baseline", os.path.join(self.root, "nope.json"))
        self.assertEqual(code, 0)


class TestExitCodes(unittest.TestCase):
    def test_nothing_to_lint_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            empty = os.path.join(d, "empty")
            os.makedirs(empty)
            self.assertEqual(ls.main([empty, "--quiet"]), 2)

    def test_strict_turns_warnings_into_failure(self):
        with tempfile.TemporaryDirectory() as d:
            skills = os.path.join(d, "skills")
            os.makedirs(skills)
            _write_skill(skills, "warner", GOOD_SKILL)  # Check 4 read-only WARN
            self.assertEqual(ls.main([skills, "--quiet"]), 0)
            self.assertEqual(ls.main([skills, "--quiet", "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
