"""Live humanize runner — humanize-korean 스킬을 `codex exec`로 실제 호출.

살아있는 스킬을 돌려 갓 나온 윤문본을 얻는다. test_humanize_live.py와
generate_fixtures.py가 공유한다. `codex` CLI 인증만 있으면 되고 별도 API 키는
필요 없다. 레포의 `skills/humanize-korean/SKILL.md`를 명시적으로 읽게 한다.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_START, _END = "<<<H>>>", "<<</H>>>"
_SENTINEL = re.compile(re.escape(_START) + r"(.*?)" + re.escape(_END), re.S)

CODEX_BIN = shutil.which("codex")


class SkillUnavailable(RuntimeError):
    """Codex CLI 부재 / 타임아웃 / 출력 파싱 실패."""


def _prompt(text: str, strict: bool) -> str:
    mode = "strict(5인 파이프라인)" if strict else "Fast"
    return (
        "먼저 skills/humanize-korean/SKILL.md와 필요한 reference 파일을 읽고 지침을 따라. "
        f"다음 텍스트를 humanize-korean 스킬 {mode} 모드로 윤문해줘. "
        f"설명·헤딩·지표 전부 빼고, 윤문된 본문만 반드시 {_START} 와 {_END} 사이에 "
        f"한 덩어리로 출력해. 파일은 만들지 마.\n\n텍스트:\n" + text
    )


def run_humanize(text: str, *, strict: bool = False, timeout: int = 300) -> str:
    """스킬을 실제 호출해 윤문본을 반환. 실패 시 SkillUnavailable."""
    if not CODEX_BIN:
        raise SkillUnavailable("`codex` CLI를 찾을 수 없음")
    try:
        proc = subprocess.run(
            [
                CODEX_BIN,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--cd",
                _REPO_ROOT,
                _prompt(text, strict),
            ],
            cwd=_REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SkillUnavailable(f"Codex 호출 타임아웃 ({timeout}s)") from exc

    out = proc.stdout or ""
    match = _SENTINEL.search(out)
    if not match:
        raise SkillUnavailable(f"센티넬 파싱 실패. 원출력 앞부분: {out[:200]!r}")
    return match.group(1).strip()
