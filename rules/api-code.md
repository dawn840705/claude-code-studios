---
paths:
  - "src/api/**"
  - "src/server/**"
  - "src/routes/**"
  - "api/**"
---

# API / Server Code Rules

Product-track counterpart of `network-code.md`. Applies to server-side request handling.

- Validate every input at the boundary — never trust a client, including your own frontend
- Authorization is checked per resource, not per route. A valid session is authentication, not permission
- Responses are versioned and additive. Removing a field or changing its type is a breaking change and needs a version, not a deploy
- Errors return a stable machine-readable code plus a human message. Never leak stack traces, SQL, internal paths or dependency versions
- Every mutation is idempotent or carries an idempotency key — retries happen, from clients and from your own infrastructure
- No secrets in code or logs. No PII in logs, including in the URL path and query string
- Schema changes go through migrations, never ad-hoc edits — a migration that cannot roll back is an R3 change (`rules/verify-route.md`)
- Rate-limit anything unauthenticated or expensive, and return the limit in the response headers
- Work that can outlive a request goes to a queue. A request has a deadline; a job does not
