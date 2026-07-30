# Reference: Datastore Data-Model Patterns

Reusable data-modeling patterns for a web+AI (SaaS) product on a document store with a memory fallback.

Field-proven source: **SpecForge** (Next.js + Firebase Firestore + Claude API + PortOne). Generalized — the schema below is reconstructed from the real code (Admin SDK, `firebase-admin/firestore`), and every data layer runs on an **in-memory fallback when the DB is unconfigured** (never propagates errors). The fallback is volatile across server restart. The patterns (index-avoidance, PII segregation, idempotency collections, memory fallback) apply to any document store (Firestore, Mongo, DynamoDB single-table, etc.).

---

## Collection inventory (9 kinds)

| Collection | Purpose | Doc ID | PII |
|---|---|---|---|
| `sessions` | Full user work session (input · analysis · training · report) | `svc_{ts}_{rand}` | **high** |
| `users` | Per-account tier · monthly usage · bonus · billing | Auth `uid` | low (email) |
| `referral_events` | Referral event log (dedup · measurement) | auto-ID | none |
| `referral_bonuses` | Daily referral-bonus cap counter | `bonus:{uid}:{YYYY-MM-DD}` | none |
| `costLedger` | Daily AI-cost accrual ledger (daily cap) | `YYYY-MM-DD` (UTC) | none |
| `surveys` | Completion-stage survey responses | `srv_{ts}_{rand}` | low (free text) |
| `ratelimits` | IP daily free-use counter (peek-only now) | `ratelimit:{ip}:{YYYY-MM-DD}` | low (IP) |
| `billingClaims` | Monthly-billing idempotency key (1st defense) | `billing_{uid}_{YYYY-MM}` | none |
| `processedWebhooks` | Payment-webhook idempotency record | webhook `event.id` | none |

The three lower blocks — `billingClaims`, `processedWebhooks`, `referral_bonuses` — exist purely as **idempotency / atomic-cap collections** that back the monetization patterns. Treat them as first-class: their absence (memory fallback) weakens the guarantees the billing/referral logic depends on.

---

## 1. `sessions` — the high-PII work record

- **Purpose**: stores the whole multi-step user flow (input → analysis → training → report → done). Source for public profile, hall-of-fame, insight aggregation, re-diagnosis loop, and podcast.
- **Doc ID**: `generateId()` → `svc_{Date.now()}_{base36 6-char}`.
- **Key fields**: raw user content (**PII**), parsed external text, per-agent outputs, chat messages (role/content/verdict/timestamp), final verdict (`pass|hold|null`), final report, step, `createdAt`/`updatedAt`, analytics fields (`totalRounds`, `passAchieved`, `estimatedCost`, `apiUsage{totalInputTokens/totalOutputTokens/totalCost/cacheCreation/cacheRead}`), review fields (`reviewStatus`, `reviewerComments` **PII**, `rubricScores`, `rubricGuide`, timestamps), `language`/`region`, `referralSource` (referrer's sessionId), `clientIp` (**PII**, abuse defense), `uid` (server-verified token value — never trust `body.uid`), `parentSessionId`/`revisionNumber` (re-diagnosis lineage, cap `MAX_REVISION=5`), `podcast{status/kind/storagePath/...}`.
- **Writes**: `saveSession` (merge:true) — create/update, review guide save, podcast field. `updateReviewStatus` — review status/comments/scores/timestamps.
- **Reads**: session API, public profile (PASS-only, PII-masked), hall-of-fame (anonymous), insight aggregation (anonymous, `listAllSessions`), review, podcast, referral (referrer lookup).
- **PII handling**: high (`rawContent`, `reviewerComments`, `clientIp`). Public-exposure paths (`getPublicProfile`/`listHallOfFame`) expose only a first-paragraph 300/200-char cap + `maskPII` (email/national-id/phone) re-mask; raw content / chat / external text are **never** exposed.

---

## 2. `users` — gating source of truth

- **Purpose**: per-account tier · monthly usage quota · bonus credits · billing (Stripe/PortOne) state. The source of truth for gating (`consumeQuota`).
- **Doc ID**: Auth `uid`.
- **Key fields**: `uid`, `email?`, `tier` (`free|basic|pro|premium`), `monthKey` (`YYYY-MM` UTC — lazy reset on month change), `diagnosisUsed`/`reportUsed`/`podcastUsed`, `bonusCredits` (persistent, **not** monthly-reset), `createdAt`, billing fields (`stripeCustomerId?`, `paymentProvider?`, `billingKey?`, `portoneCustomerId?`, `subscriptionStatus?` (`active|past_due|canceled`), `nextBillingAt?`, `currentPeriodEnd?`, `billingRetryCount?`, `introDiscountUsed?`).
- **Monthly limits** (`MONTHLY_LIMITS`): finite for every tier, **no Infinity** (see monetization pattern 2).
- **Writes**: `consumeQuota` (transaction — lazy reset + decrement + bonus cover), `refundQuota` (-1 rollback), `setTier`/`grantSubscription`, `addBonusCredit(+1)`/`addBonusCredits(+n)`, `rechargeUsage` (partial restore), `resetUsage`, `setBillingInfo`, `upsertUser`.
- **Reads**: `getUser`, reverse lookups `getUserByStripeCustomerId`/`getUserByBillingKey`/`getUserByEmail`, `getUsersDueForBilling`.
- **Index**: `getUsersDueForBilling` is a **composite query** `where(subscriptionStatus in [...]) + where(nextBillingAt <=)` → **needs a composite index** (catch → memory-fallback scan if absent). The expiry sweep `where(subscriptionStatus == canceled) + where(currentPeriodEnd <=)` also needs one. The rest (`stripeCustomerId`/`billingKey`/`email` single-equality) use automatic indexes.
- **PII**: low (email only).

---

## 3–4. `referral_events` / `referral_bonuses` — abuse-defense pair

- `referral_events` (auto-ID): grant/no-grant event log for dedup + measurement. Fields: `referrerSessionId`, `referrerUid`, `refereeSessionId`, `refereeUid: string|null`, `createdAt`, `bonusGranted: boolean`. Dedup via `hasExistingEvent` (single-equality `where refereeSessionId ==`). **Record even on no-grant** to measure abuse. No PII.
- `referral_bonuses` (ID `bonus:{referrerUid}:{YYYY-MM-DD}`): referrer daily bonus cap (`MAX_DAILY_BONUS=3`). Fields: `referrerUid`, `date`, `bonusCount` (`FieldValue.increment`), `sources` (`FieldValue.arrayUnion(refereeSessionId)`). Written by `incrementDailyCounter` (transaction, +1 only under cap). Direct-ID lookup → no index. No PII.

---

## 5. `costLedger` — daily backstop source of truth

- **Doc ID**: `YYYY-MM-DD` (UTC).
- **Fields**: `date`, `totalCostUSD` (`FieldValue.increment`), `totalCalls` (increment — **AI-call count, not session count**), `updatedAt`.
- **Writes**: `addCost(costUSD)` — per-route, once per AI call.
- **Reads**: `getTodayCost`/`isDailyCostCapReached` (gating), cost-insight aggregation (`where date >=` window).
- **Index**: direct-ID lookup + `date` single-field range → automatic. No PII.
- **Fallback**: `Map<dateKey, number>` (concurrency not guaranteed, dev only).

---

## 6–7. `surveys` / `ratelimits`

- `surveys` (ID `srv_{ts}_{rand}`): completion-stage / public survey responses (satisfaction · NPS · feature ratings · friction). Full-collection `.get()` then in-memory aggregate → no index. PII low (free-text fields).
- `ratelimits` (ID `ratelimit:{ip}:{YYYY-MM-DD}`): IP daily free-use counter (`FREE_DAILY_LIMIT`=10 + referral bonus). **Currently `peek()`-only** (read-only) — real gating is account monthly-limit (`consumeQuota`); `increment()` is a dead path. Fields include `expiresAt` (Timestamp, +2 days — **TTL policy target**). Direct-ID lookup → no index. PII low (IP).

---

## 8–9. `billingClaims` / `processedWebhooks` — idempotency collections

- `billingClaims` (ID `billing_{uid}_{YYYY-MM}`): monthly-billing idempotency key. Cron claims the doc before charging → blocks same-month duplicate charge (1st defense; 2nd is the deterministic `paymentId` at the PG). Written by `claimMonthlyBilling` (transaction, skip if present). Direct-ID lookup → no index. No PII. Fallback returns `claim=true` (idempotency **not** guaranteed — relies on paymentId idempotency).
- `processedWebhooks` (ID = webhook `event.id`): payment-webhook idempotency record (prevents double grant/downgrade). Fields: `eventId`, `provider`, `processedAt` (serverTimestamp). Written by `markEventProcessed` (transaction, skip if present) — **only after** grant/downgrade succeeds (deliberate ordering, see monetization pattern 4). Direct-ID lookup → no index. No PII. Fallback returns `true` (idempotency impossible — production billing requires the DB).

---

## Cross-collection relationships

```
Auth uid ──┬─→ users.{uid}              (tier · quota · billing)
           ├─→ sessions.uid             (session owner, server-verified token value)
           ├─→ referral_bonuses "bonus:{uid}:{date}"
           ├─→ billingClaims "billing_{uid}_{YYYY-MM}"
           └─→ referral_events.referrerUid / refereeUid

sessions.{id} ──referralSource──→ sessions.{referrer_id}
sessions.parentSessionId ──→ sessions.{parent_id}   (re-diagnosis lineage)

referral grant flow:
  referee PASS → referral API
    → sessions[referralSource] → referrer session lookup (verdict==pass, uid exists)
    → referral_events dup / self-referral check
    → referral_bonuses daily cap (+1, max 3) gate
    → users[referrerUid].bonusCredits +1  → consumeQuota covers over-limit

billing flow:
  billing/confirm → users(billingKey/subscriptionStatus/nextBillingAt) + setTier
  cron/billing → getUsersDueForBilling(users) → billingClaims claim → charge → users update
  webhook/[provider] → processedWebhooks idempotency → users(tier/downgrade)

cost/aggregation (read-only, zero LLM):
  addCost → costLedger.{date}   (daily backstop)
  insights, hall-of-fame → sessions anonymous aggregate
```

---

## Design principles worth stealing

1. **Deliberate composite-index avoidance**. Every query uses a single-equality filter (`where uid ==`, `where verdict == pass`); sort/limit happen in memory. Only unavoidable billing queries (`getUsersDueForBilling`, expiry sweep) use a composite index, and even those catch → memory-fallback scan. This keeps the schema deployable without index-management friction.

2. **Memory fallback everywhere (errors never propagate)**. `getDb()` returns the store only if all connection env vars are present, else `null`. Each module downgrades to a `Map`-based in-memory store on `db===null` or any DB exception, and **never throws** (service continues). Volatile across restart. Set `ignoreUndefinedProperties: true` so optional fields can be saved undefined.

3. **Fallback weakens specific guarantees — know which**. Under memory fallback: `costLedger` loses concurrency safety; `billingClaims`/`processedWebhooks` lose idempotency (production billing requires the real DB); `referral_bonuses` daily cap is volatile. Document these explicitly so ops doesn't run billing on the fallback.

4. **PII segregation by collection**. Keep high-PII (raw content, comments, IP) in `sessions` only; keep `users` low-PII (email only). Every public-read path applies a length cap + re-mask and never returns raw fields.

5. **Blob storage is a separate gate**. Large binary (audio, images) lives in object storage keyed by session ID, behind its own env gate — 503 quietly when unconfigured, so the core service is unaffected.
