# Unity Setup — Opt-in Hooks & Templates

This plugin ships with optional Unity-specific safeguards. They auto-detect a Unity project (presence of `Assets/` + `ProjectSettings/`) and stay silent in non-Unity projects, so installation has zero impact on Godot/Unreal/GameMaker users.

## What's included

| Asset | Type | Activation |
|---|---|---|
| `hooks/unity-meta-check.sh` | PostToolUse (Write/Edit) | **Auto** — fires when in a Unity project. Warns on `.cs`/`.shader`/`.asset`/`.prefab`/`.mat`/`.controller` writes if the paired `.meta` is missing. |
| `hooks/unity-animator-string-lint.sh` | PostToolUse (Write/Edit) | **Auto** — warns when `.cs` files use `Animator.SetBool("name", ...)` instead of cached `StringToHash`. |
| `templates/githooks/unity-pre-commit` | git pre-commit | **Manual opt-in** — blocks commit if a staged Unity asset is missing its paired `.meta`. |

## Auto-opt-in hooks (no setup needed)

If your project root has both `Assets/` and `ProjectSettings/`, the two PostToolUse hooks (`unity-meta-check.sh`, `unity-animator-string-lint.sh`) automatically fire after every Write/Edit. In any other project they exit immediately with no output.

These are **advisory** — they print to stderr but never block tool execution.

### Why these checks?

- **`.meta` missing** — Unity generates `.meta` (GUID mapping) only when the Editor has window focus. If Claude creates a `.cs` while Unity is backgrounded, the `.meta` is generated *later*. A commit in that window pushes the asset without its `.meta` → GUID corruption on other machines or CI.
- **Animator string access** — `Animator.SetBool("IsRun", true)` performs a string-to-hash search every call. Cache the hash once via `Animator.StringToHash("IsRun")` in `Start`/`Awake`, then pass the cached `int`.

## Manual git pre-commit (recommended for teams)

The advisory hooks warn but don't block. For zero-tolerance `.meta` enforcement (e.g. shared repo, CI machines), install the git pre-commit:

```bash
# In your Unity project root:
mkdir -p .claude/githooks
cp ~/.claude/plugins/marketplaces/game-studios/plugins/claude-code-game-studios/templates/githooks/unity-pre-commit .claude/githooks/pre-commit
chmod +x .claude/githooks/pre-commit
git config core.hooksPath .claude/githooks
```

(Adjust the source path if you cloned the plugin elsewhere.)

After activation:
- `git commit` is blocked when a staged asset is missing its `.meta` (or the `.meta` is unstaged).
- Recovery: focus Unity Editor once → `.meta` auto-generates → `git add` → retry.
- Intentional bypass (NOT recommended): `git commit --no-verify`.

### Bypass policy

Skipping `--no-verify` is the most common cause of GUID corruption. Configure your team's Claude Code settings to require explicit user authorization for `--no-verify` flags. The plugin's existing `validate-commit.sh` hook already handles this for non-Unity contexts; this template extends the safety net to Unity-specific concerns.

## Compatibility

- Tested on Unity 2022 LTS / Unity 6 (6000.x).
- Works with both default Unity package layout and asset store imports.
- No dependency on Unity Editor running — hooks operate on filesystem state only.

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Hook never fires | Verify `Assets/` and `ProjectSettings/` both exist at the cwd where you run Claude Code. |
| `jq` warning | Hooks fall back to `grep`-based JSON parsing automatically; no action needed. Install `jq` for slightly faster execution. |
| `.meta` warning on every save | Unity Editor backgrounded — focus once to flush all pending `.meta` files. |
| Pre-commit triggers on legitimate deletes | The hook only checks `--diff-filter=AM` (Added/Modified). Pure deletes pass through. |

## Disabling

To silence both PostToolUse hooks without uninstalling the plugin, override in your project's `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Write|Edit",
        "hooks": [
          { "type": "command",
            "command": "true",
            "timeout": 1 }
        ] }
    ]
  }
}
```

(This replaces the hook chain entirely. For finer control, fork the plugin or contribute a per-hook disable flag.)

To remove the git pre-commit:

```bash
git config --unset core.hooksPath
```
