# Routing Navigation Design Benchmarks And Patterns

Use this reference when `routing-navigation-design` needs more detail than the main `SKILL.md` should carry. Keep the main body focused on selection, evidence, output, and quality gates; use this file for route guard matrices, route table templates, redirect/history semantics, deep-link states, framework placement, route migration, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- **RFC 3986 URI syntax:** path versus query encoding, reserved characters, percent-encoding, canonical URL shape, and safe parameter handling.
- **OWASP open redirect prevention:** validate `returnTo`, `redirect`, `next`, and callback destinations against same-origin or explicit allowlists.
- **WCAG 2.2 SC 2.4.3, 2.4.4, and 2.4.5:** focus order, link purpose, and multiple navigation paths.
- **HTML History API:** `pushState`, `replaceState`, `popstate`, and navigation-state semantics for browser back/refresh.
- **React Router, Vue Router, Angular Router:** loaders, route guards, nested routes, lazy route modules, route-level error boundaries, and redirect lifecycle.
- **Next.js App Router:** layouts, route groups, loading, error, not-found, parallel routes, intercepting routes, and server/client boundary placement.
- **Problem Details and safe error semantics:** distinguish invalid parameter, unauthorized, unavailable, deleted/stale, and not-found without leaking sensitive resource existence.
- **Error prevention heuristics:** destructive or side-effecting actions should not be reachable by accidental browser history replay.

## Route Guard Classification Matrix

| Condition | HTTP equivalent | UI behavior | Existence disclosure | `returnTo` | Validation evidence |
| --- | --- | --- | --- | --- | --- |
| No session | 401 | Redirect to login or show login-required shell. | N/A | Preserve same-origin safe return. | Unauthenticated direct-entry test. |
| Authenticated but unauthorized | 403 or privacy-preserving 404 | Show denied/unavailable state without sensitive details. | No for sensitive resources. | Usually no. | Wrong-role/wrong-owner test and backend denial evidence. |
| Feature disabled or tenant unavailable | 403/404/503 depending contract | Show feature unavailable with recovery path. | Avoid tenant/resource detail leaks. | No. | Feature flag or tenant-disabled test. |
| Invalid path parameter | 400 or invalid-link state | Reject before data fetch and route to invalid-link recovery. | N/A | No. | Invalid UUID/slug/query test. |
| Deleted or archived resource | 410, 404, or resource-specific stale state | Explain stale/deleted state only when caller may know it. | Conditional. | No. | Deleted/archived fixture and recovery link test. |
| Never existed | 404 | Generic not-found with safe recovery. | No for sensitive resources. | No. | Fabricated ID test. |
| Exists and allowed | 200 | Render route normally. | Yes. | N/A | Allowed direct-entry test. |

## Route Table Template

```text
Route:
  path: /orders/:orderId/items/:itemId
  owner: OrdersRoute
  public_url_status: bookmarked | internal | external_partner | generated_only

Parameters:
  orderId: UUID v4, required, decoded once, validated before fetch
  itemId: UUID v4, required, decoded once, validated before fetch
  query: tab enum [summary, notes, activity], optional, default summary

Data dependencies:
  - GET /api/orders/:orderId
  - GET /api/orders/:orderId/items/:itemId
  - backend authorization evidence: order/item object-level denial is enforced server-side

Guards:
  - unauthenticated -> /login?returnTo=<same-origin current path>, replace history
  - unauthorized -> non-leaking denied or privacy-preserving not-found
  - unavailable -> feature unavailable with parent navigation
  - invalid param -> invalid-link state before fetch
  - deleted/archived -> stale-resource recovery state

Navigation:
  loading: route skeleton matching final layout
  success: render item detail
  error_boundary: item subtree only
  history: push for ordinary navigation; replace after submit/result
  breadcrumbs: Home > Orders > Order > Item
  recovery: parent order, orders list, search

Validation:
  route-level tests for allowed, unauthenticated, unauthorized, invalid param, deleted, never-existed, redirect, and browser back.
```

## Deep-Link State Matrix

Every route that can be opened directly should name these states:

- **Loading:** route shell or skeleton appears while session, params, feature flags, and data dependencies resolve.
- **Allowed success:** resource exists, caller has access, and route renders with stable title/breadcrumbs.
- **Unauthenticated:** session missing or expired; safe `returnTo` is preserved and invalid external returns are dropped.
- **Unauthorized:** caller lacks access; sensitive resources do not reveal title, owner, tenant, or existence.
- **Unavailable:** feature, tenant, maintenance, or entitlement blocks access; route offers a safe landing or request path.
- **Invalid parameter:** malformed path/search params are rejected before fetch and canonicalized when safe.
- **Deleted or archived:** stale resource is explained only to callers allowed to know; recovery path is available.
- **Never existed:** generic not-found with no sensitive resource details.
- **Dependency failure:** route-level error boundary contains the failure to the affected subtree.

## Redirect And History Rules

- Keep redirect chains at depth 2 or less; longer chains require route migration cleanup.
- Validate redirect destinations before navigation, not after login completes.
- Preserve user intent through auth flows only for safe same-origin destinations.
- Use `replace` for login redirect completion, canonicalization, post-submit result pages, and redirect-only compatibility routes.
- Use `push` for user-initiated navigation among meaningful pages or wizard steps the user can revisit safely.
- Do not let browser back re-run POST, payment, delete, export, import, approval, or notification-send actions.
- Route canonicalization should normalize invalid search values without hiding user errors that require recovery.
- Back navigation in wizards should be modeled separately for browser back, app back, cancel, refresh, and re-entry.

## Framework Placement Notes

| Framework style | Good placement | Watchout |
| --- | --- | --- |
| React Router data routers | `loader`, route module, `errorElement`, and route-level actions for param/data readiness. | Component-only guards can fetch before validation or leak loading states. |
| Vue Router | `beforeEach`, per-route guards, route meta, and component-level async handling. | Global guard branches can become broad policy bags. |
| Angular Router | route guards, resolvers, lazy modules, and router events. | Resolver failures need scoped recovery, not app-wide blank screens. |
| Next.js App Router | `loading.tsx`, `error.tsx`, `not-found.tsx`, layout boundaries, and server/client split. | Parallel/intercepting routes require explicit back/close behavior. |
| File-based routers | file path, route metadata, loader conventions, and generated link helpers. | Renaming files can silently break public URLs without redirect inventory. |

## Graph, Memory, And Trajectory Coupling

Route evidence is easy to over-claim because routes are referenced from many places. Treat graph and memory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current router files, link builders, breadcrumbs, templates, tests, and route owners are inspected. | Graph proximity is used as proof that all links or guards are covered. |
| Project memory | Prior route migration or guard decision names unchanged paths and has freshness evidence. | Memory predates route rename, tenant model, router migration, auth flow, or template changes. |
| Execution trajectory | Route/link/guard validation ran after the final route edit. | Output predates final edit or covers only one happy path. |
| Generated links/templates | Generated output, email/notification templates, docs, and sitemap are current. | Generated files were not regenerated or inspected. |
| Analytics/support evidence | Dead-link or support signal is tied to current route names and date range. | Signal lacks route version, tenant, or current reproducibility. |

Strong outputs state which graph or memory evidence was accepted, rejected, or left unknown.

## Route Migration And Public URL Checklist

- Identify old route, new route, route owner, and public/bookmarked/external status.
- Search generated links, email templates, notifications, docs, sitemap, analytics dashboards, support macros, and partner integration notes.
- Decide redirect status and type: permanent, temporary, compatibility-only, or no redirect with accepted break.
- Preserve path/search params intentionally or drop them with safe fallback.
- Define telemetry for old-route hits and removal date for compatibility redirect.
- Confirm rollback can restore old route or keep redirect compatibility.
- Map migration to tests, crawler/link validation, or residual risk.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Safer treatment |
| --- | --- | --- |
| Client route guard is the only authorization control. | Direct API calls bypass the UI. | Backend authorization remains authoritative; UI guard is UX-only. |
| `returnTo` accepts arbitrary absolute URLs. | Open redirect after login. | Same-origin validation and safe fallback. |
| Generic 404 for every route failure. | Hides recovery for stale links and confuses unavailable versus invalid states. | Classify unauthenticated, denied, unavailable, invalid, stale, and never-existed. |
| Direct route fetch starts before param validation. | Wastes calls and risks injection/log pollution. | Validate/canonicalize params at route entry first. |
| Back button after payment or submit revisits side-effecting route. | Duplicate action or misleading partial state. | Replace result routes and model re-entry/idempotency. |
| Route rename without caller inventory. | Emails, bookmarks, docs, and generated links break. | Old/new route map plus redirect/deprecation evidence. |
| Breadcrumbs require params not available in parent route. | Recovery navigation itself breaks. | Breadcrumb data dependencies and fallback labels are explicit. |
| Route-level error boundary is app-wide only. | Nested failure collapses the whole app. | Scope error boundaries to route subtree and recovery path. |

## Handoff Boundaries

- Use `information-architecture` for content hierarchy, labels, grouping, and navigation taxonomy.
- Use `user-flow-modeling` for full journey entry/exit/back/retry/cancel behavior.
- Use `interaction-state-modeling` for single-screen loading, empty, error, disabled, stale, optimistic, and accessibility states.
- Use `permission-boundary-modeling` and `authentication-authorization` for backend authorization model and object-level enforcement.
- Use `api-contract-design` for backend endpoint paths, response/error semantics, and generated client contracts.
- Use `frontend-change-builder` for route implementation, component placement, state/cache integration, and browser behavior.
- Use `frontend-testing` and `quality-test-gate` for executable route, guard, redirect, browser, and accessibility proof.
- Use `change-documentation-gate` or release gates when public URLs, docs, SEO, external partners, or compatibility redirects change.
