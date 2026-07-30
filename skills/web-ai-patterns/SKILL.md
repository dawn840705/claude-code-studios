---
name: web-ai-patterns
description: "Field-proven reusable patterns for web+AI (SaaS) development — LLM orchestration, i18n-safe output parsing, no-loss cost/usage gating, stored-token recurring billing, webhook idempotency, and document-store data modeling. Source: SpecForge (Next.js + Firebase + Claude API + PortOne). Use when building an AI-backed web/service product and you want battle-tested reference patterns instead of reinventing them."
argument-hint: "[ai | monetization | data]"
user-invocable: true
allowed-tools: Read, Grep, Glob
agent: backend-engineer
---

# Web + AI Reusable Patterns

A reference library of production-tested patterns for **web+AI (SaaS) products**: services where an LLM (or other paid API) is on the request path, users have tiers/quotas, and cost can scale into losses without guardrails.

**Field-proven source**: SpecForge — a Next.js + Firebase Firestore + Claude API + PortOne product. The patterns are **generalized**: concrete file paths in the reference docs are the original implementation, but each pattern applies to any web+AI stack (any streaming HTTP framework, any LLM provider with tool-use, any billing PG with a stored payment token, any document store). Use the patterns; the SpecForge names are just provenance.

Every pattern follows: **Problem → Approach → Core snippet → When to apply / Caveats.**

---

## Phase 1: Scope from the argument

`$ARGUMENTS` selects a focus area. Branch:

- **`ai`** → load `reference/ai-orchestration.md` only. Focus: LLM orchestration, streaming, i18n-safe parsing, model selection, deterministic post-processing.
- **`monetization`** (aliases: `money`, `billing`, `payment`, `cost`) → load `reference/monetization.md` only. Focus: cost/usage gating, recurring billing, webhook idempotency, referral abuse, admin CS.
- **`data`** (aliases: `data-model`, `schema`, `db`, `firestore`) → load `reference/data-model.md` only. Focus: document-store schema, index avoidance, idempotency collections, memory fallback, PII segregation.
- **no argument / anything else** → this is a browse request. Present the full index below, ask which area the user wants, and load the matching reference file(s) once they answer. If the user's surrounding context already implies an area (they're mid-implementation on billing, streaming, etc.), load that reference proactively.

Load a reference file with `Read` on the absolute path `<this-skill-dir>/reference/<file>.md`. Never dump a whole reference file into the reply — extract the pattern(s) relevant to the user's question and cite the section.

---

## Phase 2: Index of patterns

### `ai` — AI Orchestration & i18n-Safe Parsing → `reference/ai-orchestration.md`

| # | Pattern | One-line problem it solves |
|---|---|---|
| 1 | SSE streaming orchestrator + Tool-Use pipeline | Stream a multi-agent LLM pipeline with per-stage typed events; block a stage by removing its tool |
| 2 | Single-agent direct call + auto-continuation | Auto-resume an LLM response cut off at `max_tokens`; continuation cap = cost lever |
| 3 | Machine-token-based i18n-safe parsing | Parse LLM output values across locales without translated labels breaking the regex |
| 4 | Language + agent model selection + per-model cost accounting | Upgrade only core-agent × sensitive-language; branch cost on real per-model pricing |
| 5 | Deterministic post-processing safety net | Fix a predictable output-error class with a zero-LLM dictionary, preserving parser-critical lines |
| 6 | Prompt-parser contract (invariant headings) | Contract on section numbers not text, so translated report headings don't break the tab parser |

### `monetization` — Monetization / Billing / Cost-Safety → `reference/monetization.md`

Governing philosophy = **no-loss**: no unlimited tiers / multi-layer backstops / never miss a grant but never double-grant / fail toward service safety, not user harm.

| # | Pattern | One-line problem it solves |
|---|---|---|
| 1 | No-loss multi-layer gating | Three ordered gates (auth 401 → monthly quota 402 → daily cost cap 503) before the AI call; headroom absorbs concurrency overshoot |
| 2 | Monthly limit + persistent bonus credits | Finite-cap tiers + lazy reset + a persistent bonus balance for referral/CS grants without touching the happy path |
| 3 | Stored-token recurring billing + cron dunning | Run your own monthly charge scheduler on a billing key; double-charge prevention + dunning + grace-period downgrade |
| 4 | Payment webhook idempotency + grant-first ordering | Grant first, record idempotency after — so a failed grant retries instead of being skipped as "processed" |
| 5 | Referral abuse prevention | 6 server-side gates + atomic daily-cap transaction on the reward grant |
| 6 | Admin CS operations endpoint | One token-auth endpoint, `action`-branched, for refund / usage-restore / credits / tier — no CMS |

### `data` — Datastore Data-Model → `reference/data-model.md`

| Topic | What it covers |
|---|---|
| 9-collection inventory | sessions / users / referral_events / referral_bonuses / costLedger / surveys / ratelimits / billingClaims / processedWebhooks + PII grade each |
| Gating source-of-truth | `users` schema, `MONTHLY_LIMITS` (no Infinity), lazy reset, transaction writes |
| Idempotency collections | billingClaims / processedWebhooks / referral_bonuses — the atomic backbone of the billing/referral patterns |
| Design principles | deliberate composite-index avoidance · memory fallback (errors never propagate) · fallback weakens which guarantees · PII segregation by collection · blob storage as a separate gate |

---

## Phase 3: Apply

When the user is implementing, don't just quote — **adapt** the pattern to their stack:

- Map SpecForge terms to theirs (Firestore → their store, PortOne → their PG, Claude API → their LLM provider, agent names → their sub-agents).
- Preserve the **invariants** that make the pattern safe: transaction-wrapped counters (monetization 2/5), grant-first ordering (monetization 4), tool-list filtering over prompt-instructions (ai 1), machine tokens over localized labels (ai 3/6), memory fallback that never throws (data).
- Flag the caveats that bite in production: SSE early-gating before stream open, per-model pricing for an accurate cost cap, store-scoped billing keys, composite-index needs, DB-required-for-idempotency.

This skill is **read-only** — it loads and applies reference patterns; it does not write files. The skill is **COMPLETE** once the relevant pattern has been surfaced and adapted to the user's stack (and its safety invariants called out).

---

## When NOT to use this skill

- **Game-domain work** — these are web/service/SaaS patterns. For game systems use the game-pack skills.
- **A pure static site or frontend with no paid API on the request path** — the cost/billing patterns add no value; only `ai` pattern 6 (prompt-parser contract) might apply to any structured LLM output.
- **You already have a mature billing/quota system** — cross-check against these caveats rather than adopting wholesale.
