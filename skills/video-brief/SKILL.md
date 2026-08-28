---
name: video-brief
description: "Plan a video before anyone captures footage — purpose, structure, shot list, rights, and the target platform's live requirements. Use when the user says 'we need a trailer', 'make a store video', 'a demo video for the landing page', 'a short for TikTok', or before a store submission that needs a preview video. Produces a brief and a shot list; it does NOT edit video and does NOT write copy for a finished cut. Do not use to cut existing footage — that is the external video-use tool (../../docs/video-production-sources.md), and do not use for still store assets."
---

# Video Brief — decide before you capture

Two failures make a video expensive, and **neither can be fixed in the edit**:

1. **The footage does not exist.** The shot needs a feature that is not built, a
   save state nobody has, or a build that has since moved on.
2. **The platform rejects the footage.** Apple states that an app preview must
   show only content within the app and must not film people interacting with a
   device — so an over-the-shoulder shot is rejected no matter how well it is
   cut, and no edit recovers it.

Both are decided before capture. That is what this skill is for. It does not
edit, and it does not judge whether a finished cut is good — it produces the
document that makes those later steps answerable.

**Scope boundary.** Whether the video *worked* is an analytics question, not a
brief question. Do not put an unfalsifiable success claim in the brief; § 2
forces the alternative.

---

## 1. Resolve context before asking anything

1. **Project type** — the session hook prints `PROJECT_TYPE`. `game` routes to
   trailer/short defaults and game agents; `web`/`mobile`/`service` routes to
   demo/short and product agents. On `unknown`, ask before spawning anything
   (`AGENTS.md` § Agent usage rules).
2. **Read what the product already claims about itself** — `design/gdd/game-concept.md`
   and `design/gdd/game-pillars.md` on a game track, `product/prd/` and the
   product concept on a product track. A video that contradicts the pillars is a
   positioning problem, and surfacing it here is cheaper than after capture.
3. **Kind** — from `--kind`, else infer from what the user said and **state the
   inference**. The four kinds are `trailer` (store), `demo` (service/app),
   `short` (vertical feed), `longform` (devlog / tutorial).
4. **Platform** — from `--platform`, else ask. This is not cosmetic: it fixes
   duration, aspect ratio, whether sound exists, and several hard content rules.
5. **Review mode** — `--review`, else `production/review-mode.txt`, else `lean`.

---

## 2. Fix the job of the video

Ask the user directly for the four fields in the template's § 1 that the project
docs cannot answer: the specific viewer, where they meet it, the one belief they
should leave with, and the next action.

Two things to hold the line on, because both are where briefs go soft:

- **"Everyone" is not an audience and "awareness" is not a next action.** Push
  once for a specific answer. If the honest answer really is awareness with no
  CTA, write that down — a stated null is a decision; an unstated one is a gap.
- **The success metric must be falsifiable, or labelled as not attributable.**
  Wishlist counts after a trailer drop are confounded by everything else shipping
  that week. Say so in the brief rather than promising attribution the team
  cannot produce.

**Assume muted playback** unless the placement guarantees otherwise. Store pages
and feeds autoplay without sound, and that constrains the *structure* — it is not
a subtitles task at the end.

---

## 3. Re-read the platform spec — every run, no exceptions

**Fetch the vendor page for each target platform and record the date.**
`../../docs/video-production-sources.md` holds the links and the last known figures;
it does not excuse you from re-reading them.

The reason is recorded in that file: while it was being written, two figures
taken from third-party ASO blogs were wrong against the vendor documentation, and
re-reading the vendor page is what caught them. **Third-party summaries are not
an acceptable source for a platform requirement.**

| Situation | What to record | Verdict |
| ---- | ---- | ---- |
| Vendor page fetched and read | The figures, the URL, and today's date in the brief's header | unaffected |
| Fetch failed or the page moved | The last known figures from `../../docs/video-production-sources.md`, tagged `추정 — 벤더 페이지 확인 실패` per `../../rules/claim-confidence.md` | **BLOCKED** |

The second row is BLOCKED, not CONCERNS, and the reason is the `exit 3` rule in
`../../docs/deterministic-gates.md`: **a check that could not run has produced no
verdict, and no verdict is not a pass.** An unverified spec is an unknown spec,
and § 6 already says capturing against an unknown spec is how footage gets thrown
away. Writing the brief is still useful — write it, mark the platform section
unverified, and do not call it READY.

Never present an unverified figure as a requirement.

---

## 4. Draft the structure, then the shot list

Work from `../../docs/templates/video-brief.md`. Two passes, and the order matters —
the structure decides what footage is needed, not the reverse.

### 4.1 Structure

Fill the table for the resolved kind and delete the other three. The defaults
have named origins (`../../docs/video-production-sources.md`); **deviating is allowed,
deviating silently is not** — write the reason in the notes column.

For a game trailer, the two rules worth defending against pressure from inside
the team:

- **Genre legible by 0:10.** Before the viewer can name what they are looking
  at, nothing else you show can land. A studio logo on a black screen at 0:00
  spends the most valuable three seconds in the video.
- **Every claim needs footage that proves it.** "Tell, Show, Repeat" fails when
  a title card asserts something the following shot does not demonstrate. Walk
  the table and check each pair.

For a demo, the equivalent is: **lead with the problem, and place the moment it
clicks early.** This one is weaker evidence than the trailer rules — it is
aggregated practitioner advice, not a vendor rule or a named primary source
(`../../docs/video-production-sources.md` flags the caveat). Present it as the default
structure, not as a measured finding, and do not quote the retention percentages
those posts carry.

### 4.2 Shot list

Every row names footage a person must capture. The column that earns the
document is **Exists?**:

- A shot needing an unbuilt feature is a **schedule dependency**. Name it, and
  say what unblocks it. Do not quietly design around it — a trailer built only
  from what happens to exist today shows the game you have, not the one you are
  selling.
- A shot needing a scripted setup (a specific save, a staged encounter, a seeded
  account) is a **capture-day task**. It gets discovered at the worst moment if
  it is not written here.

Set the capture standard once — resolution, frame rate, HUD on/off, quality
preset, no debug overlays, no placeholder art in frame — and apply it to every
row. Mixed capture settings across shots are visible in the cut and cannot be
repaired.

### 4.3 Who to spawn

Route by `../../rules/route-hint.md`. **Route on this skill's artifact, not on the
video's stakes** — the artifact is a markdown brief, which is R1/R2 under
`../../rules/verify-route.md`, and production route and verification route are
independent axes that must not be inferred from each other. A store trailer being
a public first impression argues for checking the brief harder, not for building
it with more agents.

| Route | When | Spawn |
| ---- | ---- | ---- |
| light | A short, a devlog, or a re-cut of an approved brief | Nobody. Fill the template yourself |
| standard — **the default** | Everything else | `community-manager` (marketing lead framing) |
| heavy | Opt-in only: the user asked for a team pass, or the structure is genuinely contested | + `art-director`, plus `game-designer` (game) or `product-manager` (product) |

Tied between two routes? Take the lighter one.

**Narrow tools at spawn: `tools: Read, Glob, Grep`.** `community-manager` and
`art-director` have `Write` by default, and this skill's premise is that the
orchestrator is the sole writer. Read-only is guaranteed by permission, not by
asking nicely (`../../rules/subagent-collaboration.md` § 3.1).

Write ownership, settled before spawning as § 2.1 requires:

| Agent | Writes | Reads only |
| ---- | ---- | ---- |
| community-manager | nothing — returns findings as text | project docs, this brief's draft |
| art-director | nothing — returns findings as text | same, plus `design/art/art-bible.md` if it exists |
| game-designer / product-manager | nothing — returns findings as text | same |

Give each spawn full context; it cannot see this conversation.

---

## 5. Rights and content rules

Walk the template's § 4 and § 5 tables to the end, using only what
`../../docs/video-production-sources.md` actually records for the target platform plus
what you re-read in § 3. **Do not state a store policy from memory** —
`../../rules/claim-confidence.md` § 2 puts regulatory and policy clauses in the
verify-before-writing category, and platform policy is exactly that.

What is recorded, and therefore safe to assert: Apple requires previews to show
only in-app content and tells publishers to display only material they hold the
rights to; Google Play requires monetization off, which a copyright claim on
borrowed music can defeat. Anything beyond those, verify or mark 추정.

**An unresolved rights row makes the verdict BLOCKED, not CONCERNS.** A brief
that says "probably fine on the music" is how a rejection gets discovered after
the capture budget is spent — and unlike a spec figure, this one is not merely
unverified, it is unresolved.

---

## 6. Verdict

| Verdict | Meaning |
| ---- | ---- |
| **READY** | Structure approved, every shot either exists or has a named unblocker, platform spec verified today, rights cleared. Capture may begin |
| **CONCERNS** | Usable, but at least one of: a success metric is not attributable, a structural deviation is unexplained, a shot has an unblocker with a date but not a build. Named and fixable |
| **BLOCKED** | Rights unresolved, the platform undecided, **the vendor spec could not be re-read** (§ 3), or a required shot depends on a feature with no date. Capture must not begin — capturing against an unknown spec is how footage gets thrown away |

**READY is about the brief, not the video.** It says the expensive decisions have
been made, not that the result will be good.

---

## 7. Write the brief

**Ask before writing.** Show the structure table and the shot list in
conversation and confirm the path with the user before creating the file.

On approval, write to `production/marketing/video-brief-<name>.md` using
`../../docs/templates/video-brief.md`. That path is the convention `verify_policy.py`
P4 expects; do not invent a new one.

---

## Next steps

- `READY` → capture against the shot list, then hand off to editing. The external
  tool this repo delegates to is named in `../../docs/video-production-sources.md` §
  "Execution tooling" — it makes a **paid** transcription call per source file,
  so run `$api-cost-gate` before the first invocation.
- `BLOCKED` on a shot dependency → the shot is a story. `$create-stories`, then
  revisit this brief when it lands.
- Store submission → `$release-checklist` and `$launch-checklist` own the
  submission itself; this brief is an input to them, not a substitute.
- A cut that deviates from the approved structure → back here for re-approval,
  not ratified after the fact.
- The same defect appearing in a second video → `$lesson-log`.

## Error Recovery Protocol

If a spawned agent returns BLOCKED or errors:

1. **Surface it immediately** — "[AgentName]: BLOCKED — [reason]" before
   continuing to any dependent step.
2. **Assess the dependency.** The shot list depends on the structure; do not
   build one on a missing other.
3. **Offer options** by asking the user directly: skip and record the gap, retry
   narrower, or stop and resolve the blocker.
4. **Always produce a partial brief.** Never discard completed sections because
   one step blocked.
