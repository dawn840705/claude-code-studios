---
name: governance-bible-init
description: "Bootstrap a domain-specific governance Bible (Sound, Art, Narrative, etc.) using the Anchor + Bible pattern. Sets up the folder, README spec template, and decision protocol so a 1-person dev (or small team) can keep AI-generated assets tonally consistent without drift. Use when user says 'set up sound bible', 'art governance', 'establish narrative bible', 'bootstrap design system'."
argument-hint: "<domain> [chapter-scope]"
user-invocable: true
allowed-tools: Read, Write, Glob, Bash
agent: art-director
---

## Purpose

Solo developers and small teams generating hundreds of assets via AI tools (image/3D/audio/voice/code) face a *drift problem*: there's no full-time art/audio director enforcing tone, so each asset's quality is judged session-by-session against a fading memory of "what we agreed the project looks/sounds like." Months in, assets diverge.

This skill bootstraps the **Anchor + Bible** governance pattern for any creative domain:

- **Bible (`Anchors/README.md`)** — text spec: tone filters, naming rules, category list with TBD anchors.
- **Anchors (`Anchors/<id>.{ext}` + `<id>.prompt.txt`)** — actual reference assets that define "this is what we mean" — the *ear* / *eye* standard.
- **Decision protocol** — the workflow that prevents drift: 5–10 second A/B compare against anchor → channel into **accept / retry-once / reject** verdicts.

Every new asset is judged *against the anchor*, not against a remembered ideal.

---

## Phase 1: Identify the domain

From `$ARGUMENTS[0]`, determine the domain. Common values:

- `sound` (or `audio`) — music, voice, SFX, ambient
- `art` (or `visual`) — characters, environments, props, UI, VFX, icons
- `narrative` — dialogue lines, lore entries, item descriptions, environment text
- `ui` — interaction patterns, motion language, copy tone
- `code-style` — coding conventions, naming, idioms (less common but valid)

If `$ARGUMENTS[1]` provided, it scopes the initial Bible to a chapter / area / phase (e.g. `chapter-1`, `area-honeydew`). Recommend starting *narrow* (one chapter) and expanding gradually — drift comes from premature scope.

If no args, ask the user:

> Which domain? (sound / art / narrative / ui / code-style / other)
> Chapter scope for the initial Bible? (recommend just one — expand as anchors solidify)

---

## Phase 2: Read existing project context

Read in parallel:
- Project root README / CLAUDE.md (overall tone, references)
- Any existing memory / decision logs (e.g. `narrative meetings`, `concept doc`, `tone references`)
- Existing assets in the workshop folders (`Tools/*/output/`) — anchor candidates
- Reference games / inspirations (often listed in concept docs)

Goal: extract the **3 tone filters** (mood / theme / energy bands the project must hit). The Bible's filter checklist is project-specific; AI input here is just to surface candidates.

---

## Phase 3: Confirm tone filters with the user

Propose 3 tone filters, e.g. for a satirical retro-SF game:
1. *1950s American consumerist setting* — within Fallout / Bioshock / Outer Worlds reference range?
2. *Light propaganda satire* — cheerful denial overlaying actual horror?
3. *Mid-tempo action grit* — Helldivers 2 zone, neither too heavy nor too light?

Confirm or adjust with the user. **All 3 filters must pass** for a candidate asset to even reach Anchor comparison. Filters alone are insufficient — there are real-world examples of AI output passing all three filters but still being tonally wrong (the eyes too sharp, the music too modern, the line too snarky). The Anchor catches what the filters miss.

---

## Phase 4: Define category list and naming convention

For the chosen domain, propose 5–8 **categories** for the chapter scope. Each category has a `prefix_subcategory_scene_variant.<ext>` naming rule.

Common prefixes per domain:

| Domain | Prefixes |
|---|---|
| Sound | `mus_` / `vox_` / `sfx_` / `amb_` |
| Art | `char_` / `env_` / `ui_` / `vfx_` / `prop_` / `icon_` / `concept_` |
| Narrative | `dlg_` / `lore_` / `item_` / `env_text_` / `radio_` |

Customize per project. The user accepts the prefix list before continuing.

---

## Phase 5: Create the folder structure and Bible README

Create:

```
Documents/<DomainTitleCase>Design/
  Anchors/
    README.md                 ← The Bible
    (anchor assets land here as they're chosen)
```

Write `Anchors/README.md` containing:

1. **Purpose** — one-paragraph: this folder is the SoT for tone.
2. **Workflow** — the 4-step decision protocol (call AI → A/B compare → judge → archive prompt.txt).
3. **Tone filters** — the 3 confirmed in Phase 3.
4. **Naming convention** — the prefix list and examples.
5. **Category list** — table with each category + initial anchor status (`⏳ TBD` until populated).
6. **Tool stack** — which AI tools are sanctioned for this domain (with version pins if relevant).
7. **Change log** — append-only record of what was added/changed when.

A template is at `<plugin-root>/docs/templates/governance-bible-template.md` if you want to copy + customize, but inline-write is also fine.

---

## Phase 6: Optional — promote existing workshop assets to first anchors

If the user already has 1-2 candidate assets in `Tools/*/output/`, ask whether to promote them to first anchors *now* or wait. Promoting now:

1. `mv` the file into `Anchors/` with the new naming convention.
2. Write a `<id>.prompt.txt` next to it containing: the exact tool call (CLI command), the prompt parameters, the cost (credits/chars), the date, and the intended use.
3. Update the Bible README's category table — change `⏳ TBD` to `✅ Anchor: <filename>`.

If no candidates exist yet, leave all categories as `⏳ TBD`. Anchors are populated *as the project produces them*, not preemptively.

---

## Phase 7: Write the governance memory + meeting record

Optionally:
- Create a meeting record at `Documents/Meetings/YYYY-MM-DD-<Domain>-Governance.md` documenting the decision (use [`docs/templates/meeting-template.md`](../../docs/templates/meeting-template.md)).
- Record the rule in agent memory so it's recalled in future sessions: "all new `<domain>` assets follow Anchor + Bible at `Documents/<DomainTitleCase>Design/Anchors/`".

---

## Output

A folder structure ready for first asset, a populated Bible README, and (optionally) one or two anchors with prompt.txt files. The user can immediately start producing assets and judging them via the Anchor protocol.

---

## Sister skills

- `/api-cost-gate` — required before any paid AI call (Suno/ElevenLabs/Midjourney/etc.). Runs in front of asset generation.
- `/sot-audit` — once anchors exist, periodically audit that all *production* assets match anchor tone (variant of N-witness audit, where the anchor is the canonical witness).
