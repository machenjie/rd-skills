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

# Non-Negotiable Rules

- **Every route must have an explicit guard classification covering all four distinct outcomes:** (1) Unauthenticated — user has no session; redirect to login with `returnTo` preserved. (2) Unauthorized — user is authenticated but lacks permission to the resource; show 403-equivalent without confirming the resource exists (do not leak resource existence to unauthorized users). (3) Unavailable — feature is disabled, tenant does not have access, or maintenance mode; show explicit unavailable state (not a 404). (4) Not-found — resource genuinely does not exist; show 404 without leaking existence for sensitive resources.
- **Frontend route guards improve UX but must never replace backend authorization.** A route guard that blocks navigation in the browser is a UX optimization, not a security control. The backend API must enforce the same authorization independently. A user who bypasses frontend routing (by directly calling the API or by disabling JavaScript) must receive the correct 401/403 from the server.
- **Redirects must be loop-free, intent-preserving, and have a maximum depth of 2.** A redirect chain of `/a → /b → /c` is a navigation smell and usually indicates structural ambiguity. A redirect must not erase user intent (e.g., `returnTo` must be preserved across login redirects). Redirects used for login flows must validate that the `returnTo` destination is a same-origin URL (open redirect prevention per OWASP).
- **Deep links must define all five loading states:** (1) Loading — data is being fetched; show skeleton or progress indicator, not a blank screen. (2) Success — resource exists and user has access; render. (3) Permission-denied — resource exists but user cannot access it; show unauthorized state without confirming existence for sensitive resources. (4) Deleted/archived — resource existed but no longer does; show recovery path (parent, similar resource, or search), not a generic 404. (5) Never-existed — resource ID is invalid or fabricated; show generic 404.
- **Path parameters must be validated at route entry.** A malformed `:orderId` (non-UUID, negative integer, SQL fragment) must be rejected at the routing layer before any data fetch begins. Validation rules must be documented in the route table.
- **Browser history behavior must be explicit for destructive and wizard flows.** A user who completes a purchase and presses back must not re-submit the form. A user who abandons a multi-step wizard must land on a safe page, not a broken intermediate step. Use `history.replace()` for post-submission states; use `history.push()` for navigable steps.

# Industry Benchmarks

Anchor against: **RFC 3986 (URI Generic Syntax)** — path parameter encoding, reserved characters, percent-encoding; `+` vs `%20` in path vs. query. **OWASP Open Redirect Prevention** — validate `returnTo` is same-origin before redirect; do not trust `returnTo` query parameter from untrusted input. **WCAG 2.2 — Success Criterion 2.4.4 (Link Purpose)** and **2.4.5 (Multiple Ways)** — navigation must convey destination purpose; routes must be discoverable via multiple paths. **HTML Living Standard — History API** (`pushState`, `replaceState`, `popstate`) — controls browser history stack entries; `replace` vs. `push` semantics matter for back-button UX. **React Router v6 / Vue Router 4 / Angular Router** — file-based and programmatic routing conventions; `loader` / `beforeEach` guard lifecycle; `errorElement` / error boundary for route-level error containment. **Next.js App Router** — layouts, parallel routes, intercepting routes, and `not-found.tsx` placement. **Nielsen's Heuristics #9 (Error Prevention)** — destructive actions (delete, submit) must not be reachable via browser back; use `replace` to remove them from history.

### Route Guard Classification Matrix

| Condition | HTTP Equivalent | UI Behavior | Resource Existence Disclosed? | `returnTo` Preserved? |
| --- | --- | --- | --- | --- |
| No session (unauthenticated) | 401 | Redirect to login | N/A | Yes |
| Authenticated, no permission | 403 | Show 403 page (no resource name for sensitive) | No (for sensitive) | No |
| Feature disabled / tenant locked | 503 | Show feature-unavailable screen | N/A | No |
| Resource does not exist | 404 | Show 404 with recovery path | No (for sensitive) | No |
| Route parameter invalid | 400 | Reject at routing layer, show 400/invalid-link | N/A | No |
| Resource exists, user has access | 200 | Render normally | Yes | N/A |

### Route Table Template

```
Route: /orders/:orderId/items/:itemId
Method: GET (client navigation)
Parameters:
  orderId: UUID v4, required — validate regex /^[0-9a-f-]{36}$/i
  itemId:  UUID v4, required — validate regex /^[0-9a-f-]{36}$/i
Guards:
  1. Session exists? → NO: redirect /login?returnTo=/orders/:orderId/items/:itemId
  2. User owns order OR user is admin? → NO: 403 (do not confirm order exists)
  3. Order exists? → NO: 404 with parent link /orders/:orderId
  4. Item exists in order? → NO: 404 with parent link /orders/:orderId
Data dependencies:
  - GET /api/orders/:orderId (auth required)
  - GET /api/orders/:orderId/items/:itemId (auth required)
Loading state: skeleton overlay
Deleted/stale: "This item has been removed. View order ›"
History behavior: push (navigable; back returns to order detail)
Breadcrumbs: Home > Orders > Order #:orderId > Item #:itemId
```

# Selection Rules

Select this capability when **URL behavior, navigation guard logic, or route state management is the primary design concern**. Route elsewhere when: server-side authorization model needs design independent of routing (use `authentication-authorization`); content hierarchy, labels, and navigation structure need design before routes are defined (use `information-architecture`); API path design needs to be specified (use `api-contract-design`); component-level state that does not map to a URL needs design (use `interaction-state-modeling`).

# Risk Escalation Rules

Escalate immediately when: a route change affects a public or bookmarked URL that is referenced by external systems, search engines, or partner integrations (changing it without a redirect is a breaking change); a guard classification could disclose resource existence to unauthorized users for a sensitive resource (e.g., confirming a private user profile exists before checking permission); a `returnTo` redirect parameter is taken from user input without same-origin validation (open redirect vulnerability — OWASP A10); a route's data dependency requires elevated privileges that the frontend cannot express (coordinate with backend authorization design); or removing a named route would break existing deep links in email, notifications, or external integrations.

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

# Output Contract

Return a routing design with:

- `route_table` (per route: path, parameters with validation rules, guards per outcome type, data dependencies, loading state, deleted/stale state, history behavior, breadcrumbs)
- `redirect_map` (from → to, trigger condition, `returnTo` preservation, loop prevention)
- `guard_classification` (per route: unauthenticated / unauthorized / unavailable / not-found behavior; resource existence disclosure policy)
- `deep_link_states` (all 5 loading states per route that supports direct entry)
- `history_strategy` (push vs. replace per step; back-button behavior for destructive/wizard flows)
- `parameter_validation` (regex/type constraints per path parameter)
- `error_boundary_scope` (which route subtrees have isolated error boundaries)
- `route_level_tests` (per route: guard tests, deep-link tests, redirect loop tests, parameter rejection tests)

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

# Used By

- frontend-change-builder
- experience-impact-modeler

# Handoff

Hand off to `authentication-authorization` for server-side authorization policy; `permission-boundary-modeling` for object-level access; `information-architecture` for navigation hierarchy and label design; `interaction-state-modeling` for in-page state that does not map to URLs; `frontend-change-builder` for implementation.

# Completion Criteria

The capability is complete when **every route is specified as a stable navigation contract with security-correct guards, loop-free redirects, deep-link recovery states, history discipline for destructive flows, and parameter validation — implementable without further design decisions by the frontend builder**.
