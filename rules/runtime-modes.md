# Runtime Modes — Claude Alone, Codex Alone, or Split

**Global rule. Applies to every project and every domain.**

This studio now ships as two sibling packages:

| Package | Runtime | Invocation | Roles live in |
|---|---|---|---|
| `claude-code-studios` | Claude Code | `/skill-name` | `agents/*.md` (45 installed agents) |
| `codex-code-studios` | Codex | `$skill-name` | `skills/studio-orchestrator/references/roles/*.md` (loaded references) |

Same studio, two runtimes. A project can be worked by either one alone, or by
both at once. **Which of those is happening changes what this plugin should
do**, and it is not inferable from the code in front of you.

## The three modes

| Mode | Who works the project | This plugin's job |
|---|---|---|
| `claude` | Claude Code only, every line | **Full studio.** Unchanged from v0.6.4 — orchestrate all 45 agents, run every gate, own every artifact. This is the default. |
| `codex` | Codex only, every line | **Stand down.** `codex-code-studios` owns the work. Do not spawn studio agents, do not write studio artifacts, do not run phase gates. Answer questions and do explicitly requested one-off edits. |
| `split` | Both, divided by strength | **Partial studio, partitioned.** Work only the lines this runtime owns (§ Split mode), and never write a file the other runtime owns. |

## How a session knows which mode it is in

**At session start, `hooks/detect-runtime-mode.sh` prints
`RUNTIME_MODE=<claude|codex|split|invalid>`** — read that line rather than
globbing for the file yourself, the same way `PROJECT_TYPE` is read rather than
re-derived.

Its source is **`production/runtime.txt`**: line 1 is the mode, exactly one of
`claude`, `codex`, `split` (case and surrounding whitespace are forgiven; a CRLF
or a BOM does not break it). Absent or empty means `claude`.

**`invalid` is not a default — it is a stop.** Unrecognised content never falls
back to `claude`, because the two error directions are not symmetric: reading
`codex` as `claude` makes this runtime act on a project another runtime owns,
and that overwrite is invisible to both sides. Reading it the other way only
makes this runtime idle. On `invalid`, ask the user and fix the file before
touching anything.

**Do not infer the mode from ambient signals.** An `AGENTS.md` or a `.codex/`
directory in the project proves only that Codex was configured here at some
point — not that it is working this task, and not which lines it owns. This is
the same failure `production/track.txt` exists to prevent: *every detection
signal is a build artifact of a stack already chosen*, so the signal is missing
exactly when the question first matters. Ask the user and write the answer down.

`runtime.txt` and `track.txt` are independent axes. `track.txt` says *what is
being built* (game / product); `runtime.txt` says *who is building it*. Neither
one implies the other.

## Split mode — partition write ownership before starting

[`subagent-collaboration.md`](subagent-collaboration.md) § 2.1 already states the
rule for parallel subagents: *write ownership is partitioned before spawning —
two agents never get the same file, because a lost Edit is the one failure mode
that reports success.*

**Split mode is that same failure, one level up, and worse.** Two subagents at
least share an orchestrator that knows what it dispatched. Claude Code and Codex
share nothing — not a session, not a context window, not a tool log. Neither one
can see that the other just rewrote the file it is holding in memory, and the
loser of the race reports success either way.

So in `split` mode, before any work begins:

1. **Write the partition down** in `production/runtime.txt` under the mode line —
   which paths each runtime owns. Paths, not topics; a topic is not something a
   file-write can be checked against.
2. **Touch nothing outside your partition.** Not "ask first" — do not write it.
   If work requires a file the other runtime owns, report that and stop.
3. **Re-read before you edit**, every time. The file may have moved since this
   session started, and no hook will tell you.

Unpartitioned paths are unowned, and unowned means nobody writes them until the
user assigns them.

### Which strengths go to which runtime — UNDECIDED

The partition above is a mechanism, not a policy. **Who is better at what has
not been settled for this studio**, and this rule deliberately does not invent
it. Until the user fixes the split, ask for the partition per project rather
than assuming one.

When it is settled, it belongs in this section as paths, with the reasoning
attached — not as a general claim about which tool is smarter.

## Cross-repo relationship

`codex-code-studios/AGENTS.md` records a user instruction dated 2026-09-07: 확정된
공통 운영 원칙은 그 저장소에 계속 반영한다 — settled common policy is maintained
**there**. Two consequences for work done here:

- A change to shared studio policy (rules, gates, workflow catalog) is not
  finished when it lands in `claude-code-studios`. Report it as landed here and
  **pending** there; do not silently assume the sibling picked it up.
- Do not create a second canonical copy of a shared policy. Link across rather
  than fork — the sibling repo's own rule is 중복 정본을 만들지 않는다.

Note that `codex-code-studios/CLAUDE.md` is currently a verbatim copy of this
repo's older guide and advertises 45 agents that do not exist in that tree. Its
`AGENTS.md` marks it a transition-compatibility shim, not a source of truth.
**Do not trust it, and do not port anything from it back into this repo.**
