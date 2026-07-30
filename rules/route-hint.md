# Route Hint — Call-Count Routing

**Global rule. Applies to every project and every domain.**

`CLAUDE.md` already says *"don't spawn agents just because they exist — if the
task is simple, handle it directly."* That is the right instinct with no way to
act on it: the decision comes down to the orchestrator's feel for the task.

Upstream measurement puts a number on what that feel costs. Rewriting a
10,000-character text as 7 chunks burned **610K tokens**. The same text in a
single call: **134K, at equal quality.** A 4.5× difference, and the cause was
not model choice — it was **reloading the rulebook and the diagnosis into every
chunk.**

A studio with 45 agents, each reloading its own context, has exactly that
structure.

## Two principles

**Savings come from fewer calls, not from a cheaper model.** Never silently
downgrade a model tier to save money — model choice belongs to the user. Cut
the number of calls instead. A single Opus call routinely beats five Haiku
calls on both cost and quality, because each of those five re-reads the same
context.

**Splitting is the last resort.** Prefer one call. Split only when a hard limit
forces it, and when you do, make sure the shared context is loaded once — not
once per piece.

## The three routes

Pick a route before spawning anything.

| Route | Signals | Action |
|---|---|---|
| **light** | 1-2 files, single domain, repeating an existing pattern | Orchestrator handles it directly. **Zero agents spawned.** |
| **standard** | Single domain, but a genuine design judgment is needed | One specialist agent |
| **heavy** | Multiple domains, or a hard-to-reverse change, or evidence is explicitly required | Team fan-out + gates |

When torn between two routes, take the lighter one. Escalating costs one more
call; over-fanning-out costs N.

## Escalate on signals, not on nerves

Move up a route when a concrete signal says so:

- The work touches a boundary you cannot see the far side of
- The change is hard to undo (migrations, deletions, published output)
- The user asked for evidence, review, or a second opinion
- A gate already failed and you are reworking (see
  [`self-loop.md`](self-loop.md))

Do **not** escalate because the task merely sounds important, or to look
thorough. Fan-out that produces four summaries of the same file is not
diligence — it is the 4.5× above.

## Reference implementation

`scripts/prepare_monolith_input.py` routes Korean rewriting deterministically:

```python
ROUTE_HEAVY_MIN_CHARS = 15000   # over this  → heavy
ROUTE_HEAVY_MIN_TELLS = 8       # risk=high AND tells >= 8 → heavy
ROUTE_LIGHT_MAX_TELLS = 2       # tells <= 2 AND risk in (low, medium) → light
# otherwise → standard
```

Note what it leaves out. Z-scores and density metrics are **deliberately
excluded** because the 70 baseline cells backing them are placeholders. An
unvalidated signal is kept out of the decision entirely rather than used with a
caveat. Copy that discipline: if you cannot trust a signal, do not let it pick
the route.

## Related

- [`self-loop.md`](self-loop.md) — iterate until criteria pass; route-hint
  decides how much machinery each iteration gets
- [`docs/deterministic-gates.md`](../docs/deterministic-gates.md) — heavy-route
  gates judge by exit code, not by self-assessment
- [`subagent-collaboration.md`](subagent-collaboration.md) — how to fan out
  once you have decided on heavy
