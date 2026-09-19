"""scripts/verify_install.py 단위 테스트.

이 게이트가 지키는 것은 저장소 안의 파일이 아니라 **호스트와의 연결**이다 —
디스크에 멀쩡히 있는 사본이 실제로 로드되느냐. 2026-09-19 에 그 연결만 끊긴
적이 있고, 그때 다른 게이트는 전부 초록이었다 (`verify_trajectory` exit 0,
에이전트·스킬·훅은 0개).

그러므로 양방향으로 단언한다 — 끊긴 상태를 **잡는지**, 그리고 멀쩡한 상태를
**오탐하지 않는지**. 오탐하는 게이트는 통째로 꺼지고, 꺼진 게이트는 없는 것과
같다.

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

import verify_install as vi  # noqa: E402
from gate_report import build as build_report, is_valid  # noqa: E402

NAME = "claude-code-studios"


def make_plugin(root: str, version: str, name: str = NAME) -> str:
    """디스크에 플러그인 사본 하나를 만든다 (manifest 만 있으면 된다)."""
    manifest_dir = os.path.join(root, ".claude-plugin")
    os.makedirs(manifest_dir, exist_ok=True)
    with open(os.path.join(manifest_dir, "plugin.json"), "w", encoding="utf-8") as fh:
        json.dump({"name": name, "version": version}, fh)
    return root


def registry(entries: dict) -> dict:
    return {"version": 2, "plugins": entries}


def entry(install_path: str, version: str, scope: str = "project") -> dict:
    return {"scope": scope, "installPath": install_path, "version": version}


class TestHealthy(unittest.TestCase):
    """멀쩡한 설치를 실패로 읽으면 안 된다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_plugin(os.path.join(self.tmp.name, "0.6.5"), "0.6.5")
        self.addCleanup(self.tmp.cleanup)

    def test_registered_and_matching_passes(self):
        reg = registry({f"{NAME}@game-studios": [entry(self.root, "0.6.5")]})
        code, reason, _ = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_OK, reason)

    def test_other_plugins_in_the_registry_are_ignored(self):
        reg = registry({
            "playground@official": [entry(self.tmp.name, "abc")],
            f"{NAME}@game-studios": [entry(self.root, "0.6.5")],
        })
        code, _, _ = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_OK)

    def test_running_from_a_checkout_is_not_a_failure(self):
        """개발 체크아웃에서 돌리면 호스트가 로드하는 사본과 경로가 다르다.

        이건 정상이므로 판정을 움직여서는 안 된다 — 증거로만 남는다
        (docs/deterministic-gates.md "Adding a gate" 규칙 4).
        """
        checkout = make_plugin(os.path.join(self.tmp.name, "checkout"), "0.6.5")
        reg = registry({f"{NAME}@game-studios": [entry(self.root, "0.6.5")]})
        code, _, evidence = vi.audit(vi.read_manifest(checkout), checkout, reg)
        self.assertEqual(code, vi.EXIT_OK)
        self.assertIn("other-copy", [e["id"] for e in evidence])


class TestNotLoadable(unittest.TestCase):
    """2026-09-19 상태 — 디스크엔 있는데 호스트가 모른다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_plugin(os.path.join(self.tmp.name, "0.6.5"), "0.6.5")
        self.addCleanup(self.tmp.cleanup)

    def test_missing_entry_aborts(self):
        reg = registry({"playground@official": [entry(self.tmp.name, "abc")]})
        code, reason, evidence = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_NOT_LOADABLE)
        self.assertIn(NAME, reason)
        self.assertIn("no-entry", [e["id"] for e in evidence])

    def test_empty_registry_aborts(self):
        code, _, _ = vi.audit(vi.read_manifest(self.root), self.root, registry({}))
        self.assertEqual(code, vi.EXIT_NOT_LOADABLE)

    def test_entry_pointing_at_a_vanished_path_aborts(self):
        """다른 프로필 경로가 실려 있던 실제 사례가 이 모양으로 나타난다."""
        gone = os.path.join(self.tmp.name, "does-not-exist", "0.6.5")
        reg = registry({f"{NAME}@game-studios": [entry(gone, "0.6.5")]})
        code, reason, _ = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_NOT_LOADABLE)
        self.assertIn("installPath", reason)

    def test_a_similarly_named_plugin_does_not_count_as_registered(self):
        """`claude-code-studios-extra@x` 는 `claude-code-studios` 가 아니다."""
        other = make_plugin(os.path.join(self.tmp.name, "extra"), "1.0",
                            name=f"{NAME}-extra")
        reg = registry({f"{NAME}-extra@m": [entry(other, "1.0")]})
        code, _, _ = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_NOT_LOADABLE)


class TestStale(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_plugin(os.path.join(self.tmp.name, "0.6.5"), "0.6.5")
        self.addCleanup(self.tmp.cleanup)

    def test_version_skew_warns_rather_than_aborts(self):
        """가리키는 곳은 살아 있다 — 뭔가는 로드된다. 그래서 경고다."""
        reg = registry({f"{NAME}@game-studios": [entry(self.root, "0.6.4")]})
        code, _, evidence = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_STALE)
        self.assertIn("version-skew", [e["id"] for e in evidence])

    def test_target_without_a_manifest_warns(self):
        bare = os.path.join(self.tmp.name, "bare")
        os.makedirs(bare, exist_ok=True)
        reg = registry({f"{NAME}@game-studios": [entry(bare, "0.6.5")]})
        code, _, evidence = vi.audit(vi.read_manifest(self.root), self.root, reg)
        self.assertEqual(code, vi.EXIT_STALE)
        self.assertIn("unreadable-target", [e["id"] for e in evidence])


class TestCannotJudge(unittest.TestCase):
    """«못 읽었다» 와 «등재가 없다» 를 섞으면 이 게이트의 존재 이유가 사라진다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_missing_registry_file(self):
        with self.assertRaises(vi.CannotJudge):
            vi.load_registry(os.path.join(self.tmp.name, "nope.json"))

    def test_malformed_registry_file(self):
        path = os.path.join(self.tmp.name, "bad.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        with self.assertRaises(vi.CannotJudge):
            vi.load_registry(path)

    def test_registry_without_plugins_object(self):
        path = os.path.join(self.tmp.name, "empty.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"version": 2}, fh)
        with self.assertRaises(vi.CannotJudge):
            vi.load_registry(path)

    def test_plugin_root_without_a_manifest(self):
        with self.assertRaises(vi.CannotJudge):
            vi.read_manifest(self.tmp.name)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_plugin(os.path.join(self.tmp.name, "0.6.5"), "0.6.5")
        self.addCleanup(self.tmp.cleanup)

    def _registry_file(self, entries: dict) -> str:
        path = os.path.join(self.tmp.name, "installed_plugins.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(registry(entries), fh)
        return path

    def test_exit_codes_reach_the_caller(self):
        ok = self._registry_file({f"{NAME}@game-studios": [entry(self.root, "0.6.5")]})
        self.assertEqual(
            vi.main(["--registry", ok, "--plugin-root", self.root]), vi.EXIT_OK)

        missing = self._registry_file({})
        self.assertEqual(
            vi.main(["--registry", missing, "--plugin-root", self.root]),
            vi.EXIT_NOT_LOADABLE)

    def test_missing_registry_exits_cannot_judge_not_abort(self):
        code = vi.main(["--registry", os.path.join(self.tmp.name, "nope.json"),
                        "--plugin-root", self.root])
        self.assertEqual(code, vi.EXIT_CANNOT_JUDGE)

    def test_envelope_conforms_for_every_reachable_code(self):
        """status 는 exit_code 의 순수 함수다 — 게이트가 어긋나면 여기서 잡힌다."""
        for code in (vi.EXIT_OK, vi.EXIT_STALE, vi.EXIT_NOT_LOADABLE,
                     vi.EXIT_CANNOT_JUDGE):
            self.assertTrue(is_valid(build_report("verify_install", code,
                                                  reason="x")), f"code={code}")


if __name__ == "__main__":
    unittest.main()
