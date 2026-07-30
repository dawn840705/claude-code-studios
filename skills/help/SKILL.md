---
name: help
description: "Analyzes what is done and the users query and offers advice on what to do next. Use if user says what should I do next or what do I do now or I'm stuck or I don't know what to do"
argument-hint: "[optional: what you just finished, e.g. 'finished design-review' or 'stuck on ADRs']"
user-invocable: true
allowed-tools: Read, Glob, Grep
context: |
  !echo "=== Live Project State ===" && echo "Stage: $(cat production/stage.txt 2>/dev/null | tr -d '[:space:]' || echo 'not set')" && echo "Latest sprint: $(ls -t production/sprints/*.md 2>/dev/null | head -1 || echo 'none')" && echo "Session state: $(head -5 production/session-state/active.md 2>/dev/null || echo 'none')" && echo "=== Deterministic Phase Check (check_phase.py) ===" && python3 "${CLAUDE_PLUGIN_ROOT:-.claude}/scripts/check_phase.py" --catalog "${CLAUDE_PLUGIN_ROOT:-.claude}/docs/workflow-catalog.yaml" 2>&1 || true
model: haiku
---

# Studio Help — What Do I Do Next?

This skill is read-only — it reports findings but writes no files.

This skill figures out exactly where you are in the game development pipeline and
tells you what comes next. It is **lightweight** — not a full audit. For a full
gap analysis, use `/project-stage-detect`.

---

## Step 0: Read the Deterministic Phase Check (context block)

The context block above already ran `scripts/check_phase.py` — the deterministic
gate for phase completion (see `docs/deterministic-gates.md`). Its output is the
verdict. **Do not re-derive step completion by globbing yourself.**

Read from its output:
- `track=` and `phase=` — which track (game/product) and phase the project is in
- `[x]` complete / `[ ]` incomplete / `[?]` MANUAL / `[-]` untrackable, per step
- `next required step:` — the blocker
- `VERDICT:` and `EXIT:` — the exit-code contract:
  `0` phase complete · `1` in progress · `2` dependency violation (a step was
  skipped — surface this prominently) · `3` cannot judge

**Only if `EXIT: 3` appears** (catalog unreadable, ambiguous track): fall back
to the manual artifact checks in Step 4, and say explicitly that completion was
judged by the model, not the gate. If the track was ambiguous, ask the user
(game or app/web/service?) — never guess.

---

## Step 1: Read the Catalog

Read `.claude/docs/workflow-catalog.yaml` for step **descriptions, commands, and
ordering** (schema v2: `tracks:` → game / product → `phases:`). Use the track
reported by check_phase.py — game projects follow the game track, web/mobile/
service projects follow the product track. The catalog explains *what* each step
is; completion *status* comes from Step 0.

---

## Step 1b: Find Skills Not in the Catalog

After reading the catalog, Glob `.claude/skills/*/SKILL.md` to get the full list
of installed skills. For each file, extract the `name:` field from its frontmatter.

Compare against the `command:` values in the catalog. Any skill whose name does
not appear as a catalog command is an **uncataloged skill** — still usable but not
part of the phase-gated workflow.

Collect these for the output in Step 7 — show them as a footer block:

```
### Also installed (not in workflow)
- `/skill-name` — [description from SKILL.md frontmatter]
- `/skill-name` — [description]
```

Only show this block if at least one uncataloged skill exists. Limit to the 10
most relevant based on the user's current phase (QA skills in production, team
skills in production/polish, etc.).

---

## Step 2: Determine Current Phase

**Normal path:** use the `phase=` value from check_phase.py (Step 0) — it
already applied stage.txt-first, artifact-inference-second, for the right track.

**Fallback (EXIT: 3 only):** check in this order:

1. **Read `production/stage.txt`** — if it exists and has content, this is the
   authoritative phase name. Map it to a catalog phase key for the active track:
   - Game: "Concept" → `concept` · "Systems Design" → `systems-design` ·
     "Technical Setup" → `technical-setup` · "Pre-Production" → `pre-production` ·
     "Production" → `production` · "Polish" → `polish` · "Release" → `release`
   - Product: "Discovery" → `discovery` · "Architecture" → `architecture` ·
     "Build" → `build` · "Hardening" → `hardening` · "Ship" → `ship` ·
     "Growth & Operate" → `growth`

2. **If stage.txt is missing**, infer phase from artifacts (most-advanced match wins):
   - Game: `src/` has 10+ source files → `production` · `production/stories/*.md` →
     `pre-production` · `docs/architecture/adr-*.md` → `technical-setup` ·
     `design/gdd/systems-index.md` → `systems-design` · `design/gdd/game-concept.md`
     → `concept` · nothing → `concept`
   - Product: `src/` has 10+ source files → `build` · `production/epics/` →
     `build` · `docs/architecture/adr-*.md` → `architecture` ·
     `product/prd/prd-*.md` → `discovery` · nothing → `discovery`

---

## Step 3: Read Session Context

Read `production/session-state/active.md` if it exists. Extract:
- What was most recently worked on
- Any in-progress tasks or open questions
- Current epic/feature/task from STATUS block (if present)

This tells you what the user just finished or is stuck on — use it to personalize
the output.

---

## Step 4: Check Step Completion for the Current Phase

**Normal path:** completion per step was already decided in Step 0 by
check_phase.py — carry those verdicts forward unchanged. The subsections below
are (a) the fallback when `EXIT: 3` appeared, and (b) the special cases the
script does not cover (sprint-status.yaml, repeatable-step nuance).

### Artifact-based checks (fallback only — EXIT: 3)

If the step has `artifact.glob`:
- Use Glob to check if files matching the pattern exist
- If `min_count` is specified, verify at least that many files match
- If `artifact.pattern` is specified, use Grep to verify the pattern exists in the matched file
- **Complete** = artifact condition is met
- **Incomplete** = artifact is missing or pattern not found

If the step has `artifact.note` (no glob):
- Mark as **MANUAL** — cannot auto-detect, will ask user

If the step has no `artifact` field:
- Mark as **UNKNOWN** — completion not trackable (e.g. repeatable implementation work)

### Special case: production phase — read `sprint-status.yaml`

When the current phase is `production`, check for `production/sprint-status.yaml`
before doing any glob-based story checks. If it exists, read it directly:

- Stories with `status: in-progress` → surface as "currently active"
- Stories with `status: ready-for-dev` → surface as "next up"
- Stories with `status: done` → count as complete
- Stories with `status: blocked` → surface as blocker with the `blocker` field

This gives precise per-story status without markdown scanning. Skip the glob
artifact check for the `implement` and `story-done` steps — the YAML is authoritative.

### Special case: `repeatable: true` (non-production)

For repeatable steps outside production (e.g. "System GDDs"), the artifact
check tells you whether *any* work has been done, not whether it's finished.
Label these differently — show what's been detected, then note it may be ongoing.

---

## Step 5: Find Position and Identify Next Steps

From the completion data, determine:

1. **Last confirmed complete step** — the furthest completed required step
2. **Current blocker** — the first incomplete *required* step (this is what the
   user must do next)
3. **Optional opportunities** — incomplete *optional* steps that can be done
   before or alongside the blocker
4. **Upcoming required steps** — required steps after the current blocker
   (show as "coming up" so user can plan ahead)

If the user provided an argument (e.g. "just finished design-review"), use that
to advance past the step they named even if the artifact check is ambiguous.

---

## Step 6: Check for In-Progress Work

If `active.md` shows an active task or epic:
- Surface it prominently at the top: "It looks like you were working on [X]"
- Suggest continuing it or confirm if it's done

---

## Step 7: Present Output

Keep it **short and direct**. This is a quick orientation, not a report.

```
## Where You Are: [Phase Label]

**In progress:** [from active.md, if any]

### ✓ Done
- [completed step name]
- [completed step name]

### → Next up (REQUIRED)
**[Step name]** — [description]
Command: `[/command]`

### ~ Also available (OPTIONAL)
- **[Step name]** — [description] → `/command`
- **[Step name]** — [description] → `/command`

### Coming up after that
- [Next required step name] (`/command`)
- [Next required step name] (`/command`)

---
Approaching **[next phase]** gate → run `/gate-check` when ready.
```

**If check_phase.py reported `EXIT: 2` (dependency violation):** lead with it,
before the normal layout — name the completed step, the skipped required
dependency, and the command that fills the gap:

```
⚠ Dependency violation: [step] is done but its required dependency
  [dep-step] is missing. Run `[/dep-command]` first — later artifacts built on
  a skipped step tend to need rework.
```

**Formatting rules:**
- `✓` for confirmed complete
- `→` for the current required next step (only one — the first blocker)
- `~` for optional steps available now
- Show commands inline as backtick code
- If a step has no command (e.g. "Implement Stories"), explain what to do instead of showing a slash command
- For MANUAL steps, ask the user: "I can't tell if [step] is done — has it been completed?"

Verdict: **COMPLETE** — next steps identified.

---

## Step 8: Gate Warning (if close)

After the current phase's steps, check if the user is likely approaching a gate:
- If all required steps in the current phase are complete (or nearly complete),
  add: "You're close to the **[Current] → [Next]** gate. Run `/gate-check` when ready."
- If multiple required steps remain, skip the gate warning — it's not relevant yet.

---

## Step 9: Escalation Paths

After the recommendations, if the user seems stuck or confused, add:

```
---
Need more detail?
- `/project-stage-detect` — full gap analysis with all missing artifacts listed
- `/gate-check` — formal readiness check for your next phase
- `/start` — re-orient from scratch
```

Only show this if the user's input suggested confusion (e.g. "I don't know", "stuck",
"lost", "not sure"). Don't show it for simple "what's next?" queries.

---

## Collaborative Protocol

- **Never auto-run the next skill.** Recommend it, let the user invoke it.
- **Ask about MANUAL steps** rather than assuming complete or incomplete.
- **Match the user's tone** — if they sound stressed ("I'm totally lost"), be
  reassuring and give one action, not a list of six.
- **One primary recommendation** — the user should leave knowing exactly one thing
  to do next. Optional steps and "coming up" are secondary context.
