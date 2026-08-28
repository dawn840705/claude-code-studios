# Player Metrics (RLDD): [Game Title]

> **Status**: Draft | In Review | Approved
> **Author**: [level-designer / gameplay-programmer, jointly]
> **Measured On Build**: [commit SHA or build number — mandatory, see § 1]
> **Last Updated**: [Date]
> **Links To**: `design/gdd/game-concept.md`, `design/gdd/combat.md` (or the GDD
> that owns the character controller)
> **Consumed By**: every file in `design/levels/`, `docs/templates/difficulty-curve.md`

---

## Why this document exists

You cannot design a jump for a character whose jump you have not measured.

Rational Level Design (RLD) is the Ubisoft-lineage practice of measuring player
capability **first**, then expressing every challenge as a number against those
measurements. A 5-metre gap is not "hard" — it is *impossible* if the character
clears 4 metres, and *trivial* if they clear 9. Without this document the word
"hard" in a level doc is an adjective nobody can check.

This is the level-design instance of the repo-wide rule in
`rules/claim-confidence.md` and `docs/deterministic-gates.md`: **a claim is
admissible when it reduces to something measurable.** Difficulty scored against
a metrics table is arithmetic. Difficulty scored by feel is an opinion wearing a
number.

**Scope boundary.** This document says what the player *can* do. It does not say
what they *should* face — that is `docs/templates/difficulty-curve.md` (macro
arc) and the level documents (per-level placement). Keep the three separate; a
metrics table that starts editorialising about pacing has become a design doc
and will stop being trusted as a measurement.

---

## 1. Measurement protocol

> **Guidance**: Every row below is a measurement, not an intention. The number in
> the GDD is what someone wanted; the number here is what the build does. When
> they disagree, this document records the build and the disagreement becomes a
> bug report, not an edit to this table.

Three rules, all of them load-bearing:

1. **Record the build.** A metric without a build reference is unfalsifiable.
   Put the commit SHA or build number in the header block above.
2. **Record the method.** "How measured" must be specific enough that a second
   person gets the same number — which input, from what starting state, on what
   surface, averaged over how many trials.
3. **Measure in the engine, not in the code.** A jump derived from
   `jumpForce / gravity` is a prediction. Ship it only when a measured value
   disagrees by less than the tolerance you state, and note both.

Metrics are a **dependency, not a snapshot.** § 5 covers what happens when they
change.

---

## 2. Core traversal metrics

> **Guidance**: Fill only the rows your game actually has. Delete the rest — an
> unfilled row reads as an unmeasured one, and this document's whole value is
> that a blank means "we do not know" rather than "we did not bother".
>
> Units: pick one and state it (metres for 3D, tiles or pixels for 2D). Mixed
> units inside one table silently produce wrong derived constants in § 3, and
> nothing downstream will catch it.

**Unit of measure**: [metres | tiles | pixels — state it once, use it everywhere]

| Metric | Value | How measured | Tolerance | Notes |
|--------|-------|--------------|-----------|-------|
| Standing capsule height | [e.g., 1.8] | [Collider extents in editor] | [±0] | [Drives every doorway and cover height] |
| Crouch capsule height | [e.g., 0.9] | [Collider extents, crouch state] | [±0] | [Cover that clears one but not the other is a design decision, not an accident] |
| Capsule radius | [e.g., 0.35] | [Collider extents] | [±0] | [Minimum corridor width before the camera clips] |
| Eye height / camera height | [e.g., 1.65] | [Camera local Y] | [±0] | [What "visible from here" means in a sightline test] |
| Walk speed | [e.g., 2.5 /s] | [Distance over 10s, flat ground, avg of 3] | [±0.1] | |
| Run speed | [e.g., 6.0 /s] | [Same, sprint held from standstill + 2s ramp] | [±0.2] | [If there is an acceleration ramp, say how long it is — short corridors never reach top speed] |
| Standing jump height (apex) | [e.g., 1.4] | [Apex Y minus start Y, no horizontal input] | [±0.05] | |
| Standing jump distance | [e.g., 2.2] | [Landing X minus takeoff X, no run-up] | [±0.1] | |
| Running jump distance | [e.g., 4.1] | [Full run-up, flat takeoff and landing] | [±0.15] | [**The number levels are built from.** Measure it, do not derive it] |
| Running jump distance, +1 unit landing | [e.g., 3.2] | [Same, landing one unit higher] | [±0.15] | [Measure it separately. A rising landing eats horizontal distance, and the amount is not derivable from the flat figure] |
| Fall distance survived, no damage | [e.g., 5.0] | [Drop from increasing heights until damage] | [±0.25] | |
| Fall distance survived, non-fatal | [e.g., 12.0] | [Same, until death] | [±0.5] | |
| Ledge-grab reach (up / out) | [e.g., 0.6 / 0.4] | [Max offset where grab still registers] | [±0.05] | [A grab window is a forgiveness budget — state it, do not leave it emergent] |
| Glide / dash / double-jump distance | [e.g., 6.5] | [From apex of first jump] | [±0.2] | |
| Climb / mantle speed | [e.g., 1.2 /s] | [Fixed-height wall, avg of 3] | [±0.1] | |
| Interaction reach | [e.g., 1.5] | [Max distance a prompt appears] | [±0.05] | |
| Coyote time | [e.g., 0.12 s] | [Frames after leaving ground where jump still fires] | [±1 frame] | [Forgiveness that is measured can be tuned; forgiveness that is emergent cannot] |
| Input buffer window | [e.g., 0.15 s] | [Frames before landing where jump is queued] | [±1 frame] | |
| [Add game-specific verb] | | | | |

### Combat metrics (delete if the game has no combat)

| Metric | Value | How measured | Tolerance | Notes |
|--------|-------|--------------|-----------|-------|
| Effective weapon range | [e.g., 25] | [Distance where damage falloff begins] | [±1] | [Sets the arena size that makes this weapon relevant] |
| Maximum weapon range | [e.g., 60] | [Distance where damage reaches zero] | [±2] | [Sightlines longer than this are decorative, not tactical] |
| Dodge / roll distance | [e.g., 3.0] | [Travel per input] | [±0.1] | [Arena minimum width = this × the number of consecutive dodges the design expects] |
| Invulnerability window | [e.g., 0.4 s] | [Frames of i-frames per dodge] | [±1 frame] | |
| Time-to-kill, baseline enemy | [e.g., 1.8 s] | [Optimal DPS, no misses] | [±0.2] | [Encounter length is TTK × count; a "short fight" is arithmetic] |
| Time-to-die from baseline enemy | [e.g., 6.0 s] | [Standing still, one enemy] | [±0.5] | |

---

## 3. Derived design constants

> **Guidance**: This is the table level designers actually build from. Each row
> is derived from § 2 by a stated formula and a stated margin — write the formula
> down, because a constant whose derivation is lost gets copied into the next
> project where it is wrong.
>
> The margin is a design value, not a fact: it is how much of the player's
> maximum capability the design refuses to demand outside a deliberate challenge.
> A larger margin is more forgiving, a smaller one more demanding. Pick it once,
> here, state why, and let every level inherit it.

**Traversal margin**: [e.g., 15%] · **Why this number**: [the design argument, in
one sentence. "It felt right" is an acceptable answer if it is what happened —
what is not acceptable is leaving it unstated, because the next person will read
it as derived]

| Constant | Formula | Value | Meaning |
|----------|---------|-------|---------|
| Trivial gap | ≤ standing jump distance × (1 − margin) | [e.g., ≤ 1.9] | Crossable without thinking. Use for traversal that is not the point |
| Standard gap | ≤ running jump distance × (1 − margin) | [e.g., ≤ 3.5] | The default. Requires a run-up but not precision |
| Challenge gap | ≤ running jump distance | [e.g., ≤ 4.1] | Requires commitment. **Never place one before the mechanic's Ketsu beat** (see the level doc's Teaching Structure) |
| Impossible gap | > running jump distance | [e.g., > 4.1] | A wall, communicating "not this way". Make it **visibly** impossible rather than marginally so: at 4.2 against a 4.1 maximum the gap is unreachable but does not look it, so the level is communicating one thing and enforcing another. State the width you consider unmistakable |
| Safe drop | ≤ fall distance survived, no damage | [e.g., ≤ 5.0] | One-way traversal with no cost |
| Punishing drop | ≤ non-fatal fall distance | [e.g., ≤ 12.0] | One-way with a cost. State the cost |
| Minimum corridor width | ≥ capsule radius × [e.g., 4] | [e.g., ≥ 1.4] | The multiplier is yours to set — derive it from where **your** camera actually starts colliding, not from this example |
| Minimum combat arena | ≥ dodge distance × [e.g., 3] | [e.g., ≥ 9.0] | Space to execute the defensive verb the combat design assumes |
| Full-cover height | ≥ standing capsule height | [e.g., ≥ 1.8] | Blocks sight standing |
| Half-cover height | ≥ crouch height, < standing | [e.g., 0.9–1.79] | Blocks sight crouched only |
| Non-cover | < crouch height | [e.g., < 0.9] | Protects nothing. If the art reads as cover and the height does not, that is a defect — report it, do not tune the height silently |
| [Add constant] | | | |

---

## 4. Challenge scoring

> **Guidance**: RLD's contribution is that difficulty becomes a *derived* number.
> Score each atom of gameplay — one gap, one enemy, one hazard — from the
> measured demand it places against measured capability. Then the level document's
> "Difficulty 5/10" column has a derivation instead of a vibe.
>
> Score the atom, not the moment. A 3/10 gap over a 9/10 hazard is not a 12 and
> it is not a 6; see § 4.2.

### 4.1 Atom scoring

**These cut points are a house convention, not RLD.** The sourced part of RLD is
the method — score each atom against measured capability. The specific
percentages below are a starting scale this repo picked so that projects begin
from the same one; nothing in the literature fixes them. **Change them if your
game disagrees**, change them in this file so every level inherits the change,
and say in the row below why.

**Scale basis**: [house default | tuned for this game on YYYY-MM-DD because …]

| Score | Demand relative to capability | Example |
|-------|------------------------------|---------|
| 1 | ≤ 40% of the relevant metric | A gap at 1.5 against a 4.1 running jump |
| 3 | ≤ 60% | Standard gap, no run-up constraint |
| 5 | ≤ 80% | Standard gap with a constrained approach |
| 7 | ≤ 95% | Challenge gap, forgiving landing |
| 9 | ≤ 100% | Challenge gap, landing within the coyote/grab window |
| 10 | > 100% of one metric, possible only by combining two | Gap crossable only with jump + dash |

Anything scoring above 10 is not a hard challenge, it is an unreachable one.
Report it as a defect against § 3's "Impossible gap" row.

### 4.2 Combination

Difficulty of a combined challenge is **not** the sum of its atoms. Two rules,
both from the same underlying fact — the player has one attention budget:

- **Do not add the scores.** A 5 gap under fire is not a 10 — the gap's demand
  against the measured jump did not change; what changed is unmeasured. Record it
  as `5 (+ combat pressure)`. A summed number would look derived while being
  invented, which is worse than an adjective because nobody would check it.
- **A challenge that demands two *unpractised* verbs at once is a teaching
  failure, not a difficulty setting.** Check the level's Teaching Structure: if
  either verb has not reached its Ketsu beat, the combination is premature.

---

## 5. Invalidation — what breaks when a metric changes

> **Guidance**: This is the section that pays for the document. A character
> controller tune is not a local change; it silently reclassifies every gap in
> the game. Without this section that reclassification is discovered by
> playtesters, one level at a time.

| If this changes | These become wrong | Action |
|-----------------|-------------------|--------|
| Any § 2 metric | Every § 3 constant derived from it | Re-derive § 3 before touching any level |
| Running jump distance | Every gap in every level document | Run `$propagate-design-change` with this document as the origin |
| Cover heights (capsule) | Every cover placement | Re-run `$spatial-audit` on built levels — it measures cover against the capsule directly |
| Weapon range or TTK | Every arena size and encounter length | Re-check § 3's arena minimum, then `$balance-check` |
| Margin (§ 3) | Every constant, no metric changed | A deliberate difficulty-wide decision. Pin it as a decision with a revisit trigger (`rules/decision-lifecycle.md`) |

**Drift check.** This document and the built levels are two witnesses to the same
truth. When you suspect they have separated, `$sot-audit` is the skill built for
N-witness drift — do not hand-check more than a couple of levels.

---

## 6. What this document does NOT decide

- **Whether a challenge is fun.** That is a playtest result (`$playtest-report`).
  Metrics make a playtest verdict *interpretable*; they do not substitute for one.
- **Whether the character controller is good.** A measured jump of 4.1 is a fact.
  Whether 4.1 feels good is a `$prototype` and playtest question.
- **Where challenges go.** Placement is the level document's job.
- **The macro difficulty arc.** That is `docs/templates/difficulty-curve.md`.

---

## Sources

Rational Level Design is a named practice with primary sources; cite them rather
than presenting it as house method. Link only — see `docs/level-design-sources.md`
for why nothing is copied into this repo.
