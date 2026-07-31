"""Tests for hooks/lib/detect-layout.sh and the three hooks that consume it.

The bug these cover: every path-sensitive hook hardcoded a lowercase web layout
(src/, assets/, design/gdd/). Unity forces Assets/ + ProjectSettings/ and keeps
code under Assets/**/*.cs, so on a real Unity project detect-gaps.sh reported
"NEW PROJECT" (and skipped checks 1-5 entirely), validate-commit.sh matched
nothing on every commit, and validate-assets.sh skipped every file — while its
lowercase-only naming rule sat there waiting to fire on PascalCase the moment
the path filter was fixed.

Both directions are asserted throughout: Unity projects must now be handled,
and generic/web projects must behave exactly as they did before.
"""

import json
import os
import shutil
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(REPO, "hooks")
LIB = os.path.join(HOOKS, "lib", "detect-layout.sh")

DETECT_GAPS = os.path.join(HOOKS, "detect-gaps.sh")
VALIDATE_COMMIT = os.path.join(HOOKS, "validate-commit.sh")
VALIDATE_ASSETS = os.path.join(HOOKS, "validate-assets.sh")

COMMIT_EVENT = json.dumps(
    {"tool_name": "Bash", "tool_input": {"command": 'git commit -m "test"'}}
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def write(root, relpath, content=""):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def run_hook(script, cwd, stdin="", env=None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", script],
        cwd=str(cwd),
        input=stdin,
        capture_output=True,
        text=True,
        env=full_env,
    )


def probe(cwd, snippet, env=None, prelude=""):
    """Source the helper in `cwd` and run a shell snippet against it."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", "-c", f'{prelude}\n. "{LIB}"\n{snippet}'],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=full_env,
    )


# Shadows the `command` builtin so the helper believes jq is absent, which is
# the only way to exercise the grep fallback on a machine that has jq.
NO_JQ = (
    'command() { if [ "$1" = "-v" ] && [ "$2" = "jq" ]; then return 1; fi; '
    'builtin command "$@"; }'
)


def write_event(file_path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})


def git_init(root):
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True,
                   capture_output=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "config", key, value], cwd=str(root), check=True,
                       capture_output=True)


def git_add_all(root):
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True,
                   capture_output=True)


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def unity(tmp_path):
    """A mature Unity project: 60 scripts, 80 design docs, no src/ or design/gdd/."""
    root = tmp_path / "unity"
    os.makedirs(root / "ProjectSettings")
    for i in range(60):
        write(root, f"Assets/02.Scripts/Gameplay/Behaviour{i}.cs",
              f"public class Behaviour{i} {{}}\n")
    for i in range(80):
        write(root, f"Documents/Specs/Spec{i}.md", f"# Spec {i}\n")
    # Library/ holds tens of thousands of generated files in a real project.
    write(root, "Library/ScriptAssemblies/Generated.cs", "// generated\n")
    return root


@pytest.fixture
def web(tmp_path):
    """The layout every hook assumed before v0.6.2."""
    root = tmp_path / "web"
    for i in range(6):
        write(root, f"src/gameplay/combat/mod{i}.ts", f"export const a{i} = 1;\n")
    write(root, "design/gdd/combat-system.md", "# Combat\n")
    write(root, "assets/data/items.json", '{"ok": true}\n')
    return root


@pytest.fixture
def empty(tmp_path):
    root = tmp_path / "empty"
    os.makedirs(root)
    return root


# --------------------------------------------------------------------------
# detect-layout.sh — engine detection and layout resolution
# --------------------------------------------------------------------------

def test_helper_detects_unity(unity):
    out = probe(unity, 'echo "$STUDIO_ENGINE"').stdout.strip()
    assert out == "unity"


def test_helper_detects_generic_for_web(web):
    out = probe(web, 'echo "$STUDIO_ENGINE"').stdout.strip()
    assert out == "generic"


def test_helper_detects_godot(tmp_path):
    root = tmp_path / "g"
    write(root, "project.godot", "")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "godot"


def test_helper_detects_unreal(tmp_path):
    root = tmp_path / "u"
    write(root, "MyGame.uproject", "{}")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "unreal"


def test_helper_detects_gamemaker(tmp_path):
    root = tmp_path / "gm"
    write(root, "MyGame.yyp", "{}")
    assert probe(root, 'echo "$STUDIO_ENGINE"').stdout.strip() == "gamemaker"


def test_unity_source_count_excludes_library(unity):
    """Library/ and Temp/ are generated — counting them would also blow the
    SessionStart timeout on a real project."""
    assert probe(unity, "studio_count_sources").stdout.strip() == "60"


def test_unity_design_root_is_documents(unity):
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.strip()
    assert out == "Documents"
    assert probe(unity, "studio_count_design_docs").stdout.strip() == "80"


def test_design_roots_keep_every_existing_candidate(unity):
    """A Unity project can carry both its own Documents/ and a template gdd tree."""
    write(unity, "design/gdd/combat-system.md", "# Combat\n")
    roots = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.split()
    assert set(roots) == {"design/gdd", "Documents"}


def test_design_roots_fall_back_to_canonical_path_when_none_exist(empty):
    assert probe(empty, 'echo "$STUDIO_DESIGN_ROOTS"').stdout.strip() == "design/gdd"


def test_generic_layout_unchanged(web):
    """src/ stays the primary root; assets/, snake and design/gdd are as before."""
    out = probe(web, 'echo "$STUDIO_ASSET_ROOTS|$STUDIO_ASSET_NAMING|'
                     '$STUDIO_DESIGN_ROOTS"').stdout.strip()
    assert out == "assets|snake|design/gdd"
    roots = probe(web, 'echo "$STUDIO_SRC_ROOTS"').stdout.split()
    assert roots[0] == "src"


def test_generic_monorepo_roots_are_additive(tmp_path):
    """packages/ counts, but only because it exists — src/ alone is unaffected."""
    root = tmp_path / "mono"
    write(root, "packages/api/index.ts", "export const a = 1;\n")
    write(root, "src/main.ts", "export const b = 2;\n")
    assert probe(root, "studio_count_sources").stdout.strip() == "2"


def test_naming_convention_is_per_engine(unity, web):
    assert probe(unity, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "pascal"
    assert probe(web, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "snake"


def test_find_subdir_handles_unity_nesting(unity):
    """Unity nests as Assets/02.Scripts/Gameplay/ — a fixed src/gameplay never resolves."""
    out = probe(unity, "studio_find_subdir Gameplay gameplay").stdout.strip()
    assert out == "Assets/02.Scripts/Gameplay"


def test_source_globs_are_not_shell_expanded(tmp_path):
    """An unquoted "-name *.cs" string would be glob-expanded against $PWD
    before find ever saw it, silently narrowing the search to one file."""
    root = tmp_path / "u"
    os.makedirs(root / "ProjectSettings")
    write(root, "Assets/A.cs", "")
    write(root, "Assets/B.cs", "")
    # A .cs file in the project root is what would poison the glob.
    write(root, "Decoy.cs", "")
    assert probe(root, "studio_count_sources").stdout.strip() == "2"


def test_naming_violation_pascal_allows_unity_conventions(unity):
    for name in ("PlayerController.cs", "CARD_MaxHP.asset", "Monster_Base.prefab"):
        result = probe(unity, f'studio_naming_violation "{name}"')
        assert result.stdout == "", f"{name} should be accepted under PascalCase"


def test_naming_violation_pascal_still_rejects_spaces_and_hyphens(unity):
    assert "whitespace" in probe(unity, 'studio_naming_violation "Bad Name.png"').stdout
    assert "hyphen" in probe(unity, 'studio_naming_violation "my-texture.png"').stdout


def test_naming_violation_snake_unchanged(web):
    assert "lowercase" in probe(web, 'studio_naming_violation "Hero.png"').stdout
    assert probe(web, 'studio_naming_violation "hero_idle.png"').stdout == ""


# --- overrides ------------------------------------------------------------

def test_env_override_wins(web):
    out = probe(web, 'echo "$STUDIO_ENGINE|$STUDIO_ASSET_NAMING|$STUDIO_LAYOUT_SOURCE"',
                env={"STUDIO_ENGINE": "unity", "STUDIO_ASSET_NAMING": "any"})
    assert out.stdout.strip() == "unity|any|env"


def test_env_override_of_design_roots_is_colon_separated(unity):
    write(unity, "Docs/Readme.md", "# hi\n")
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"',
                env={"STUDIO_DESIGN_ROOTS": "Docs:Documents"})
    assert out.stdout.split() == ["Docs", "Documents"]


def test_dedicated_config_file_overrides_detection(unity):
    write(unity, ".claude/studio-layout.json",
          json.dumps({"assetNaming": "any", "designRoots": ["Documents"]}))
    out = probe(unity, 'echo "$STUDIO_ASSET_NAMING|$STUDIO_LAYOUT_SOURCE"')
    assert out.stdout.strip().startswith("any|")


@pytest.mark.skipif(shutil.which("jq") is None, reason="array config needs jq")
def test_settings_json_layout_block_is_read(unity):
    write(unity, ".claude/settings.json",
          json.dumps({"studio": {"layout": {"srcRoots": ["Assets/02.Scripts"]}}}))
    assert probe(unity, 'echo "$STUDIO_SRC_ROOTS"').stdout.strip() == "Assets/02.Scripts"


def test_string_config_values_are_readable_without_jq(unity):
    """No jq means the grep fallback, which understands scalars only."""
    write(unity, ".claude/studio-layout.json",
          '{\n  "assetNaming": "snake",\n  "designRoots": "Docs"\n}')
    write(unity, "Docs/Readme.md", "# hi\n")
    out = probe(unity, 'echo "$STUDIO_ASSET_NAMING|$STUDIO_DESIGN_ROOTS"', prelude=NO_JQ)
    assert out.stdout.strip() == "snake|Docs"


def test_array_config_without_jq_degrades_to_detection(unity):
    """An unreadable array must fall through to detection, never to garbage."""
    write(unity, ".claude/studio-layout.json", '{"designRoots": ["Docs"]}')
    out = probe(unity, 'echo "$STUDIO_DESIGN_ROOTS"', prelude=NO_JQ)
    assert out.stdout.strip() == "Documents"


def test_invalid_naming_value_falls_back_to_engine_default(unity):
    write(unity, ".claude/studio-layout.json", json.dumps({"assetNaming": "bogus"}))
    assert probe(unity, 'echo "$STUDIO_ASSET_NAMING"').stdout.strip() == "pascal"


def test_helper_is_idempotent_when_sourced_twice(web):
    result = probe(web, f'. "{LIB}"\necho "$STUDIO_ENGINE"')
    assert result.returncode == 0
    assert result.stdout.strip() == "generic"


def test_helper_is_silent_without_debug(web):
    result = probe(web, "true")
    assert result.stdout == ""
    assert result.stderr == ""


# --------------------------------------------------------------------------
# detect-gaps.sh
# --------------------------------------------------------------------------

def test_unity_project_is_not_reported_as_new(unity):
    """The headline bug: 60 scripts and 80 docs read as a fresh start."""
    result = run_hook(DETECT_GAPS, unity)
    assert result.returncode == 0
    assert "NEW PROJECT" not in result.stdout


def test_empty_project_is_still_reported_as_new(empty):
    result = run_hook(DETECT_GAPS, empty)
    assert "NEW PROJECT" in result.stdout


def test_bare_engine_scaffold_is_not_new(tmp_path):
    """Unity scaffolding only exists because someone created the project."""
    root = tmp_path / "bare"
    os.makedirs(root / "Assets")
    os.makedirs(root / "ProjectSettings")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, root).stdout


def test_web_project_with_code_is_not_new(web):
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, web).stdout


def test_production_artifacts_rule_out_fresh(empty):
    """Nothing creates production/ by accident — this repo itself is the case
    that has no src/ at all yet is obviously not a fresh start."""
    write(empty, "production/session-logs/2026-07-31.md", "# log\n")
    assert "NEW PROJECT" not in run_hook(DETECT_GAPS, empty).stdout


def test_empty_production_directory_does_not_count(empty):
    os.makedirs(empty / "production")
    assert "NEW PROJECT" in run_hook(DETECT_GAPS, empty).stdout


def test_unity_gap_checks_actually_run(unity):
    """Checks 1-5 were unreachable behind the fresh-project early exit."""
    shutil.rmtree(unity / "Documents")
    for i in range(6):
        write(unity, f"Assets/02.Scripts/Gameplay/Combat/C{i}.cs", "class C {}\n")
    write(unity, "Assets/02.Scripts/Core/Boot.cs", "class Boot {}\n")

    out = run_hook(DETECT_GAPS, unity).stdout
    assert "Substantial codebase" in out
    assert "Assets/02.Scripts/Gameplay/Combat/" in out
    assert "no architecture docs directory" in out


def test_web_gap_checks_unchanged(web):
    os.remove(web / "design" / "gdd" / "combat-system.md")
    write(web, "src/core/boot.ts", "export const boot = 1;\n")
    out = run_hook(DETECT_GAPS, web).stdout
    assert "src/gameplay/combat/" in out
    assert "no architecture docs directory" in out


def test_design_doc_presence_silences_the_gameplay_check(web):
    """design/gdd/combat-system.md covers src/gameplay/combat/."""
    out = run_hook(DETECT_GAPS, web).stdout
    assert "GAP" not in out


def test_meta_sidecars_do_not_inflate_the_system_file_count(unity):
    """Every Unity asset has a .meta twin — counting both halves the threshold."""
    shutil.rmtree(unity / "Documents")
    for i in range(3):
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs", "class C {}\n")
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs.meta", "guid: x\n")
    out = run_hook(DETECT_GAPS, unity).stdout
    assert "Cover/" not in out, "3 scripts + 3 .meta must not read as 6 files"


def test_design_docs_are_found_in_nested_directories(unity):
    """Design roots are rarely flat — Documents/Specs/CoverSystem.md counts."""
    for i in range(6):
        write(unity, f"Assets/02.Scripts/Gameplay/Cover/C{i}.cs", "class C {}\n")
    write(unity, "Documents/Specs/CoverSystem.md", "# Cover\n")
    assert "Cover/" not in run_hook(DETECT_GAPS, unity).stdout


def test_design_doc_lookup_is_case_insensitive(unity):
    assert probe(unity, 'studio_design_doc_exists Cover && echo hit').stdout.strip() == ""
    write(unity, "Documents/cover-system.md", "# Cover\n")
    assert probe(unity, 'studio_design_doc_exists Cover && echo hit').stdout.strip() == "hit"


def test_adr_directory_satisfies_the_architecture_check(unity):
    write(unity, "Assets/02.Scripts/Core/Boot.cs", "class Boot {}\n")
    for i in range(3):
        write(unity, f"design/adr/adr-00{i}.md", f"# ADR {i}\n")
    out = run_hook(DETECT_GAPS, unity).stdout
    assert "architecture docs" not in out


def test_detect_gaps_survives_a_missing_helper(unity, tmp_path):
    """A broken install must not fail the session."""
    staged = tmp_path / "hooks_copy"
    os.makedirs(staged)
    shutil.copy(DETECT_GAPS, staged / "detect-gaps.sh")
    result = run_hook(str(staged / "detect-gaps.sh"), unity)
    assert result.returncode == 0
    assert "detect-layout.sh not found" in result.stdout


# --------------------------------------------------------------------------
# validate-commit.sh
# --------------------------------------------------------------------------

def test_commit_hook_fires_on_unity_sources(unity):
    git_init(unity)
    write(unity, "Assets/02.Scripts/PlayerController.cs",
          "public class PlayerController {\n    // TODO: refactor\n    int health = 100;\n}\n")
    git_add_all(unity)

    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert result.returncode == 0
    assert "hardcoded gameplay values" in result.stderr
    assert "TODO/FIXME without owner tag" in result.stderr
    assert "PlayerController.cs" in result.stderr


def test_commit_hook_still_fires_on_web_sources(web):
    git_init(web)
    write(web, "src/gameplay/combat.ts", "// FIXME broken\nexport const damage = 12;\n")
    git_add_all(web)

    stderr = run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT).stderr
    assert "hardcoded gameplay values" in stderr
    assert "src/gameplay/combat.ts" in stderr


def test_commit_hook_matches_owned_todos_as_clean(unity):
    git_init(unity)
    write(unity, "Assets/02.Scripts/Clean.cs",
          "public class Clean {\n    // TODO(dawn): later\n}\n")
    git_add_all(unity)
    assert "TODO/FIXME" not in run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT).stderr


def test_commit_hook_blocks_invalid_json_under_unity_assets(unity):
    git_init(unity)
    write(unity, "Assets/Resources/cards.json", '{"a":')
    git_add_all(unity)

    result = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT)
    assert result.returncode == 2
    assert "not valid JSON" in result.stderr


def test_commit_hook_blocks_invalid_json_in_web_layout(web):
    git_init(web)
    write(web, "assets/data/broken.json", '{"a":')
    git_add_all(web)
    assert run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT).returncode == 2


def test_commit_hook_enforces_gdd_sections_in_canonical_path(web):
    git_init(web)
    git_add_all(web)
    stderr = run_hook(VALIDATE_COMMIT, web, stdin=COMMIT_EVENT).stderr
    assert "missing required section: Player Fantasy" in stderr


def test_commit_hook_ignores_ordinary_docs_outside_the_gdd_path(unity):
    """Documents/ is a general doc tree — not every note owes a Player Fantasy."""
    git_init(unity)
    write(unity, "Documents/Meeting.md", "# Standup\n\nWe talked about things.\n")
    git_add_all(unity)
    assert "missing required section" not in run_hook(
        VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT).stderr


def test_commit_hook_enforces_sections_on_gdd_shaped_docs_anywhere(unity):
    """Three sections present means someone was writing a GDD — finish it."""
    git_init(unity)
    write(unity, "Documents/Specs/CombatSpec.md",
          "# Combat\n\n## Overview\nx\n\n## Dependencies\ny\n\n## Formulas\nz\n")
    git_add_all(unity)
    stderr = run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT).stderr
    assert "missing required section: Player Fantasy" in stderr


def test_commit_hook_ignores_non_commit_commands(unity):
    git_init(unity)
    write(unity, "Assets/02.Scripts/Bad.cs", "// TODO: x\nint damage = 5;\n")
    git_add_all(unity)
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    result = run_hook(VALIDATE_COMMIT, unity, stdin=event)
    assert result.returncode == 0
    assert result.stderr == ""


def test_commit_hook_produces_no_stdout(unity):
    """grep findings used to leak into stdout instead of the stderr report."""
    git_init(unity)
    write(unity, "Assets/02.Scripts/Noisy.cs", "// TODO: x\nint damage = 5;\n")
    git_add_all(unity)
    assert run_hook(VALIDATE_COMMIT, unity, stdin=COMMIT_EVENT).stdout == ""


# --------------------------------------------------------------------------
# validate-assets.sh
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "Assets/Art/PlayerController.cs",
    "Assets/Data/CARD_MaxHP.asset",
    "Assets/Prefabs/Monster_Base.prefab",
])
def test_unity_pascal_names_are_accepted(unity, name):
    """Fixing the path match alone would have warned on every one of these."""
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event(name))
    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize("name,reason", [
    ("Assets/Art/Bad Name.png", "whitespace"),
    ("Assets/Art/my-texture.png", "hyphen"),
])
def test_unity_still_rejects_spaces_and_hyphens(unity, name, reason):
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event(name))
    assert result.returncode == 0
    assert reason in result.stderr


def test_web_naming_rule_unchanged(web):
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/Sprites/Hero.png"))
    assert "must be lowercase with underscores" in result.stderr
    assert run_hook(VALIDATE_ASSETS, web,
                    stdin=write_event("assets/sprites/hero.png")).stderr == ""


def test_files_outside_asset_roots_are_skipped(unity):
    assert run_hook(VALIDATE_ASSETS, unity, stdin=write_event("src/foo.ts")).stderr == ""


def test_meta_sidecars_are_skipped(unity):
    event = write_event("Assets/Art/Bad Name.png.meta")
    assert run_hook(VALIDATE_ASSETS, unity, stdin=event).stderr == ""


def test_invalid_json_blocks_under_unity_assets(unity):
    write(unity, "Assets/Resources/cards.json", '{"a":')
    result = run_hook(VALIDATE_ASSETS, unity, stdin=write_event("Assets/Resources/cards.json"))
    assert result.returncode == 1
    assert "not valid JSON" in result.stderr


def test_invalid_json_blocks_in_web_layout(web):
    write(web, "assets/data/bad.json", '{"a":')
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/data/bad.json"))
    assert result.returncode == 1


def test_valid_json_passes(web):
    result = run_hook(VALIDATE_ASSETS, web, stdin=write_event("assets/data/items.json"))
    assert result.returncode == 0


def test_empty_file_path_is_skipped(unity):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    result = run_hook(VALIDATE_ASSETS, unity, stdin=event)
    assert result.returncode == 0
    assert result.stderr == ""


def test_assets_hook_survives_a_missing_helper(tmp_path):
    """Without the helper it must still enforce the legacy web rules."""
    staged = tmp_path / "hooks_copy"
    os.makedirs(staged)
    shutil.copy(VALIDATE_ASSETS, staged / "validate-assets.sh")
    project = tmp_path / "proj"
    write(project, "assets/data/items.json", "{}")

    result = run_hook(str(staged / "validate-assets.sh"), project,
                      stdin=write_event("assets/Sprites/Hero.png"))
    assert result.returncode == 0
    assert "must be lowercase with underscores" in result.stderr


# --------------------------------------------------------------------------
# the two Unity hooks that already worked — guard against regression
# --------------------------------------------------------------------------

def test_unity_meta_check_still_flags_missing_meta(unity):
    write(unity, "Assets/02.Scripts/New.cs", "public class New {}\n")
    result = run_hook(os.path.join(HOOKS, "unity-meta-check.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/New.cs"))
    assert result.returncode == 0
    assert "Missing .meta" in result.stderr


def test_unity_meta_check_still_skips_non_unity_projects(web):
    result = run_hook(os.path.join(HOOKS, "unity-meta-check.sh"), web,
                      stdin=write_event("src/foo.cs"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_animator_lint_still_flags_string_access(unity):
    write(unity, "Assets/02.Scripts/Anim.cs",
          'void Update() { animator.SetBool("IsRunning", true); }\n')
    result = run_hook(os.path.join(HOOKS, "unity-animator-string-lint.sh"), unity,
                      stdin=write_event("Assets/02.Scripts/Anim.cs"))
    assert result.returncode == 0
    assert "Animator string-access detected" in result.stderr


# --------------------------------------------------------------------------
# plugin manifest
# --------------------------------------------------------------------------

def test_post_tool_use_matcher_includes_multiedit():
    manifest = os.path.join(REPO, ".claude-plugin", "plugin.json")
    with open(manifest, encoding="utf-8") as fh:
        data = json.load(fh)
    matchers = [entry["matcher"] for entry in data["hooks"]["PostToolUse"]]
    assert all("MultiEdit" in m for m in matchers), matchers


def test_every_layout_aware_hook_sources_the_helper():
    for script in (DETECT_GAPS, VALIDATE_COMMIT, VALIDATE_ASSETS):
        with open(script, encoding="utf-8") as fh:
            body = fh.read()
        assert "lib/detect-layout.sh" in body, script
        # The source must be guarded — a missing helper cannot kill a hook.
        assert '-f "$SCRIPT_DIR/lib/detect-layout.sh"' in body, script


def test_no_hook_uses_perl_grep():
    """Windows Git Bash ships grep without -P."""
    scripts = [os.path.join(HOOKS, n) for n in os.listdir(HOOKS) if n.endswith(".sh")]
    scripts.append(LIB)
    for path in scripts:
        with open(path, encoding="utf-8") as fh:
            code = [ln for ln in fh if not ln.lstrip().startswith("#")]
        for line in code:
            assert "grep -P" not in line, (path, line)
            assert "grep -qP" not in line, (path, line)
