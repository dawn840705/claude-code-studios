# Rules Reference

## Global Rules (always active, path-independent)

These apply to every project using the plugin, regardless of which files are being edited:

| Rule File | Enforces |
| ---- | ---- |
| `verify-route.md` | Routes **verification** by reversibility, the axis `route-hint.md` does not cover: R1 (one edit undoes it) → the file's own gate · R2 (revert undoes it) → gates + review · R3 (needs coordination) → gates + a *separate* reviewing subagent + `/gate-check` · **R4 (irreversible, or costs users) → never unattended**. Uncertainty escalates; de-escalation must state a reason; the route is reported in the output |
| `self-loop.md` | Quality-gated deliverables are never one-shot: plan → execute → score (script exit code first, model grading only for the rest) → judge, until all criteria ≥ 8. Guards three failure modes: score inflation, runaway loops (max 5 iterations, stall detection), and **rewriting without evidence** (§ 2.1 — no defect ticket, no edit). Terminates DONE / FAILED / BLOCKED; the policy axis (`verify_policy.py`) can block regardless of scores. Executable form: `/self-loop` |
| `subagent-collaboration.md` | Multi-subagent parallel collaboration pattern for broad/deep design decisions — when to fan out, prompt requirements, result integration, meeting minutes |
| `route-hint.md` | Pick a route before spawning: **light** (orchestrator handles it, 0 agents) / **standard** (1 specialist) / **heavy** (team fan-out + gates). Savings come from fewer calls, not a cheaper model; splitting is the last resort. Measured upstream: 7-chunk fan-out 610K tokens vs. 134K single call at equal quality |
| `lesson-capture.md` | Every project doubles as teaching material. 5 standing triggers (repeated trap ×2, design hole exposed by feedback, assumption overturned, tooling pitfall, design pattern locked by data) prompt a lesson entry in `Documents/Lessons/`. Executable form: `/lesson-log`, `/lesson-review` |

## Path-Specific Rules

Rules in `.claude/rules/` are automatically enforced when editing files in matching paths:

| Rule File | Path Pattern | Enforces |
| ---- | ---- | ---- |
| `gameplay-code.md` | `src/gameplay/**` | Data-driven values, delta time, no UI references |
| `engine-code.md` | `src/core/**` | Zero allocs in hot paths, thread safety, API stability |
| `ai-code.md` | `src/ai/**` | Performance budgets, debuggability, data-driven params |
| `network-code.md` | `src/networking/**` | Server-authoritative, versioned messages, security |
| `ui-code.md` | `src/ui/**` | No game state ownership, localization-ready, accessibility |
| `design-docs.md` | `design/gdd/**` | Required 8 sections, formula format, edge cases |
| `narrative.md` | `design/narrative/**` | Lore consistency, character voice, canon levels |
| `data-files.md` | `assets/data/**` | JSON validity, naming conventions, schema rules |
| `test-standards.md` | `tests/**` | Test naming, coverage requirements, fixture patterns |
| `prototype-code.md` | `prototypes/**` | Relaxed standards, README required, hypothesis documented |
| `shader-code.md` | `assets/shaders/**` | Naming conventions, performance targets, cross-platform rules |
