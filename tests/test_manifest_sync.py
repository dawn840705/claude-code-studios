"""Validate the Codex plugin manifest, marketplace entry, and advertised roster."""

import json
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_MANIFEST = os.path.join(REPO, ".codex-plugin", "plugin.json")
MARKETPLACE_MANIFEST = os.path.join(REPO, ".agents", "plugins", "marketplace.json")
CHANGELOG = os.path.join(REPO, "CHANGELOG.md")
ROLES = os.path.join(REPO, "skills", "studio-orchestrator", "references", "roles")

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def plugin():
    return load(PLUGIN_MANIFEST)


@pytest.fixture(scope="module")
def marketplace_entry():
    data = load(MARKETPLACE_MANIFEST)
    entries = [p for p in data["plugins"] if p["name"] == "codex-code-studios"]
    assert len(entries) == 1, "expected exactly one codex-code-studios entry"
    return entries[0]


def count_skills():
    root = os.path.join(REPO, "skills")
    return sum(
        1
        for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name, "SKILL.md"))
    )


def count_roles():
    return sum(
        1
        for name in os.listdir(ROLES)
        if name.endswith(".md") and not name.upper().startswith("README")
    )


def test_plugin_version_is_semver(plugin):
    assert SEMVER.match(plugin["version"]), plugin["version"]


def test_manifest_exposes_skills_and_default_hooks(plugin):
    assert plugin["name"] == "codex-code-studios"
    assert plugin["skills"] == "./skills/"
    assert "hooks" not in plugin, "default hooks/hooks.json must be auto-discovered"
    assert os.path.isfile(os.path.join(REPO, "hooks", "hooks.json"))


def test_marketplace_points_to_repository_root(marketplace_entry):
    assert marketplace_entry["source"] == {"source": "local", "path": "./"}
    assert marketplace_entry["policy"]["installation"] == "AVAILABLE"
    assert marketplace_entry["category"] == "Developer Tools"


def test_changelog_documents_the_current_version(plugin):
    first = next(line for line in read(CHANGELOG).splitlines() if line.startswith("## "))
    heading = first[3:].strip()
    assert heading.lower().startswith("unreleased") or heading.startswith(
        f"v{plugin['version']}"
    ), f"CHANGELOG top section is {heading!r}, plugin.json is {plugin['version']}"


def test_advertised_counts_match_the_filesystem(plugin):
    body = json.dumps(plugin, ensure_ascii=False)
    claimed_skills = re.findall(r"(\d+) workflow skills", body)
    claimed_roles = re.findall(r"(\d+) specialist role guides", body)
    assert claimed_skills and claimed_roles
    assert all(int(value) == count_skills() for value in claimed_skills)
    assert all(int(value) == count_roles() for value in claimed_roles)


def test_every_role_has_frontmatter():
    for name in os.listdir(ROLES):
        if not name.endswith(".md"):
            continue
        text = read(os.path.join(ROLES, name))
        assert text.startswith("---\nname:"), name
        assert "\ndescription:" in text.split("\n---\n", 1)[0], name
