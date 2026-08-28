# Token Efficiency Rules

Six lightweight rules to keep agent collaboration efficient over long-running game projects. Adopt as-is or fork — they assume Claude Code-style workflows but generalise to any agent harness.

---

## R1 — Commit messages: 5-15 lines

Structure:
```
<title — 1 line, imperative voice>

<core change — 3 bullets max, what changed and why>
<impact — 1-2 lines, what the user / team / build sees>
<next — 1 line, what comes after this commit>
```

Skip 50-line auto-generated bodies (HEREDOC dumps from agents). They cost reader time and rarely add value over a focused 5-15 line summary. If the change genuinely requires more explanation, write it in the PR description, not the commit body.

**Anti-pattern:** Commit messages that recap every file diff line-by-line, or that quote large portions of changed code.

---

## R2 — Meeting notes: ~80 lines for daily / per-topic preserves analysis

- **Daily roll-up** (`YYYY-MM-DD.md`) — keep ≤ 80 lines. Decisions, carryovers, links to commits — nothing more. Permanent insights become **separate memory files**, one-off observations live inline in commit messages.
- **Topic-specific** (`YYYY-MM-DD-<topic>.md`) — can be longer. **Preserve rejected-option analysis** including the reasoning that ruled them out — a future-you may revisit and need that context. Don't compress topic meetings into the daily roll-up.
- **Every meeting** has a header metadata table: date / facilitator / topic / decision status / cross-reference links.

---

## R3 — Bulk operations: skip mid-progress reports, verify once at the end

For changes spanning 5+ commits or 5+ files:
- **Don't** narrate each step ("now I'll do X", "now I'll do Y").
- **Do** run a single end-of-batch verification: build / test suite / smoke check / agent-only mid-progress (no user-facing report).

**Exception — keep mid-progress reports when:**
- Compile-risk territory (5+ new files in a tightly-typed language, plugin manifest changes that affect every session, hook config changes).
- Decision-authority territory (any choice the user owns — name / scope / spend / public-facing copy).

In those cases, surface a check-in even mid-batch. The cost of a 5-line "here's what I'm about to do" is much lower than the cost of an unwound batch.

---

## R4 — File reads: use parallel `Read` / `Grep` for independent inputs

When you need to read N files to make a decision, issue them as parallel tool calls in one message. This keeps the agent context warm and reduces wall-clock time. Sequential reads are only needed when each file's content informs which file to read next.

---

## R5 — Memory writes: permanent value only

Save to durable agent memory **only** when:
- The decision survives this session (rule, naming convention, tone filter, deferred-decision trigger).
- Future-you (or a different agent) needs to apply it without re-derivation.
- The information is not derivable from the codebase (i.e. not "this function does X" — that's just code).

Anything else lives in the commit message, the meeting note, or the inline `// ` comment near the affected code.

**Anti-pattern:** memory entries that summarise a single PR's changes. Use the PR description.

---

## R6 — User intent acknowledgments: 1-line, then act

When the user provides clear, executable intent ("OK", "go", "approve", "all of it", "reject"), respond with:
- **One short ack line** (`OK — proceeding`).
- **Immediately** start the action.

Don't:
- Re-summarize the user's message back at them.
- Re-list every step the user just approved.
- Ask follow-up clarifications when the original request was unambiguous.

This rule pairs with **R3** — many bulk operations begin with a single "OK" and just need to start running.

For paid API calls and other gated actions, this rule is **constrained by the gate** (e.g. `/api-cost-gate`) — the user's "OK" still needs to satisfy whatever pre-flight disclosure the gate requires.

---

## Adoption notes

- Adopt these rules as a project-level memory or in your `CLAUDE.md` — pin them so every agent session inherits them.
- Customize the line counts (R1, R2) to your team's preference. The principle (lean over verbose) matters more than the exact thresholds.
- These rules are **pull-based** — they only fire when an agent is making a decision about how much to write / report. They don't replace standard linting, testing, or review.

---

## Origin

Distilled from real production logs of Claude Code sessions on a multi-month game project. Each rule corrects a specific pattern that *cost reader time without delivering proportionate value*. R1-R6 are listed in roughly the order each pattern surfaced.
