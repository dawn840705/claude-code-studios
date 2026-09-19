"""훅 테스트가 쓸 **진짜 POSIX bash** 를 찾는다.

훅 테스트는 `subprocess.run(["bash", ...])` 로 이름만 넘겼다. 리눅스·맥에서는
맞는 말이지만 Windows 에서는 아니다 — `CreateProcess` 의 탐색 순서가
**System32 를 PATH 보다 먼저** 보고, 거기 있는 `bash.exe` 는 Git Bash 가 아니라
**WSL 런처**다. 배포판이 설치돼 있지 않으면 그 런처는 «Install <Distro>» 안내문을
UTF-16 으로 찍고 `exit 1` 한다.

그 결과가 2026-09-19 에 이 저장소에서 확인된 상태다 — Windows 에서 훅 테스트
90건(`test_hooks_layout` 70 · `test_runtime_mode_hook` 20)이 전멸하는데, 실패
메시지는 훅 버그처럼 보인다 (`hook must never fail the session: ... rc=1`).
훅은 멀쩡했고 실행된 적이 없었다. CI 가 ubuntu 전용이라 아무도 못 봤다.

**후보를 이름으로 믿지 않고 실제로 태워 본다.** `shutil.which` 도 PATH 순서에
따라 같은 WSL 스텁을 집을 수 있어서, 「bash 라고 불리는 무언가를 찾았다」는
근거가 못 된다. `echo ok` 가 돌아오는 것만 bash 로 친다.

표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

PROBE_TIMEOUT = 30

# 잘 알려진 Git Bash 위치. PATH 가 System32 를 먼저 두는 기계에서 `which` 가
# WSL 스텁을 집어도 여기서 건진다.
WELL_KNOWN = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def _works(path: str) -> bool:
    """이 실행 파일이 실제로 POSIX 셸로 동작하는가."""
    try:
        proc = subprocess.run([path, "-c", "echo ok"],
                              capture_output=True, timeout=PROBE_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == b"ok"


def find_bash() -> str | None:
    """쓸 수 있는 bash 의 절대 경로, 없으면 None.

    순서 = `$BASH`(명시 지정이 이긴다) → PATH → 잘 알려진 Git Bash 경로.
    """
    seen: list[str] = []
    for candidate in (os.environ.get("BASH"), shutil.which("bash"), *WELL_KNOWN):
        if not candidate or candidate in seen:
            continue
        seen.append(candidate)
        if _works(candidate):
            return candidate
    return None


BASH = find_bash()

requires_bash = pytest.mark.skipif(
    BASH is None,
    reason=("POSIX bash 를 못 찾았다. Git Bash 를 설치하거나 $BASH 로 경로를 "
            "지정할 것 — System32 의 WSL 런처는 bash 가 아니다."),
)
