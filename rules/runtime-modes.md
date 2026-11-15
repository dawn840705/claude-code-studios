# Runtime Modes — Codex Is a Subagent; Split Is Its Write Boundary

**Global rule. Applies to every project and every domain.**

## Codex is a subagent of this studio (2026-11-15)

> 사장님 원문: *«이 프로젝트 자체는 클로드 코드 스튜디오라서 코덱스는 클로드 코드
> 스튜디오에서 코덱스 CLI를 통해서 여러 가지 일을 하는 방식으로 지금 여러
> 프로젝트에서 진행 중이거든. 그 부분만 빼고 코덱스를 직접적으로 뭔가 하는 건
> 없어.»*

**This is the operating model.** Claude Code runs the studio — orchestration,
gates, artifacts, the sprint loop. Codex does not run a studio of its own; it is
called **from here**, through the Codex CLI, as one more worker. StarDiver has
worked this way since 2026-11-01 (Claude = 총괄·기획·검토, Codex = 개발·디자인 via
`codex exec`).

### How to call it

Field-tested in StarDiver (its archived contract § v7.9-c, 2026-09-23):

| Work | Call |
|---|---|
| Write — implementation, scenes, assets | `codex exec -C <project> -m <model> "<prompt>" < /dev/null`, as a background Bash job. **Close stdin** — left open, Codex waits for input and stalls (15 minutes lost on 9-23). |
| Read — review, cross-check, research | The codex plugin's companion: `codex-companion.mjs task --background "<prompt>"`, then `status` / `result`; or `review` / `adversarial-review`. |

- **Do not call it through the `codex:codex-rescue` subagent.** When that
  subagent ends, the Codex turn ends with it (`turn_aborted`, 9-23 incident).
- **Pick the model for the task and pass it explicitly.** Left unset, every task
  runs on the default. If the user keeps a difficulty→model table (their global
  `CLAUDE.md`), follow it; if not, use the default and say so.
- **The prompt is self-contained and carries file links** — Codex sees none of
  this conversation and reads only its own contract file unprompted. Name the
  write pathspec, the done criteria, and where the result goes.
- **Keep Codex's own studio plugin off.** With `codex-code-studios` enabled in
  `~/.codex/config.toml`, every `codex exec` run loads its hooks and skills, and
  its hook reads an absent `runtime.txt` as "Codex runs the full studio". Set
  `[plugins."codex-code-studios@code-studios"] enabled = false` on each machine
  (home computer: done 2026-11-16). That is the user's config — propose it, do
  not write it unasked.
- **If it seems stuck, read its log instead of guessing** —
  `~/.codex/sessions/<date>/rollout-*.jsonl` (`turn_aborted`,
  `rate_limit_reached_type`).

### When to hand it work

| Use Codex for | Why |
|---|---|
| Implementation inside the paths it owns (§ Split mode) | The project's write boundary says who touches product code |
| A bounded implementation task with its files named | Parallel hands, partitioned by path like any subagent |
| A second diagnosis when the first pass is stuck | A different model does not repeat this context's conclusions |
| The R3+ separate review ([`verify-route.md`](verify-route.md) § 4), read-only | The reviewer must not be the author — a different model is the strongest "not the author" available |

Not for: anything a few tool calls finish here, R4 actions, or a step whose
result this turn needs before it can continue.

### What comes back is a subagent's report

Codex output is held to the same rule as any agent's: it describes intent, not
results. **Read the returned diff and run the gates before reporting done.** A
Codex review returns findings; you decide what to fix. While Codex is writing,
nothing else edits its files ([`subagent-collaboration.md`](subagent-collaboration.md) § 2.1).

## The three modes

| Mode | What it means now | This plugin's job |
|---|---|---|
| `claude` | Claude Code runs the studio; Codex, if used, takes tasks case by case | **Full studio.** Orchestrate the agents, run every gate, own every artifact. This is the default. |
| `split` | Claude Code runs the studio, and **Codex owns a declared set of paths** (typically product code and assets) | **Full studio, but never write a path Codex owns** — hand that work to Codex (§ How to call it) and review what comes back. § Split mode. |
| `codex` | Codex runs a studio of its own (`codex-code-studios`) | **Deprecated** (next release after v0.6.7) — no project is worked this way any more. The hook still parses it and flags it; it stays for at least one minor version. **Stand down**: answer questions and do explicitly requested one-off edits only. Confirm with the user and change the file. |

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
   If work needs a path Codex owns, hand it to Codex with that pathspec
   (§ How to call it); a path neither side owns, report and stop.
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

Per project, written as paths in `runtime.txt`. The one settled example:
StarDiver (2026-11-01) gives Codex `Assets/**`, `ProjectSettings/**`,
`Packages/**` and most of `Tools/**`, and keeps `Documents/**` and `.claude/**`
for Claude — Claude plans, orders and reviews; it does not edit product code.

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
