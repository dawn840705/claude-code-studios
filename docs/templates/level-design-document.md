# Level: [Level Name]

## Quick Reference

- **Area/Region**: [Where in the game world]
- **Type**: [Combat / Exploration / Puzzle / Hub / Boss / Mixed]
- **Estimated Play Time**: [X-Y minutes]
- **Difficulty**: [1-10 relative scale — derived, see Challenges below]
- **Prerequisite**: [What the player must have done to reach this level]
- **Metrics Basis**: [`design/gdd/player-metrics.md` @ build/commit — the measured
  capabilities every distance in this document is scored against. If this is
  blank, no difficulty number below is checkable]
- **Status**: [Concept | Layout | Graybox | Art Pass | Polish | Final]

## Narrative Context

- **Story Moment**: [Where in the narrative arc does this level occur]
- **Narrative Purpose**: [What story beat this level delivers]
- **Emotional Target**: [What the player should feel during this level]
- **Lore Discoveries**: [What world-building the player can find here]

## Teaching Structure (기승전결 / Kishōtenketsu)

> **Guidance**: A level that teaches something should teach *one* thing, in four
> beats. This is the structure Nintendo credits for its Mario levels, borrowed
> from the four-act narrative form: **ki** (introduce), **shō** (develop),
> **ten** (twist), **ketsu** (conclude). It is a teaching tool first and a pacing
> tool second — the pacing works *because* the player is being taught.
>
> The value over "easy → hard" is the **ten** beat. Escalation alone only asks
> for more of the same execution; the twist recontextualises the mechanic, which
> is what turns knowing-the-input into understanding-the-idea.
>
> **When this does not apply, say so and delete the section.** Hub areas, open
> sandboxes, pure-narrative sequences and levels that teach nothing new have no
> mechanic to run through four beats, and forcing the structure onto them
> produces a filled-in table that describes nothing. Naming the exception is the
> correct output.

**Mechanic taught**: [The single verb, rule, or interaction this level is about.
If you need to write two here, this is either two levels or a combination level —
say which, and name the beat each mechanic has already reached elsewhere.]

| Beat | Purpose | In this level | Fail state |
|------|---------|--------------|-----------|
| **Ki** 起 — Introduction | Show the mechanic in isolation, with nothing else competing for attention | [What the player meets first] | **None.** A safe space to experiment. If the player can fail here, this is not a Ki beat |
| **Shō** 承 — Development | Same mechanic, higher demand. The player confirms their model is right | [How the demand rises] | Reversible — retry cost near zero |
| **Ten** 転 — Twist | Recontextualise. The mechanic does something the player did not expect, or meets a condition that changes what it means | [The twist] | Real, but fair — the player has all the information needed |
| **Ketsu** 結 — Conclusion | Combine. Demands the full understanding built by the first three beats | [The final test] | Real. This is where the challenge-tier atoms belong |

**Two rules that make the structure checkable:**

1. **The Ten beat introduces no new verb.** If the twist requires a mechanic the
   player has not seen, it is not a twist — it is a second Ki beat wearing a
   costume, and the level now teaches two things badly.
2. **Challenge-tier difficulty appears no earlier than Ketsu.** Cross-check the
   Challenges table below against the level's beat boundaries.

## Layout

### Overview Map

```
[ASCII diagram of the level layout. Use these symbols:]
[S] = Start point
[E] = Exit/end point
[C] = Combat encounter
[P] = Puzzle
[R] = Reward/loot
[!] = Story beat
[?] = Secret/optional
[>] = One-way passage
[=] = Two-way passage
[@] = NPC
[B] = Boss encounter
```

### Critical Path

[The mandatory route through the level, step by step.]

1. Player enters at [S]
2. [Description of what happens along the path]
3. Player exits at [E]

### Optional Paths

| Path | Access Requirement | Reward | Discovery Hint |
|------|-------------------|--------|---------------|

### Points of Interest

| Location | Type | Description | Purpose |
|----------|------|-------------|---------|

## Encounters

> **Difficulty numbers in this section are derived, not asserted.** Each score
> comes from the atom-scoring table in `docs/templates/player-metrics.md` § 4:
> the demand as a percentage of the measured capability. A score with no
> measurement behind it is an adjective — write `?` instead, which at least
> tells a reader the number is missing rather than wrong.

### Traversal Challenges

| ID | Position | Type | Measurement | vs. Metric | Score | Beat |
|----|----------|------|-------------|-----------|-------|------|
| T-01 | [Map ref] | Gap | [2.8 m] | [68% of 4.1 running jump] | 3/10 | Shō |
| T-02 | [Map ref] | Rising gap | [3.0 m, +1 m landing] | [94% of 3.2 rising jump] | 7/10 | Ketsu |
| T-03 | [Map ref] | Drop | [4.0 m] | [80% of 5.0 safe drop] | 1/10 | Ki |

### Combat Encounters

| ID | Position | Enemy Composition | Difficulty | Arena Notes |
|----|----------|------------------|-----------|-------------|
| E-01 | [Map ref] | [2x Grunt, 1x Ranged] | 3/10 | Open area, cover on flanks |
| E-02 | [Map ref] | [1x Elite, 3x Grunt] | 5/10 | Narrow corridor, no retreat |

### Non-Combat Encounters

| ID | Position | Type | Description | Solution Hint |
|----|----------|------|-------------|---------------|

## Pacing Chart

```
Intensity
10 |                              *
 8 |                         *   * *
 6 |            *  *        * * *   *
 4 |     *  *  * ** *   *  *
 2 | * ** ** *        * * *          *
 0 |S-----------------------------------------E
     [Start]    [Mid]              [Climax] [Exit]
```

[Describe the intended rhythm: where are the peaks, valleys, rest points?]

## Audio Direction

| Zone/Moment | Music Track | Ambience | Key SFX |
|-------------|------------|----------|---------|
| [Entry] | [Track] | [Ambient sounds] | [Door opening] |
| [Combat] | [Combat music] | [Muted ambience] | [Combat SFX] |
| [Post-combat] | [Calm transition] | [Return to ambience] | |

## Visual Direction

- **Lighting**: [Key, fill, ambient description]
- **Color Palette**: [Dominant colors and why]
- **Mood Board References**: [Description of visual references]
- **Landmarks**: [Visible navigation aids and their locations]
- **Sight Lines**: [What the player should see from key positions]

## Collectibles and Secrets

| Item | Location | Visibility | Hint | Required For |
|------|----------|-----------|------|-------------|

## Technical Notes

- **Estimated Object Count**: [N]
- **Streaming Zones**: [Where to break the level for streaming]
- **Performance Concerns**: [Any known heavy areas]
- **Required Systems**: [What game systems are active in this level]
