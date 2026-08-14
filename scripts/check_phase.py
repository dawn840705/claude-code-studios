#!/usr/bin/env python3
"""Deterministic workflow-phase gate for claude-code-studios.

Evaluates step completion for the current phase against
`docs/workflow-catalog.yaml` (schema v2, dual-track) using the artifact globs
declared there. This moves phase-completion judgment OUT of the model: /help
and /project-stage-detect read this script's exit code instead of re-deriving
completion by globbing themselves (docs/deterministic-gates.md).

Standard library only — no third-party dependencies. The catalog is parsed by
a purpose-built YAML-subset reader (see CatalogParser); the catalog file must
stay within that subset (single-line scalars, block/flow lists, comments).

Usage:
    python3 scripts/check_phase.py                     # auto track + phase, compact report
    python3 scripts/check_phase.py --track product     # force track
    python3 scripts/check_phase.py --phase build       # force phase
    python3 scripts/check_phase.py --json              # machine-readable output
    python3 scripts/check_phase.py --validate          # catalog schema check (CI)
    python3 scripts/check_phase.py --root /path/to/project

Exit codes (docs/deterministic-gates.md contract):
    0  current phase COMPLETE — every required, script-checkable step passed
       and no required MANUAL steps remain unconfirmed
    1  current phase IN PROGRESS — required steps incomplete, or required
       MANUAL steps need human confirmation (the normal mid-phase state)
    2  DEPENDENCY VIOLATION — a completed step's required dependency is still
       incomplete (a step was skipped), or --validate found a broken catalog
    3  CANNOT JUDGE — catalog missing/unparseable, or track is ambiguous.
       No verdict was produced; never treat this as a pass.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob as globmod
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_report  # noqa: E402

DEFAULT_CATALOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "workflow-catalog.yaml"
)

# Engine markers that identify a GAME project (mirrors hooks/detect-project-type.sh).
GAME_MARKERS = (
    ("dir", "Assets", "dir", "ProjectSettings"),
    ("file", "project.godot", None, None),
    ("glob", "*.uproject", None, None),
    ("glob", "*.yyp", None, None),
    ("dir", "design/gdd", None, None),
)
PRODUCT_MARKERS = (
    ("dir", "product/prd", None, None),
    ("glob", "next.config.*", None, None),
    ("file", "pubspec.yaml", None, None),
    ("file", "vercel.json", None, None),
    ("file", "netlify.toml", None, None),
)


# --------------------------------------------------------------------------
# Minimal YAML-subset parser (indentation-based; enough for the catalog)
# --------------------------------------------------------------------------

class CatalogError(Exception):
    pass


def _parse_scalar(raw: str):
    s = raw.strip()
    if s in ("null", "~", ""):
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p) for p in inner.split(",")]
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        return s


class CatalogParser:
    """Parses the indentation-based subset of YAML used by the catalog.

    Supported: nested mappings, block lists of scalars or mappings, flow lists,
    quoted/plain single-line scalars, full-line and NO inline comments (a `#`
    inside a quoted value is preserved). Not supported: multiline scalars,
    anchors, flow mappings.
    """

    def __init__(self, text: str):
        self.lines: list[tuple[int, str]] = []
        for ln in text.splitlines():
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            indent = len(ln) - len(ln.lstrip(" "))
            self.lines.append((indent, ln.strip()))
        self.pos = 0

    def parse(self):
        if not self.lines:
            raise CatalogError("catalog is empty")
        return self._block(self.lines[0][0])

    def _block(self, indent: int):
        # Decide mapping vs list from the first line at this indent.
        if self.pos >= len(self.lines):
            return {}
        if self.lines[self.pos][1].startswith("- "):
            return self._list(indent)
        return self._mapping(indent)

    def _mapping(self, indent: int) -> dict:
        out: dict = {}
        while self.pos < len(self.lines):
            ind, content = self.lines[self.pos]
            if ind < indent:
                break
            if ind > indent:
                raise CatalogError(f"unexpected indent at: {content!r}")
            if content.startswith("- "):
                break
            m = re.match(r"^([^:]+):\s*(.*)$", content)
            if not m:
                raise CatalogError(f"not a key: line: {content!r}")
            key = _parse_scalar(m.group(1))
            value_raw = m.group(2)
            self.pos += 1
            if value_raw == "":
                # nested block, or empty value
                if self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                    out[key] = self._block(self.lines[self.pos][0])
                else:
                    out[key] = None
            else:
                out[key] = _parse_scalar(value_raw)
        return out

    def _list(self, indent: int) -> list:
        out: list = []
        while self.pos < len(self.lines):
            ind, content = self.lines[self.pos]
            if ind < indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            self.pos += 1
            if ":" in item:
                # list item is a mapping; first pair is inline, rest are indented deeper
                m = re.match(r"^([^:]+):\s*(.*)$", item)
                entry: dict = {}
                key = _parse_scalar(m.group(1))
                if m.group(2) == "":
                    if self.pos < len(self.lines) and self.lines[self.pos][0] > ind + 2:
                        entry[key] = self._block(self.lines[self.pos][0])
                    else:
                        entry[key] = None
                else:
                    entry[key] = _parse_scalar(m.group(2))
                # continuation keys of the same item are indented past the dash
                if self.pos < len(self.lines) and self.lines[self.pos][0] == ind + 2:
                    rest = self._mapping(ind + 2)
                    entry.update(rest)
                out.append(entry)
            else:
                out.append(_parse_scalar(item))
        return out


def load_catalog(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = CatalogParser(f.read()).parse()
    if data.get("version") != 2 or "tracks" not in data:
        raise CatalogError("catalog must be schema version: 2 with a tracks: block")
    return data


# --------------------------------------------------------------------------
# Artifact checks
# --------------------------------------------------------------------------

def check_artifact(root: str, artifact: dict | None) -> str:
    """Returns COMPLETE / INCOMPLETE / MANUAL / UNKNOWN."""
    if not artifact:
        return "UNKNOWN"
    pat = artifact.get("glob")
    if not pat:
        return "MANUAL" if artifact.get("note") else "UNKNOWN"
    matches = sorted(globmod.glob(os.path.join(root, pat), recursive=True))
    min_count = artifact.get("min_count") or 1
    if len(matches) < min_count:
        return "INCOMPLETE"
    text_pat = artifact.get("pattern")
    if text_pat:
        rx = re.compile(text_pat)
        for mpath in matches:
            try:
                with open(mpath, encoding="utf-8", errors="replace") as f:
                    if rx.search(f.read()):
                        return "COMPLETE"
            except OSError:
                continue
        return "INCOMPLETE"
    return "COMPLETE"


# --------------------------------------------------------------------------
# Track / phase resolution
# --------------------------------------------------------------------------

def _marker_hit(root: str, kind: str, a: str, kind2, b) -> bool:
    def one(k, v):
        p = os.path.join(root, v)
        if k == "dir":
            return os.path.isdir(p)
        if k == "file":
            return os.path.isfile(p)
        if k == "glob":
            return any(fnmatch.fnmatch(n, v) for n in os.listdir(root)) if os.path.isdir(root) else False
        return False

    if not one(kind, a):
        return False
    if kind2 is not None:
        return one(kind2, b)
    return True


def read_track_file(root: str) -> str | None:
    """Explicit track decision written by the orchestrator, or None.

    Markers are build artifacts of a stack already chosen, so a greenfield project
    has none and the two detectors here and in hooks/detect-project-type.sh used to
    disagree (hook: 'unknown', this: 'game'). production/track.txt is where the
    user's answer is recorded; both readers now honour it first.
    """
    path = os.path.join(root, "production", "track.txt")
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read().strip().lower()
    except OSError:
        return None
    if raw == "game":
        return "game"
    if raw in ("product", "web", "mobile", "service"):
        return "product"
    return None


def detect_track(root: str) -> str | None:
    """Returns 'game', 'product', or None when ambiguous/undetectable."""
    explicit = read_track_file(root)
    if explicit:
        return explicit
    game = any(_marker_hit(root, *m) for m in GAME_MARKERS)
    product = any(_marker_hit(root, *m) for m in PRODUCT_MARKERS)
    if game and product:
        return None  # ambiguous — caller must pass --track
    if game:
        return "game"
    if product:
        return "product"
    return "game"  # fresh/empty project: default to the original track


def resolve_phase(root: str, phases: dict, explicit: str | None) -> str:
    if explicit:
        if explicit not in phases:
            raise CatalogError(f"unknown phase {explicit!r}; catalog has: {', '.join(phases)}")
        return explicit
    stage_file = os.path.join(root, "production", "stage.txt")
    if os.path.isfile(stage_file):
        with open(stage_file, encoding="utf-8") as f:
            raw = f.read().strip()
        if raw:
            key = raw.lower().replace(" ", "-")
            if key in phases:
                return key
            for pkey, ph in phases.items():
                if str(ph.get("label", "")).lower() == raw.lower():
                    return pkey
    # No (usable) stage.txt: first phase whose required checkable steps are not all complete
    for pkey, ph in phases.items():
        for step in ph.get("steps") or []:
            if not step.get("required"):
                continue
            if check_artifact(root, step.get("artifact")) == "INCOMPLETE":
                return pkey
    return list(phases)[-1]


# --------------------------------------------------------------------------
# Dependency resolution
# --------------------------------------------------------------------------

def flatten_steps(phases: dict) -> list[dict]:
    """All steps in catalog order, each annotated with its phase key."""
    flat = []
    for pkey, ph in phases.items():
        for step in ph.get("steps") or []:
            s = dict(step)
            s["_phase"] = pkey
            flat.append(s)
    return flat


def resolve_dep(flat: list[dict], idx: int, ref: str) -> dict | None:
    """Resolve a depends_on reference for flat[idx].

    Qualified refs ("phase:step") match exactly. Unqualified refs match the
    NEAREST step with that id at or before idx (same phase first by proximity).
    """
    if ":" in ref:
        pkey, sid = ref.split(":", 1)
        for s in flat:
            if s["_phase"] == pkey and s.get("id") == sid:
                return s
        return None
    for j in range(idx - 1, -1, -1):
        if flat[j].get("id") == ref:
            return flat[j]
    # fall back to any later definition (forward refs are a validation warning)
    for s in flat:
        if s.get("id") == ref:
            return s
    return None


# --------------------------------------------------------------------------
# Validation (--validate, for CI)
# --------------------------------------------------------------------------

def validate_catalog(data: dict) -> list[str]:
    errors: list[str] = []
    tracks = data.get("tracks") or {}
    if not tracks:
        errors.append("no tracks defined")
    for tkey, track in tracks.items():
        phases = track.get("phases") or {}
        if not phases:
            errors.append(f"track {tkey!r}: no phases")
            continue
        flat = flatten_steps(phases)
        for pkey, ph in phases.items():
            nxt = ph.get("next_phase")
            if nxt is not None and nxt not in phases:
                errors.append(f"{tkey}/{pkey}: next_phase {nxt!r} does not exist")
            for step in ph.get("steps") or []:
                sid = step.get("id")
                if not sid:
                    errors.append(f"{tkey}/{pkey}: step without id")
                    continue
                if "required" not in step:
                    errors.append(f"{tkey}/{pkey}/{sid}: missing required: field")
                art = step.get("artifact")
                if art and not art.get("glob") and not art.get("note"):
                    errors.append(f"{tkey}/{pkey}/{sid}: artifact has neither glob nor note")
                for ref in step.get("depends_on") or []:
                    idx = next(
                        i for i, s in enumerate(flat)
                        if s.get("id") == sid and s["_phase"] == pkey
                    )
                    if resolve_dep(flat, idx, str(ref)) is None:
                        errors.append(f"{tkey}/{pkey}/{sid}: depends_on {ref!r} not found")
    return errors


# --------------------------------------------------------------------------
# Main evaluation
# --------------------------------------------------------------------------

def evaluate(root: str, phases: dict, phase_key: str) -> dict:
    flat = flatten_steps(phases)
    status: dict[int, str] = {
        i: check_artifact(root, s.get("artifact")) for i, s in enumerate(flat)
    }

    # Dependency violations — anywhere in the flow, not just the current phase.
    violations = []
    for i, s in enumerate(flat):
        if status[i] != "COMPLETE":
            continue
        for ref in s.get("depends_on") or []:
            dep = resolve_dep(flat, i, str(ref))
            if dep is None:
                continue
            j = flat.index(dep)
            if dep.get("required") and status[j] == "INCOMPLETE":
                violations.append({
                    "step": f"{s['_phase']}:{s.get('id')}",
                    "missing_dependency": f"{dep['_phase']}:{dep.get('id')}",
                    "dependency_command": dep.get("command"),
                })

    steps_out = []
    blocker = None
    manual_pending = 0
    incomplete_required = 0
    for i, s in enumerate(flat):
        if s["_phase"] != phase_key:
            continue
        st = status[i]
        if s.get("required"):
            if st == "INCOMPLETE":
                incomplete_required += 1
                if blocker is None:
                    blocker = s
            elif st == "MANUAL":
                manual_pending += 1
        steps_out.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "command": s.get("command"),
            "required": bool(s.get("required")),
            "repeatable": bool(s.get("repeatable")),
            "status": st,
        })

    if violations:
        exit_code = 2
        verdict = "DEPENDENCY VIOLATION"
    elif incomplete_required == 0 and manual_pending == 0:
        exit_code = 0
        verdict = "PHASE COMPLETE"
    else:
        exit_code = 1
        verdict = "IN PROGRESS"

    return {
        "phase": phase_key,
        "phase_label": phases[phase_key].get("label"),
        "next_phase": phases[phase_key].get("next_phase"),
        "verdict": verdict,
        "exit_code": exit_code,
        "steps": steps_out,
        "blocker": (
            {"id": blocker.get("id"), "name": blocker.get("name"), "command": blocker.get("command")}
            if blocker else None
        ),
        "manual_pending": manual_pending,
        "violations": violations,
    }


def print_report(track: str, result: dict) -> None:
    mark = {"COMPLETE": "x", "INCOMPLETE": " ", "MANUAL": "?", "UNKNOWN": "-"}
    print(f"track={track} phase={result['phase']} ({result['phase_label']})")
    for s in result["steps"]:
        req = "REQUIRED" if s["required"] else "optional"
        cmd = f"  {s['command']}" if s.get("command") else ""
        print(f"  [{mark[s['status']]}] {s['name']} ({req}){cmd}")
    if result["manual_pending"]:
        print(f"  {result['manual_pending']} required MANUAL step(s) need human confirmation ('?')")
    for v in result["violations"]:
        print(
            f"  !! {v['step']} is complete but its required dependency "
            f"{v['missing_dependency']} is not ({v['dependency_command'] or 'no command'})"
        )
    if result["blocker"]:
        b = result["blocker"]
        print(f"  next required step: {b['name']}" + (f" -> {b['command']}" if b.get("command") else ""))
    print(f"VERDICT: {result['verdict']}")
    print(f"EXIT: {result['exit_code']} "
          f"(0 complete / 1 in progress / 2 dependency violation / 3 cannot judge)")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Deterministic workflow-phase gate")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--root", default=".", help="project root (default: cwd)")
    ap.add_argument("--track", choices=["game", "product", "auto"], default="auto")
    ap.add_argument("--phase", default=None, help="phase key (default: stage.txt, else inferred)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--validate", action="store_true", help="validate catalog schema and exit")
    args = ap.parse_args(argv)

    try:
        data = load_catalog(args.catalog)
    except (OSError, CatalogError) as e:
        print(f"CANNOT JUDGE: catalog unreadable — {e}")
        print("EXIT: 3")
        return 3

    if args.validate:
        errors = validate_catalog(data)
        if errors:
            for e in errors:
                print(f"INVALID: {e}")
            print(f"EXIT: 2 ({len(errors)} schema error(s))")
            return 2
        n_tracks = len(data["tracks"])
        n_steps = sum(
            len(ph.get("steps") or [])
            for t in data["tracks"].values()
            for ph in (t.get("phases") or {}).values()
        )
        print(f"VALID: {n_tracks} track(s), {n_steps} steps")
        print("EXIT: 0")
        return 0

    root = os.path.abspath(args.root)
    track = args.track
    if track == "auto":
        detected = detect_track(root)
        if detected is None:
            print("CANNOT JUDGE: both game and product markers present — "
                  "write game|product to production/track.txt, or pass --track explicitly")
            print("EXIT: 3")
            return 3
        track = detected

    phases = (data["tracks"].get(track) or {}).get("phases") or {}
    if not phases:
        print(f"CANNOT JUDGE: track {track!r} not in catalog")
        print("EXIT: 3")
        return 3

    try:
        phase_key = resolve_phase(root, phases, args.phase)
    except CatalogError as e:
        print(f"CANNOT JUDGE: {e}")
        print("EXIT: 3")
        return 3

    result = evaluate(root, phases, phase_key)
    if args.as_json:
        # 공통 4필드 봉투를 **추가**한다 — 기존 키는 그대로.
        # /project-stage-detect 가 이 출력을 이미 소비하고 있으므로 형태를 바꾸지 않는다.
        blocker = result.get("blocker")
        evidence = [
            {"id": s["id"], "detail": s["status"]}
            for s in result.get("steps", []) if s.get("status") != "COMPLETE"
        ]
        next_action = None
        if blocker:
            next_action = f"Next step: {blocker.get('command') or blocker.get('id')}"
        elif result.get("violations"):
            next_action = ("A completed step's required dependency is missing. "
                           "Resolve the dependency before continuing.")
        result["gate_report"] = gate_report.build(
            "check_phase", result["exit_code"],
            reason=f"{track}:{result['phase']} — {result['verdict']}",
            evidence=evidence + [{"id": "violation", "detail": v}
                                 for v in result.get("violations", [])],
            next_action=next_action,
        )
        print(json.dumps({"track": track, **result}, indent=2, ensure_ascii=False))
    else:
        print_report(track, result)
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
