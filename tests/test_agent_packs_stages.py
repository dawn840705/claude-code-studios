"""docs/agent-packs.yaml `stages:` 와 docs/workflow-catalog.yaml phase 의 정합 검사.

v0.6.3 에서 스테이지별 에이전트 배정을 CLAUDE.md 본문에서 agent-packs.yaml 로
옮겼다. 그 결과 CLAUDE.md 는 "현재 phase 는 check_phase.py 에게 묻고, 그 phase 의
담당 에이전트는 agent-packs.yaml 에서 찾아라" 라는 **조인**을 지시한다.

조인은 양쪽 키가 같을 때만 성립한다. 초안은 스테이지를 5개만 적어서
concept·systems-design·technical-setup·architecture 가 비어 있었고, 그 상태에서
check_phase.py 가 `concept` 을 반환하면 조회가 조용히 실패했다 — 오케스트레이터는
빈 결과를 받고 추측으로 되돌아간다. 압축이 만든 결함이라 압축과 함께 잠근다.

`python3 -m unittest` 와 pytest 양쪽에서 동작. 표준 라이브러리만 사용
(check_phase.py 와 같은 이유 — 저장소 규칙이 stdlib-only).
"""
from __future__ import annotations

import os
import re
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
PACKS = os.path.join(_ROOT, "docs", "agent-packs.yaml")
CATALOG = os.path.join(_ROOT, "docs", "workflow-catalog.yaml")
AGENTS_DIR = os.path.join(_ROOT, "agents")

TRACKS = ("game", "product")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def catalog_phases() -> dict[str, list[str]]:
    """{track: [phase ids in order]} — 6칸/4칸 들여쓰기로 트랙과 phase 를 구분."""
    out: dict[str, list[str]] = {}
    track = None
    in_tracks = False
    for line in _read(CATALOG).splitlines():
        if re.match(r"^tracks:\s*$", line):
            in_tracks = True
            continue
        if not in_tracks:
            continue
        m = re.match(r"^  ([a-z-]+):\s*$", line)
        if m:
            track = m.group(1)
            out.setdefault(track, [])
            continue
        m = re.match(r"^      ([a-z-]+):\s*$", line)
        if m and track:
            out[track].append(m.group(1))
    return out


def packs_stages() -> dict[str, dict[str, dict[str, list[str]]]]:
    """{track: {stage: {'primary': [...], 'support': [...]}}} — `stages:` 블록만."""
    text = _read(PACKS)
    block = text.split("\nstages:", 1)[1]
    # 다음 최상위 키에서 멈춘다 (post_release, cross_stage, packs …)
    block = re.split(r"\n(?=[a-z_]+:)", block, maxsplit=1)[0]

    out: dict[str, dict[str, dict[str, list[str]]]] = {}
    track = stage = None
    for raw in block.splitlines():
        line = raw.split("#")[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^  ([a-z-]+):\s*$", line)
        if m:
            track = m.group(1)
            out.setdefault(track, {})
            stage = None
            continue
        m = re.match(r"^    ([a-z-]+):\s*$", line)
        if m and track:
            stage = m.group(1)
            out[track][stage] = {"primary": [], "support": []}
            continue
        m = re.match(r"^      (primary|support):\s*\[(.*)\]\s*$", line)
        if m and track and stage:
            vals = [v.strip() for v in m.group(2).split(",") if v.strip()]
            out[track][stage][m.group(1)] = vals
    return out


class TestStageKeysMatchCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = catalog_phases()
        self.packs = packs_stages()

    def test_both_files_parsed(self):
        for track in TRACKS:
            self.assertTrue(self.catalog.get(track), f"catalog track missing: {track}")
            self.assertTrue(self.packs.get(track), f"packs track missing: {track}")

    def test_every_catalog_phase_has_staffing(self):
        """check_phase.py 가 반환할 수 있는 phase 는 전부 담당자가 있어야 한다."""
        for track in TRACKS:
            missing = [p for p in self.catalog[track] if p not in self.packs[track]]
            self.assertEqual(
                missing, [],
                f"{track}: 카탈로그 phase 인데 agent-packs.yaml stages 에 없음 → "
                f"조인 실패, 오케스트레이터가 추측으로 되돌아감: {missing}",
            )

    def test_no_orphan_staffing_entries(self):
        """반대 방향 — 카탈로그에 없는 stage 를 적어두면 영원히 조회되지 않는다."""
        for track in TRACKS:
            orphans = [s for s in self.packs[track] if s not in self.catalog[track]]
            self.assertEqual(
                orphans, [],
                f"{track}: 카탈로그에 대응 phase 가 없는 stage. 운영 국면이라면 "
                f"`post_release:` 로 옮길 것: {orphans}",
            )

    def test_every_stage_has_at_least_one_primary(self):
        for track in TRACKS:
            for stage, roles in self.packs[track].items():
                self.assertTrue(
                    roles["primary"],
                    f"{track}.{stage}: primary 가 비어 있다 — 담당자 없는 스테이지",
                )

    def test_all_referenced_agents_exist(self):
        existing = {f[:-3] for f in os.listdir(AGENTS_DIR) if f.endswith(".md")}
        for track in TRACKS:
            for stage, roles in self.packs[track].items():
                for kind in ("primary", "support"):
                    for name in roles[kind]:
                        self.assertIn(
                            name, existing,
                            f"{track}.{stage}.{kind}: 존재하지 않는 에이전트 {name}",
                        )

    def test_pack_discipline_is_not_violated_by_staffing(self):
        """game 스테이지에 product 전용 에이전트가 섞이면 CLAUDE.md 규칙과 모순된다."""
        text = _read(PACKS)
        def members(pack: str) -> set[str]:
            blk = text.split(f"\n  {pack}:", 1)[1]
            blk = re.split(r"\n  [a-z]+:", blk, maxsplit=1)[0]
            return set(re.findall(r"^\s*- name:\s*([\w-]+)", blk, re.M))

        game_only, product_only = members("game"), members("product")
        for stage, roles in self.packs["game"].items():
            for name in roles["primary"] + roles["support"]:
                self.assertNotIn(name, product_only,
                                 f"game.{stage} 에 product 전용 에이전트: {name}")
        for stage, roles in self.packs["product"].items():
            for name in roles["primary"] + roles["support"]:
                self.assertNotIn(name, game_only,
                                 f"product.{stage} 에 game 전용 에이전트: {name}")


if __name__ == "__main__":
    unittest.main()
