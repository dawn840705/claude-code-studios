# Codex Hook Input/Output Schemas

Codex sends a JSON object on stdin. Common fields include the event name,
session metadata, `tool_name`, and `tool_input`. Hooks must use the payload for
the event they match and return valid JSON when they want to add model context.

## PreToolUse: command execution

Codex may report the command tool as `exec_command`; the `Bash` matcher alias is
kept for compatibility.

```json
{
  "tool_name": "exec_command",
  "tool_input": {
    "command": "git commit -m 'feat: add player health system'"
  }
}
```

Exit 0 allows the tool. Exit 2 plus stderr blocks it. Advisory text on an
allowed call should be valid JSON, for example:

```json
{"systemMessage":"Review the protected-branch checklist before pushing."}
```

## PostToolUse: apply_patch

Codex's native file editor reports `tool_name: "apply_patch"`. One patch can
contain multiple file operations, so validators must extract every `Add File`,
`Update File`, `Delete File`, and `Move to` header from `tool_input.command`.

```json
{
  "tool_name": "apply_patch",
  "tool_input": {
    "command": "*** Begin Patch\n*** Update File: src/gameplay/health.gd\n*** Add File: assets/data/enemy_stats.json\n*** End Patch"
  }
}
```

The `Write`, `Edit`, and `MultiEdit` aliases may still provide
`tool_input.file_path`; `hooks/lib/hook-io.sh` supports both shapes.

PostToolUse advisory context uses:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "The changed asset name violates the project convention."
  }
}
```

Exit 2 plus stderr replaces the tool result with a blocking error for an
unambiguous mechanical failure such as invalid JSON.

## SessionStart

Stdout is added as initial session context. Code Studios uses this to report
the project track, stage hints, documentation gaps, and recovery state.

## PreCompact and PostCompact

Plain stdout is ignored for these events. Return a JSON `systemMessage` so the
checkpoint or recovery instruction reaches Codex.

## SubagentStart and SubagentStop

The payload includes `agent_id` and `agent_type`. Code Studios records those in
`production/session-logs/agent-audit.log`. `SubagentStop` returns `{}` on a
successful exit because the event expects JSON output.

## SessionEnd

Runs on actual session shutdown. Code Studios uses it for session logging. Do
not map this behavior to `Stop`, which fires at the end of individual turns.

## Exit codes

| Exit | Meaning |
| --- | --- |
| `0` | Allow/success; stdout must match the event's JSON contract when present |
| `2` | Block the matched operation and surface stderr to Codex |
| other | Hook failure; do not use as a policy verdict |

Prefer `jq` for parsing, then Python's standard JSON parser, with a guarded
fallback. Normalize Windows path separators before matching paths.
