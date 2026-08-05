#!/usr/bin/env python3
"""Golden-trajectory gate for the plugin's own routing.

`/regression-suite` manages tests for the *user's product*. Nothing has ever
regression-tested **the plugin's own behaviour** — and that behaviour is not
written in any one file. It is a *join*:

    check_phase.py  ──reads──>  workflow-catalog.yaml   (which steps, what order)
                                         │
                                    phase id
                                         │
    orchestrator    ──looks up──>  agent-packs.yaml     (who staffs that phase)

One line changed in either file silently re-routes every skill that runs in that
phase. A renamed phase, a deleted step, an agent moved between packs, a support
role quietly promoted — none of it fails a test today, and none of it is visible
in review unless someone happens to hold both files in their head at once.

This script records that derived routing as a **golden trajectory** and fails
when it changes without the snapshot being updated in the same commit. That is
the whole idea: the diff stops being invisible. A legitimate change is one line
of `--update` and shows up in review as an explicit routing diff.

What the trajectory captures, per track and phase:

    steps      step ids in catalog order          (what happens, in what order)
    required   step ids that block the phase      (what cannot be skipped)
    depends_on step dependency edges              (what must precede what)
    primary    agents owning the phase output     (who is called by default)
    support    agents called on demand            (who is available)

Not captured on purpose: prose, labels, descriptions. Those change often and
mean nothing to routing; including them would make the gate noisy, and a noisy
gate gets `--update`d without being read, which is the same as not having it.

Exit codes — the contract in docs/deterministic-gates.md:

    0  routing matches the golden trajectory
    1  (unused — a routing drift is never "just a warning")
    2  routing drifted; review the diff, then re-record with --update
    3  cannot judge — a source file is missing or unparseable

Standard library only.

Usage:
    python3 scripts/verify_trajectory.py            # judge
    python3 scripts/verify_trajectory.py --update   # re-record after a real change
    python3 scripts/verify_trajectory.py --print    # dump current routing as JSON
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_report import build as build_report, emit as emit_report  # noqa: E402

EXIT_OK = 0
EXIT_DRIFT = 2
EXIT_CANNOT_JUDGE = 3

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

CATALOG = os.path.join(_ROOT, "docs", "workflow-catalog.yaml")
PACKS = os.path.join(_ROOT, "docs", "agent-packs.yaml")
GOLDEN = os.path.join(_ROOT, "tests", "trajectories", "routing.json")

TRACKS = ("game", "product")


class CannotJudge(Exception):
    """No verdict is possible — maps to exit 3, never to a pass."""


def _read(path: str) -> str:
    if not os.path.isfile(path):
        raise CannotJudge(f"missing source file: {os.path.relpath(path, _ROOT)}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# --- extraction --------------------------------------------------------------
#
# Both files are parsed with purpose-built readers rather than PyYAML: the repo
# runtime is stdlib-only (docs/deterministic-gates.md, "Adding a gate" rule 5),
# and check_phase.py already establishes that the catalog stays inside a YAML
# subset for exactly this reason.


def extract_catalog() -> dict[str, dict[str, dict]]:
    text = _read(CATALOG)
    out: dict[str, dict[str, dict]] = {}
    track = phase = step = None
    in_tracks = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if re.match(r"^tracks:\s*$", line):
            in_tracks = True
            continue
        if not in_tracks or not line.strip() or line.lstrip().startswith("#"):
            continue

        m = re.match(r"^  ([a-z-]+):\s*$", line)
        if m:
            track, phase, step = m.group(1), None, None
            out.setdefault(track, {})
            continue
        m = re.match(r"^      ([a-z-]+):\s*$", line)
        if m and track:
            phase, step = m.group(1), None
            out[track][phase] = {"steps": [], "required": [], "depends_on": {}}
            continue
        m = re.match(r"^          - id:\s*(\S+)", line)
        if m and phase:
            step = m.group(1)
            out[track][phase]["steps"].append(step)
            continue
        if not step:
            continue
        m = re.match(r"^            required:\s*(\S+)", line)
        if m and m.group(1).lower() == "true":
            out[track][phase]["required"].append(step)
            continue
        m = re.match(r"^            depends_on:\s*\[(.*)\]", line)
        if m:
            deps = [d.strip() for d in m.group(1).split(",") if d.strip()]
            if deps:
                out[track][phase]["depends_on"][step] = deps

    if not all(out.get(t) for t in TRACKS):
        raise CannotJudge(f"catalog parsed no phases for one of {TRACKS}")
    return out


def extract_staffing() -> dict[str, dict[str, dict[str, list[str]]]]:
    text = _read(PACKS)
    if "\nstages:" not in text:
        raise CannotJudge("agent-packs.yaml has no `stages:` block")
    block = text.split("\nstages:", 1)[1]
    block = re.split(r"\n(?=[a-z_]+:)", block, maxsplit=1)[0]

    out: dict[str, dict[str, dict[str, list[str]]]] = {}
    track = stage = None
    for raw in block.splitlines():
        line = raw.split("#")[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^  ([a-z-]+):\s*$", line)
        if m:
            track, stage = m.group(1), None
            out.setdefault(track, {})
            continue
        m = re.match(r"^    ([a-z-]+):\s*$", line)
        if m and track:
            stage = m.group(1)
            out[track][stage] = {"primary": [], "support": []}
            continue
        m = re.match(r"^      (primary|support):\s*\[(.*)\]\s*$", line)
        if m and track and stage:
            out[track][stage][m.group(1)] = [
                v.strip() for v in m.group(2).split(",") if v.strip()
            ]

    if not all(out.get(t) for t in TRACKS):
        raise CannotJudge(f"agent-packs.yaml parsed no stages for one of {TRACKS}")
    return out


def build_trajectory() -> dict:
    catalog = extract_catalog()
    staffing = extract_staffing()
    traj: dict[str, dict] = {}
    for track in TRACKS:
        traj[track] = {}
        for phase, data in catalog[track].items():
            roles = staffing[track].get(phase, {"primary": [], "support": []})
            traj[track][phase] = {
                "steps": data["steps"],
                "required": data["required"],
                "depends_on": data["depends_on"],
                "primary": roles["primary"],
                "support": roles["support"],
            }
    return traj


# --- diff --------------------------------------------------------------------


def diff(golden: dict, current: dict) -> list[str]:
    """Human-readable drift lines. Empty list means the routing is unchanged."""
    lines: list[str] = []
    for track in sorted(set(golden) | set(current)):
        g_phases, c_phases = golden.get(track, {}), current.get(track, {})
        for phase in sorted(set(g_phases) | set(c_phases)):
            if phase not in g_phases:
                lines.append(f"{track}.{phase}: PHASE ADDED")
                continue
            if phase not in c_phases:
                lines.append(f"{track}.{phase}: PHASE REMOVED")
                continue
            g, c = g_phases[phase], c_phases[phase]
            for field in ("steps", "required", "primary", "support"):
                if g.get(field) != c.get(field):
                    added = [x for x in c.get(field, []) if x not in g.get(field, [])]
                    removed = [x for x in g.get(field, []) if x not in c.get(field, [])]
                    detail = []
                    if added:
                        detail.append(f"+{added}")
                    if removed:
                        detail.append(f"-{removed}")
                    if not detail:      # same members, different order
                        detail.append(f"reordered: {g.get(field)} -> {c.get(field)}")
                    lines.append(f"{track}.{phase}.{field}: {' '.join(detail)}")
            if g.get("depends_on") != c.get("depends_on"):
                lines.append(
                    f"{track}.{phase}.depends_on: {g.get('depends_on')} -> {c.get('depends_on')}"
                )
    return lines


def load_golden() -> dict:
    if not os.path.isfile(GOLDEN):
        raise CannotJudge(
            f"no golden trajectory at {os.path.relpath(GOLDEN, _ROOT)} — "
            "record one with --update"
        )
    try:
        with open(GOLDEN, encoding="utf-8") as fh:
            return json.load(fh)["tracks"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise CannotJudge(f"golden trajectory unreadable: {exc}") from exc


def write_golden(traj: dict) -> None:
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    payload = {
        "_comment": (
            "Golden trajectory: the routing derived by joining "
            "docs/workflow-catalog.yaml (steps) with docs/agent-packs.yaml "
            "(staffing). Regenerate with `python3 scripts/verify_trajectory.py "
            "--update` and review the diff — a change here means every skill "
            "running in that phase now routes differently."
        ),
        "tracks": traj,
    }
    with open(GOLDEN, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Golden-trajectory gate for plugin routing")
    ap.add_argument("--update", action="store_true", help="re-record the golden trajectory")
    ap.add_argument("--print", dest="dump", action="store_true", help="print current routing")
    ap.add_argument("--quiet", action="store_true", help="summary line only")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit the shared gate report (scripts/gate_report.py)")
    args = ap.parse_args(argv)

    try:
        current = build_trajectory()
    except CannotJudge as exc:
        if args.as_json:
            emit_report(build_report("verify_trajectory", EXIT_CANNOT_JUDGE,
                                     reason=str(exc)))
        else:
            print(f"verify_trajectory: CANNOT JUDGE — {exc} (exit {EXIT_CANNOT_JUDGE})",
                  file=sys.stderr)
            print("A gate that could not run has produced no verdict. "
                  "Do not read this as a pass.", file=sys.stderr)
        return EXIT_CANNOT_JUDGE

    if args.dump:
        print(json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True))
        return EXIT_OK

    if args.update:
        write_golden(current)
        phases = sum(len(v) for v in current.values())
        print(f"verify_trajectory: golden trajectory recorded "
              f"({len(current)} tracks, {phases} phases) -> "
              f"{os.path.relpath(GOLDEN, _ROOT)}")
        return EXIT_OK

    try:
        golden = load_golden()
    except CannotJudge as exc:
        if args.as_json:
            emit_report(build_report("verify_trajectory", EXIT_CANNOT_JUDGE,
                                     reason=str(exc)))
        else:
            print(f"verify_trajectory: CANNOT JUDGE — {exc} (exit {EXIT_CANNOT_JUDGE})",
                  file=sys.stderr)
        return EXIT_CANNOT_JUDGE

    drift = diff(golden, current)
    phases = sum(len(v) for v in current.values())

    if args.as_json:
        code = EXIT_OK if not drift else EXIT_DRIFT
        emit_report(build_report(
            "verify_trajectory", code,
            reason=(f"{phases} phases unchanged" if not drift
                    else f"{len(drift)} routing change(s) since the golden trajectory"),
            evidence=[{"id": "drift", "detail": d} for d in drift],
            next_action=(None if not drift else
                         "Review the diff. If intended, re-record in the same "
                         "commit: python3 scripts/verify_trajectory.py --update"),
        ))
        return code

    if not drift:
        print(f"verify_trajectory: MATCH — {phases} phases unchanged (exit {EXIT_OK})")
        return EXIT_OK

    if not args.quiet:
        print("Routing drifted from the golden trajectory:\n")
        for line in drift:
            print(f"  {line}")
        print()
        print("Every skill running in these phases now routes differently.")
        print("If that is intended, re-record it in the same commit:")
        print("  python3 scripts/verify_trajectory.py --update")
        print()
    print(f"verify_trajectory: DRIFT — {len(drift)} change(s) (exit {EXIT_DRIFT})")
    return EXIT_DRIFT


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
