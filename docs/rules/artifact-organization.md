# Artifact Organization Rules

How to lay out AI-generated assets, agent-produced documents, and engine import targets so that nothing gets lost, drift is detectable, and the same workflow handles tools used today *and* tools you might adopt tomorrow.

---

## Three-zone discipline

Every AI-generated artifact lives in **exactly one** of three zones. The zone determines git tracking, naming, and lifetime.

### Zone 1 — Workshop (`Tools/<Service>/output/`)

- **Purpose:** scratch space for raw tool output. Where the bytes land *immediately* after a tool call.
- **Git status:** `.gitignore`d. Never committed.
- **Lifetime:** ephemeral. Survives until the next call or until promoted to Zone 2.
- **Naming:** whatever the tool produces — no convention enforced.

Examples: `Tools/SunoAPI/output/<task-id>/`, `Tools/MidjourneyAPI/output/<batch>/`, `Tools/TripoAPI/output/<job>/`.

**Why ignored:** raw output is iteration cost, not deliverable. Committing it pollutes history with rejected variations. Workshop discipline keeps repository signal-to-noise high.

### Zone 2 — Curated (`Documents/<Domain>Design/`)

- **Purpose:** anchor assets, accepted variants, design references — the artifacts that *define what we agreed*.
- **Git status:** committed.
- **Lifetime:** permanent (until intentionally archived).
- **Naming:** strict convention (see below).

Subdivisions:
- `Documents/<Domain>Design/Anchors/` — tone-defining anchor assets + their `.prompt.txt` reproduction notes.
- `Documents/<Domain>Design/<Category>/` — accepted non-anchor production assets.
- `Documents/<Domain>Design/_archive/` — superseded but historically interesting.

Examples: `Documents/AudioDesign/Anchors/`, `Documents/ArtDesign/Concepts/Bugs/`, `Documents/NarrativeDesign/Lore/`.

### Zone 3 — Engine import (`Assets/`, `src/`, etc.)

- **Purpose:** assets that the engine actually loads at build time.
- **Git status:** typically committed. Large binaries (`.fbx`, large `.png`, audio) sometimes via Git LFS or `.gitignore` if regenerable.
- **Lifetime:** governed by engine + build pipeline.
- **Naming:** engine conventions (e.g. Unity `_normal.png` suffixes, Godot `.import` companions).

Some artifacts live in **both** Zone 2 and Zone 3 — for example, a 3D mesh's render preview lives in Zone 2 (design reference, committed `.png`), while the `.fbx` itself lives in Zone 3 (`Assets/03.Models/`, often `.gitignore`d if regenerable).

---

## Naming convention

```
<prefix>_<subcategory>_<scene>_<variant>.<ext>
```

Domain-specific prefixes:

| Domain | Prefix | Example |
|---|---|---|
| Sound — music | `mus_` | `mus_combat_ch1_anchor.mp3` |
| Sound — voice | `vox_` | `vox_host_ch1_intro.mp3` |
| Sound — SFX | `sfx_` | `sfx_weapon_pistol_v01.wav` |
| Sound — ambient | `amb_` | `amb_jungle_loop_anchor.ogg` |
| Art — character | `char_` | `char_protagonist_anchor.png` |
| Art — environment | `env_` | `env_forest_dawn_v02.png` |
| Art — UI | `ui_` | `ui_card_strength_anchor.png` |
| Art — VFX | `vfx_` | `vfx_explosion_concept_v01.png` |
| Art — prop | `prop_` | `prop_cover_lowwall_anchor.png` |
| Art — icon | `icon_` | `icon_ability_dash_v01.png` |
| Art — concept | `concept_` | `concept_chapter1_keyvis_v02.png` |
| Narrative — dialogue | `dlg_` | `dlg_npc_merchant_greeting.txt` |
| Narrative — lore | `lore_` | `lore_world_history_v01.md` |

Variant suffix conventions:
- `_a / _b / _c` — same-batch variants for A/B comparison.
- `_v01 / _v02 / _v03` — time-ordered iterations.
- `_anchor` — *not* used in filename; anchor status is signified by *folder location* (`Anchors/` vs `<Category>/`).

The prefix list is **append-only** per project — adding a new domain (e.g. `cinematic_` for in-engine cutscenes) is fine; renaming an existing prefix is destructive.

---

## Companion files

Every Zone 2 artifact ships with a `.prompt.txt` reproduction note:

```
Documents/AudioDesign/Anchors/
  mus_combat_ch1_anchor.mp3       ← the asset
  mus_combat_ch1_anchor.prompt.txt ← how it was generated
```

The `.prompt.txt` contains:
1. **Reproduce command** — exact CLI / API call (copy-pasteable).
2. **Meta** — tool, model, settings, generation date, cost.
3. **Tone keywords** — extracted style descriptors that became part of the Bible README.
4. **Use** — what scenes / categories this asset is for.
5. **Variation plan** — known follow-ups (e.g. "Ch2 variation TBD when Phase 5 begins").

This means *anyone* (including future-you with stale memory) can reproduce or extend the asset without re-deriving its prompt.

---

## Promotion workflow (Zone 1 → Zone 2)

```
1. AI tool runs, drops raw output in Tools/<Service>/output/
2. User auditions the output (5-10 second A/B vs anchor).
3. If accepted:
     a. mv to Zone 2 with proper <prefix>_<sub>_<scene>_<variant> name
     b. write companion <name>.prompt.txt
     c. update the Bible README's category table
4. If rejected: leave in workshop or delete; do NOT commit.
```

Engine import (Zone 3) typically *follows* promotion — the curated Zone 2 asset is referenced by an engine-side import target. This separation prevents engine-only changes from polluting design history.

---

## What this prevents

| Failure mode | Without zones | With zones |
|---|---|---|
| Workshop noise in git history | Every Suno call commits 2 mp3s | Workshop is `.gitignore`d |
| Cannot reproduce 6-month-old asset | Lost to memory | `.prompt.txt` captures everything |
| Asset name conflicts | `combat_music.mp3` collides | Prefix system: `mus_combat_ch1_anchor.mp3` |
| Engine asset drift from design source | Edits in Zone 3 only — design docs go stale | Promotion gate forces Zone 2 update |
| New AI tool adopted | Mixed conventions per tool | All tools share same Zone 2 / Zone 3 layout |

---

## Engine-agnostic

Same three zones apply for Unity (`Assets/`), Godot (`res://`, scripts/scenes), Unreal (`Content/`, `Source/`), GameMaker (`projects/<name>/`), or any engine-less / web project. The path roots change; the discipline is identical.

---

## Adoption notes

1. Add `Tools/*/output/` to `.gitignore`.
2. Create `Documents/<Domain>Design/` for each domain you produce assets in.
3. Decide your prefix list in advance — add to `docs/rules/artifact-organization.md` (this file) per project.
4. Wire `/governance-bible-init` to set up Zone 2 anchor folders + Bible README.
5. Wire `/api-cost-gate` in front of any paid Zone 1 calls.

The combination of these three rules — workshop discipline, prefix naming, companion `.prompt.txt` — is what lets a 1-person dev managing AI-generated assets across many tools maintain a coherent project at the 6+ month scale.
