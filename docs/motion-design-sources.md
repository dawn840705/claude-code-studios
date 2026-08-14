# Motion Design Sources — product track, cite and verify before you rely

Reference list for web/app interface motion. Same discipline as
`docs/video-production-sources.md` and `docs/level-design-sources.md`: **this file
holds links, one-line summaries and read dates. It copies nothing.**

Product track only. None of this transfers to a game engine — it is DOM, CSS and
React, and a Unity or Godot project should ignore this file entirely.

---

## Hazard — licence claims are not licences

A footer that says "MIT" is a claim, not a licence. Verify the repository actually
carries a `LICENSE` file before vendoring any code from a source here. This plugin
ships to users and cannot carry someone else's code on an unverified claim.
`rules/claim-confidence.md` applies: an unverified licence is `[확인 필요]`, not fact.

Paraphrasing a technique, or writing our own implementation after reading a
described behaviour, is not vendoring and carries no such risk.

---

## Kinetics — spring-physics micro-interactions

| | |
| ---- | ---- |
| Site | [kinetics.colorion.co](https://kinetics.colorion.co/) |
| Source | [github.com/ckissi/kinetics](https://github.com/ckissi/kinetics) |
| What it is | A gallery of ~143 interface animations built on spring physics rather than fixed-duration easing. Static Astro site, no signup, no API. |
| Read date | 2026-08-14 |

**What it is actually good for, in this order:**

1. **The per-effect AI prompt.** Every card ships CSS, React, *and* a natural-language
   prompt written as a spec with prohibitions included — "animate only the height with
   `cubic-bezier(0.34, 1.56, 0.64, 1)` over ~0.5s… no JS height measurement, no
   max-height hacks". That is a briefing format worth imitating in `/ux-design` output,
   independent of whether the effect itself is ever used.
2. **A duration-versus-spring argument, stated well.** A fixed duration has no idea
   where an interruption left it, so it snaps or stutters; a spring keeps integrating
   from its current velocity. Usable in a UX spec's motion section.
3. **AI-app state vocabulary.** Its Feedback & State category includes Token Stream,
   Agent Handoff, Optimistic Rollback, Rate Limit Cooldown and Vector Recall — visual
   treatments for states an LLM-backed product has and a conventional app does not.
   `/web-ai-patterns` covers those states in code and says nothing about how they look.

**Two cautions, both measured:**

- **Licence unverified.** The site footer says "MIT licensed"; the GitHub repository
  has no `LICENSE` file and no declared licence. Read the prompts, write our own
  implementation. Do not copy the CSS or React verbatim into a deliverable without
  resolving this with the author first.
- **Its own counts disagree.** The site says 144 patterns, the repository README says
  35, distinct named cards number 143 (Pulse Badge appears twice) and the search index
  holds 142 keys. Treat any figure from this source as `추정` unless counted directly.

**Not a dependency.** Nothing here gets installed, added to `.claude/settings.json`, or
vendored into this repository. It is a reading source for `/ux-design` and
`frontend-engineer` on product-track work.
