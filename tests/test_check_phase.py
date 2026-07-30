"""Tests for scripts/check_phase.py — the deterministic workflow-phase gate.

Covers: catalog parsing (the real catalog file), artifact checks, track
detection, phase resolution, dependency violations, and the exit-code contract
(0 complete / 1 in progress / 2 dependency violation / 3 cannot judge).
"""

import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "check_phase.py")
CATALOG = os.path.join(REPO, "docs", "workflow-catalog.yaml")

sys.path.insert(0, os.path.join(REPO, "scripts"))
import check_phase  # noqa: E402


# --------------------------------------------------------------------------
# Catalog parsing
# --------------------------------------------------------------------------

def test_real_catalog_parses():
    data = check_phase.load_catalog(CATALOG)
    assert data["version"] == 2
    assert set(data["tracks"]) == {"game", "product"}


def test_real_catalog_game_track_preserved():
    """The v1 game flow survived the v2 restructure intact."""
    data = check_phase.load_catalog(CATALOG)
    game = data["tracks"]["game"]["phases"]
    assert list(game) == [
        "concept", "systems-design", "technical-setup",
        "pre-production", "production", "polish", "release",
    ]
    engine = next(s for s in game["concept"]["steps"] if s["id"] == "engine-setup")
    assert engine["required"] is True
    assert engine["artifact"]["glob"] == ".claude/docs/technical-preferences.md"
    assert engine["artifact"]["pattern"] == "Engine: [^[]"
    adr = next(s for s in game["technical-setup"]["steps"] if s["id"] == "architecture-decision")
    assert adr["artifact"]["min_count"] == 3


def test_real_catalog_product_track_shape():
    data = check_phase.load_catalog(CATALOG)
    product = data["tracks"]["product"]["phases"]
    assert list(product) == [
        "discovery", "architecture", "build", "hardening", "ship", "growth",
    ]
    prd = next(s for s in product["discovery"]["steps"] if s["id"] == "create-prd")
    assert prd["command"] == "/create-prd"
    assert prd["artifact"]["glob"] == "product/prd/prd-*.md"
    assert product["growth"]["next_phase"] is None


def test_real_catalog_validates():
    assert check_phase.validate_catalog(check_phase.load_catalog(CATALOG)) == []


def test_parser_rejects_v1_catalog(tmp_path):
    cat = tmp_path / "cat.yaml"
    cat.write_text("phases:\n  concept:\n    label: Concept\n")
    with pytest.raises(check_phase.CatalogError):
        check_phase.load_catalog(str(cat))


# --------------------------------------------------------------------------
# Artifact checks
# --------------------------------------------------------------------------

def test_artifact_glob_and_min_count(tmp_path):
    art = {"glob": "docs/adr-*.md", "min_count": 2}
    assert check_phase.check_artifact(str(tmp_path), art) == "INCOMPLETE"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "adr-001.md").write_text("x")
    assert check_phase.check_artifact(str(tmp_path), art) == "INCOMPLETE"
    (tmp_path / "docs" / "adr-002.md").write_text("x")
    assert check_phase.check_artifact(str(tmp_path), art) == "COMPLETE"


def test_artifact_pattern(tmp_path):
    (tmp_path / "prefs.md").write_text("Engine: [TBD]")
    art = {"glob": "prefs.md", "pattern": "Engine: [^[]"}
    assert check_phase.check_artifact(str(tmp_path), art) == "INCOMPLETE"
    (tmp_path / "prefs.md").write_text("Engine: Godot 4.3")
    assert check_phase.check_artifact(str(tmp_path), art) == "COMPLETE"


def test_artifact_note_is_manual_and_none_is_unknown(tmp_path):
    assert check_phase.check_artifact(str(tmp_path), {"note": "ask a human"}) == "MANUAL"
    assert check_phase.check_artifact(str(tmp_path), None) == "UNKNOWN"


# --------------------------------------------------------------------------
# Track detection
# --------------------------------------------------------------------------

def test_detect_track(tmp_path):
    assert check_phase.detect_track(str(tmp_path)) == "game"  # empty → default
    (tmp_path / "product" / "prd").mkdir(parents=True)
    assert check_phase.detect_track(str(tmp_path)) == "product"
    (tmp_path / "design" / "gdd").mkdir(parents=True)
    assert check_phase.detect_track(str(tmp_path)) is None  # ambiguous


# --------------------------------------------------------------------------
# Phase resolution
# --------------------------------------------------------------------------

def _phases(track="game"):
    return check_phase.load_catalog(CATALOG)["tracks"][track]["phases"]


def test_stage_txt_wins(tmp_path):
    (tmp_path / "production").mkdir()
    (tmp_path / "production" / "stage.txt").write_text("Systems Design\n")
    assert check_phase.resolve_phase(str(tmp_path), _phases(), None) == "systems-design"


def test_phase_inferred_from_artifacts(tmp_path):
    # Nothing exists → first phase with an incomplete required step = concept
    assert check_phase.resolve_phase(str(tmp_path), _phases(), None) == "concept"


def test_explicit_phase_must_exist(tmp_path):
    with pytest.raises(check_phase.CatalogError):
        check_phase.resolve_phase(str(tmp_path), _phases(), "nope")


# --------------------------------------------------------------------------
# Evaluation + exit codes (via CLI, the real contract surface)
# --------------------------------------------------------------------------

def run_cli(root, *extra):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), *extra],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout


def test_exit_1_fresh_project(tmp_path):
    code, out = run_cli(tmp_path)
    assert code == 1
    assert "VERDICT: IN PROGRESS" in out


def test_exit_0_concept_phase_complete(tmp_path):
    (tmp_path / ".claude" / "docs").mkdir(parents=True)
    (tmp_path / ".claude" / "docs" / "technical-preferences.md").write_text("Engine: Godot 4.3")
    (tmp_path / "design" / "gdd").mkdir(parents=True)
    (tmp_path / "design" / "gdd" / "game-concept.md").write_text("x")
    (tmp_path / "design" / "gdd" / "systems-index.md").write_text("x")
    (tmp_path / "design" / "art").mkdir(parents=True)
    (tmp_path / "design" / "art" / "art-bible.md").write_text("x")
    code, out = run_cli(tmp_path, "--phase", "concept")
    assert code == 0, out
    assert "VERDICT: PHASE COMPLETE" in out


def test_exit_2_dependency_violation(tmp_path):
    # art-bible exists but its required dependency game-concept does not
    (tmp_path / "design" / "art").mkdir(parents=True)
    (tmp_path / "design" / "art" / "art-bible.md").write_text("x")
    (tmp_path / "design" / "gdd").mkdir(parents=True)  # marks track=game
    code, out = run_cli(tmp_path)
    assert code == 2, out
    assert "VERDICT: DEPENDENCY VIOLATION" in out
    assert "game-concept" in out


def test_exit_3_ambiguous_track(tmp_path):
    (tmp_path / "design" / "gdd").mkdir(parents=True)
    (tmp_path / "product" / "prd").mkdir(parents=True)
    code, out = run_cli(tmp_path)
    assert code == 3
    assert "CANNOT JUDGE" in out
    # explicit --track resolves it
    code2, _ = run_cli(tmp_path, "--track", "product")
    assert code2 in (0, 1, 2)


def test_exit_3_missing_catalog(tmp_path):
    code, out = run_cli(tmp_path, "--catalog", str(tmp_path / "missing.yaml"))
    assert code == 3
    assert "CANNOT JUDGE" in out


def test_product_track_flow(tmp_path):
    (tmp_path / "product" / "prd").mkdir(parents=True)
    code, out = run_cli(tmp_path, "--json")
    assert code == 1
    import json as jsonmod
    data = jsonmod.loads(out)
    assert data["track"] == "product"
    assert data["phase"] == "discovery"
    assert data["blocker"]["id"] == "product-concept"


def test_manual_required_step_blocks_exit_0(tmp_path):
    """hardening: security-audit is required + note-only → MANUAL keeps exit at 1."""
    (tmp_path / "product" / "prd").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "regression-suite.md").write_text("x")
    code, out = run_cli(tmp_path, "--phase", "hardening", "--track", "product")
    assert code == 1
    assert "MANUAL" in out


def test_validate_cli():
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--validate"], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout
    assert "VALID" in proc.stdout


def test_validate_catches_broken_depends_on(tmp_path):
    cat = tmp_path / "cat.yaml"
    cat.write_text(
        "version: 2\n"
        "tracks:\n"
        "  game:\n"
        "    label: \"Game\"\n"
        "    phases:\n"
        "      concept:\n"
        "        label: \"Concept\"\n"
        "        next_phase: null\n"
        "        steps:\n"
        "          - id: a\n"
        "            name: \"A\"\n"
        "            required: true\n"
        "            depends_on: [ghost]\n"
    )
    data = check_phase.load_catalog(str(cat))
    errors = check_phase.validate_catalog(data)
    assert any("ghost" in e for e in errors)
