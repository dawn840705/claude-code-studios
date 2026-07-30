# Rules Reference

## Global Rules (always active, path-independent)

These apply to every project using the plugin, regardless of which files are being edited:

| Rule File | Enforces |
| ---- | ---- |
| `self-loop.md` | Quality-gated deliverables are never one-shot: plan → execute → score (1-10, evidence-cited) → judge, until all criteria ≥ 8. Guards against score inflation and runaway loops (max 5 iterations, stall detection). Executable form: `/self-loop` |
| `subagent-collaboration.md` | Multi-subagent parallel collaboration pattern for broad/deep design decisions — when to fan out, prompt requirements, result integration, meeting minutes |
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
