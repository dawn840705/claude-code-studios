---
name: create-prd
description: "Guided, section-by-section PRD authoring for a single product feature. Gathers context from the product concept and existing PRDs, walks through each required section collaboratively, and writes to a feature-named file under product/prd/. Product-track counterpart of $design-system."
---

When this skill is invoked:

## 1. Parse Arguments & Validate

Resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

A feature name is **required**. If missing:

1. Check if `product/prd/product-concept.md` exists.
2. If it exists: read its scope/feature list, find the highest-priority feature
   without a PRD (`product/prd/prd-<feature>.md` does not exist), and use
   a direct user question:
   - Prompt: "The next feature without a PRD is **[feature-name]**. Author its PRD?"
   - Options: `[A] Yes — write the PRD for [feature-name]` / `[B] Pick a different feature` / `[C] Stop here`
3. If no product concept exists, fail with:
   > "Usage: `$create-prd <feature-name>` — e.g., `$create-prd onboarding`
   > No product concept found. Run `$product-concept` first — it writes
   > `product/prd/product-concept.md`, which this skill reads."

Normalize the feature name to kebab-case for the filename
(e.g., "user onboarding" becomes `prd-user-onboarding.md`).

If `product/prd/prd-<feature>.md` already exists, do NOT overwrite. Offer
retrofit: identify missing/placeholder sections and fill only those (mirror
`$design-system` retrofit behavior — never touch existing section content).

---

## 2. Gather Context (Read Phase)

Read all relevant context **before** asking the user anything:

- **Product concept**: `product/prd/product-concept.md` — problem, users,
  value proposition, scope tiers. Fail if missing (see above).
- **Stack pin**: `.codex/studio/technical-preferences.md` — platform, framework,
  constraints. If missing, warn: stack-unaware PRDs breed infeasible requirements.
- **Existing PRDs**: Glob `product/prd/prd-*.md` — read titles + dependency
  sections to cross-reference. A new PRD must not contradict or duplicate an
  existing one.
- **Accessibility tier**: `design/accessibility-requirements.md` if present —
  requirements below must respect the committed tier.
- **UX specs**: Glob `design/ux/*.md` for screens this feature touches.

---

## 3. Author Section by Section (Write Phase)

Walk the user through each required section **in order, one at a time**:
propose a draft from the context you read, ask for corrections, then move on.
Do not fabricate business facts (pricing, launch dates, user counts) — ask.

Required sections (all 8 must exist for the PRD to pass review):

1. **Overview & Problem** — the user problem, evidence it exists, why now
2. **Goals & Success Metrics** — measurable targets with numbers and a
   measurement source (analytics event, funnel step). "Users are happier" is
   not a metric.
3. **Users & Scenarios** — target segment(s) and 2-4 concrete usage scenarios
4. **Scope (MoSCoW)** — Must / Should / Could / Won't for this release.
   The Won't list is mandatory — an empty Won't list means scope was not decided.
5. **Functional Requirements** — numbered FR-1, FR-2, … testable statements
6. **Non-Functional Requirements** — performance, security, accessibility
   (cite the committed tier), i18n, offline behavior where relevant
7. **Dependencies** — other PRDs, ADRs, external services; each with a note on
   what breaks if the dependency slips
8. **Acceptance Criteria** — checkable list a QA agent can verify; each
   criterion maps to at least one FR

After drafting all sections, show the user a compact summary of what will be
written and ask for approval before writing the file:

> "May I write this PRD to `product/prd/prd-<feature>.md`?"

Only write after explicit approval. Write the full document with frontmatter:

```yaml
---
feature: <feature-name>
status: Draft   # Draft → In Review → Approved
version: 0.1
---
```

---

## 4. Verdict & Handoff

Self-check before closing (all must hold, else fix before reporting):
- All 8 sections present, none placeholder-only
- Every success metric has a number and a measurement source
- Every acceptance criterion maps to an FR
- Won't list is non-empty

Report the verdict:
- **COMPLETE** — PRD written, all checks hold. Set `status: In Review`.
- **BLOCKED** — a business fact is missing and the user must decide (name it).

### Recommended next steps

- `$design-review product/prd/prd-<feature>.md` — validate the PRD before it
  feeds architecture
- `$ux-design` — author UX specs for this feature's key screens
- More features to specify? Run `$create-prd` again — the catalog step is
  repeatable (one PRD per feature)
- All MVP features covered? → `$create-architecture` (Architecture phase)
