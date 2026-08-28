# Video Brief: [Video Name]

> **Status**: Draft | Approved | Captured | Locked
> **Kind**: [trailer | demo | short | longform]
> **Owner**: [community-manager (marketing lead) / product-manager]
> **Target platform(s)**: [Steam / App Store / Google Play / YouTube / TikTok / internal]
> **Platform spec read on**: [YYYY-MM-DD — see § 5; a spec nobody re-read is 추정, not fact]
> **Last Updated**: [Date]

---

## 1. The decision this brief exists to make

> **Guidance**: A video is expensive in the one resource a small team cannot buy
> back — the build has to be presentable, someone has to capture it, and every
> cut is a judgment. The brief is where the expensive decisions get made
> *before* capture, because two failures cannot be fixed in the edit at all:
> footage that does not exist, and footage a platform will reject.

| Field | Answer |
|-------|--------|
| **Who is this for** | [The specific viewer. "Gamers" and "users" are not answers — who are they, and what were they doing 5 seconds before this video started playing?] |
| **Where do they meet it** | [Store page autoplay / a feed / a link you sent / an embedded landing page. This decides sound, length and aspect ratio before anything else does] |
| **What must they believe afterward** | [One sentence. If you cannot write one, the video has no job] |
| **What do they do next** | [Wishlist / install / sign up / nothing — awareness only. "Nothing" is a legitimate answer; an unstated CTA is not] |
| **How we would know it worked** | [The metric, and whether it is actually attributable to this video. Say "not attributable" when it is not — an unfalsifiable success criterion is worse than none] |

**Does it play with sound?** [Yes / No / **Assume not**]
Store pages and feeds autoplay muted. If the answer is "assume not", every beat
must survive with the audio off, and that is a constraint on the *structure*, not
a subtitle task at the end.

---

## 2. Structure

> **Guidance**: Pick the structure for your kind and delete the others. These are
> defaults with named origins (`docs/video-production-sources.md`), not laws —
> but deviate on purpose and write the reason in the notes column.

### 2a. Game trailer (store)

The practitioner default: start from the game's own chronological order, then cut
everything that is not doing work. Genre must be legible in the first 5–10
seconds — before that, the viewer does not know what they are looking at, so
nothing else you show can land.

| Beat | Target time | Content | Notes |
|------|------------|---------|-------|
| Hook | 0:00–0:03 | [The most legible action in the game. Not a logo, not a fade from black] | Steam: autoplays muted at the top of the page |
| Genre statement | 0:03–0:10 | [The viewer should now be able to name the genre and the core verb] | |
| Development | 0:10–0:50 | ["Tell, Show, Repeat" — a title card claims something, the footage proves it. Repeat 3–4 times] | Each claim needs footage that actually proves it |
| Escalation | 0:50–1:15 | [Variety, scale, or the thing you saved] | |
| Close | 1:15–1:30 | [Title, platform, date or "wishlist now"] | The only place logos belong |

**Total target**: [60–90 s]

### 2b. Product demo (service / app)

Problem first, product second. The viewer must recognise their own situation
before anything is shown to them; a demo that opens on the logo has spent its
most valuable seconds on the least persuasive content.

| Beat | Target time | Content | Notes |
|------|------------|---------|-------|
| Problem | 0:00–0:10 | [The pain, stated as the viewer would state it] | Lead here, not with branding |
| The turn | 0:10–0:25 | [The moment it clicks — the single interaction where the value becomes obvious] | Place it early; a payoff at 1:20 is a payoff most of the audience never reaches (추정 — 실무 관행, 1차 출처 없음) |
| Proof | 0:25–1:00 | [A concrete outcome in the real product: the report generated, the time saved, the state changed] | Real UI. If this is going to a mobile store, mocked UI also breaks a platform rule — check § 5 |
| CTA | 1:00–1:15 | [The one next action] | |

**Total target**: [60–180 s, shorter end preferred. This range is aggregated
practitioner advice, not a measured finding and not a platform rule — see
`docs/video-production-sources.md` for the caveat. If the video runs long, say
what the extra time buys]

### 2c. Short form (TikTok / Shorts / Reels)

| Beat | Target time | Content |
|------|------------|---------|
| Hook | 0:00–0:02 | [The single most arresting frame or claim. There is no runway] |
| Payoff | 0:02–0:20 | [Deliver what the hook promised — the entire video is this contract] |
| Tag | 0:20–0:30 | [Name and where to find it] |

Vertical 9:16, burned-in captions, no reliance on sound.

### 2d. Devlog / tutorial (long form)

| Beat | Content |
|------|---------|
| Cold open | [The result, the problem, or the surprising claim — before any intro] |
| Context | [What the viewer needs to follow along, and nothing more] |
| Body | [Chaptered. One idea per chapter; list them so the edit has a spine] |
| Resolution | [What changed, what is still open] |

Chapters go in the description as timestamps. Length follows the content here,
unlike every other kind on this page.

---

## 3. Shot list

> **Guidance**: This is the section that earns the brief. Every row is footage
> someone has to capture, and **capture is the step that cannot be redone
> cheaply** once the build has moved on. Write it before you record, not after.
>
> "Exists?" is the important column. A shot that needs a feature that is not
> built yet is a schedule dependency, and it belongs in the sprint plan rather
> than being discovered on capture day.

| # | Beat | Shot | Source | Capture settings | Exists? | Notes |
|---|------|------|--------|-----------------|---------|-------|
| 1 | Hook | [What happens on screen] | [Build / scene / URL] | [Resolution, fps, HUD on/off, quality preset] | [Yes / Needs feature X / Needs a scripted setup] | |
| 2 | | | | | | |

**Capture standard** (set once, applied to every row): [e.g., 2560×1440, 60 fps,
max settings, HUD on, no debug overlays, no placeholder art in frame]

**Blocking dependencies**: [Shots that cannot be captured yet, and what unblocks
each. If this list is non-empty, the brief is approved but capture is not.]

---

## 4. Assets and rights

| Asset | Source | Licence / rights | Cleared? |
|-------|--------|-----------------|----------|
| Music | [Track] | [Licence and territory] | |
| SFX | | | |
| Voiceover | | | |
| Fonts / logos | | | |
| Third-party IP visible in frame | | | |

**Rights are a hard gate, not a checklist item.** You need the rights to
everything visible and audible regardless of platform; on top of that, Apple
tells publishers explicitly to show only material they hold the rights to in a
preview, and Google Play requires monetization to be off — which a copyright
claim on borrowed music can defeat on its own. Do not write any other store
policy here from memory; take it from § 5 or mark it 추정.

Unresolved rows make the brief **BLOCKED**, not CONCERNS.

---

## 5. Platform specification

> **Guidance**: Copy in only the platforms this video actually targets, from
> `docs/video-production-sources.md`, **and record the date the vendor page was
> read**. Vendor requirements change without notice, and third-party ASO blogs
> get them wrong often enough that they are not an acceptable source.

| Platform | Requirement | This video | Compliant? |
|----------|------------|-----------|-----------|
| [Platform] | [Duration] | [Actual] | |
| | [Aspect / resolution / fps] | | |
| | [Codec / container / file size] | | |
| | [Content rules — capture source, no fingers on device, age suitability, disclosure] | | |
| | [Hosting rules — YouTube URL form, monetization off, visibility, embeddable] | | |

**Spec read on**: [YYYY-MM-DD] · **Source**: [vendor URL]

---

## 6. Verification before lock

| Check | How | Result |
|-------|-----|--------|
| Plays legibly with sound off | Watch muted end to end | |
| Genre / value legible by 0:10 | Show it to someone who has not seen the product | |
| Every claim has footage that proves it | Walk the structure table against the cut | |
| Nothing on screen is placeholder, debug, or unreleased | Frame check | |
| Platform spec | § 5 table, all rows | |
| Rights | § 4 table, all rows cleared | |
| Poster / thumbnail frame chosen deliberately | [Apple: default is 5 s in; Google Play uses the feature graphic] | |

---

## 7. Execution handoff

Editing is not done in this document. `docs/video-production-sources.md` §
"Execution tooling" names the external tool this repo delegates to
(`browser-use/video-use`) and what it costs — it makes a **paid** transcription
call per source file, so gate it with `/api-cost-gate` before the first run.

**What crosses the handoff**: this brief, the shot list with captured file paths,
and the structure table as the intended cut order. What does not cross it: the
decision authority. A cut that deviates from the approved structure comes back
here for re-approval rather than being ratified after the fact.
