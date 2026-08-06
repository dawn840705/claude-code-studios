# Level Design Sources — cite, link, do not copy

Reference list for `/spatial-audit` and the spatial-design skills. **This file
holds links and one-line summaries only.** The licensing section below is the
reason, and it is not a formality.

---

## Licensing — why nothing is copied into this repo

### The Level Design Book — CC BY-NC-SA 4.0

[book.leveldesignbook.com](https://book.leveldesignbook.com/) is licensed
[CC BY-NC-SA 4.0](https://book.leveldesignbook.com/appendix/license). Two of its
three clauses are incompatible with this repo:

- **ShareAlike** — any derivative must carry CC BY-NC-SA 4.0. This plugin is
  **MIT** (`.claude-plugin/plugin.json`). Pasting their prose into `docs/` or a
  skill would relicense that material and put two incompatible licenses in one
  distribution.
- **NonCommercial** — this plugin is used to build commercial games. NC material
  embedded in the toolchain is a liability we get nothing for.

So: **link and paraphrase in our own words; never paste, never mirror, never
vendor the `.md` endpoints.** Reading their pages at authoring time to check a
claim is normal use and is fine. Shipping their sentences is not.

This is the same call the repo made for `claude-seo` — cite the upstream, route
work to it, do not vendor it (CHANGELOG, Unreleased).

The site publishes an [llms.txt index](https://book.leveldesignbook.com/llms.txt)
and a `.md` version of every page (append `.md` to any page URL). That makes it
convenient to *read*. Convenience to read is not permission to copy.

Attribution format when a finding leans on one of their pages:

> "Prospect-refuge", The Level Design Book, https://book.leveldesignbook.com/process/blockout/massing/prospect-refuge

### Christopher Totten — *An Architectural Approach to Level Design*, 2nd ed.

Routledge, copyrighted, no open license. Cite from your own reading. Do not
quote at length and do not reproduce its figures.

Note: The Level Design Book **deliberately excludes material from other level
design books** (their fair-use judgment), so Totten's content is not available
through it. The two sources are separate and must be cited separately.

### Articles, videos and platform documentation

Everything in the "Practice" table below is someone else's copyrighted article,
video or vendor documentation. Same rule, no exceptions: **link, paraphrase in
our own words, never paste.** Vendor documentation (Steamworks and the mobile
stores) has a second failure mode — it changes without notice, so a figure taken
from it is only true on the date it was read. Where this repo repeats a platform
number, it carries a read date; when it matters, re-read before relying on it.

---

## Primary sources

| Source | What it gives us | Link |
| ---- | ---- | ---- |
| The Level Design Book — Massing | Volume hierarchy, additive vs subtractive, readability | [/process/blockout/massing](https://book.leveldesignbook.com/process/blockout/massing) |
| — Prospect-refuge | Vantage/safety theory applied to cover and sightlines | [/process/blockout/massing/prospect-refuge](https://book.leveldesignbook.com/process/blockout/massing/prospect-refuge) |
| — Composition | Landmarks, vistas, approaches; also why "leading lines" aren't real | [/process/blockout/massing/composition](https://book.leveldesignbook.com/process/blockout/massing/composition) |
| — Metrics | Proportions and distances; how big a level *feels* | [/process/blockout/metrics](https://book.leveldesignbook.com/process/blockout/metrics) |
| — Modular kit design | Measuring and designing 3D tilesets | [/process/blockout/metrics/modular](https://book.leveldesignbook.com/process/blockout/metrics/modular) |
| — Wayfinding | Guiding the player without telling them | [/process/blockout/wayfinding](https://book.leveldesignbook.com/process/blockout/wayfinding) |
| — Circulation | How areas link; the connectivity graph | [/process/layout/flow/circulation](https://book.leveldesignbook.com/process/layout/flow/circulation) |
| — Verticality | How up and down feel to traverse | [/process/layout/flow/verticality](https://book.leveldesignbook.com/process/layout/flow/verticality) |
| — Parti | The one-sentence core idea of a layout | [/process/layout/parti](https://book.leveldesignbook.com/process/layout/parti) |
| — Typology | Abstract layout patterns with concrete examples | [/process/layout/typology](https://book.leveldesignbook.com/process/layout/typology) |
| — Cover | Shapes that block sightlines | [/process/combat/cover](https://book.leveldesignbook.com/process/combat/cover) |
| — Map balance | Fairness of player options; pvp symmetry | [/process/combat/balance](https://book.leveldesignbook.com/process/combat/balance) |
| — D6 lighting | Six interior lighting strategies, spatially | [/process/lighting/d6-lighting](https://book.leveldesignbook.com/process/lighting/d6-lighting) |
| — Lighting for darkness | Dark mood while preserving readability | [/process/lighting/darkness](https://book.leveldesignbook.com/process/lighting/darkness) |
| Totten, *An Architectural Approach to Level Design*, 2nd ed. (Routledge) | The book-length treatment: massing, program, parti, Disneyland case study | — |
| Francis D.K. Ching, *Architecture: Form, Space, and Order* | The upstream architectural vocabulary the above borrows from | — |
| Kevin Lynch, *The Image of the City* (1960) | Path / edge / district / node / landmark — strongest for open world | — |
| Jay Appleton, *The Experience of Landscape* (1975) | Prospect-refuge, the original formulation | — |

## Practice — techniques with named origins

Cite these by name rather than presenting them as house method. Both are used in
`docs/templates/player-metrics.md`, `docs/templates/level-design-document.md`
(Teaching Structure) and `agents/level-designer.md`.

| Source | What it gives us | Link |
| ---- | ---- | ---- |
| Luke McMillan, "The Rational Design Handbook: An Intro to RLD" | The RLD method — quantify UX elements to make difficulty comparable | [gamedeveloper.com](https://www.gamedeveloper.com/design/the-rational-design-handbook-an-intro-to-rld) |
| — "The Rational Design Handbook: Four Primary Metrics" | Which player capabilities to measure first | [gamedeveloper.com](https://www.gamedeveloper.com/design/the-rational-design-handbook-four-primary-metrics) |
| Chris McEntee, "Rational Design: The Core of *Rayman Origins*" | RLD as practised at Ubisoft on a shipped platformer — scoring each atom of gameplay, pacing spatially | [gamedeveloper.com](https://www.gamedeveloper.com/design/rational-design-the-core-of-i-rayman-origins-i-) |
| Mark Brown (Game Maker's Toolkit), "Super Mario 3D World's 4 Step Level Design" | Kishōtenketsu as a level structure; the four beats and why the twist is the load-bearing one | [Internet Archive copy](https://archive.org/details/SuperMario3DWorlds4StepLevelDesignGameMakersToolkit) · channel: [Game Maker's Toolkit](https://www.youtube.com/c/MarkBrownGMT) |

**On the kishōtenketsu attribution.** The four-act form is a classical East Asian
narrative structure (起承転結), not a Nintendo invention; nobody owns 기승전결, so
cite the *application*, not the form.

That application is credited to Koichi Hayashida (Nintendo), and Brown's video is
the best-known explanation of it. **We have not read a Hayashida interview
first-hand** — the attribution here comes through Brown, so it is second-hand
(`추정` under `rules/claim-confidence.md`). Do not present it as a primary source
until someone in this repo has cited the interview directly.

## Pre-production — reference gathering

Tools, not theory. Listed because "gather references before you block out" is a
step designers skip and then rediscover expensively.

| Tool | Role | Note |
| ---- | ---- | ---- |
| [noclip.website](https://noclip.website) | Free-fly model viewer for levels from shipped games | Reference shots and layout analysis in the actual geometry. Read-only, in-browser |
| [PureRef](https://www.pureref.com/) | Always-on-top reference board | Free; the standard tool for the mood-board step |

---

## Explicitly rejected

**Shape psychology and color psychology.** "Round = safe", "angular = threat",
"red = danger" as universal claims. There is no evidence base, and the primary
source we lean on rejects them by name — its page is titled
[Shape and color psychology](https://book.leveldesignbook.com/process/env-art/psychology)
and subtitled *"Bullshit design theories that link abstract visual phenomena to
universal human behavior."*

No skill in this repo may score a space by the mood of its shapes. A shape claim
is admissible only when it reduces to something measurable: sightline length,
traversal cost, silhouette distinctness at range, contrast ratio.

**"Leading lines."** Same category — see the Composition page above.

Both are easy to generate convincingly and impossible to verify, which is
exactly the combination `rules/claim-confidence.md` exists to stop.

---

## Unity-side tooling

| Tool | Role | Note |
| ---- | ---- | ---- |
| `hera-agent-unity` | Editor control from the shell — `exec` / `console` / `scene` / `editor` / `screenshot` | Stateless CLI over an in-editor HTTP server, **not** an MCP. `exec` runs arbitrary C#, so the ProBuilder API is *probably* reachable **(추정 — `exec` 의 컴파일 컨텍스트가 `Unity.ProBuilder` 어셈블리를 참조하는지 확인 안 됨. 첫 호출에서 확인할 것)**. `screenshot` is documented but **[확인 필요]** — this project's tooling log verified `exec` / `console` / `scene load` / `editor refresh\|play\|stop` and not that one. Trap: no output means the call did not run — see the sentinel contract in `skills/spatial-audit/SKILL.md` § 2A |
| ProBuilder (`com.unity.probuilder`) | In-editor blockout / greyboxing | Unity official, free. The grid it is configured to determines every metric downstream |
| Unity MCP (CoplayDev, IvanMurzak) | Alternative editor-control path | Not used here. `docs/engine/unity-mcp-workflow.md` documents the MCP route for projects that do use it |
