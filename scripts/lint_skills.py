#!/usr/bin/env python3
"""Structural linter for claude-code-studios skills and agents.

This is the executable form of the 7 static checks defined in
`skills/skill-test/SKILL.md` (Phase 2A). That skill is read and performed by an
LLM, so it cannot run in CI and does nothing unless a human invokes it. This
script is the SSOT for the *mechanical* checks; the skill keeps the qualitative
evaluation on top.

Standard library only — no third-party dependencies.

Usage:
    python3 scripts/lint_skills.py skills/ agents/
    python3 scripts/lint_skills.py skills/gate-check      # single skill
    python3 scripts/lint_skills.py skills/ --strict       # warnings fail too
    python3 scripts/lint_skills.py skills/ --quiet        # summary line only

Baseline (how CI stays green while pre-existing debt is paid down):

    python3 scripts/lint_skills.py skills/ agents/ --write-baseline
    python3 scripts/lint_skills.py skills/ agents/ --baseline scripts/lint_baseline.json

Known failures recorded in the baseline are reported but do not fail the run.
Anything NOT in the baseline does — so a new skill with a broken frontmatter is
blocked immediately, which is the whole point of having this in CI. A baseline
entry that no longer fails is reported as fixed and should be deleted.

Exit codes:
    0  no un-baselined failures (warnings allowed unless --strict)
    1  at least one failure (or warning under --strict)
    2  bad invocation / nothing to lint
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_baseline.json")

# --- frontmatter conventions -------------------------------------------------

SKILL_REQUIRED_FIELDS = (
    "name",
    "description",
    "argument-hint",
    "user-invocable",
    "allowed-tools",
)
AGENT_REQUIRED_FIELDS = ("name", "description", "tools", "model", "maxTurns")

VERDICT_KEYWORDS = (
    "PASS",
    "FAIL",
    "CONCERNS",
    "APPROVED",
    "BLOCKED",
    "COMPLETE",
    "READY",
    "COMPLIANT",
    "NON-COMPLIANT",
)

WRITE_TOOLS = ("Write", "Edit")

# ask-before-write language (Check 4)
ASK_PATTERNS = (
    re.compile(r"may i write", re.I),
    re.compile(r"before writing", re.I),
    re.compile(r"ask .{0,40}before .{0,20}(writ|creat)", re.I | re.S),
    re.compile(r"(approval|confirm)[^.\n]{0,60}(writ|creat|overwrit)", re.I),
    re.compile(r"(writ|creat)[^.\n]{0,60}(approval|confirmation|permission)", re.I),
)

# next-step handoff (Check 5)
HANDOFF_PATTERNS = (
    re.compile(r"^#{1,4}\s.*(next step|follow[- ]?up|after this|recommended next)", re.I | re.M),
    re.compile(r"(recommended next|next step|follow[- ]?up)", re.I),
)

PHASE_HEADING = re.compile(r"^#{2,3}\s*(phase\s*\d+|step\s*\d+|\d+[\.\)])", re.I | re.M)
ANY_H2 = re.compile(r"^##\s+\S", re.M)

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


class Result:
    """Per-file lint outcome."""

    def __init__(self, path: str, kind: str):
        self.path = path
        self.kind = kind  # "skill" | "agent"
        self.failures: list[str] = []
        self.warnings: list[str] = []

    @property
    def verdict(self) -> str:
        if self.failures:
            return "NON-COMPLIANT"
        if self.warnings:
            return "WARNINGS"
        return "COMPLIANT"

    def issues(self) -> str:
        return "; ".join(self.failures + self.warnings)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Extract top-level `key: value` pairs from the YAML frontmatter block.

    Deliberately naive — we only need presence and simple scalar values, and a
    YAML dependency is not worth it. Nested keys are ignored (they are indented,
    so the leading-character guard skips them).
    """
    m = FRONTMATTER.match(text)
    if not m:
        return None
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def lint_skill(path: str, text: str) -> Result:
    r = Result(path, "skill")
    fm = parse_frontmatter(text)
    body = FRONTMATTER.sub("", text, count=1)

    # Check 1 — required frontmatter fields
    if fm is None:
        r.failures.append("Check 1: no YAML frontmatter block")
        fm = {}
    else:
        missing = [f for f in SKILL_REQUIRED_FIELDS if f not in fm]
        if missing:
            r.failures.append("Check 1: missing " + ", ".join(missing))

    # Check 2 — >= 2 numbered phase headings (fall back to any 2 H2 headings)
    phases = len(PHASE_HEADING.findall(body))
    if phases < 2:
        h2 = len(ANY_H2.findall(body))
        if h2 < 2:
            r.failures.append(f"Check 2: only {max(phases, h2)} phase-like heading(s), need 2")
        phases = max(phases, h2)

    # Check 3 — verdict keywords
    if not any(k in body for k in VERDICT_KEYWORDS):
        r.failures.append("Check 3: no verdict keyword")

    # Check 4 — ask-before-write, mandatory when the skill can write
    has_ask = any(p.search(body) for p in ASK_PATTERNS)
    tools = fm.get("allowed-tools", "")
    can_write = any(t in tools for t in WRITE_TOOLS)
    if not has_ask:
        if can_write:
            r.failures.append("Check 4: allowed-tools has Write/Edit but no ask-before-write language")
        else:
            r.warnings.append("Check 4: no ask-before-write language (read-only skill, allowed)")

    # Check 5 — next-step handoff
    if not any(p.search(body) for p in HANDOFF_PATTERNS):
        r.warnings.append("Check 5: no next-step handoff")

    # Check 6 — fork context complexity
    if fm.get("context") == "fork" and phases < 5:
        r.warnings.append(f"Check 6: context: fork with only {phases} phases (expected >= 5)")

    # Check 7 — argument-hint plausibility
    hint = fm.get("argument-hint", "").strip().strip('"').strip("'")
    if "argument-hint" in fm and not hint:
        r.warnings.append("Check 7: argument-hint is empty")

    return r


def lint_agent(path: str, text: str) -> Result:
    r = Result(path, "agent")
    fm = parse_frontmatter(text)
    if fm is None:
        r.failures.append("no YAML frontmatter block")
        return r
    missing = [f for f in AGENT_REQUIRED_FIELDS if f not in fm]
    if missing:
        r.failures.append("missing " + ", ".join(missing))
    if not fm.get("description", "").strip():
        r.failures.append("empty description")
    return r


def collect(targets: list[str]) -> list[tuple[str, str]]:
    """Resolve CLI targets to (path, kind) pairs."""
    found: list[tuple[str, str]] = []
    for t in targets:
        t = t.rstrip("/")
        if os.path.isfile(t):
            kind = "agent" if os.path.basename(os.path.dirname(t)) == "agents" else "skill"
            found.append((t, kind))
            continue
        if not os.path.isdir(t):
            print(f"lint_skills: no such path: {t}", file=sys.stderr)
            continue
        base = os.path.basename(t)
        if base == "agents":
            for name in sorted(os.listdir(t)):
                if name.endswith(".md"):
                    found.append((os.path.join(t, name), "agent"))
        else:
            # a skills/ root, or a single skill directory
            skill_md = os.path.join(t, "SKILL.md")
            if os.path.isfile(skill_md):
                found.append((skill_md, "skill"))
            else:
                for name in sorted(os.listdir(t)):
                    cand = os.path.join(t, name, "SKILL.md")
                    if os.path.isfile(cand):
                        found.append((cand, "skill"))
    return found


def label(path: str, kind: str) -> str:
    if kind == "skill":
        return os.path.basename(os.path.dirname(path))
    return os.path.splitext(os.path.basename(path))[0]


def load_baseline(path: str) -> dict[str, list[str]]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("known_failures", {})


def write_baseline(path: str, results: list[Result]) -> int:
    known = {
        label(r.path, r.kind): sorted(r.failures)
        for r in sorted(results, key=lambda x: x.path)
        if r.failures
    }
    payload = {
        "_comment": (
            "Pre-existing lint failures, recorded so CI blocks NEW violations without "
            "demanding the whole backlog be fixed first. Delete an entry once it is fixed "
            "— the linter reports stale entries."
        ),
        "known_failures": known,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"baseline written: {path} ({len(known)} known failures)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Structural linter for studios skills and agents")
    ap.add_argument("targets", nargs="+", help="skills/ agents/ or a specific path")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--quiet", action="store_true", help="print the summary line only")
    ap.add_argument(
        "--baseline",
        nargs="?",
        const=DEFAULT_BASELINE,
        help="ignore failures recorded in this baseline file (default: scripts/lint_baseline.json)",
    )
    ap.add_argument(
        "--write-baseline",
        nargs="?",
        const=DEFAULT_BASELINE,
        metavar="PATH",
        help="record current failures as the baseline and exit",
    )
    args = ap.parse_args(argv)

    files = collect(args.targets)
    if not files:
        print("lint_skills: nothing to lint", file=sys.stderr)
        return 2

    results = []
    for path, kind in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        results.append(lint_skill(path, text) if kind == "skill" else lint_agent(path, text))

    if args.write_baseline:
        return write_baseline(args.write_baseline, results)

    baseline = load_baseline(args.baseline) if args.baseline else {}

    # Split failures into baselined (tolerated) and new (blocking).
    new_failures: list[Result] = []
    baselined: list[Result] = []
    for r in results:
        if not r.failures:
            continue
        known = baseline.get(label(r.path, r.kind))
        if known is not None and sorted(r.failures) == sorted(known):
            baselined.append(r)
        else:
            new_failures.append(r)

    warned = [r for r in results if r.warnings and not r.failures]

    # A baseline entry is stale only if we actually linted it this run AND it now
    # passes. Without the `in seen` guard a partial run (one skill, one dir) would
    # report every unlinted entry as fixed.
    seen = {label(r.path, r.kind) for r in results}
    failing_now = {label(r.path, r.kind) for r in baselined + new_failures}
    stale = sorted(k for k in baseline if k in seen and k not in failing_now)

    if not args.quiet:
        width = max(len(label(r.path, r.kind)) for r in results) + 2
        print(f"=== lint_skills: {len(results)} file(s) ===\n")
        for r in sorted(new_failures, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} NON-COMPLIANT  {r.issues()}")
        for r in sorted(warned, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} WARNINGS       {r.issues()}")
        for r in sorted(baselined, key=lambda x: x.path):
            print(f"{label(r.path, r.kind):<{width}} baselined      {r.issues()}")
        if stale:
            print("\nStale baseline entries (now passing — remove them):")
            for k in stale:
                print(f"  {k}")
        if new_failures or warned or baselined or stale:
            print()

    compliant = len(results) - len(new_failures) - len(baselined) - len(warned)
    summary = (
        f"Summary: {compliant} COMPLIANT, {len(warned)} WARNINGS, "
        f"{len(new_failures)} NON-COMPLIANT (of {len(results)})"
    )
    if baselined:
        summary += f" — {len(baselined)} baselined failure(s) tolerated"
    print(summary)

    if new_failures:
        return 1
    if args.strict and warned:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
