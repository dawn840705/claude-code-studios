# Agent Roster

41 agents, each with a dedicated definition file in `agents/`. Use the agent
best suited to the task at hand. When a task spans multiple domains, the
coordinating agent (usually `producer`, `product-manager`, or the domain lead)
delegates to specialists.

Agents are organized into three domain packs (source of truth:
`docs/agent-packs.yaml`). The `detect-project-type.sh` hook picks the active
packs at session start:

- **core** — domain-neutral roles active in EVERY project.
- **game** — game-only roles (active on `PROJECT_TYPE=game`).
- **product** — app/web/service roles (active on `PROJECT_TYPE=web|mobile|service`).

There are no engine-specific agents in v0.4.0. Engine guidance is handled by
`/setup-engine` and version-aware reference docs, not dedicated agents.

## Core pack (always active)

### Directors

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `creative-director` | High-level vision (≈vision-lead) | Major creative/product decisions, pillar conflicts, tone/direction, scope arbitration |
| `technical-director` | Technical vision | Architecture decisions, tech stack choices, performance strategy, technical risk |
| `producer` | Production management | Sprint planning, milestone tracking, risk management, cross-department coordination |

### Programming (general)

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `lead-programmer` | Code architecture | System design, code review, API design, coding standards, work assignment |
| `ui-programmer` | UI implementation | UI framework, screens, HUDs, widgets, data binding |
| `ai-programmer` | AI / decision systems | Behavior trees, pathfinding, NPC logic, state machines, LLM integration |
| `engine-programmer` | Core systems | Rendering, physics, memory management, resource loading, scene management |
| `tools-programmer` | Dev tools | Editor extensions, content authoring tools, debug utilities, pipeline automation |
| `prototyper` | Rapid prototyping | Throwaway prototypes, mechanic testing, feasibility validation |
| `network-programmer` | Networking | Replication, lag compensation, matchmaking, network protocol (service: realtime) |

### QA / Ops (general)

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `qa-lead` | Quality assurance | Test strategy, bug triage, release quality gates, testing process |
| `qa-tester` | Test execution | Test cases, bug reports, regression checklists |
| `performance-analyst` | Performance | Profiling, bottleneck ID, optimization recommendations, metrics tracking |
| `security-engineer` | Security | Vulnerability review, anti-cheat, exploit prevention, auth, data protection |
| `accessibility-specialist` | Accessibility | WCAG compliance, colorblind modes, remapping, text scaling |
| `localization-lead` | Internationalization | i18n architecture, string externalization, translation pipeline, locale testing |
| `release-manager` | Release pipeline | Certification, store submissions, versioning, release-day coordination |
| `devops-engineer` | Build/deploy | CI/CD, build scripts, version control workflow, deployment infrastructure |
| `ux-designer` | UX flows | User flows, interaction design, information architecture, accessibility, input handling |
| `analytics-engineer` | Telemetry | Event tracking, funnel analysis, A/B test design, dashboards |

### Hybrids (game/product, framed either way)

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `art-director` | Visual direction (≈design-lead) | Style guides, art bible (game) or web design system (product), asset standards |
| `narrative-director` | Story/content (≈content-strategist) | Story arcs, world-building, character design, messaging architecture |
| `community-manager` | Community (≈marketing-lead) | Patch notes, social, player/user feedback, crisis comms |
| `writer` | Copy/content (≈content-writer) | Dialogue, lore, item descriptions (game) or product microcopy/UX writing |

## Game pack (active on `PROJECT_TYPE=game`)

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `game-designer` | Game design | Core loops, mechanics, progression, economy, balancing, player experience |
| `gameplay-programmer` | Gameplay code | Mechanic/player-system/combat/interaction implementation |
| `systems-designer` | Systems design | Combat formulas, progression curves, crafting recipes, interaction matrices |
| `economy-designer` | Economy/balance | Resource economies, loot tables, progression curves, virtual markets |
| `level-designer` | Level design | Spatial layouts, encounters, pacing, environmental storytelling |
| `world-builder` | World/lore design | Factions, cultures, history, geography, world rules |
| `live-ops-designer` | Live operations | Seasons, battle passes, content cadence, retention mechanics, live economy |
| `technical-artist` | Tech art | Shaders, VFX, rendering optimization, art pipeline tools |
| `audio-director` | Audio direction | Music direction, sound design philosophy, audio implementation strategy, mix balance |
| `sound-designer` | Sound design | SFX spec sheets, audio event docs, mixing parameters |

## Product pack (active on `PROJECT_TYPE=web|mobile|service`)

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `product-manager` | Product management | PRD, roadmap, prioritization, success metrics, stakeholder alignment |
| `frontend-engineer` | Web frontend | React/Next.js UI, client state, responsive layouts, Core Web Vitals |
| `backend-engineer` | Backend | REST/GraphQL APIs, DB schemas, auth/session, server validation, scalability |
| `mobile-engineer` | Mobile | React Native/Expo, native modules, offline behavior, app store builds |
| `data-engineer` | Data | Event schemas, ETL/ELT pipelines, data warehousing, data quality |
| `growth-engineer` | Growth | Acquisition, activation, retention, monetization loops, conversion funnels, SEO, A/B experiments |
| `technical-writer` | Documentation | API docs, user guides, onboarding docs, operational runbooks |
