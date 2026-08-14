---
paths:
  - "src/app/**"
  - "src/components/**"
  - "src/pages/**"
  - "app/**"
  - "components/**"
---

# Frontend Code Rules

Product-track counterpart of `ui-code.md`. Applies to web and mobile client code.

- Server state and client state stay separate — server data lives in the data layer (fetch/query cache), never copied into component state where it can go stale
- No hardcoded user-facing strings — route through the i18n layer from day one, even for a single-locale launch. Retrofitting is the expensive path
- Every interactive element is reachable and operable by keyboard; never remove the focus ring without replacing it
- Semantic HTML before ARIA — a `<button>` beats a `<div role="button">` and needs no attributes to be correct
- A component that fetches renders four states, not one: loading, empty, error, and content. The other three are not an afterthought
- Reserve space for late-loading content — layout shift is a shipped-quality metric (CLS), not a cosmetic detail
- Images and fonts are sized and formatted at build time, not left to the browser at runtime
- Nothing secret reaches the client bundle. Anything in client code is public, including env vars the bundler inlines
- Respect `prefers-reduced-motion`, and make every animation skippable
- Accessibility target is the tier committed in `design/accessibility-requirements.md` — WCAG 2.1 AA unless that file says otherwise
