"""Tests for hooks/detect-runtime-mode.sh.

Why this exists: `rules/runtime-modes.md` says a project may be worked by Claude
Code alone, by Codex alone, or by both — and that in `codex` mode this plugin
must **stand down**. A rule nothing reads is a rule that does not hold, so the
mode has to reach the session the same way PROJECT_TYPE does: as a line a
SessionStart hook prints.

The failure these cover is asymmetric. Reading `codex` as `claude` makes this
runtime act on a project another runtime owns — an overwrite the other side
cannot see. Reading `claude` as `codex` only makes it idle. So garbage in the
file must NOT fall back to the acting mode; it reports `invalid` and stops.
"""

import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "hooks", "detect-runtime-mode.sh")


def run(cwd):
    proc = subprocess.run(
        ["bash", HOOK],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        # 훅은 UTF-8 로 찍는다. text=True 만 주면 locale.getencoding() 을 타서
        # 한국어 Windows 에서 디코딩하다 죽는다 (tests/test_console_encoding.py).
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, f"hook must never fail the session: {proc.stderr}"
    return proc.stdout


def mode_of(stdout):
    for line in stdout.splitlines():
        if line.startswith("RUNTIME_MODE="):
            return line.split("=", 1)[1].strip()
    pytest.fail(f"no RUNTIME_MODE line in:\n{stdout}")


def write_runtime(root, text):
    os.makedirs(os.path.join(root, "production"), exist_ok=True)
    with open(os.path.join(root, "production", "runtime.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# the default
# --------------------------------------------------------------------------

def test_absent_file_means_claude(tmp_path):
    """No declaration means this runtime is working the project alone."""
    assert mode_of(run(tmp_path)) == "claude"


def test_empty_file_is_treated_as_absent(tmp_path):
    write_runtime(tmp_path, "")
    assert mode_of(run(tmp_path)) == "claude"


def test_whitespace_only_file_is_treated_as_absent(tmp_path):
    write_runtime(tmp_path, "   \n\n")
    assert mode_of(run(tmp_path)) == "claude"


# --------------------------------------------------------------------------
# the three declared modes
# --------------------------------------------------------------------------

@pytest.mark.parametrize("declared", ["claude", "codex", "split"])
def test_declared_mode_is_reported(tmp_path, declared):
    write_runtime(tmp_path, declared + "\n")
    assert mode_of(run(tmp_path)) == declared


@pytest.mark.parametrize("declared", ["  codex  ", "CODEX", "Codex\r\n", "﻿codex"])
def test_mode_survives_whitespace_case_crlf_and_bom(tmp_path, declared):
    """A file edited on Windows or saved by an editor that adds a BOM still parses.

    Falling to `invalid` here would be safe but useless; falling to `claude`
    would make this runtime act on a project Codex owns.
    """
    write_runtime(tmp_path, declared)
    assert mode_of(run(tmp_path)) == "codex"


def test_only_the_first_line_decides_the_mode(tmp_path):
    """Lines 2+ are the partition, not alternative modes."""
    write_runtime(tmp_path, "codex\nclaude: docs/\n")
    assert mode_of(run(tmp_path)) == "codex"


# --------------------------------------------------------------------------
# the asymmetry: unreadable must not become the acting mode
# --------------------------------------------------------------------------

@pytest.mark.parametrize("garbage", ["codex-only", "both", "claude+codex", "1"])
def test_unrecognised_mode_is_invalid_not_a_silent_default(tmp_path, garbage):
    write_runtime(tmp_path, garbage + "\n")
    out = run(tmp_path)
    assert mode_of(out) == "invalid"
    assert garbage in out, "the operator must see what the file actually says"
    assert "Ask the user" in out


def test_invalid_never_claims_full_studio(tmp_path):
    write_runtime(tmp_path, "codex-only\n")
    out = run(tmp_path)
    assert "Full studio" not in out


# --------------------------------------------------------------------------
# split mode carries the partition
# --------------------------------------------------------------------------

def test_split_echoes_the_declared_partition(tmp_path):
    write_runtime(tmp_path, "split\nclaude: docs/ rules/\ncodex: skills/ scripts/\n")
    out = run(tmp_path)
    assert mode_of(out) == "split"
    assert "claude: docs/ rules/" in out
    assert "codex: skills/ scripts/" in out


def test_split_without_a_partition_says_so(tmp_path):
    """Split mode with nothing declared is the dangerous case, not the quiet one."""
    write_runtime(tmp_path, "split\n")
    out = run(tmp_path)
    assert "NO PARTITION DECLARED" in out


def test_split_ignores_blank_partition_lines(tmp_path):
    write_runtime(tmp_path, "split\n\n\nclaude: docs/\n\n")
    out = run(tmp_path)
    assert "NO PARTITION DECLARED" not in out
    assert "claude: docs/" in out


# --------------------------------------------------------------------------
# contract with the rest of the studio
# --------------------------------------------------------------------------

def test_mode_is_independent_of_track(tmp_path):
    """runtime.txt says who builds; track.txt says what is built. Neither implies the other."""
    write_runtime(tmp_path, "codex\n")
    with open(os.path.join(tmp_path, "production", "track.txt"), "w", encoding="utf-8") as fh:
        fh.write("game\n")
    assert mode_of(run(tmp_path)) == "codex"


def test_hook_is_registered_in_the_plugin_manifest():
    """An unregistered hook never runs, and the rule would be documentation only."""
    import json
    with open(os.path.join(REPO, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    commands = [
        h["command"]
        for entry in manifest["hooks"]["SessionStart"]
        for h in entry["hooks"]
    ]
    assert any("detect-runtime-mode.sh" in c for c in commands)
