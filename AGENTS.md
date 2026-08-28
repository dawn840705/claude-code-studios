# Code Studios contributor guide

This repository is the source package for the `codex-code-studios` Codex plugin.

## Source of truth

- `.codex-plugin/plugin.json` defines the Codex plugin.
- `.agents/plugins/marketplace.json` defines the local/shareable marketplace entry.
- `skills/*/SKILL.md` contains user-facing workflows. Keep every skill valid under the Codex skill format.
- `skills/studio-orchestrator/references/roles/*.md` contains specialist personas. They are references loaded by the orchestrator, not independently installed Codex agents.
- `hooks/hooks.json` and `hooks/*.sh` implement Codex lifecycle hooks.
- `rules/*.md`, `docs/`, and `templates/` are plugin resources. They are not Codex command-approval rule files.

## Change rules

1. Preserve existing public skill names unless a migration explicitly documents a rename.
2. Use `$skill-name` when referring to a Codex skill invocation.
3. Resolve bundled resources relative to the invoking `SKILL.md` or `PLUGIN_ROOT`; reserve `.codex/` for state stored in the user's project.
4. Keep hook stdout valid for the matching Codex hook event. Advisory PostToolUse feedback belongs in `hookSpecificOutput.additionalContext`.
5. Run the plugin validator, every skill validator, the skill linter, shell syntax checks, and the full test suite before release.

The legacy `.claude-plugin/` manifest and `CLAUDE.md` remain only as a transition compatibility layer for the 0.7 release. Do not make them the source of truth for new Codex behavior.
