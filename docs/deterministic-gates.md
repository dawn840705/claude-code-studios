# Deterministic Gates

## The problem this solves

Every quality gate in this plugin used to end the same way: an LLM looked at
something and declared PASS or FAIL. `/gate-check` globs for files and writes a
verdict in prose. `/smoke-check` runs a test suite and then *reads its own
output* to decide. `/self-loop` grades each criterion 1-10 — by scoring itself.

`/self-loop` already knows this is dangerous and defends against it: 8+ requires
quoted evidence, all-9s on round one means the criteria were too loose, five
iterations max, stop after two stalled rounds. Those are good defenses. They are
also all the same kind of defense — **asking the model to doubt itself.**

The upstream project this pattern came from (`epoko77-ai/im-not-ai`, see
[`NOTICE.md`](../NOTICE.md)) hit the wall and drew a different conclusion. Their
note on retiring the LLM-scored version: *"LLM arithmetic is unreliable, so the
over-rewrite guard itself was soft."* Their fix was not a better prompt. It was
to move the verdict **out of the model** and make a script's exit code the
source of truth.

## The contract

A deterministic gate is a script that exits with one of four codes. Nothing
else is a gate.

| Code | Meaning | What the caller must do |
|---|---|---|
| `0` | **Converged** — every axis passed | Proceed |
| `1` | **Warning** — a soft threshold was crossed | Report it; a human decides |
| `2` | **Abort** — a hard threshold was crossed | Stop. Do not adopt the output |
| `3` | **Cannot judge** — the gate itself failed to run | Never treat as pass |

Code `3` is the one people get wrong. A gate that could not run has produced no
verdict, and "no verdict" is not "pass". If a gate exits 3, say so and stop —
do not fall back to reading the output and guessing.

**The reference implementation is [`scripts/verify_gates.py`](../scripts/verify_gates.py).**
It judges four axes for Korean rewriting (character change rate, target
attainment, antithesis wipeout, golden checks + number injection) and reports a
fifth (sentence touch rate) without letting it affect the exit code — a signal
that is merely informative must not move the verdict.

**[`scripts/check_phase.py`](../scripts/check_phase.py) applies the same
contract to workflow-phase completion.** The catalog
(`docs/workflow-catalog.yaml`, schema v2) declares artifact globs and explicit
`depends_on` per step; the script evaluates them and exits `0` (phase complete)
/ `1` (in progress) / `2` (dependency violation — a completed step's required
dependency is missing) / `3` (cannot judge: catalog unreadable or track
ambiguous). `/help` runs it in its context block and `/project-stage-detect`
runs it as its first step — both carry its verdicts forward instead of
re-globbing. Model-side artifact checks remain only as the documented fallback
for exit 3, and must be labeled as such. CI validates the catalog schema with
`check_phase.py --validate` (broken globs, dangling `depends_on`, missing
`required:` fields are unmergeable).

## Rules for callers

**The exit code overrides the model.** If the script says FAIL, it is FAIL, no
matter how the output reads to you. You may explain the failure. You may not
overturn it.

**Never re-derive the verdict from stdout.** Parsing the runner's text to decide
PASS/FAIL puts the judgment back in the model, which is the thing this document
exists to prevent. Read the exit code. Use the text only to *explain* it.

**A gate that cannot run is not a gate that passed.** Distinguish these three
states explicitly and never collapse them: PASS (ran, exit 0) · FAIL (ran,
non-zero) · NOT RUN (did not run). `/smoke-check` treats NOT RUN as PASS WITH
WARNINGS by design — that is a deliberate, documented policy for environments
without an engine binary, not license to guess.

**Say which gate decided.** Every verdict should name the script and the code:
`verify_gates.py → exit 2 (ABORT: change rate 54% ≥ 50%)`. A verdict with no
traceable source is indistinguishable from an opinion.

## What stays qualitative

Not everything can be a script, and pretending otherwise is its own failure.

- **`/gate-check` is intentionally excluded.** It judges whether an artifact
  exists *and says something meaningful*, which is irreducibly qualitative. Its
  verdict is documented as advisory — the user decides. Forcing code judgment
  in would break the design.
- **Readability, tone, and "does this argument hold"** stay with the model.
- Within `/self-loop`, criteria split into two kinds. Ask of each: *can this be
  judged by a script?* If yes, write the script and let its exit code set the
  score. If no, score it 1-10 with cited evidence as before.

The goal is not to eliminate model judgment. It is to stop the model from
grading things a script could have measured.

## Generated files are gated too

`reference/quick-rules.md` and `reference/diagnosis-rules.md` are **built** from
`reference/ai-tell-taxonomy.md` (the SSOT). Editing them by hand desyncs the
runtime silently — the file looks fine and the build is wrong.

Two CI checks make that unmergeable:

```bash
python3 scripts/build_quick_rules.py --check      # exit 0 = in sync
python3 scripts/build_diagnosis_rules.py --check
```

Same contract: the exit code is the verdict. If you need to change those files,
change the taxonomy and rebuild.

## Adding a gate

1. Exit `0` / `1` / `2` / `3`. No other codes.
2. Put every threshold in a named constant at the top of the file. A threshold
   buried in an expression cannot be reviewed.
3. Print *why* — the caller has to explain the verdict to a human.
4. Keep informative-only signals out of the exit code (see P4 in
   `verify_gates.py`).
5. Standard library only. The vendored runtime has zero third-party
   dependencies and that is worth keeping.
6. Add it to [`.github/workflows/test.yml`](../.github/workflows/test.yml).
   A gate that does not run in CI will rot.
