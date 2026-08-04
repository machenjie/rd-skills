# Routing Navigation Design Benchmarks And Patterns

Load this reference when URL shape, direct entry, route guards, redirects/history, public-link migration, or route-level failure containment changes. Do not load it for taxonomy labels or a component-local navigation callback.

## Direct-Entry Contract

| Condition | Route behavior | Required proof |
| --- | --- | --- |
| Loading/readiness | Resolve session, flags, params, and data without exposing protected content or collapsing the whole app. | Route shell/boundary and dependency readiness test. |
| Allowed | Render stable title, breadcrumb/parent recovery, and canonical URL. | Direct-entry and refresh behavior. |
| Unauthenticated | Reauthenticate and preserve intent only through a validated same-origin/allowlisted return destination. | Missing/expired session plus malicious return target. |
| Unauthorized | Follow the current disclosure policy without leaking resource, tenant, owner, title, or counts. | Wrong-role/owner/tenant test plus backend denial evidence. |
| Invalid parameter | Decode once, validate/canonicalize before fetch, and offer safe recovery. | Malformed/reserved/oversized parameter cases. |
| Deleted, archived, or stale | Explain the state only to actors allowed to know; preserve parent/search recovery. | Known-stale fixture and disclosure rule. |
| Never existed or unavailable | Distinguish only when the current product/security contract allows it. | Fabricated ID and feature/tenant/dependency state. |

For a protected route, UI guards shape navigation and recovery while server-side authorization at the resource/action boundary owns allow and deny behavior. Scope loaders and error/not-found boundaries to the smallest route subtree that can recover.

## URL, Redirect, And History

- Encode path identity and hierarchy intentionally; put optional view state in query/search only when share/back/reload behavior requires it, and keep sensitive values out of URLs.
- Validate redirect destinations and post-authentication targets against the same origin or an explicit allowlist.
- Forward parameters required to preserve approved intent.
- Strip unrelated or sensitive state.
- Bound or detect compatibility loops.
- Treat arbitrary absolute destinations and silent loops as security or operability failures.
- Use push or replace according to user meaning, not framework defaults.
- Prevent consequential side effects from repeating during browser back, refresh, re-entry, or app back.
- Route repeated navigation to a stable result or status with idempotency when needed.
- Public/bookmarked/generated/partner routes need old/new inventory, redirect or accepted break, generated-link/template/doc updates, telemetry/removal trigger, rollback, and consumer owner.

## Evidence And Limits

Inspect current router modules, link builders, breadcrumbs, guards/loaders, generated links, emails/notifications/docs, tests, and external consumers in scope. Link search does not prove unknown bookmarks, partner clients, deployed redirects, browser history, or production analytics. Browser tests cover only the engines, roles, and routes exercised.

Reject client-only authorization, fetch-before-validation, and a generic 404 that collapses distinct recoverable states when the current product and security disclosure contract permits their safe distinction and recovery. Also reject route rename without caller inventory, global-only error boundaries, breadcrumbs with unavailable data, and post-submit history that can replay effects.

Route taxonomy to information-architecture, journeys to user-flow-modeling, and screen states to interaction-state-modeling. Route backend/API denial semantics to permission-boundary-modeling and api-contract-design, and implementation to frontend-change-builder. Route route/accessibility proof to frontend-testing or quality-test-gate, and public-link/docs/SEO compatibility to change-documentation-gate. Route rollout/redirect retirement to delivery-release-gate.
