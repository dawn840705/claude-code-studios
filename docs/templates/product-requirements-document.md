# PRD: [Product Name]

*Created: [Date] · Version: [v0.1] · Status: [Draft / Under Review / Approved]*

> **Scope of this template.** This is the **product-level** PRD — the whole
> product, written once and versioned. It is not the per-feature PRD that
> `$create-prd` writes to `product/prd/prd-<feature>.md`. This one sets the
> frame; those specify one feature inside it.
>
> Suggested path: `product/prd/product-requirements.md`
>
> **Two things this does not do**, so you don't find out later:
> - It does **not** satisfy the discovery-phase `product-concept` step.
>   `check_phase.py` and `$create-prd` both look for
>   `product/prd/product-concept.md` by exact name and will still report it
>   missing. Write that file too — the overlap is § 1-3 and § 5, so it is a
>   condensation, not new work.
> - `$create-prd` does **not** read this file (it globs `prd-*.md` only). Paste
>   the relevant § 6 subsection into the feature PRD prompt yourself.
>
> Game projects should use `game-concept.md` + `game-design-document.md`
> instead. This is the product-track (web / mobile / service) counterpart.

---

## 1. Product Overview

### 1.1 One-line definition

> [One sentence a stranger understands. Format: "[Product] helps [who] do
> [what] by [how]." If you need two sentences, the product isn't decided yet.]

### 1.2 Problem

[What breaks today, for whom, how often, and what it costs them. Be specific
enough that someone could go verify it. "Users find X inconvenient" is not a
problem statement — "users abandon X at step 3 because Y" is.

Mark anything you have not verified. See `rules/claim-confidence.md`.]

### 1.3 Opportunity

[Why now? What changed — a new platform, a cost curve, a regulation, a
behaviour shift — that makes this buildable or wanted now and not two years
ago. If nothing changed, say so; that is a real answer and it affects
prioritisation.]

---

## 2. Target Users and Personas

### 2.1 Personas

Two to three. More than three usually means the target is not decided.

| | Persona A | Persona B | Persona C |
| ---- | ---- | ---- | ---- |
| **Name / age** | [Name, age] | | |
| **Situation** | [Their context when they'd reach for this] | | |
| **What they want** | [Their goal, in their words] | | |
| **What they do today** | [Current workaround — this is your real competitor] | | |
| **What would make them quit** | [Dealbreaker] | | |

### 2.2 Non-targets

[Who this is explicitly **not** for. Every excluded group is a set of
feature requests you get to decline later without re-litigating.]

---

## 3. Core Value and Differentiation

[What this does that the alternatives do not. State each differentiator as a
claim someone could disprove.]

| # | Differentiator | Why a competitor can't just copy it | Evidence |
| ---- | ---- | ---- | ---- |
| 1 | [Claim] | [Moat: data, distribution, cost structure, integration, timing] | [Source — or mark it `(추정)` / `[확인 필요]` per `rules/claim-confidence.md`] |
| 2 | | | |
| 3 | | | |

> A differentiator with no answer in column 3 is a feature, not a moat. That
> is allowed — just don't plan around it as if it were defensible.

---

## 4. Core Loop

[What the user does repeatedly, and what brings them back. Products have loops
the same way games do; if you can't draw one, retention has no mechanism.]

- **First session**: [What happens in the first 5 minutes? When do they first
  get value?]
- **Repeat loop**: [The recurring cycle — trigger → action → reward → next
  trigger]
- **Reason to return**: [What specifically pulls them back tomorrow / next week]
- **Graduation risk**: [Does the user eventually stop needing this? If yes,
  that's not a flaw — but the business model must survive it.]

---

## 5. MVP Scope

**Core hypothesis**: [The single statement the MVP tests.]

**In scope**

1. [Feature — and which part of the hypothesis it tests]
2. [Feature]
3. [Feature]

**Deliberately excluded from MVP** (deferred, not rejected — rejected things
go in § 11)

- [Feature] — [why deferred]
- [Feature] — [why deferred]

---

## 6. Functional Requirements

One subsection per MVP feature. Keep each to what a builder needs to start.

### 6.1 [Feature name] — [P0 / P1 / P2]

- **User-visible behaviour**: [What happens, from the user's side]
- **Inputs / outputs**: [Data in, data out]
- **Rules and edge cases**: [Limits, validation, what happens when it fails]
- **Acceptance**: [How we know it's done — must be checkable, not "works well"]
- **Depends on**: [Other features, external services, decisions not yet made]

### 6.2 [Feature name] — [Priority]

[Repeat.]

---

## 7. Non-Functional Requirements

Fill every row or write "N/A — [reason]". A blank row means nobody thought
about it, and the difference matters at hardening.

| Area | Requirement | How it's verified |
| ---- | ---- | ---- |
| **Cost** | [Per-user ceiling; what happens when it's hit — degrade, queue, or refuse. Paid AI calls: gate with `$api-cost-gate`] | [Gate / dashboard / alert] |
| **Performance** | [Concrete numbers: p95 latency, cold start, bundle size] | [Which test] |
| **Security / privacy** | [What data is collected, where it lives, who can read it, retention] | [Which audit — `$security-audit`] |
| **Offline / degraded** | [Behaviour with no network, or when a dependency is down] | [Which test] |
| **Accessibility** | [Target level, and the specific things that matter here] | [`$ux-review`, `docs/templates/accessibility-requirements.md`] |
| **Localisation** | [Languages at launch; what is translated vs generated] | [`$localize`] |
| **Compliance** | [Platform policy, industry regulation, age rating] | [Which checklist] |

---

## 8. Business Model Summary

[Two paragraphs plus the table. The full model — unit economics, PG fees,
break-even, abuse defence — belongs in a separate business-model document,
not here. This section is the summary a reader needs to follow the PRD.]

| Tier | Price | Limits | Who it's for |
| ---- | ---- | ---- | ---- |
| [Free] | [₩0] | [Quota] | [Persona] |
| [Paid] | [₩X/mo] | [Quota] | [Persona] |

**Cost floor**: [What one free user costs us per month. If it isn't zero, say
what makes it survivable.]

---

## 9. Success Metrics

Name the one metric that decides whether this worked before listing the rest.

**North Star**: [One metric, with the number that counts as success and the
date you'll judge it.]

| Metric | Definition (how it's computed) | Baseline | Target | By when |
| ---- | ---- | ---- | ---- | ---- |
| [Activation] | [Exact event sequence, not a vibe] | [Now] | [Goal] | [Date] |
| [Retention] | [D1 / D7 / D30, defined] | | | |
| [Conversion] | | | | |
| [Cost per user] | | | | |

> Each metric needs an event that actually fires. If the instrumentation
> doesn't exist yet, that's a work item, not a footnote.

---

## 10. Release Roadmap

| Milestone | Contents | Exit criteria | Target date |
| ---- | ---- | ---- | ---- |
| [M1 — MVP] | [What ships] | [What must be true to call it done] | [Date] |
| [M2] | | | |
| [M3] | | | |

---

## 11. Risks and Assumptions

### Assumptions

Things we are betting on without proof. Each one should name what would
disprove it.

| Assumption | If it's wrong | How we'd find out early |
| ---- | ---- | ---- |
| [Statement] | [Consequence] | [Signal, test, or date] |

### Risks

| Risk | Likelihood | Impact | Mitigation | Owner |
| ---- | ---- | ---- | ---- | ---- |
| [Product risk — nobody wants it] | [H/M/L] | [H/M/L] | | |
| [Technical risk] | | | | |
| [Market / competitive risk] | | | | |
| [Legal / policy risk] | | | | |
| [Cost risk] | | | | |

---

## 12. Out of Scope

Explicitly rejected, with the reason. This section exists so the same idea
doesn't come back in three weeks — see `rules/decision-lifecycle.md`.

- **NOT [thing]** — [why rejected, and what would have to change to revisit]
- **NOT [thing]** — [why]

---

## 13. Open Questions

Unresolved, with an owner and a way to resolve each. A question with no
resolution path is a risk; move it to § 11.

| # | Question | Blocks | How we'll answer it | Owner |
| ---- | ---- | ---- | ---- | ---- |
| Q1 | | [Which feature / milestone] | [Prototype, research, user decision] | |
| Q2 | | | | |

**Needs a decision from the user** (things the agent cannot resolve alone —
accounts, budgets, legal, brand):

- [ ] [Item]

---

## Next Steps

- [ ] Review with `product-manager` and `creative-director`
- [ ] Condense § 1-3 + § 5 into `product/prd/product-concept.md` — the discovery
      step both `check_phase.py` and `$create-prd` require by exact filename
- [ ] Pin the stack in `.codex/studio/technical-preferences.md`
- [ ] Per-feature PRDs for each § 6 item (`$create-prd <feature>`)
- [ ] Architecture decisions for anything in § 7 with a hard number (`$architecture-decision`)
- [ ] Pin the § 12 rejections as decisions with revisit triggers (`rules/decision-lifecycle.md`)
- [ ] `$project-stage-detect` to confirm discovery is actually complete before
      moving on — it reads `check_phase.py`'s exit code, which judges the
      product track. (`$gate-check` takes game-track phase names only.)
