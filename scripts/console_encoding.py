"""콘솔 인코딩 고정 — 종료 코드가 콘솔 코드페이지에 좌우되지 않게 한다.

`CLAUDE.md § Deterministic gates` 는 «종료 코드가 판정이다» 라고 못박고, 호출한
쪽은 stdout 을 읽지 않고 종료 코드만 믿는다. 그런데 Windows 한국어 콘솔(cp949)
에서는 게이트가 리포트의 em-dash(—) 하나를 인코딩하지 못해 UnicodeEncodeError
로 죽고, 그 죽음이 `exit 1` 로 나온다. 통과한 작업이 FAIL 로 읽힌다.

그래서 진입부에서 stdout/stderr 를 UTF-8 로 못박는다.

`errors="replace"` 인 이유 — 인코딩을 바꿀 수 없는 예외 환경에서도 게이트가
«못 읽는 글자» 때문에 판정을 못 내리는 일은 없어야 한다. 글자가 깨질지언정
판정은 나온다. 반대로 비ASCII 를 지우는 해법은 쓰지 않는다: 게이트 리포트가
한국어인 것은 사양이고, 글자를 없애면 사람이 리포트를 못 읽는다.

표준 라이브러리만 쓴다 (`CLAUDE.md § 작업 원칙` — 런타임 의존성 추가는 별도 승인).
"""

from __future__ import annotations

import sys

__all__ = ["force_utf8"]


def force_utf8() -> None:
    """`sys.stdout`/`sys.stderr` 를 UTF-8 로 재설정한다. 절대 예외를 내지 않는다.

    각 스크립트 `main()` 의 첫 줄에서 부른다. 모듈 최상단이 아니라 `main()` 인
    이유 = argparse 의 한국어 `--help` 도 같은 보호를 받아야 하고, 스크립트를
    import 해서 `main()` 을 부르는 호출자(테스트 포함)도 같은 경로를 밟아야
    하기 때문이다.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            # 스트림이 없거나(pythonw), TextIOWrapper 가 아닌 대체물로 갈렸다.
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError, LookupError):
            # detach 된 스트림·닫힌 스트림·없는 코덱. 어느 쪽이든 치명적이지 않다.
            continue
