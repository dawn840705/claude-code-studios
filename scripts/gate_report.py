#!/usr/bin/env python3
"""One machine-readable shape for every gate verdict.

`docs/deterministic-gates.md` already forbids re-deriving a verdict by parsing a
runner's output — "read the exit code, use the text only to explain it". But
every gate then printed free prose, so a caller that needed *why* had only one
option: parse the prose. The rule was unfollowable in practice, and an
unfollowable rule is worse than none, because it looks like it is holding.

This module is the missing half. Four fields, identical across gates:

    status        the verdict as a word, derived from the exit code — never set
                  independently, so the two cannot disagree
    reason        one line: why this status
    next_action   what the caller must do about it
    evidence      the specific findings, as data rather than sentences

Together with `exit_code` and `gate`, that is everything a hook, a skill, or CI
needs — with nothing left to interpret. A skill reads `status`; a human reads
`reason`; a follow-up reads `next_action`; a report cites `evidence`.

**`status` is a pure function of `exit_code`.** That is the point: a gate cannot
print ABORT while exiting 0, which is exactly the class of bug that shipped in
`validate-assets.sh` (it printed "Blocking" and exited 1, a code Claude never
sees). Deriving one from the other makes that state unrepresentable.

Standard library only, and deliberately small — this is an envelope, not a
framework. Gates keep their own reporting; they add this alongside it.

Usage inside a gate:

    from gate_report import build, emit
    report = build("verify_policy", code, reason="2 abort, 0 warning",
                   evidence=[{"id": "P2", "detail": "...", "source": "x.py"}])
    if args.json:
        emit(report)
"""

from __future__ import annotations

import json
import sys

# The 4-code contract (docs/deterministic-gates.md). `3` is the one people get
# wrong, so its wording says outright what it is not.
STATUS_BY_EXIT = {
    0: "PASS",
    1: "WARNING",
    2: "ABORT",
    3: "CANNOT_JUDGE",
}

DEFAULT_NEXT_ACTION = {
    0: "Proceed.",
    1: "Report the warning; a human decides whether to proceed.",
    2: "Stop. Do not adopt the output or mark the work done.",
    3: "This gate produced no verdict. Do NOT read it as a pass — "
       "fix the gate or say explicitly that it did not run.",
}

SCHEMA_KEYS = ("gate", "status", "exit_code", "reason", "next_action", "evidence")


class UnknownExitCode(ValueError):
    """A gate exited outside the contract. Callers cannot interpret that."""


def build(
    gate: str,
    exit_code: int,
    reason: str,
    evidence: list[dict] | None = None,
    next_action: str | None = None,
) -> dict:
    """Assemble the envelope. `status` is derived, never passed in."""
    if exit_code not in STATUS_BY_EXIT:
        raise UnknownExitCode(
            f"{gate} exited {exit_code}; the contract allows only "
            f"{sorted(STATUS_BY_EXIT)} (docs/deterministic-gates.md)"
        )
    return {
        "gate": gate,
        "status": STATUS_BY_EXIT[exit_code],
        "exit_code": exit_code,
        "reason": reason,
        "next_action": next_action or DEFAULT_NEXT_ACTION[exit_code],
        "evidence": evidence or [],
    }


def emit(report: dict, stream=None) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=2),
          file=stream or sys.stdout)


def is_valid(report: dict) -> bool:
    """Conformance check — used by tests so gates cannot drift apart."""
    if not all(k in report for k in SCHEMA_KEYS):
        return False
    if report["exit_code"] not in STATUS_BY_EXIT:
        return False
    if report["status"] != STATUS_BY_EXIT[report["exit_code"]]:
        return False
    if not isinstance(report["evidence"], list):
        return False
    return bool(report["gate"] and report["reason"] and report["next_action"])
