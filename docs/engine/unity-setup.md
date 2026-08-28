# Unity Setup — Opt-in Hooks & Templates

This plugin ships with optional Unity-specific safeguards. They auto-detect a Unity project (presence of `Assets/` + `ProjectSettings/`) and stay silent in non-Unity projects, so installation has zero impact on Godot/Unreal/GameMaker users.

## What's included

| Asset | Type | Activation |
|---|---|---|
| `hooks/unity-meta-check.sh` | PostToolUse (`apply_patch`/edit aliases) | **Auto** — checks every changed Unity asset and warns when the paired `.meta` is missing. |
| `hooks/unity-animator-string-lint.sh` | PostToolUse (`apply_patch`/edit aliases) | **Auto** — checks changed `.cs` files for `Animator.SetBool("name", ...)` instead of cached `StringToHash`. |
| `templates/githooks/unity-pre-commit` | git pre-commit | **Manual opt-in** — blocks commit if a staged Unity asset is missing its paired `.meta`. |

## Auto-opt-in hooks (no setup needed)

If your project root has both `Assets/` and `ProjectSettings/`, the two PostToolUse hooks (`unity-meta-check.sh`, `unity-animator-string-lint.sh`) automatically inspect every file in a Codex `apply_patch`. In any other project they exit immediately with no output.

These are **advisory** — they print to stderr but never block tool execution.

## The rest of the hook set (v0.6.2+)

The two hooks above were Unity-aware from the start; the general-purpose hooks
were not. Until v0.6.2 they hardcoded `src/`, `assets/` and `design/gdd/`, so on
a Unity project `detect-gaps.sh` reported a mature codebase as `NEW PROJECT`,
`validate-commit.sh` matched nothing on every commit, and `validate-assets.sh`
skipped every file. They now read the layout from `hooks/lib/detect-layout.sh`
and work on `Assets/**/*.cs` without configuration.

One consequence worth knowing: the asset naming rule is **`pascal`** on Unity,
not `snake`. `PlayerController.cs`, `CARD_MaxHP.asset` and `Monster_Base.prefab`
are all accepted — only whitespace and hyphens are flagged, since a `.cs` file
name has to match its class name. If your project's design docs live somewhere
other than `design/gdd/` or `Documents/`, point the hooks at them:

```json
// .codex/studio-layout.json
{ "designRoots": ["Documents/Specs"], "assetNaming": "pascal" }
```

Full contract: [../hooks-reference.md](../hooks-reference.md).

### Why these checks?

- **`.meta` missing** — Unity generates `.meta` (GUID mapping) only when the Editor has window focus. If Codex creates a `.cs` while Unity is backgrounded, the `.meta` is generated *later*. A commit in that window pushes the asset without its `.meta` → GUID corruption on other machines or CI.
- **Animator string access** — `Animator.SetBool("IsRun", true)` performs a string-to-hash search every call. Cache the hash once via `Animator.StringToHash("IsRun")` in `Start`/`Awake`, then pass the cached `int`.

## Manual git pre-commit (recommended for teams)

The advisory hooks warn but don't block. For zero-tolerance `.meta` enforcement (e.g. shared repo, CI machines), install the git pre-commit:

```bash
# In your Unity project root:
mkdir -p .codex/githooks
cp /path/to/codex-code-studios/templates/githooks/unity-pre-commit .codex/githooks/pre-commit
chmod +x .codex/githooks/pre-commit
git config core.hooksPath .codex/githooks
```

(Adjust the source path if you cloned the plugin elsewhere.)

After activation:
- `git commit` is blocked when a staged asset is missing its `.meta` (or the `.meta` is unstaged).
- Recovery: focus Unity Editor once → `.meta` auto-generates → `git add` → retry.
- Intentional bypass (NOT recommended): `git commit --no-verify`.

### Bypass policy

Using `--no-verify` is a common cause of GUID corruption. Record a team policy in `AGENTS.md` that it requires explicit user authorization. The plugin's `validate-commit.sh` hook and this template cover complementary checks.

## Compatibility

- Tested on Unity 2022 LTS / Unity 6 (6000.x).
- Works with both default Unity package layout and asset store imports.
- No dependency on Unity Editor running — hooks operate on filesystem state only.

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Hook never fires | Verify `Assets/` and `ProjectSettings/` both exist at the cwd where you run Codex and that plugin hooks were trusted. |
| JSON payload not parsed | Install `jq` or Python 3; simple file-path payloads retain a guarded fallback. |
| `.meta` warning on every save | Unity Editor backgrounded — focus once to flush all pending `.meta` files. |
| Pre-commit triggers on legitimate deletes | The hook only checks `--diff-filter=AM` (Added/Modified). Pure deletes pass through. |

## Disabling

Disable or remove the plugin to stop its registered hooks. For a customized
hook set, fork the plugin and edit `hooks/hooks.json`; Codex will require a new
trust review after the hook configuration changes.

To remove the git pre-commit:

```bash
git config --unset core.hooksPath
```
