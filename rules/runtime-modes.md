# Runtime Modes — Codex Is a Subagent (legacy: Codex Alone, Split)

**Global rule. Applies to every project and every domain.**

## Codex is a subagent of this studio (2026-11-15)

> 사장님 원문: *«이 프로젝트 자체는 클로드 코드 스튜디오라서 코덱스는 클로드 코드
> 스튜디오에서 코덱스 CLI를 통해서 여러 가지 일을 하는 방식으로 지금 여러
> 프로젝트에서 진행 중이거든. 그 부분만 빼고 코덱스를 직접적으로 뭔가 하는 건
> 없어.»*

**This is the operating model.** Claude Code runs the studio — orchestration,
gates, artifacts, the sprint loop. Codex does not run a studio of its own; it is
called **from here**, through the Codex CLI, as one more worker. So in practice
every project is mode `claude`, and the `codex` / `split` modes below are
**deprecated** (§ The three modes).

### How to call it

Through the `codex:codex-rescue` agent (Agent tool) — it forwards one task to the
Codex CLI and returns its output. A bare `codex exec` in Bash is the fallback when
that plugin is not installed. Either way:

- **Pick the model for the task, and pass it explicitly** (`--model`, `--effort`).
  The forwarder leaves both unset unless told, which runs every task on the
  default. If the user keeps a difficulty→model table (their global
  `CLAUDE.md`), follow it; if not, leave the default and say so.
- **The prompt is self-contained and carries file links** — Codex sees none of
  this conversation, and reads only its own contract file unprompted.
- **Say "read-only" unless Codex is the one making the change.** The forwarder
  adds `--write` by default. When Codex does write, it owns those files: nothing else (you, another agent)
  edits them until it returns — [`subagent-collaboration.md`](subagent-collaboration.md) § 2.1.

### When to hand it work

| Use Codex for | Why |
|---|---|
| A bounded implementation task with its files named | Parallel hands, partitioned by path like any subagent |
| A second diagnosis when the first pass is stuck | A different model does not repeat this context's conclusions |
| The R3+ separate review ([`verify-route.md`](verify-route.md) § 4), read-only | The reviewer must not be the author — a different model is the strongest "not the author" available |

Not for: anything a few tool calls finish here, R4 actions, or a step whose
result this turn needs before it can continue.

### What comes back is a subagent's report

Codex output is held to the same rule as any agent's: it describes intent, not
results. **Read the changed files and run the gates before reporting done.** A
Codex review returns findings; you decide what to fix.

This studio now ships as two sibling packages:

| Package | Runtime | Invocation | Roles live in |
|---|---|---|---|
| `claude-code-studios` | Claude Code | `/skill-name` | `agents/*.md` (45 installed agents) |
| `codex-code-studios` | Codex | `$skill-name` | `skills/studio-orchestrator/references/roles/*.md` (loaded references) |

Same studio, two runtimes. A project can be worked by either one alone, or by
both at once. **Which of those is happening changes what this plugin should
do**, and it is not inferable from the code in front of you.

## The three modes

> **`codex` and `split` are deprecated** (next release after v0.6.7). They describe
> Codex running `codex-code-studios` as a second, peer runtime, which is no longer
> how any project is worked. The hook still recognises both and prints a
> deprecation line; they stay for at least one minor version so a project that
> still declares one is not misread. A project on either should confirm with the
> user and set `production/runtime.txt` to `claude` (or delete it). Everything
> below about them is kept for those projects only.

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

**The partition says who writes, not who checks.** If one runtime's R3+ work is
to be reviewed by the other ([`verify-route.md`](verify-route.md) § 4 — the
reviewer is not the author), add a `review:` line to the partition, e.g.
`review: claude reviews codex`. The hook echoes it with the rest of the
partition. Without that line, review stays inside the authoring runtime — a
separate subagent plus the script gates — and R4 goes to the user, exactly as in
single-runtime mode.

### Memory is a repository file, not a runtime feature

Claude Code's auto memory (`~/.claude/projects/*/memory/`) lives outside the
repository, so **Codex cannot read it**. In a split project anything recorded
there is a rule only one of the two workers obeys. StarDiver found 171 owner
instructions and decisions sitting in it, and its `CLAUDE.md` cited memory
entries by name in seven places — evidence the Codex side had no way to open
(inbox 2026-10-01). Codex's own memories feature has the same problem in the
other direction.

So in `split` mode, write everything worth keeping into the repository, by kind:

| Kind | Home |
|---|---|
| Standing rule for both runtimes | the contract pair — `CLAUDE.md` ↔ `AGENTS.md`, same content in both |
| Settled call | the pinned-decision section ([`decision-lifecycle.md`](decision-lifecycle.md)) or an ADR |
| Request from one runtime to the other | the project's inbox file |
| Where work stands | `production/session-state/active.md` ([`work-records.md`](work-records.md)) |
| Any other fact | a shared index document the contract pair links to |

Then turn the per-runtime memory off so nothing new lands there:
`"autoMemoryEnabled": false` in the project's `.claude/settings.json`, and
`memories = false` under `[features]` in the Codex config. That is the user's
settings file — propose it, do not write it unasked.

**When handing work to the other runtime, put file links in the instruction.**
The only thing either side reads without being told is its own contract file;
"see the decision from last week" points at nothing.

### Which strengths go to which runtime

Superseded by § Codex is a subagent — the split is now per task, decided by the
orchestrator when it hands work to Codex, not per project as a path partition.

## Cross-repo relationship

**Settled studio policy lives here, in `claude-code-studios`** (2026-11-15). The
earlier instruction in `codex-code-studios/AGENTS.md` (2026-09-07: 확정된 공통
운영 원칙은 그 저장소에 반영한다) was written when Codex ran its own studio; that
file now carries a dated note pointing back here (codex-code-studios 19c3e70).

- A policy change is finished when it lands here. Do not report it as
  "pending in the sibling" — the sibling no longer runs any project.
- Do not port new policy into `codex-code-studios`, and do not create a second
  canonical copy of anything. Link, do not fork.

Note that `codex-code-studios/CLAUDE.md` is currently a verbatim copy of this
repo's older guide and advertises 45 agents that do not exist in that tree. Its
`AGENTS.md` marks it a transition-compatibility shim, not a source of truth.
**Do not trust it, and do not port anything from it back into this repo.**
