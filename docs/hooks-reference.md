# Active Hooks

Hooks are configured in `.claude-plugin/plugin.json` (or `.claude/settings.json`
for a manual install) and fire automatically:

| Hook | Event | Trigger | Action |
| ---- | ----- | ------- | ------ |
| `validate-commit.sh` | PreToolUse (Bash) | `git commit` commands | Validates design doc sections, JSON data files, hardcoded values, TODO format |
| `validate-push.sh` | PreToolUse (Bash) | `git push` commands | Warns on pushes to protected branches (develop/main) |
| `validate-assets.sh` | PostToolUse (Write/Edit/MultiEdit) | Asset file changes | Checks naming conventions and JSON validity for files under the project's asset root |
| `unity-meta-check.sh` | PostToolUse (Write/Edit/MultiEdit) | Unity asset writes | Warns when a `.cs`/`.shader`/`.asset`/`.prefab`/`.mat`/`.controller` has no paired `.meta` |
| `unity-animator-string-lint.sh` | PostToolUse (Write/Edit/MultiEdit) | `.cs` writes | Warns on `Animator.SetBool("literal")` instead of a cached `StringToHash` |
| `session-start.sh` | SessionStart | Session begins | Loads sprint context, milestone, git activity; detects and previews active session state file for recovery |
| `detect-gaps.sh` | SessionStart | Session begins | Detects fresh projects (suggests /start) and missing documentation when code/prototypes exist, suggests /reverse-document or /project-stage-detect |
| `detect-project-type.sh` | SessionStart | Session begins | Prints `PROJECT_TYPE=<game\|web\|mobile\|service\|unknown>` so the orchestrator activates the right agent pack |
| `detect-runtime-mode.sh` | SessionStart | Session begins | Prints `RUNTIME_MODE=<claude\|codex\|split\|invalid>` from `production/runtime.txt` so the orchestrator knows whether to run the full studio, **stand down** for `codex-code-studios`, or work a declared path partition. Unrecognised content reports `invalid` rather than defaulting to the acting mode |
| `pre-compact.sh` | PreCompact | Context compression | Dumps session state (active.md, modified files, WIP design docs) into conversation before compaction so it survives summarization |
| `post-compact.sh` | PostCompact | After compaction | Reminds Claude to restore session state from `active.md` checkpoint |
| `notify.sh` | Notification | Notification event | Shows Windows toast notification via PowerShell |
| `session-stop.sh` | Stop | Session ends | Summarizes accomplishments and updates session log |
| `log-agent.sh` | SubagentStart | Agent spawned | Audit trail start — logs subagent invocation with timestamp |
| `log-agent-stop.sh` | SubagentStop | Agent stops | Audit trail stop — completes subagent record |
| `validate-skill-change.sh` | PostToolUse (Write/Edit/MultiEdit) | Skill file changes | Advises running `/skill-test` after any `.claude/skills/` file is written or edited |

Hook reference documentation: `.claude/docs/hooks-reference/`
Hook input schema documentation: `.claude/docs/hooks-reference/hook-input-schemas.md`

## Which hooks can actually block

A hook that only ever exits 0 has never rendered a verdict, and "no verdict" is
not "pass" — the same rule [`deterministic-gates.md`](./deterministic-gates.md)
states for gates. Read this table before treating a silent hook as a green light.

| Hook | Highest exit code | Can it block? |
| ---- | ----------------- | ------------- |
| `validate-commit.sh` | 2 | **Yes** — blocks the `git commit` |
| `validate-push.sh` | 2 | **Yes** — blocks the `git push` |
| `validate-assets.sh` | 2 | **Yes** — invalid JSON only; naming stays advisory |
| `validate-skill-change.sh` | 0 | No — advisory only |
| `unity-meta-check.sh` | 0 | No — advisory only |
| `unity-animator-string-lint.sh` | 0 | No — advisory only |
| `detect-gaps.sh` | 0 | No — advisory only |
| `session-start.sh` · `session-stop.sh` · `pre-compact.sh` | 0 | No — context injection, not judgment |
| `post-compact.sh` · `notify.sh` | no explicit exit | No — context injection, not judgment |
| `log-agent.sh` · `log-agent-stop.sh` · `detect-project-type.sh` · `detect-runtime-mode.sh` | 0 | No — audit trail / detection output |

Only three hooks in this plugin render a verdict. Everything else informs.

---

## Layout detection — `hooks/lib/detect-layout.sh`

**Any hook that touches a project path must get that path from the helper, never
from a hardcoded literal.** Detection lives in exactly one file so the hooks
cannot drift apart again.

They did drift: `detect-gaps.sh`, `validate-commit.sh` and `validate-assets.sh`
each assumed `src/`, `assets/` and `design/gdd/`. Unity forces `Assets/` +
`ProjectSettings/` and keeps code under `Assets/**/*.cs`, so on a Unity project
the first hook reported a 60-script codebase as `NEW PROJECT` (and exited before
its own gap checks ran), the second matched nothing on every commit, and the
third skipped every file — hiding the fact that its lowercase-only naming rule
would reject `PlayerController.cs`, which is the *correct* Unity name.

### What it exports

| Variable | Unity | Godot | Unreal | Generic |
| --- | --- | --- | --- | --- |
| `STUDIO_ENGINE` | `unity` | `godot` | `unreal` | `generic` |
| `STUDIO_SRC_ROOTS` | `Assets` | `.` | `Source`, `Plugins` | `src`, `lib`, `app`, `packages` |
| `STUDIO_SRC_EXTS` | `cs` | `gd cs` | `cpp h hpp` | `gd cs cpp c h hpp rs py js ts …` |
| `STUDIO_DESIGN_ROOTS` | every existing candidate: `design/gdd`, `Documents`, `Docs`, `docs/design`, … | | | `design/gdd`, `product/prd`, `docs/design` |
| `STUDIO_ASSET_ROOTS` | `Assets` | `assets`, `Assets` | `Content` | `assets` |
| `STUDIO_ASSET_NAMING` | `pascal` | `snake` | `pascal` | `snake` |

Helper functions: `studio_find_sources`, `studio_count_sources`,
`studio_count_design_docs`, `studio_design_doc_exists`, `studio_find_subdir`,
`studio_is_engine_project`, `studio_path_has_ext`, `studio_asset_root_regex`,
`studio_naming_violation`. Generated directories (`Library/`, `Temp/`,
`node_modules/`, `Intermediate/`, …) are pruned from every walk — Unity's
`Library/` alone would blow the SessionStart timeout.

Design roots are **not exclusive**: every candidate that exists is kept, because
a Unity project commonly carries both its own `Documents/` tree and a
`design/gdd/` tree copied from the template.

### Naming conventions are per-engine

`pascal` is not a relaxation of `snake` — it is a different correct answer.
Unity requires a `.cs` file name to match its class name, so `PlayerController.cs`,
`CARD_MaxHP.asset` and `Monster_Base.prefab` are all correct and none of them
can be lowercased. Under `pascal` only whitespace and hyphens are flagged. Under
`snake` (web, Godot) the original lowercase-with-underscores rule is unchanged.

### Overriding detection

Highest priority first:

1. **Environment** — `STUDIO_ENGINE`, `STUDIO_SRC_ROOTS`, `STUDIO_SRC_EXTS`,
   `STUDIO_DESIGN_ROOTS`, `STUDIO_ASSET_ROOTS`, `STUDIO_ASSET_NAMING`,
   `STUDIO_PRODUCTION_ROOTS` (colon-separated for list values).
2. **`.claude/studio-layout.json`** — the preferred file.
3. **`.claude/settings.json`** → `"studio": { "layout": { … } }`.

```json
{
  "engine": "unity",
  "srcRoots": ["Assets/02.Scripts"],
  "designRoots": ["Documents/Specs", "design/gdd"],
  "productionRoots": "Documents/Plan:production/sprints",
  "assetNaming": "pascal"
}
```

Keys: `engine`, `srcRoots`, `srcExtensions`, `designRoots`, `assetRoots`,
`assetNaming`, `productionRoots`. List values accept a JSON array or a
colon-separated string; without `jq` installed only the string form is readable,
and an unreadable value falls through to detection rather than to an empty
layout.

> **`jq` caveat, concretely.** Git Bash on Windows usually has no `jq`. If you
> write `"productionRoots": ["Documents"]` there, the array is unreadable and
> the default `production/sprints` is silently kept — the warning you were
> trying to silence keeps firing. Use the string form to be portable:
> `"productionRoots": "Documents:Documents/Queue"`.

`productionRoots` is what `detect-gaps.sh` Check 5 looks in before reporting
"large codebase but no production planning". It defaults to `production/sprints`
and `production/milestones`. A project that keeps its plans somewhere else — a
`Documents/Plan.md`, a work queue, an ordering board — sets this instead of
living with a false alarm every session. It changes *where the check looks*, not
whether it runs: point it at a directory that does not exist and the warning
still fires, naming that directory.

`assetNaming` accepts `pascal`, `snake` or `any` — `any` disables the naming
check entirely for projects that carry a third-party asset store tree.

### Rules for adding a hook

1. **Source the helper, guarded.** A missing helper must never fail a hook:

   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
       . "$SCRIPT_DIR/lib/detect-layout.sh"
   else
       :  # fall back to the legacy literal paths, or exit 0
   fi
   ```

2. **Select code files by extension, not by directory.** `studio_path_has_ext`
   is portable across every engine; `^src/gameplay/` is portable across none.
3. **Stay advisory by default; block with `exit 2`.** Exit 0 with a stderr
   warning for anything judgeable. Reserve blocking for unambiguous, mechanical
   failures (invalid JSON), never for style opinions — and when you do block,
   **use `exit 2`, not `exit 1`.** Only `exit 2` feeds stderr back to Claude;
   `exit 1` surfaces to the user and is otherwise ignored, so a hook that means
   "Claude must fix this" and exits 1 has produced no verdict at all. See the
   4-code contract in [`deterministic-gates.md`](./deterministic-gates.md).
4. **`grep -E` only.** Windows Git Bash ships a grep without `-P`. Enforced by
   `tests/test_hooks_layout.py::test_no_hook_uses_perl_grep`.
5. **Cover both directions in `tests/test_hooks_layout.py`** — the engine
   project must be handled *and* the generic project must be unchanged.
