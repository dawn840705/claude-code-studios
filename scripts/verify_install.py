#!/usr/bin/env python3
"""Install-registration gate — will the host actually load this plugin?

Every gate in this repo judges *contents*: the routing join, the catalog's
globs, the generated files, the policy of a diff. All of them read the copy on
disk. None of them ask the prior question — **is that copy wired in?**

On 2026-09-19 that gap came due. A session had:

    the cache directory present, 0.6.5, 45 agents and 90 skills on disk
    `enabledPlugins: {"claude-code-studios@game-studios": true}` in the project
    `verify_trajectory.py` → exit 0 ("MATCH — 13 phases unchanged")

and **zero** of it loaded: no SessionStart hook output, no agents, no skills.
The host's `installed_plugins.json` had lost its entry, so a setting that says
*enable this* pointed at nothing. Nothing reported an error, because from every
existing gate's point of view the plugin was in perfect health. The failure was
found only because someone audited by hand.

This gate closes that. It reads the host's install registry and answers one
question: is this plugin registered, and does that registration point at a copy
that exists?

**It cannot be a hook.** The hooks are exactly what does not run when this
fails, so a hook-based check would be silent in the one case it exists for.
It is a script a human (or a skill) runs when the studio seems absent.

Exit codes — the contract in docs/deterministic-gates.md:

    0  registered; the registered path exists and its manifest agrees
    1  registered but stale — the entry's version disagrees with the
       plugin.json at the path it points to
    2  not loadable — no entry at all, or every entry points at a path that
       is gone. This is the 2026-09-19 state.
    3  cannot judge — no registry file, or it is unreadable

Exit 3 is deliberately reserved for "the registry could not be read", not for
"the plugin is missing from it". An absent entry is a finding, not a failure to
look; collapsing the two would hide the very bug this gate exists to catch.

Standard library only.

Usage:
    python3 scripts/verify_install.py           # judge this copy
    python3 scripts/verify_install.py --json    # shared gate envelope
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_report import build as build_report, emit as emit_report  # noqa: E402
from console_encoding import force_utf8  # noqa: E402

EXIT_OK = 0
EXIT_STALE = 1
EXIT_NOT_LOADABLE = 2
EXIT_CANNOT_JUDGE = 3

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

# Where the host keeps its install registry. CLAUDE_CONFIG_DIR wins when set —
# without honouring it, a relocated config would read as "not registered", and a
# gate that cries wolf gets switched off wholesale.
REGISTRY_RELPATH = ("plugins", "installed_plugins.json")
MANIFEST_RELPATH = (".claude-plugin", "plugin.json")


class CannotJudge(Exception):
    """No verdict is possible — maps to exit 3, never to a pass."""


def config_dir() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude")


def registry_path() -> str:
    return os.path.join(config_dir(), *REGISTRY_RELPATH)


def read_manifest(root: str) -> dict:
    """`(name, version)` of the plugin rooted at `root`."""
    path = os.path.join(root, *MANIFEST_RELPATH)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise CannotJudge(f"no plugin manifest at {path}")
    except (OSError, ValueError) as exc:
        raise CannotJudge(f"unreadable plugin manifest {path}: {exc}")
    name = data.get("name")
    if not name:
        raise CannotJudge(f"{path} declares no name")
    return {"name": name, "version": data.get("version")}


def load_registry(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise CannotJudge(
            f"no install registry at {path} — set CLAUDE_CONFIG_DIR if the "
            f"host keeps its config elsewhere")
    except (OSError, ValueError) as exc:
        raise CannotJudge(f"unreadable install registry {path}: {exc}")
    if not isinstance(data.get("plugins"), dict):
        raise CannotJudge(f"{path} has no 'plugins' object")
    return data


def _same_path(a: str, b: str) -> bool:
    norm = lambda p: os.path.normcase(os.path.normpath(os.path.realpath(p)))
    return norm(a) == norm(b)


def entries_for(registry: dict, name: str) -> list[dict]:
    """Every registration of `name`, whatever marketplace it came from."""
    found = []
    for key, records in registry["plugins"].items():
        if key.split("@", 1)[0] != name:
            continue
        for record in records if isinstance(records, list) else [records]:
            if isinstance(record, dict):
                found.append({"key": key, **record})
    return found


def audit(manifest: dict, root: str, registry: dict) -> tuple[int, str, list[dict]]:
    """Judge one plugin against one registry. Returns (exit code, reason, evidence)."""
    name = manifest["name"]
    entries = entries_for(registry, name)

    if not entries:
        return EXIT_NOT_LOADABLE, f"{name} is in no install registry entry", [{
            "id": "no-entry",
            "detail": (f"'{name}' does not appear in the registry. A project's "
                       f"enabledPlugins may still say true — that setting points "
                       f"at nothing, and nothing loads."),
            "source": name,
        }]

    evidence: list[dict] = []
    live = []
    for entry in entries:
        install_path = entry.get("installPath") or ""
        exists = bool(install_path) and os.path.isdir(install_path)
        evidence.append({
            "id": "entry",
            "detail": (f"{entry['key']} version={entry.get('version')} "
                       f"scope={entry.get('scope')} installPath_exists={exists}"),
            "source": install_path or "(no installPath)",
        })
        if exists:
            live.append((entry, install_path))

    if not live:
        return EXIT_NOT_LOADABLE, (
            f"{name} is registered {len(entries)}x but no installPath exists"
        ), evidence

    stale = []
    for entry, install_path in live:
        try:
            installed = read_manifest(install_path)
        except CannotJudge as exc:
            stale.append({
                "id": "unreadable-target",
                "detail": f"{entry['key']}: {exc}",
                "source": install_path,
            })
            continue
        if entry.get("version") != installed["version"]:
            stale.append({
                "id": "version-skew",
                "detail": (f"{entry['key']}: registry says "
                           f"{entry.get('version')}, the plugin.json it points "
                           f"at says {installed['version']}"),
                "source": install_path,
            })

    # Informative only — never moves the verdict (docs/deterministic-gates.md,
    # "Adding a gate" rule 4). Running the gate from a git checkout while the
    # host loads the cached copy is normal, not a fault.
    if not any(_same_path(p, root) for _, p in live):
        evidence.append({
            "id": "other-copy",
            "detail": ("the host loads a different copy than the one this gate "
                       "ran from — expected when run from a checkout"),
            "source": root,
        })

    if stale:
        evidence.extend(stale)
        return EXIT_STALE, (
            f"{name} is registered but {len(stale)} entry/entries are stale"
        ), evidence

    return EXIT_OK, (
        f"{name} registered {len(live)}x; every installPath exists and matches "
        f"its manifest"
    ), evidence


def main(argv: list[str]) -> int:
    force_utf8()  # 판정이 콘솔 코드페이지에 좌우되지 않게 (console_encoding 참조)
    ap = argparse.ArgumentParser(
        description="Is this plugin registered with the host, so it will load?")
    ap.add_argument("--registry", help="install registry path (default: the host's)")
    ap.add_argument("--plugin-root", help="plugin root to judge (default: this copy)")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit the shared gate report (scripts/gate_report.py)")
    args = ap.parse_args(argv)

    root = args.plugin_root or _ROOT
    path = args.registry or registry_path()

    try:
        manifest = read_manifest(root)
        code, reason, evidence = audit(manifest, root, load_registry(path))
    except CannotJudge as exc:
        if args.as_json:
            emit_report(build_report("verify_install", EXIT_CANNOT_JUDGE,
                                     reason=str(exc)))
        else:
            print(f"verify_install: CANNOT JUDGE — {exc} "
                  f"(exit {EXIT_CANNOT_JUDGE})", file=sys.stderr)
            print("A gate that could not run has produced no verdict. "
                  "Do not read this as a pass.", file=sys.stderr)
        return EXIT_CANNOT_JUDGE

    next_action = None
    if code == EXIT_NOT_LOADABLE:
        next_action = (
            "The host will not load this plugin. Re-install it "
            "(/plugin, or `claude plugin install <name>@<marketplace>`) so the "
            "registry entry is rebuilt, then restart the session — hooks are "
            "read at session start.")
    elif code == EXIT_STALE:
        next_action = ("Re-install or update the plugin so the registry entry "
                       "and the plugin.json it points at agree.")

    if args.as_json:
        emit_report(build_report("verify_install", code, reason=reason,
                                 evidence=evidence, next_action=next_action))
        return code

    label = {EXIT_OK: "OK", EXIT_STALE: "STALE", EXIT_NOT_LOADABLE: "NOT LOADABLE"}[code]
    print(f"registry: {path}")
    for item in evidence:
        print(f"  [{item['id']}] {item['detail']}")
    print(f"verify_install: {label} — {reason} (exit {code})")
    if next_action:
        print()
        print(next_action)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
