# Meeting — <topic>

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Facilitator | <Producer / Director / Lead> + <participating agents> |
| Topic | <one-line agenda — what's being decided> |
| Decision status | ⏳ Pending / ✅ Accepted / ❌ Rejected / ⏸ Deferred |
| Roll-up report | [`YYYY-MM-DD.md`](YYYY-MM-DD.md) (daily summary, optional) |
| Companion | [<related-meeting>.md](<related-meeting>.md) (optional, for parity decisions) |

---

## § 0 — Context

(2-5 bullets — only what a future reader needs to interpret the decision. Avoid restating known project state.)

- <relevant prior decision / memory>
- <constraint that drives this meeting>
- <existing assets in scope>

---

## § 1 — Question 1: <one-line>

(Replace with the actual question; add §2, §3 etc. as needed.)

### Option A — <name>
<2-3 sentences: what + trade-off + cost>

### Option B — <name>
<2-3 sentences>

### Option C — <name>
<2-3 sentences>

### <Lead> recommendation — **<option>**
<1 sentence reason>

---

## § 2 — Question 2: <one-line>

(Same shape as §1.)

---

## § 3 — Cross-cutting analysis (optional)

(Use when decisions in §1 and §2 are coupled, or when a parity comparison is needed.
e.g. "How does this Q1 choice constrain Q2", or "Comparison with sibling decision in [companion meeting]".)

### Reusable parts (5 items max)

1. <pattern that transfers from sibling decision>
2. ...

### Domain-specific differences (3 items max)

1. <where this domain diverges>
2. ...

---

## § 4 — Producer / Director synthesis

<Lead role> recommendation **fully accepted** — plus N additional considerations:

1. **<concern 1>** — <why it matters> → <action implication>
2. **<concern 2>** — ...
3. ...

---

## § 4.5 — Tooling decisions (optional)

(Use when the meeting also concludes a tool stack change — adoption / deprecation / deferral.)

### <tool A> — adopted / deprecated / deferred
**Why:** <2-3 lines>

### Resulting stack

| Category | Tool | Notes |
|---|---|---|
| ... | ... | ... |

**Re-evaluation triggers** — <when do we revisit?>

---

## § 5 — Decisions + carryovers

| ID | Item | Adopted |
|---|---|---|
| D0 | (precondition — gating decision needed *before* others) | ⏳ separate track |
| D1 | Q1 chosen option | ✅ Option <X> (<short reason>) |
| D2 | Q2 chosen option | ✅ |
| D3 | Implementation order | ✅ <step 1 → step 2 → step 3> |
| D4 | Folder / location | ✅ `<path>` |
| D5 | Naming convention | ✅ `<pattern>` |
| D6 | Initial scope | ✅ <chapter / area / phase> only — gradual expansion |

⭐ = recommendation entry.

---

## § 6 — Memorialisation (permanent value)

Once D1–DN are accepted, write a **permanent rule memory**:
- Title: `<domain>_governance_rule_YYYY-MM-DD`
- Body: chosen options / triggers / naming / location / re-evaluation conditions
- Apply trigger: every new asset / decision in this domain

Follow-up actions (after D-table accepted):
- ① Promote existing assets to first anchors (if any) → <target folder>
- ② Write Bible README draft (chapter-1 categories only, gradual expansion)
- ③ Register memory + index entry

D1–DN rule adoption is **independent** of any precondition D0 (precondition gates *first asset registration*, not the rule itself).

---

## Notes on using this template

- **Header table is mandatory** — date / facilitator / topic / status / cross-references. Future-you depends on these.
- **80-line target for daily roll-ups** (`YYYY-MM-DD.md`); topic-specific meetings (this template) can be longer when preserving rejected-option analysis.
- **Topic-specific meetings preserve original analysis** including rejected options + reasoning. Don't compress into the daily roll-up.
- **Always log decisions in the D-table format** — easy to skim, easy to convert to memory.
- **Status changes** flow ⏳ → ✅ / ❌ / ⏸. Never delete a decision; if it's later overturned, append a new meeting and link.

This template is engine-agnostic, genre-agnostic, platform-agnostic. Use as-is for any project decision meeting.
