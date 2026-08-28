# Spatial Audit: [Scene Name]

*Date: [YYYY-MM-DD] · Genre: [sp | pvp | open] · Lenses: [all | ...]*

## Verdict

**[PASS | CONCERNS | FAIL | BLOCKED]** — [one sentence naming the deciding finding]

| | |
| ---- | ---- |
| **Extraction channel** | [live editor via `hera-agent-unity` / scene files only] |
| **Sentinel** | [`__SPATIAL_AUDIT_OK__ n=NNN` seen / **absent — extraction did not run**] |
| **Genre source** | [passed as `--genre X` / inferred from `PATH` / asked the user] |
| **Level document** | [path — or **none found**, in which case intent-comparison questions were skipped] |
| **Areas** | [the project's own partition, or "derived from NavMesh": list them] |
| **Scene scope** | [object count, bounds, area count] |
| **Screenshots** | [paths / "screenshot unavailable" / "none"] |
| **Review mode** | [solo / lean / full — and which agents produced findings] |

> **Reading the two failure states.** *Sentinel absent* → verdict is BLOCKED,
> every section below is empty, and nothing may be filled in from scene files:
> the editor was in a bad state and a file pass would paper over it. *Channel B
> (no editor)* → a valid partial audit; massing and circulation stand, while
> prospect-refuge and wayfinding are marked **NOT MEASURED** because files carry
> no NavMesh, no raycasts, and no camera view. Anything derived rather than
> measured is tagged `추정 — 파일 기반` per `rules/claim-confidence.md`.

---

## Findings

Ordered by severity. Every row needs a location; a finding without one is not a
finding. Mark anything derived rather than measured per `rules/claim-confidence.md`.

| # | Lens | Severity | Location | Observation (measured) | Why it matters | Source |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| F1 | [massing] | [blocking / defect / note] | [object name or x,y,z] | [the number] | [consequence for the player] | [principle + link, or "measured only"] |
| F2 | | | | | | |

---

## 1. Massing

**[PASS / CONCERNS / FAIL]**

- **Volume hierarchy**: [tier count and the dominant mass — or "flat: N masses within X% of each other"]
- **Additive / subtractive**: [which, and whether it is consistent]
- **Parti in one sentence**: [the sentence — or "could not state one", which is itself the finding]

[Findings referencing F# above.]

---

## 2. Circulation

**[PASS / CONCERNS / FAIL]**

- **Topology**: [linear / loop / hub-and-spoke / grid] — [matches / contradicts] the level document
- **Connections per area**: [table or list]
- **Dead ends**: [count and locations — defect in pvp, often intent in sp]
- **Verticality**: [are level changes readable before commitment]

---

## 3. Prospect-refuge

**[PASS / CONCERNS / FAIL / NOT MEASURED — channel B]**

- **Exposure positions** (wide sightline, no cover): [count / sample coords]
- **Dead refuge** (cover, no sightline): [count / sample coords]
- **Cover height vs capsule**: [values; flag any cover that protects neither standing nor crouching]
- **pvp only — spawn symmetry**: [side A vs side B sightline delta, as a number]

---

## 4. Wayfinding

**[PASS / CONCERNS / FAIL / NOT MEASURED — channel B]**

- **Landmarks**: [count, and whether each is unique in silhouette at range]
- **Vistas on the critical path**: [locations, and what each previews]
- **Light as guidance**: [do the brightest points lie on the intended path]
- **Lynch five** (open world): [path / edge / district / node / landmark — or "over-fits this layout"]

---

## What was not judged

[Explicit. Fun, pacing, encounter difficulty, and art quality are out of scope —
say which questions this audit cannot answer so nobody reads silence as approval.]

---

## Sources

Principles cited above, with links. **Do not paste source text into this report**
— The Level Design Book is CC BY-NC-SA 4.0 and this repo is MIT
(`docs/level-design-sources.md`).

- [Principle] — [page title, URL]

---

## Next steps

- [ ] [Highest-severity finding] → [owner / skill]
- [ ] Rework via `/self-loop` using the findings above as defect tickets
- [ ] Update `Layout` in the level document
- [ ] Re-audit after rework
