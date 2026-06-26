---
name: routing-navigation-design
description: Designs route tables, guards, redirects, deep links, unauthorized and stale-link handling, 404 behavior, and navigation recovery.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "32"
changeforge_version: 0.1.0
---

# Mission

**Design a complete navigation contract for every changed route** — covering the route table, path parameter validation, guard classification (unauthenticated vs. unauthorized vs. unavailable vs. not-found), redirect loop prevention, deep-link loading and recovery states, browser history behavior, and stale-link handling — so that routes are implementable as stable, security-correct product contracts that survive direct entry, bookmark, back-button, and permission-change scenarios without leaking resource existence or trapping users in dead states.

# When To Use

Use this capability when: a change adds, removes, or renames routes; route parameters change (shape, validation, encoding); navigation guards need to be added or revised; a redirect chain is being introduced or modified; an existing deep link is changing target behavior; unauthorized or not-found states need differentiation; back-button behavior after a destructive action is under-specified; or breadcrumb or tab navigation changes require consistent URL and state management.

# Do Not Use When

Do not use this capability for: purely visual navigation styling changes with no route behavior impact (use a frontend component design); server-side authorization policy design where the routing outcome is a side effect (use `authentication-authorization`); information architecture and content labeling where URL behavior is not the primary concern (use `information-architecture`); or API routing/path parameter design (use `api-contract-design`).

# Stage Fit

Use during experience planning when a route, redirect, deep link, breadcrumb, wizard step, stale link, or back-button behavior becomes part of the product contract. Use during frontend implementation review when route guards, loaders, route-level error boundaries, URL/search state, parameter validation, lazy route modules, or navigation side effects are added or changed. Use during testing when direct entry, bookmark, refresh, browser back, unauthenticated, unauthorized, unavailable, not-found, deleted/stale, invalid-parameter, and redirect-loop cases need proof. Repository graph, project memory, analytics, support reports, and previous route decisions may suggest candidate route behavior, but current routes, router config, tests, generated links, notification/email templates, and backend authorization contracts must confirm active behavior before route evidence is treated as current.

# Non-Negotiable Rules

- **Every route must have an explicit guard classification covering all four distinct outcomes:** (1) Unauthenticated — user has no session; redirect to login with `returnTo` preserved. (2) Unauthorized — user is authenticated but lacks permission to the resource; show 403-equivalent without confirming the resource exists (do not leak resource existence to unauthorized users). (3) Unavailable — feature is disabled, tenant does not have access, or maintenance mode; show explicit unavailable state (not a 404). (4) Not-found — resource genuinely does not exist; show 404 without leaking existence for sensitive resources.
- **Frontend route guards improve UX but must never replace backend authorization.** A route guard that blocks navigation in the browser is a UX optimization, not a security control. The backend API must enforce the same authorization independently. A user who bypasses frontend routing (by directly calling the API or by disabling JavaScript) must receive the correct 401/403 from the server.
- **Redirects must be loop-free, intent-preserving, and have a maximum depth of 2.** A redirect chain of `/a → /b → /c` is a navigation smell and usually indicates structural ambiguity. A redirect must not erase user intent (e.g., `returnTo` must be preserved across login redirects). Redirects used for login flows must validate that the `returnTo` destination is a same-origin URL (open redirect prevention per OWASP).
- **Deep links must define all five loading states:** (1) Loading — data is being fetched; show skeleton or progress indicator, not a blank screen. (2) Success — resource exists and user has access; render. (3) Permission-denied — resource exists but user cannot access it; show unauthorized state without confirming existence for sensitive resources. (4) Deleted/archived — resource existed but no longer does; show recovery path (parent, similar resource, or search), not a generic 404. (5) Never-existed — resource ID is invalid or fabricated; show generic 404.
- **Path parameters must be validated at route entry.** A malformed `:orderId` (non-UUID, negative integer, SQL fragment) must be rejected at the routing layer before any data fetch begins. Validation rules must be documented in the route table.
- **Browser history behavior must be explicit for destructive and wizard flows.** A user who completes a purchase and presses back must not re-submit the form. A user who abandons a multi-step wizard must land on a safe page, not a broken intermediate step. Use `history.replace()` for post-submission states; use `history.push()` for navigable steps.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- |
| New or changed route contract | Route added, removed, renamed, nested, lazy-loaded, or given new path/search params. | Define path, owner, params, loader/data dependencies, guard order, deep-link states, titles, breadcrumbs, and tests. | Current route config, generated links, route owner, parameter schema, deep-link state table. | `page-component-decomposition`, `interaction-state-modeling`, `frontend-testing` | Visual-only navigation styling. |
| Guard or redirect revision | Login redirect, `returnTo`, permission gate, feature/tenant gate, canonical redirect, or stale-link redirect changes. | Preserve intent without open redirects, loops, or existence disclosure. | Guard classification, same-origin return validation, redirect map, loop-depth proof, backend-auth boundary. | `permission-boundary-modeling`, `security-privacy-gate`, `api-contract-design` | Client guard as security proof. |
| Deep-link and stale-link recovery | Email/notification/bookmark/search result opens a route directly, or deleted/archived resources remain linked. | Model loading, allowed, denied, unavailable, deleted/archived, never-existed, invalid-param, and recovery states. | Entry source, route params, data dependency, stale-resource policy, parent/search recovery path. | `user-flow-modeling`, `information-architecture`, `interaction-state-modeling` | Generic 404 for every failure. |
| Wizard/destructive/history flow | Checkout, submit, delete, archive, import/export, multi-step wizard, or post-action confirmation changes browser history. | Prevent back-button resubmission and define refresh, back, cancel, and re-entry behavior. | Push/replace decision, side-effecting step map, idempotency/retry handoff, browser-back tests. | `user-flow-modeling`, `idempotency-retry-design`, `frontend-testing` | Browser default as an implicit contract. |
| Route migration or public URL compatibility | Public/bookmarked URLs, SEO paths, external partner links, emails, notifications, or generated clients change. | Preserve compatibility or define redirect/deprecation strategy and consumer impact. | Old/new route map, caller inventory, redirect status, telemetry, rollback path. | `consumer-impact-analysis`, `version-compatibility`, `quality-test-gate` | Breaking links without explicit migration. |

# Industry Benchmarks

Anchor against RFC 3986 URI syntax, OWASP open-redirect prevention, WCAG 2.2 link purpose/multiple-ways/focus-order requirements, HTML History API semantics, React Router/Vue Router/Angular Router guard and error-boundary conventions, Next.js App Router not-found/error/layout patterns, and error-prevention heuristics for destructive flows. Keep this body focused on routing, evidence, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for guard matrices, route-table templates, deep-link states, redirect/history rules, framework placement notes, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when **URL behavior, navigation guard logic, or route state management is the primary design concern**. Route elsewhere when: server-side authorization model needs design independent of routing (use `authentication-authorization`); content hierarchy, labels, and navigation structure need design before routes are defined (use `information-architecture`); API path design needs to be specified (use `api-contract-design`); component-level state that does not map to a URL needs design (use `interaction-state-modeling`).

# Risk Escalation Rules

Escalate immediately when: a route change affects a public or bookmarked URL that is referenced by external systems, search engines, or partner integrations (changing it without a redirect is a breaking change); a guard classification could disclose resource existence to unauthorized users for a sensitive resource (e.g., confirming a private user profile exists before checking permission); a `returnTo` redirect parameter is taken from user input without same-origin validation (open redirect vulnerability — OWASP A10); a route's data dependency requires elevated privileges that the frontend cannot express (coordinate with backend authorization design); or removing a named route would break existing deep links in email, notifications, or external integrations.

# Proactive Professional Triggers

- **Signal:** a route accepts `returnTo`, `redirect`, `next`, `continue`, or `callbackUrl` from user input. **Hidden risk:** open redirect, login-loop, or intent loss after authentication. **Required professional action:** require same-origin allowlist, safe fallback, loop-depth limit, and tests. **Route to:** `security-privacy-gate`, `web-security`, `frontend-testing`. **Evidence required:** rejected external URL case, valid return case, invalid return fallback, and no token/PII in URL.
- **Signal:** route guard checks role, tenant, feature flag, or ownership in the client but backend/API evidence is not named. **Hidden risk:** client-side permission illusion and resource-existence leak. **Required professional action:** model the client guard as UX only and hand off server enforcement. **Route to:** `permission-boundary-modeling`, `authentication-authorization`, `security-privacy-gate`. **Evidence required:** backend policy/API denial path or explicit not-verified residual risk.
- **Signal:** deep link comes from email, notification, external partner, search index, QR code, or saved bookmark. **Hidden risk:** stale resource, wrong tenant, invalid params, or broken recovery path. **Required professional action:** define direct-entry loading and recovery states before implementation. **Route to:** `user-flow-modeling`, `information-architecture`, `frontend-testing`. **Evidence required:** entry source, param validation, deleted/archived/never-existed branch, recovery destination.
- **Signal:** destructive, payment, import/export, approval, or multi-step wizard route uses default browser history. **Hidden risk:** duplicate side effect, resubmission, unsafe retry, or partial-state confusion. **Required professional action:** define push/replace/re-entry/cancel behavior and hand off idempotency when needed. **Route to:** `user-flow-modeling`, `idempotency-retry-design`, `quality-test-gate`. **Evidence required:** history strategy, side-effecting step map, back/refresh test or residual risk.
- **Signal:** old route is removed or renamed and generated links, email templates, docs, sitemap, analytics, or partner URLs were not searched. **Hidden risk:** public URL break and unmeasured dead links. **Required professional action:** inventory callers and define redirect/deprecation/telemetry. **Route to:** `consumer-impact-analysis`, `version-compatibility`, `change-documentation-gate`. **Evidence required:** searched sources, old/new map, redirect or deprecation policy.
- **Signal:** repository graph or project memory says a route pattern exists, but current router config, tests, generated links, and templates were not inspected. **Hidden risk:** stale memory preserves dead links or obsolete guards. **Required professional action:** confirm with current source and mark unsupported memory as a hint only. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** inspected paths, accepted/rejected memory, unknown route surfaces, validation gap.

# Critical Details

- **Conflating unauthorized and not-found is both a UX failure and a security risk.** "Page not found" for a resource the user is not allowed to see is a reasonable privacy choice for sensitive resources (user profiles, confidential records). "You don't have permission" for a resource that does not exist is confusing and gives false information. The guard must decide: is the resource sensitive enough that acknowledging its existence is itself a disclosure?
- **The `returnTo` parameter is an injection surface.** An attacker can craft a link like `/login?returnTo=https://evil.com`. After login, the redirect sends the user (with a fresh session) to the attacker's site. Rule: validate that `returnTo` is same-origin before redirecting. If invalid, redirect to the safe default landing page.
- **Wizard and multi-step flows require history discipline.** If a user is on step 3 of a 5-step checkout and presses back, they expect to see step 2 — not to re-trigger a payment. Each step that the user can navigate back to should use `push`; each step that must not be re-entered (post-submission confirmation, post-payment result) should use `replace`.
- **Route-level error boundaries prevent total app collapse on partial failure.** A 404 for a nested resource (e.g., a comment in a thread) must not collapse the entire application to an error screen. Route error boundaries (`errorElement` in React Router, `error.tsx` in Next.js) scope the failure to the affected subtree.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Frontend guard redirects to login; backend API returns 200 for unauthenticated requests | Authorization is UI-only; direct API caller bypasses all access control | Backend API enforces 401/403 independently of frontend routing |
| Unauthorized and not-found both show generic "Page not found" | Confirms resource existence to unauthorized users for authorized-but-hidden resources; confusing UX when resource genuinely doesn't exist | Guard distinguishes 403 vs 404; sensitive resources show 403 without confirming existence |
| `returnTo=/login?returnTo=https://evil.com` in redirect chain | Open redirect; user lands on attacker site after auth | Validate `returnTo` is same-origin before redirect |
| Back button after payment confirmation resubmits payment form | Duplicate charge risk; browser replays POST | Use `history.replace` on payment confirmation to remove POST from history stack |
| Deep link to deleted resource shows generic 404 | User loses context; no recovery path | Show "This order has been cancelled. View your orders ›" with parent link |
| Route parameter `:id` accepts `'; DROP TABLE orders;--` | Parameter injection risk | Validate route parameters against strict regex/UUID pattern at routing layer before any data fetch |

# Failure Modes

- Route renders blank screen while guard check is pending (no loading state defined).
- Unauthorized shows resource title in the 403 page header — leaks existence.
- Login redirect uses `history.push` instead of `replace`; user can back-button loop between login and the guarded page.
- `returnTo` not sanitized; phishing link exploits open redirect on login flow.
- Deep link to a resource in a tenant the user switched out of: renders the wrong tenant's data because tenant context is from session, not from URL.
- Route parameter accepts spaces and SQL fragments; no validation at routing layer.
- Wizard back-navigation re-triggers idempotent-but-not-safe action (e.g., send email confirmation on every visit to step 2).
- Breadcrumb links navigate to parent routes that themselves require parameters not available in the breadcrumb context.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 route-selection, guard, output, and quality-gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete route table, redirect map, guard classification, stale-link plan, deep-link recovery, or browser-history contract. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when guard matrices, route-table templates, redirect/history semantics, framework placement, route migration, or graph/memory/trajectory evidence need more depth. Use [examples/example-output.md](examples/example-output.md) only when expected output shape is unclear. Do not load references for pure routing or metadata-only edits with no route contract output.

# Output Contract

Return a routing design with:

- `mode_selected` (new/changed route contract, guard/redirect revision, deep-link/stale-link recovery, wizard/destructive/history flow, or route migration/public URL compatibility)
- `route_scope` (owning product surface, changed routes, current route tree, old/new paths, excluded screens, and public/bookmarked URL status)
- `source_evidence` (current router config, page files, loaders/actions, generated link builders, email/notification templates, breadcrumbs, sitemap/docs, backend authorization contract, tests, repository graph, project memory, execution trajectory, and freshness limits)
- `route_table` (per route: path, parameters with validation rules, guards per outcome type, data dependencies, loading state, deleted/stale state, history behavior, breadcrumbs)
- `redirect_map` (from → to, trigger condition, `returnTo` preservation, loop prevention)
- `guard_classification` (per route: unauthenticated / unauthorized / unavailable / not-found behavior; resource existence disclosure policy)
- `deep_link_states` (all 5 loading states per route that supports direct entry)
- `history_strategy` (push vs. replace per step; back-button behavior for destructive/wizard flows)
- `parameter_validation` (regex/type constraints per path parameter)
- `error_boundary_scope` (which route subtrees have isolated error boundaries)
- `route_level_tests` (per route: guard tests, deep-link tests, redirect loop tests, parameter rejection tests)
- `route_change_to_validation_map` (each changed route, param, guard, redirect, deep-link state, error boundary, breadcrumb, generated link, public URL, or history behavior mapped to test/validator/manual review or residual risk)
- `reuse_and_placement_rationale` (existing route modules, loaders, link builders, error boundaries, guards, layout slots, and test harnesses reused; rejected duplicate route/guard/helper locations)
- `behavior_preservation` (old valid links, return intent, back/refresh behavior, route titles, breadcrumbs, analytics, permission-denied behavior, and stale-link recovery preserved or intentionally changed)
- `handoff_boundaries` (what belongs to information architecture, user flow, interaction state, permission/backend auth, API contract, frontend implementation, documentation, or release)
- `validation_evidence` (commands, route tests, browser checks, link crawler, screenshot/manual evidence, freshness, or not-verified disclosure)
- `evidence_limits` (what was not inspected: production links, partner URLs, email archives, SEO index, generated clients, backend auth, browser matrix, or live analytics)

# Evidence Contract

Close routing-navigation design only when these answers are concrete:

- **Boundary basis:** selected mode, current route surface, old/new route contract, security/UX benchmark, and route owner.
- **Current boundaries inspected:** router config, page/layout/loader/action files, generated links, breadcrumbs, docs/templates, tests, backend authorization/API contract, repository graph, project memory, and execution trajectory accepted or rejected for freshness.
- **Placement rationale:** why route guard, loader, redirect, error boundary, breadcrumb, and link generation belong at the selected router/page/layout/helper boundary and why duplicate or frontend-only security placement is rejected.
- **Navigation proof:** guard classification, non-leaking denial, direct-entry state, stale/deleted recovery, invalid-param branch, redirect loop control, push/replace choice, and public URL compatibility named for every changed route.
- **Validation proof:** each route, param, guard, redirect, stale/deep-link state, history behavior, and generated link maps to route-level tests, browser/manual checks, crawler/link validation, or named residual risk.
- **Behavior preservation and residual risk:** old valid links and safe denials are preserved or intentionally changed; uninspected partner links, templates, SEO surfaces, browser behavior, or backend auth evidence have owner and next gate.

# Quality Gate

The routing design is complete only when:

1. Every route has a guard classification for all four outcomes (unauthenticated, unauthorized, unavailable, not-found).
2. Frontend guards are confirmed NOT to replace backend authorization.
3. `returnTo` parameter is validated same-origin before any redirect.
4. All deep-link routes define all five loading states.
5. Path parameters have explicit validation rules documented.
6. Redirect chains have maximum depth 2; no loops possible.
7. History strategy (push vs. replace) is specified for every wizard and post-submission route.
8. Resource existence disclosure policy is explicit for sensitive resources.
9. Route-level error boundaries are scoped appropriately.
10. Route-level tests cover guard, deep-link, redirect, and parameter-validation behaviors.
11. Current-source, repository graph, project memory, and execution trajectory evidence are freshness-scoped; inferred route coverage is marked not verified.
12. Every changed public/bookmarked/generated route has caller inventory, redirect/deprecation decision, or named residual risk.
13. Breadcrumbs, titles, generated links, email/notification templates, sitemap/docs, and analytics paths are inspected or explicitly out of scope.
14. Every changed route behavior maps to validation evidence or a named residual risk with next owner.

# Used By

- frontend-change-builder
- experience-impact-modeler

# Handoff

Hand off to `authentication-authorization` for server-side authorization policy; `permission-boundary-modeling` for object-level access; `information-architecture` for navigation hierarchy and label design; `interaction-state-modeling` for in-page state that does not map to URLs; `frontend-change-builder` for implementation.

# Completion Criteria

The capability is complete when **every route is specified as a stable navigation contract with security-correct guards, loop-free redirects, deep-link recovery states, history discipline for destructive flows, and parameter validation — implementable without further design decisions by the frontend builder**.
