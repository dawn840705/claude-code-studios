"""Tests that the two plugin manifests agree with each other and with reality.

Why this exists: `.claude-plugin/marketplace.json` sat at version 0.6.0 and
"83 workflow skills" through both the v0.6.1 and v0.6.2 releases — the release
commits updated `plugin.json` and forgot its twin. Nothing caught it, because
the manifest that the marketplace actually advertises is not exercised by any
other test. A stale version there means users are offered an old build.

The counts are checked against the filesystem rather than against each other,
so adding a skill without updating the description is also unmergeable.
"""

import json
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_MANIFEST = os.path.join(REPO, ".claude-plugin", "plugin.json")
MARKETPLACE_MANIFEST = os.path.join(REPO, ".claude-plugin", "marketplace.json")
CLAUDE_MD = os.path.join(REPO, "CLAUDE.md")
CHANGELOG = os.path.join(REPO, "CHANGELOG.md")

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
    entries = [p for p in data["plugins"] if p["name"] == "claude-code-studios"]
    assert len(entries) == 1, "expected exactly one claude-code-studios entry"
    return entries[0]


def count_skills():
    root = os.path.join(REPO, "skills")
    return sum(1 for name in os.listdir(root)
               if os.path.isfile(os.path.join(root, name, "SKILL.md")))


def count_agents():
    root = os.path.join(REPO, "agents")
    return sum(1 for name in os.listdir(root)
               if name.endswith(".md") and not name.upper().startswith("README"))


# --------------------------------------------------------------------------
# version
# --------------------------------------------------------------------------

def test_plugin_version_is_semver(plugin):
    assert SEMVER.match(plugin["version"]), plugin["version"]


def test_marketplace_version_matches_plugin(plugin, marketplace_entry):
    """The exact drift that shipped in v0.6.1 and v0.6.2."""
    assert marketplace_entry["version"] == plugin["version"]


def test_changelog_documents_the_current_version(plugin):
    """The top section must name this version — or be an Unreleased section
    while work is in flight."""
    first = next(line for line in read(CHANGELOG).splitlines()
                 if line.startswith("## "))
    heading = first[3:].strip()
    assert heading.lower().startswith("unreleased") or heading.startswith(
        f"v{plugin['version']}"
    ), f"CHANGELOG top section is {heading!r}, plugin.json is {plugin['version']}"


# --------------------------------------------------------------------------
# counts advertised in prose
# --------------------------------------------------------------------------

@pytest.mark.parametrize("label,path", [
    ("plugin.json", PLUGIN_MANIFEST),
    ("marketplace.json", MARKETPLACE_MANIFEST),
    ("CLAUDE.md", CLAUDE_MD),
])
def test_advertised_counts_match_the_filesystem(label, path):
    body = read(path)
    skills, agents = count_skills(), count_agents()

    claimed_skills = re.findall(r"(\d+) workflow skills", body)
    claimed_agents = re.findall(r"(\d+) specialist agents", body)
    assert claimed_skills, f"{label} advertises no skill count"
    assert claimed_agents, f"{label} advertises no agent count"

    for value in claimed_skills:
        assert int(value) == skills, f"{label} says {value} skills, found {skills}"
    for value in claimed_agents:
        assert int(value) == agents, f"{label} says {value} agents, found {agents}"


# --------------------------------------------------------------------------
# shared fields
# --------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["license", "author"])
def test_shared_fields_agree(plugin, marketplace_entry, field):
    assert marketplace_entry[field] == plugin[field]


def test_marketplace_keywords_are_a_subset(plugin, marketplace_entry):
    """The marketplace list may be shorter, but must not invent keywords."""
    extra = set(marketplace_entry["keywords"]) - set(plugin["keywords"])
    assert not extra, f"marketplace-only keywords: {sorted(extra)}"
