"""Tests for the `unknown` branch of hooks/detect-project-type.sh.

On a user-scope install most sessions are in projects that never use the studio
(usage audit, inbox 2026-11-15). Telling the model to ask "game or product?" in
every one of them is noise; the question belongs to projects that have started
studio work, i.e. have a production/ directory.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posix_bash import BASH, requires_bash  # noqa: E402

pytestmark = requires_bash

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "detect-project-type.sh")


def run(cwd):
    proc = subprocess.run([BASH, HOOK], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_unknown_without_studio_artifacts_does_not_ask(tmp_path):
    out = run(tmp_path)
    assert "PROJECT_TYPE=unknown" in out
    assert "Do not ask at session start" in out
    assert "production/track.txt" in out
    assert "ask the user whether" not in out


def test_unknown_with_production_dir_still_asks(tmp_path):
    (tmp_path / "production").mkdir()
    out = run(tmp_path)
    assert "PROJECT_TYPE=unknown" in out
    assert "ask the user whether" in out
