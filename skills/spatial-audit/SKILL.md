---
name: spatial-audit
description: "Audit an existing Unity scene's spatial layout against four architectural lenses — massing, circulation, prospect-refuge, wayfinding. Use when the user says 'this level feels off', 'audit the layout', 'why is this map confusing', 'is this arena balanced', or after a blockout is walkable but before art passes. Read-only: it judges a level that already exists. Do NOT use to author a new layout from nothing (that is /quick-design or /team-level), and not for narrative pacing or encounter tuning."
argument-hint: "<scene-or-path> [--genre sp|pvp|open] [--lens massing|circulation|prospect-refuge|wayfinding|all] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Write, Task, AskUserQuestion
---

> **Orchestrator-run, on purpose.** There is no `agent:` key here. Extraction
> needs Bash and `level-designer` is denied Bash (`disallowedTools`), so the
> orchestrator extracts and the agent judges. § 3 spells out the split and the
> tool narrowing required at spawn time.

# Spatial Audit — architectural lenses on a built level

A blockout that is walkable is not a blockout that works. This skill reads a
level **that already exists** and judges its space the way an architect reviews
a building: what the massing says, how circulation connects, where the player
can see without being seen, and whether they can find their way.

It reports. It does not rebuild — every finding names a location and a reason so
a human decides what to move.

**Scope boundary.** Nothing here judges whether a level is *fun*. Fun is a
playtest result (`/playtest-report`). This skill judges whether the space is
legible, navigable, and fair — the properties that make a playtest's verdict
interpretable instead of noise.

---

## 1. Parse arguments and resolve context

1. **Target** — a scene name, a scene path, or nothing. If nothing, list the
   scenes under the project's scene root and ask which one with
   `AskUserQuestion`. Never audit "the whole project".
1b. **The level document** — find the level's design doc (usually
   `docs/templates/level-design-document.md`-shaped). Several § 3 questions
   compare the built scene against what the doc *claims* (topology, critical
   path, intended route), and without it those questions are unanswerable.
   If there is no level document, say so in the report header and skip those
   questions rather than inventing an intent to measure against.
2. **Genre** — `sp` (single-player / PvE), `pvp` (competitive arena), or `open`
   (open world / sandbox). This is not cosmetic: it changes which findings are
   defects and which are intent (§ 3). If not passed, infer from the project's
   design docs and **state the inference in the report header**; if the docs are
   silent, ask.
3. **Lens** — default `all`. Narrow only when the user asked a narrow question.
4. **Review mode** — `--review`, else `production/review-mode.txt`, else `lean`.

---

## 2. Extract the scene — live editor first, files as fallback

Two channels, and **which one you get is not your choice — it is a fact about
the environment.** Route on it precisely:

| Situation | Channel | Consequence |
| ---- | ---- | ---- |
| `hera-agent-unity` present, editor responding | **A** | Full audit |
| CLI missing, or editor not running | **B** | Valid partial audit; two lenses degrade (below) |
| CLI responded but the **sentinel is absent** | neither | **BLOCKED** — the editor is in a bad state and a file audit would paper over it |

The third row is the one that matters. A closed editor is a normal condition; a
*blocked* editor is a fault, and silently downgrading to files would hide it.

**Record the channel in the report header.** A file-only audit cannot see
runtime state and must say so.

### 2A. Live Unity via `hera-agent-unity` (preferred)

The CLI is stateless — each call is an independent request, so there is no
session to lose. Its command set is roughly five: `exec` (arbitrary C#),
`console`, `scene`, `editor`, `screenshot`.

> `exec`, `console`, `scene load`, `editor refresh|play|stop` are verified in
> use. **`screenshot` is documented but not verified** in this project's tooling
> log — if it errors, drop to numbers-only and note it, don't retry blind.

**The silent-failure contract — this is mandatory.** `exec` can return nothing
at all when the editor's main thread is blocked (a modal dialog is the recorded
cause). No output is indistinguishable from a successful snippet that found
nothing, and reading that as "the scene has no cover" is the worst output this
skill can produce. So:

- Every `exec` snippet **must** end by emitting a sentinel line carrying the
  count it found: `__SPATIAL_AUDIT_OK__ n=<count>`.
  Emit it the way `exec` actually returns data in this project — if `Debug.Log`
  goes to the Unity console rather than into `exec`'s response, the sentinel
  must go through the return channel instead. **Verify on the first call of a
  session with a trivial snippet before trusting any extraction**; otherwise a
  sentinel that never surfaces BLOCKS every audit for the wrong reason.
- If the sentinel is absent, the extraction **did not run**. The verdict is
  **BLOCKED** — never PASS and never "no findings". This is the prose analogue
  of the `exit 3` rule in `docs/deterministic-gates.md`: a check that could not
  run has produced no verdict, and no verdict is not a pass. **This skill emits
  no exit code** — the sentinel is a model-side check, not a gate.
- On a missing sentinel: report BLOCKED, check `hera-agent-unity console` for
  compile errors or editor events, name the suspected cause, and stop. Do not
  fall back to channel B — a reader must know the editor was unreachable.
- Snippets are read-only. No `exec` in this skill may move, create, or delete a
  GameObject, and that includes moving a camera to frame a screenshot. Use
  existing cameras and spawn points. Extraction and judgment stay separate; the
  user moves things.

What to pull, per lens (one `exec` per lens, not one per object — a per-object
round trip on a 500-object scene is the slow path and adds nothing):

| Lens | Extract |
| ---- | ---- |
| massing | Renderer bounds (center, size) of static geometry, grouped by rough volume; count of distinct volume tiers; **child-object count per mass** (the additive/subtractive tell — a mass built from many parts is articulated, one built from few large ones is monolithic) |
| circulation | NavMesh triangulation or walkable surface bounds; door/portal/trigger colliders; per-area connection count |
| prospect-refuge | Raycast sightlines from a sample grid of standing positions; cover collider heights vs the player capsule (standing **and** crouch) |
| wayfinding | Renderers visible at >20m from sample points **along the critical path taken from the level document** (§ 1b — without it, sample the NavMesh instead and say so); light positions and intensities; distinct silhouettes above the skyline |

**Areas** for "per-area" counts: use the project's own partition if it has one
(scene sections, room volumes, spawn zones). If it doesn't, derive areas from
NavMesh connectivity and **list the derived areas in the report** so a reader
can disagree with the partition rather than with the numbers built on it.

If `screenshot` works, take one per area from an existing camera or spawn point
and read it. When the picture and the number disagree, **the number is the
finding and the picture is the evidence** — report both and let the reader see
the conflict; do not average them into a softer claim.

### 2B. Scene files (no editor needed)

Parse the `.unity` scene YAML and prefab YAML directly with Read/Grep. This
yields transforms, collider extents, light placement, and prefab composition —
enough for massing, rough circulation, and metrics. It **cannot** give you
NavMesh, runtime raycasts, or what the camera actually sees. Mark every
prospect-refuge and wayfinding finding from this channel as `추정 — 파일 기반`
per `rules/claim-confidence.md`.

---

## 3. Judge, one lens at a time

Spawn `level-designer` with the extracted data. **You** run the extraction and
hand it the numbers — that agent is denied Bash (`disallowedTools`) and cannot
call hera itself.

**Narrow its tools at spawn: `tools: Read, Glob, Grep`.** By default
`level-designer` has `Write, Edit`, and this skill's whole premise is that it
reports rather than rebuilds. Read-only is guaranteed by permission, not by
asking nicely — `rules/subagent-collaboration.md` § 3.1.

Also required in every spawn prompt here:

- The **§ 3 mandatory items 6 and 7** — forbidden ground and return boundary.
  Forbidden: do not edit any scene, prefab, or design document; do not spawn
  further agents.
- **`rules/claim-confidence.md`** verbatim in the prompt when the extraction came
  from channel B, so the agent tags derived findings `추정 — 파일 기반` instead of
  stating them flat. The rule is not in § 3's default item list; the caller
  carries it.

For `--review full`, add `ux-designer` (wayfinding) and `systems-designer` (pvp
balance). Fan-out is opt-in because a report file is R1/R2 under
`rules/verify-route.md` and three agents is over-routing for the default case.
Write ownership when you do fan out — fill this in before writing the prompts,
per § 2.1:

| Agent | Writes | Reads only |
| ---- | ---- | ---- |
| level-designer | nothing — returns findings as text | extraction data, level document |
| ux-designer | nothing — returns findings as text | same |
| systems-designer | nothing — returns findings as text | same |

The orchestrator is the sole writer of the report. Three agents proposing edits
to one file is the § 2.1 failure this table exists to prevent.

Every finding needs: **location** (coordinates or object name), **observation**
(the measured value), **why it matters**, and **severity**. A finding without a
location is not a finding.

### 3.1 Massing — the logic of the volumes

- Is there a clear volume hierarchy, or are all masses the same size? A level
  where everything is the same scale gives the player nothing to navigate by.
- Additive (articulated, human-scaled) vs subtractive (continuous, monolithic) —
  is the choice consistent, or accidental?
- Can the layout be described in one sentence? If not, the parti is missing and
  players will not form a mental map.

**Do not apply shape psychology.** "Round shapes feel safe", "angular shapes
feel threatening" — there is no evidence for these and the source literature
explicitly rejects them (§ 6). If you catch yourself scoring a shape by its
mood, delete the finding. Shape claims must reduce to a measurable consequence:
sightline, traversal cost, silhouette legibility.

### 3.2 Circulation — how areas connect

- Connectivity per area: dead ends, single-exit rooms, unintended shortcuts.
- Topology: linear / loop / hub-and-spoke / grid — is the actual graph the one
  the level document claims? This is doc-vs-asset drift; if you find more than a
  couple of these, stop hand-checking and run `/sot-audit` with the level
  document and the scene as witnesses — that skill is built for N-witness drift.
- Verticality: are level changes readable before the player commits to them?

Genre split: a dead end is a **defect** in `pvp` (a death trap with no counter-
play), often **intent** in `sp` (a reward alcove), and **fine** in `open`.

### 3.3 Prospect-refuge — seeing without being seen

Vantage and cover, measured. Report the ratio, not a verdict on "tension".

- Positions with wide sightlines and no cover → exposure. Too many and the space
  reads as hostile without meaning to.
- Positions with cover and no sightline → enclosure with no payoff.
- Cover height vs the player capsule, standing and crouched. Cover that clears
  neither threshold protects nothing — report each instance with both numbers
  and let the reader judge; do not editorialise about what players "trust".

Genre split: `pvp` wants the ratio roughly symmetric between spawns, so
**measure both sides and report the delta as a number** — a measured delta is
worth more than any adjective. `sp` deliberately varies it to pace tension.
`open` should vary it by district. See "Map balance" in
`docs/level-design-sources.md` for the underlying treatment.

### 3.4 Wayfinding — can they find their way

- Landmarks: is anything visible from far away and unique in silhouette? Count
  them. Zero is a finding.
- Vistas: does the critical path ever open onto a view that previews what comes
  next?
- Light and contrast as guidance: do the brightest points in the frame lie on
  the intended path, or off it?
- Lynch's five (path / edge / district / node / landmark) are most useful in
  `open`; in a single corridor they over-fit — say so rather than forcing them.

---

## 4. Verdict

The verdict is **advisory** — it judges whether the space says something
coherent, which no script can decide. Where a number decides, the number
decides: cover height against capsule height, spawn sightline delta, area
connection counts. Report those as measurements, and do not let a judgment
override an arithmetic result.

| Verdict | Meaning |
| ---- | ---- |
| **PASS** | No blocking finding. Minor notes may remain. |
| **CONCERNS** | The level works but at least one lens has a defect that will cost playtest signal. Named, located, fixable. |
| **FAIL** | A lens is broken badly enough that playtest results will be uninterpretable — e.g. no landmark in an open map, or an asymmetric spawn advantage in pvp. |
| **BLOCKED** | Extraction did not run (missing sentinel, editor unreachable). No verdict is possible; say so rather than guessing. |

A BLOCKED audit is not a failed audit. Reporting "I could not read the scene" is
the correct output when the editor is down.

---

## 5. Write the report

**Ask before writing.** Show the findings in conversation first and confirm the
path with the user before you create the file — this skill is read-only toward
the project and the report is its only artifact.

On approval, write to `production/qa/spatial-audit-<scene>.md` using
`docs/templates/spatial-audit-report.md`. That path is the convention
`verify_policy.py` P4 expects; do not invent a new one.

---

## 6. Sources and what not to copy

Findings should cite where the principle comes from. Two rules about that:

- **The Level Design Book is CC BY-NC-SA 4.0.** Link and paraphrase; do **not**
  copy its text into this repo or into a generated report. This plugin is MIT,
  and NonCommercial + ShareAlike cannot be carried into it. See
  `docs/level-design-sources.md` for the citation list and the exact
  license terms.
- **Totten's book is not in that online book** — its authors deliberately
  exclude other level-design books. Cite it separately, from your own reading,
  and never quote at length.

---

## Next steps

- `CONCERNS` / `FAIL` → rework with `/self-loop` (a low score alone is not a
  licence to rewrite — each edit needs the defect ticket this audit produced)
- Findings that change the design of record → update the level document
  (`docs/templates/level-design-document.md` § Layout)
- Layout defects that trace to an unstated intent → pin the intent as a decision
  with a revisit trigger (`rules/decision-lifecycle.md`)
- Before the art pass → `/design-review`; after it → `/perf-profile`
- Recurring defect across two levels → `/lesson-log`
