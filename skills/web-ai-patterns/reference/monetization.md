# Reference: Monetization / Billing / Cost-Safety Patterns

Reusable patterns for monetization, subscription billing, and cost-safety in web+AI (SaaS) products that burn paid API on every request.

Field-proven source: **SpecForge** (Next.js + Firebase + Claude API + PortOne). Generalized — the concrete paths are the original implementation; each pattern applies to any product with metered paid-API cost, any billing PG that supports a stored payment token, and any transactional datastore.

**Governing philosophy = "no-loss"**: A service that burns LLM/paid API is one where abuse, bugs, or concurrency each mean "cost scales with usage." Without guardrails, *losses* scale instead of revenue. Every pattern below derives from: "no unlimited tiers / multi-layer backstops / never miss a grant but never double-grant / on failure, fail toward the *service's* safety (block/withhold), never toward user harm (over-block/under-grant)."

Each pattern: **Problem → Approach → Core snippet → When to apply / Caveats.**

---

## 1. No-loss multi-layer gating

**Problem**: A paid-AI endpoint leaks cost on three axes: (a) unauthenticated abuse, (b) an individual user's over-use, (c) service-wide runaway (bug / abuse / traffic spike). One layer of defense means cost goes unbounded if any single layer is breached.

**Approach**: Pass **three independent gates in order** right before the AI call. Each gate early-returns a distinct HTTP code on failure and never enters the AI call.

```
AUTH_ENFORCE(401) → consumeQuota monthly-limit(402) → DAILY_COST_CAP daily backstop(503) → AI call
```

- **Gate 1 — auth enforce**: `AUTH_ENFORCE === "true"` and no uid → 401. Blocks anonymous cost leakage.
- **Gate 2 — monthly limit (per account)**: `consumeQuota(uid, kind)` atomically decrements this month's usage. Over limit → 402. (see pattern 2)
- **Gate 3 — daily backstop (service-wide)**: Independent of any individual user. When today's accumulated cost hits the threshold, every new call gets 503. The last safety net belonging to "the whole service," not any one user.

The key trick in gate 3 is **absorbing concurrency overshoot with a headroom**. There's a gap between the entry check (read) and the cost add (write); if N concurrent requests all read "still under threshold" and pass together, they exceed the cap. Instead of building a full reservation system, lower the **effective block threshold = cap − headroom** and absorb the overshoot as margin.

```ts
// cost/ledger.ts — daily backstop
export async function isDailyCostCapReached(): Promise<boolean> {
  const todayCost = await getTodayCost();
  // effective threshold = cap - headroom (e.g. $10 - $1.3 = $8.7).
  // In-flight requests add cost after, so they're protected. Small overshoot absorbed as margin.
  return todayCost >= getDailyCostCap() - getDailyCostHeadroom();
}

// addCost is called once per AI call (multiple per session). The increment field is
// totalCalls — naming it totalSessions would look like ~10x over-counting.
export async function addCost(costUSD: number): Promise<void> {
  if (costUSD <= 0) return;
  // Firestore FieldValue.increment (concurrency-safe) → memory fallback on failure
}
```

Route ordering (the core 3 lines):
```ts
if (await isDailyCostCapReached()) return json({ error: "DAILY_COST_CAP" }, 503);   // early block
const { tier, uid } = await getRequestTier(req);
if (process.env.AUTH_ENFORCE === "true" && !uid) return json({ error: "AUTH_REQUIRED" }, 401);
const quota = await consumeQuota(uid, quotaKind);
if (!quota.ok) return json({ error: "LIMIT_EXCEEDED", used, limit }, 402);
// ... AI call from here. On finish, addCost(actual spend) accrues to the ledger.
```

**When to apply / Caveats**:
- Check the daily backstop **before opening an SSE stream** for the early-block to matter.
- Over-blocking (503 to a paying user) is "reverse loss." So lower the threshold below cap (prevent overshoot) but not too aggressively (blocks legit users) — headroom at ~13% of cap ($1.3/$10) is the balance.
- `addCost` counts "AI calls," not "sessions." If you need session-level aggregation, count in a separate collection (aggregation-distortion warning).
- Cost must **branch on the actual model's pricing** for the backstop to be accurate. If you upgrade models (cheap→expensive), keep a per-model pricing table (`pricingForModel(model)`).
- **Auxiliary** AI endpoints (speech normalize / OCR etc.) skip gate 2 (no monthly decrement): `AUTH → DAILY_COST_CAP → call → addCost`. Cost still enters the backstop only.
- If the AI fails with a server error, **refund** the decremented quota (`refundQuota`) so the user isn't charged for nothing.

---

## 2. Monthly limit + persistent bonus credits

**Problem**: An "unlimited" plan opens cost to infinity under abuse/over-use. But a pure monthly limit has no way to express "exceptional extra grants" like referral rewards or CS corrections (you'd have to make the counter negative or reset it — messy).

**Approach**:
1. **Finite cap on every tier** (`MONTHLY_LIMITS`, no `Infinity`) — remove the very notion of "unlimited."
2. **Lazy reset**: no batch job — at decrement time, if `monthKey` changed, zero the counters.
3. **Persistent bonus credits** (`bonusCredits`): a separate balance that accrues independent of the monthly reset. When the monthly limit is exceeded, **leave `used` as-is and decrement one bonus** to cover it. The happy path (in-limit use) is never touched, so behavior stays invariant.

```ts
// tier/index.ts — no Infinity IS the no-loss guard
export const MONTHLY_LIMITS = {
  free:    { diagnosis: 1,   report: 1,  podcast: 0  },
  basic:   { diagnosis: 15,  report: 5,  podcast: 5  },
  pro:     { diagnosis: 50,  report: 20, podcast: 15 },
  premium: { diagnosis: 150, report: 50, podcast: 40 },
};
```

```ts
// users/index.ts — consumeQuota (transaction)
await db.runTransaction(async (tx) => {
  let user = snap.exists ? snap.data() : defaultUser(uid);

  // lazy reset: on month change, zero used only. bonusCredits persists.
  if (user.monthKey !== nowKey) {
    user = { ...user, monthKey: nowKey, diagnosisUsed: 0, reportUsed: 0, podcastUsed: 0 };
  }

  const limitVal = MONTHLY_LIMITS[user.tier][kind];
  const usedVal = user[field] ?? 0;

  if (limitVal !== Infinity && usedVal >= limitVal) {
    // over limit — if bonus exists, keep used + decrement 1 bonus (additive fallback)
    const bonus = user.bonusCredits ?? 0;
    if (bonus > 0) {
      tx.set(ref, { ...user, bonusCredits: bonus - 1 }, { merge: true });
      result = { ok: true, used: usedVal, limit: limitVal, bonusUsed: true };
      return;
    }
    result = { ok: false, reason: "LIMIT_EXCEEDED", used: usedVal, limit: limitVal };
    return;
  }
  // happy path: normal +1
  tx.set(ref, { ...user, [field]: usedVal + 1 }, { merge: true });
});
```

**When to apply / Caveats**:
- Decrement must be in a **transaction** (read-modify-write). Concurrent requests racing the counter leak the limit or double-charge.
- Lazy-reset benefit: no cron/batch. But a user who was absent all month resets on next access, so when displaying a reset time, use a computed value (1st of next month).
- Bonus must **not increase `used`** — so "normal limit-consumption stats" and "exceptional grants" don't mix.
- Server-error rollback `refundQuota` decrements the counter (floored at 0). CS partial-restore `rechargeUsage` decrements a specified amount. Both are transactions.
- **On DB-unconfigured, mirror the transaction logic in a memory fallback**, so it runs DB-less for dev/test and errors don't propagate (the datastore fallback pattern).

---

## 3. Stored-token recurring billing + cron dunning

**Problem**: A subscription needs monthly auto-charge, but (a) a given PG (e.g. Stripe) may be region/seller-unsupported, or (b) you don't want to lock into the PG's subscription scheduler — so you must run your own monthly scheduler on a **stored payment token (billing key)**. That means handling double-charge, payment failure, and cancellation grace yourself.

**Approach (5-stage lifecycle)**:
1. `prepareBilling` — server issues `storeId/channelKey/issueId/customerId`.
2. (browser SDK) `requestIssueBillingKey` issues the real `billingKey`.
3. `confirmBilling` — **first immediate charge** with the billing key + activate subscription.
4. `chargeBillingKey` — a **daily cron** charges users whose `nextBillingAt` is due.
5. `cancelBilling` — delete the billing key on cancel.

**Double-charge prevention (core)**:
- **Layer 1 — deterministic paymentId**: `svc_{uid}_{tier}_{YYYY-MM}`. Same user + same month = same ID, so the **PG itself rejects the duplicate**. If webhook payloads don't carry uid/tier, reverse-parse this ID to recover them (`parsePaymentId` — fixed right-2-token parse, safe even if uid contains `_`).
- **Layer 2 — monthly idempotency claim**: cron claims a `billing_{uid}_{YYYY-MM}` doc in a transaction before charging. Skip if present. (app-level defense)

**Dunning (payment-failure retry) state transitions**:
```ts
async function handleChargeFailure(user) {
  const nextRetry = (user.billingRetryCount ?? 0) + 1;
  if (nextRetry < MAX_RETRY) {            // MAX_RETRY = 3
    await setBillingInfo(user.uid, {
      subscriptionStatus: "past_due",
      billingRetryCount: nextRetry,
      nextBillingAt: Date.now() + DAY_MS,  // retry tomorrow
    });
  } else {                                // 3 exhausted → downgrade
    await setTier(user.uid, "free");
    await setBillingInfo(user.uid, { subscriptionStatus: "canceled", billingRetryCount: nextRetry });
  }
}
```

**Expiry downgrade**: cancel doesn't cut off immediately — it marks `subscriptionStatus="canceled"` → keeps tier until `currentPeriodEnd` → the **cron sweep** (`canceled && currentPeriodEnd<=now`) downgrades to `free` + deletes the billing key. (The paid period is honored = dispute prevention.)

**Cron charge loop (claim → charge → update, per-user isolated)**:
```ts
for (const user of due) {              // getUsersDueForBilling(now)
  if (!user.billingKey) { /* downgrade */ continue; }
  if (!(await claimMonthlyBilling(user.uid, monthKey))) { skipped++; continue; }  // idempotent claim
  try {
    const result = await chargeBillingKey(user.billingKey, user.uid, user.tier);
    if (result.ok) {
      const next = addOneMonth(user.nextBillingAt ?? now);
      await setBillingInfo(user.uid, { subscriptionStatus:"active", nextBillingAt:next, currentPeriodEnd:next, billingRetryCount:0 });
    }
  } catch (err) {
    console.error(err);               // per-user try/catch — never abort the whole loop
    await handleChargeFailure(user);
  }
}
```

**Intro discount (once per user, abuse-blocked)**: gate on `introDiscountUsed` (persistent flag). Cancel-then-resubscribe still sees `true`, so full price.

**When to apply / Caveats**:
- **Auth**: cron verifies `Authorization: Bearer <CRON_SECRET>`. If unset, 401 without runtime error (no-op). Vercel Cron on Hobby is **once/day** → schedule `0 1 * * *`.
- **The billing key is store-scoped**. Issue (browser) / charge / delete must all use the **same storeId** or you get `BILLING_KEY_NOT_FOUND` — inject storeId explicitly at client construction.
- **Preserve PG error diagnostics**: a PG rejection (`PgProviderError`) often has an empty `err.message` and puts info in `err.data` (type/pgCode/pgMessage). Merge `err.data` into logs (like `describePortoneError`) or you log empty strings. Never log full card/billing-key — mask to first 8 chars.
- Composite Firestore indexes needed (`subscriptionStatus IN + nextBillingAt range` etc.). If absent/unconfigured, memory-fallback scan → no-op.
- Even if the save after a successful `confirm` charge fails, the webhook (`Transaction.Paid`) should reinforce the grant (double-write).

---

## 4. Payment webhook idempotency + grant-first ordering

**Problem**: PG webhooks are **re-delivered (at-least-once)**. Naive "record idempotency first → then grant" means: if a grant fails, the redelivery skips as "already processed" → **paid but never granted**, a critical bug.

**Approach**: **Grant/downgrade first, record idempotency only after success.** If the grant fails, don't record and **return 500 to force PG retry**. Because `setTier` is merge-set idempotent, a redelivery re-granting the same tier is harmless — so this ordering is safe.

```ts
// payment/webhook/[provider] — payment_success
try {
  await grantSubscription(event.uid, event.tier);   // ① grant first (merge-set idempotent)
  if (event.customerId) await setCustomerId(event.uid, event.customerId);
} catch (err) {
  return json({ error: "grant_failed" }, 500);       // force retry (prevent under-grant)
}
await markEventProcessed(event.eventId, provider).catch(() => {/* record failure harmless */}); // ② record after success
```

**Idempotency record is a transaction** (`processedWebhooks/{eventId}` exists-check → record if absent):
```ts
await db.runTransaction(async (tx) => {
  const snap = await tx.get(ref);
  if (snap.exists) { isNew = false; return; }         // already processed → skip
  tx.set(ref, { eventId, provider, processedAt: serverTimestamp() });
  isNew = true;
});
```

**Shared dynamic route + signature-verification branch**: a `[provider]` dynamic segment handles multiple PGs in one route, but signature-header formats differ — Stripe is a single `stripe-signature` string; PortOne uses **Standard Webhooks 3 headers** (`webhook-id`/`webhook-signature`/`webhook-timestamp`). Branch via an adapter registry.

```ts
const PROVIDERS = { stripe: stripeProvider, portone: portoneProvider };
// provider === "portone" → 3-header object, else stripe-signature string
```

**When to apply / Caveats**:
- **Always return 200** is the webhook default (prevent retry loops). **Exception = deliberate 500 on grant/downgrade failure** (force retry).
- Signature mismatch / unconfigured / unknown provider / verify exception → quietly 200 (never propagate error).
- Downgrade (`subscription_ended`) needs a **reverse lookup**: Stripe customerId→uid, PortOne billingKey→uid. A failed reverse lookup (no mapping) is safely ignored (200) — never downgrade an unknown target.
- Payment failure (`invoice.payment_failed` etc.) must **not downgrade immediately** — downgrade only on the final cancel event after the PG's dunning retries (dispute prevention).
- **DB-unconfigured means no idempotency guarantee** → double-grant risk. Production billing requires the datastore (warn-log).

---

## 5. Referral abuse prevention

**Problem**: A "reward on invite" loop has many abuse vectors — self-referral, repeated event triggers, unqualified referrals, bot mass-generation. Opened without defense, bonus cost leaks and stats are polluted.

**Approach**: Put **6 sequential gates** in one reward-granting function, judge all checks from **server-stored values** (never trust the client body). Gate the daily cap with an **atomic counter transaction**, accruing only when it passes.

```ts
// referral/index.ts — grantReferralBonus (gate order)
① referrer session exists?           → else no grant
② referrer session verdict === pass? → else no grant (unqualified)
③ referrer uid exists?               → legacy anonymous session gets no grant
④ referrer uid === referee uid?      → self-referral block (refereeUid is server-verified session value)
⑤ same refereeSessionId processed?   → duplicate block (referral_events lookup)
⑥ incrementDailyCounter() passes?    → daily cap (3) atomic gate → grant bonus only if it passes
```

**The daily-cap gate atomizes check+increment inside the transaction** so concurrent requests can't breach the cap:
```ts
await db.runTransaction(async (tx) => {
  const currentCount = snap.exists ? snap.data().bonusCount ?? 0 : 0;
  if (currentCount >= MAX_DAILY_BONUS) { granted = false; return; }
  tx.set(ref, { referrerUid, date, bonusCount: FieldValue.increment(1),
                sources: FieldValue.arrayUnion(refereeSessionId) }, { merge: true });
  granted = true;
});
// addBonusCredit(referrerUid) only when granted === true
```

**When to apply / Caveats**:
- **referee uid uses the server-stored session value** (`refereeSession.uid`). The request body uid is forgeable — never trust it.
- Even on no-grant, **record the event** (`bonusGranted: false`) to measure abuse attempts and serve as the duplicate-check basis.
- Use **single-equality filters only** in Firestore queries so no composite index is needed (`where refereeSessionId ==`).
- Accrue rewards to pattern 2's `bonusCredits` (persistent) — naturally covers monthly-limit overflow.
- Daily-cap counter doc ID = `bonus:{referrerUid}:{YYYY-MM-DD}` (date-scoped).

---

## 6. Admin CS operations endpoint

**Problem**: An early service can't afford a separate CMS, but CS tasks — refund, usage-restore, tier grant — are needed immediately. Touching the DB directly is dangerous and non-reproducible.

**Approach**: A **single token-auth endpoint** branches CS tasks by `action`. GET reads; POST does 5 actions (`reset_usage`/`refund`/`recharge`/`add_credits`/`set_tier`). The operator (or an orchestrator agent) handles it with one curl.

```ts
// admin/user — token auth (no separate auth infra)
function isAuthorized(req) {
  const adminToken = process.env.ADMIN_TOKEN;
  if (!adminToken) return false;                    // unset → all 401
  const provided = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : null;
  return provided === adminToken.trim();
}
// email → uid: Auth getUserByEmail first, then users.email fallback
async function resolveUid(email) {
  return (await getAuthUidByEmail(email)) ?? (await getUserByEmail(email))?.uid ?? null;
}
```

**Action summary**:

| action | Effect | Key safeguard |
|---|---|---|
| `reset_usage` | zero all used counters + monthKey=current | preserve tier·bonusCredits·createdAt·email (merge-set) |
| `recharge` | partial decrement of specified used ("restore") | floor at 0, monthKey unchanged, 400 if amount 0 |
| `add_credits` | add bonusCredits (persistent) | 400 if credits ≤ 0 |
| `set_tier` | grant free tier (comp) | 400 on invalid tier |
| `refund` | PG payment cancel (full/partial) | deterministic paymentId reconstruct if unspecified, 400 on free tier |

**Refund paymentId reconstruction**: if unspecified, deterministically rebuild from (specified tier or current subscription tier) + this month via `buildPaymentId(uid, tier)` (reuse pattern 3's ID rule). If `reason` contains "downgrade/cancel", auto-run `setTier(free)` + subscription-status cleanup too.

**When to apply / Caveats**:
- **Minimal PII exposure**: never include raw user content / chat / sensitive input in the response. Only quota/tier metadata.
- **Unauthenticated → all 401** (404 also valid — pick per your existence-disclosure policy). 401 even when the token is unset.
- DB-unconfigured: GET returns `{found:false}`, POST returns 503 (never propagate error).
- PG-unconfigured: refund → 503; PG refund failure (already-canceled / amount-exceeded / not-found) → **preserve diagnostic and 502**.
- All write functions reuse pattern 2's transactions/fallbacks (`resetUsage`/`rechargeUsage`/`addBonusCredits`/`setTier`).
- This pattern fits the "solo dev handles CS by command" model. At scale, add an audit log (who/when/why).
