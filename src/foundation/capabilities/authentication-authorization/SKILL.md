---
name: authentication-authorization
description: Separates identity proof from action authorization and requires object-level authorization for resource-specific operations.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "41"
changeforge_version: 0.1.0
---

# Mission

Implement authentication and authorization so that **identity proof and action permission are separate, server-enforced, object-aware, tenant-aware, deny-by-default, fully audited, and consistent across every entry point** — including UI, API, internal RPC, background jobs, scheduled tasks, bulk imports, admin tools, and support overrides.

# When To Use

Use this capability when a change touches: sign-in state, sessions, tokens (access/refresh/id), service accounts, machine-to-machine identity, API keys, OAuth 2.0 / OIDC flows, SAML federation, roles, groups, scopes, claims, policies (RBAC/ABAC/ReBAC), tenant scoping, object-level access (owner/sharee/admin), delegation, impersonation, denial behavior, rate-limited-by-identity, sudo/step-up, or audit logging of access decisions.

# Do Not Use When

Do not use this capability to treat authentication as authorization (the most common breach class), to enforce protected actions only through hidden UI controls, to add a single role check at the controller and call it complete, or to replace `authentication-security` (token/session/credential lifecycle hardening) and `permission-boundary-modeling` (policy matrix design before code).

# Non-Negotiable Rules

- **Authentication ≠ authorization.** Proving who you are does not authorize what you do. Every protected action must check both.
- **Backend is the enforcement plane.** Frontend may hide UI for UX; backend must independently enforce. UI-only checks are not a control.
- **Deny by default.** Missing identity, missing scope, missing tenant context, missing resource record, or unknown resource type → denial. Only an explicit allow returns access.
- **Object-level authorization (OLA) is mandatory** for any resource-specific read, update, delete, export, share, transition, bulk operation, or action. Role-only checks (`hasRole('user')`) on object endpoints are the OWASP API #1 vulnerability (BOLA).
- Authorization decisions must consider: **subject (who) · action (verb) · resource (object + type) · resource scope (tenant/org/owner/shared-with) · context (env, time, MFA freshness, IP, device) · purpose (where required by privacy regulation)**.
- **Single decision point.** Centralize the policy decision (PDP) — even if enforcement (PEP) is distributed — so the policy is auditable in one place. Scattering policy across controllers guarantees drift.
- Denials must be **client-safe** (no information leak) and **audit-worthy** (correlation id, subject, action, resource, decision, reason code) without exposing whether the resource exists when existence itself is protected.
- **Privileged operations** (admin, support impersonation, bulk delete, export, billing change, role grant, configuration change) require: re-authentication or MFA step-up, dual control where regulated, immutable audit, and rate limiting.
- Authorization cache must be **bounded in TTL** (seconds-to-minutes) and **invalidated on**: role change, membership change, resource ownership change, tenant suspension, token revocation, policy update.
- Tokens / sessions carry **only the minimum claims**; sensitive attributes are fetched on demand from the authoritative source (avoid stale role embedded for 24h).
- Every protected operation has a **permission test** that asserts both the positive (allowed actor succeeds) and at least three negative cases (unauthenticated, insufficient scope, wrong tenant/owner). Untested policy is unenforced policy.

# Industry Benchmarks

Anchor against: **OWASP API Security Top 10 (2023)** — especially **API1:2023 Broken Object Level Authorization** and **API5:2023 Broken Function Level Authorization**; **OWASP ASVS v4** chapters V1 (Architecture), V4 (Access Control), V8 (Data Protection); **OAuth 2.0 / 2.1 (RFC 6749 + drafts)**, **OAuth 2.0 Security Best Current Practice (RFC 9700)**, **PKCE (RFC 7636)** mandatory for all public clients, **OIDC Core 1.0**, **Token Exchange (RFC 8693)**, **JWT (RFC 7519)** with **JWT Best Current Practice (RFC 8725)** and **JWS/JWE (RFC 7515/7516)**, **SAML 2.0** where federation requires; **NIST SP 800-63B** (authentication assurance levels) and **NIST SP 800-162** (ABAC); **XACML 3.0** conceptual model (PEP/PDP/PIP/PAP separation) — even if you do not use XACML, the separation is the point; **Open Policy Agent (OPA) + Rego** or **Cedar (AWS)** for externalized policy; **Google Zanzibar** model (ReBAC) for fine-grained relationship-based access (also: **SpiceDB / OpenFGA / Permify** implementations); **AWS IAM** least-privilege patterns; **GDPR Art. 32** (security of processing) for audit and access controls on personal data; **SOC 2 CC6** controls for logical access; **ISO/IEC 27001 A.9** access control.

### Access Control Model Selection

| Model | Pick when | Avoid when | Standard reference |
| --- | --- | --- | --- |
| **RBAC** (roles → permissions) | Small set of well-known roles; user-to-role mapping is stable | Many resources with per-object sharing; complex ownership trees | NIST RBAC, INCITS 359 |
| **ABAC** (attributes + rules) | Decisions depend on subject/resource/env attributes (department, classification, time, location) | Simple role checks are sufficient; policy author skill is limited | NIST SP 800-162, XACML |
| **ReBAC** (relationship graph) | Per-object sharing, hierarchies (folders, orgs, teams), invite/share flows like Google Drive / GitHub | No relationship semantics; flat role world | Google Zanzibar; OpenFGA |
| **PBAC / Policy-as-code** | Cross-cutting compliance rules; auditable policy authored separately from code | Tiny app; OPA/Cedar operational cost not justified | OPA, Cedar |
| **Capability-based** | Distributed services where bearer of token = holder of capability (unforgeable refs) | Centralized revocation matters more than decentralization | Tahoe-LAFS, macaroons |

Most real systems combine: **RBAC for coarse roles + ReBAC for object sharing + ABAC for context guards**. The pure form is rarely sufficient.

### Decision Tree: Where to Place the Authorization Check

```
Is this an object-specific action (CRUD on a resource, transition, share, export)?
├─ Yes → REQUIRES object-level check (subject can act on THIS resource):
│        1. Load resource (or its id) with tenant scope in the query (defense in depth).
│        2. Resolve subject's relationship to resource (owner / member / sharee / admin).
│        3. Evaluate policy(subject, action, resource, context) at PDP.
│        4. Audit decision regardless of outcome.
│
└─ No → Function-level action (e.g., "create new project", "view billing")?
         1. Check scope/role at controller.
         2. Audit decision.

Is this a list/search endpoint?
└─ Yes → Filter at query time by tenant + visibility predicate (NEVER list-then-filter-in-app).
         Pagination must be deterministic within the visible set.
```

### Tenant Isolation Defense-in-Depth

| Layer | Control |
| --- | --- |
| Identity token | `tenant_id` claim issued at login; signed; short-lived |
| Request context | Resolved from token, never from request body/header alone |
| Repository / query | Mandatory `WHERE tenant_id = :ctx` filter; enforced by repository base class or row-level security |
| Database | Postgres Row-Level Security (RLS) policies; or schema-per-tenant where regulated |
| Audit | Every read/write logs tenant_id; cross-tenant access alerts |

# Selection Rules

Select this capability when **identity-to-action enforcement** is primary. Adjacent routing:

- Prefer `permission-boundary-modeling` for policy matrix and ownership modeling **before** implementation.
- Prefer `authentication-security` for credential, session, token lifecycle hardening.
- Prefer `web-security` for browser-specific concerns (cookies, CSRF, CORS, clickjacking).
- Prefer `secret-configuration-security` for API keys, service credentials, signing keys storage.
- Prefer `threat-modeling` when the question is broader account/privilege threat surface.
- Use **with** `logging-error-handling` for audit-safe denial logging.

# Risk Escalation Rules

Escalate when access decisions affect: sensitive personal data (PII/PHI/financial), cross-tenant boundaries (the highest-impact bug class in multi-tenant SaaS), administrative actions, service account scope expansion, exports (data exfiltration risk), billing/payments, destructive operations (bulk delete, account close), public APIs, OAuth scope additions to existing clients, impersonation/support-as-user flows, third-party app authorization, or any access path that bypasses normal flow (admin SQL console, support scripts, batch jobs). Escalate any deviation from deny-by-default. Escalate any caching of authorization decisions beyond 5 minutes for mutable membership.

# Critical Details

Role checks are rarely enough for resource-specific operations. A user with role `editor` may still lack access to **this** specific document, folder, project, or tenant. Apply these refinements:

- **BOLA / IDOR is the #1 API bug.** Every endpoint that takes a resource id in the path, query, or body must verify the subject's relationship to that resource — not just that they are authenticated and have a role.
- **Mass assignment companion.** Even with correct OLA, allowing the client to mutate fields like `owner_id`, `tenant_id`, `role`, `is_admin` via PATCH defeats the policy. Allowlist mutable fields per action.
- **Object existence leak.** Returning `403` for forbidden and `404` for non-existent leaks resource existence. Either return `404` uniformly for "not visible to you" (common) or accept the leak knowingly.
- **List endpoints leak via differential timing or count.** Filter at the database layer; never fetch then filter in app code.
- **N+1 authorization.** Bulk endpoints (return list of N items) must batch policy evaluation; per-item PDP calls become a DoS surface.
- **Centralize the PDP, distribute the PEP.** Code calls a policy module (`canUserDo(subject, action, resource, context)`) at the action site. The module is auditable in one file. Inline `if user.role == "admin"` scattered across controllers becomes ungovernable.
- **Sudo / step-up authentication.** Sensitive actions (delete account, change MFA, view full SSN, payment) require recent strong authentication (e.g., MFA within last 5–15 min). GitHub, AWS, Stripe all do this.
- **Impersonation / support-as-user.** Must be: explicitly opt-in (or contractual), time-boxed, scope-limited, banner-visible, audit-logged with the impersonator's identity, and never used to perform destructive actions without dual control.
- **Token claims staleness.** Roles in a JWT are frozen at issue time. If a user is demoted, their token remains until expiry. Solutions: short-lived tokens (≤ 15 min) with refresh, token revocation list, or claim-on-demand from a fast cache invalidated by membership changes.
- **Service-to-service identity.** Service accounts must not have human-level scopes. Use OAuth 2.0 client credentials or mTLS / SPIFFE/SPIRE workload identity. Rotate. Audit.
- **Delegation chains.** When service A calls service B on behalf of user U, B must see U's identity (token exchange RFC 8693) — not A's service identity — otherwise audit and authorization are broken at B.
- **Background jobs and webhooks.** They lack a user context; they must run with **system identity** scoped to the minimum necessary. Never reuse a user's token at job time.
- **Bulk operations.** "Delete all matching" endpoints must verify authorization on each item — not just on the query predicate — because the predicate may include items the subject cannot delete individually.
- **Public endpoint with optional auth.** When the same endpoint serves anonymous and authenticated users with different data, the **default** must be the anonymous view; authentication enriches, never relaxes.
- **Authorization in GraphQL.** Field-level authorization at resolvers; never at the gateway alone. Query depth + complexity limits are part of authorization (DoS).
- **Authorization in event consumers.** Events from one tenant must not be processed in another tenant's scope by mistake (consumer group misconfiguration → cross-tenant breach).
- **Audit log integrity.** Audit records of authorization decisions must be append-only, tamper-evident, retained per compliance (often ≥ 1 year), and accessible without containing the authorization check itself (chicken-and-egg).

### Anti-examples (BOLA family)

| Code | Why it is broken |
| --- | --- |
| `GET /api/orders/{id}` → returns order if authenticated | Any user reads any order by guessing/enumerating id |
| `PATCH /api/users/{id}` with `body.role = "admin"` accepted | Mass-assignment privilege escalation |
| `GET /api/files?owner_id={id}` | Trusting client-supplied tenant/owner = total bypass |
| `DELETE /api/projects/{id}` checks `user.role == "owner"` (role) but not `project.owner_id == user.id` (object) | Cross-tenant delete |
| Frontend hides "Admin" tab; backend `GET /admin/users` returns full list to any session | UI-only enforcement |
| List endpoint queries all rows then `.filter(visible)` in app | Memory exhaustion + timing leak |
| Same `404` for "not found" and "forbidden" only on some endpoints | Inconsistent → enumerable existence |

# Failure Modes

- Authenticated users access objects by changing the id in URL / body (BOLA / IDOR).
- UI hides a button but the backend endpoint still performs the action.
- Tenant scope is checked on list queries but not on detail/mutation/export queries.
- Admin bypass paths (support tools, SQL console, batch jobs) are undocumented and unaudited.
- Denial responses reveal whether a private resource exists (403 vs 404 leak).
- Mass-assignment via PATCH accepts `tenant_id`, `owner_id`, `role` from the client body.
- Role embedded in long-lived JWT outlives the revocation by hours/days.
- Service accounts run with human-superuser scopes "for convenience".
- Background jobs run as `system` with no scope checks because "the system did it".
- GraphQL field-level checks missed; deep query exposes related entities through nested resolvers.
- Audit logs missing: action succeeded but no record of who/why/when; investigation impossible.
- Permission cache invalidation forgotten on role demotion; demoted user retains access until TTL expires.
- Impersonation flow logs the impersonated user as the actor, hiding the support agent's identity.
- "Soft delete" returns hidden records to admin queries without re-authorization.

# Output Contract

Return an authentication-and-authorization implementation plan with:

- `identity_sources` (IdPs, OAuth providers, SAML, internal credential store, service-account issuer)
- `subject_types` (end user, service account, support agent acting as user, anonymous, system)
- `actions_catalog` (named verbs per resource type, e.g., `order.read`, `order.refund`)
- `resources_catalog` (typed, with tenant/owner attributes)
- `policy_model` (RBAC / ABAC / ReBAC / combination; PDP location; policy authoring artifact — code, OPA Rego, Cedar, Zanzibar tuples)
- `object_level_rules` (per resource type → relationship → allowed actions)
- `tenant_isolation_strategy` (token claim, request context, repository filter, DB RLS, audit)
- `enforcement_points` (controller, service, repository, GraphQL resolver, message consumer, job worker)
- `denial_behavior` (status codes, message taxonomy, existence-leak policy)
- `audit_events` (schema, retention, integrity controls, alerting on suspicious patterns)
- `step_up_rules` (which actions require recent strong auth)
- `cache_rules` (what is cached, TTL, invalidation triggers)
- `session_or_token_rules` (handoff to `authentication-security` for lifecycle)
- `tests` (positive + at least: unauthenticated, insufficient scope, wrong tenant, wrong owner, expired credential, mass-assignment attempt, list-endpoint cross-tenant)
- `residual_risks` and `owner`

# Quality Gate

The auth design passes only when:

1. Authentication and authorization are **separate concerns**, both enforced server-side.
2. Every protected endpoint has an **object-level rule** documented and tested (not just role check).
3. Tenant isolation is enforced at the database query layer, not just at controller.
4. Deny-by-default is provable (a new endpoint without explicit policy → forbidden by framework).
5. Mass-assignment is prevented (per-action allowlist of mutable fields).
6. Existence-leak policy is explicit and consistent (always 404 vs always 403 for forbidden — pick and apply uniformly).
7. Privileged actions require step-up and dual control where regulated.
8. Cache invalidation on role/membership/ownership change is implemented and tested.
9. Audit events exist for every allow and every deny on sensitive actions; logs are tamper-evident and retained per compliance.
10. Permission tests include negative cases (≥ 3 classes per protected action).
11. Service accounts and background jobs have scoped identities — no human-superuser sharing.

# Used By

- backend-change-builder
- security-privacy-gate

# Handoff

Hand off to `permission-boundary-modeling` for policy matrix design; `authentication-security` for credential, token, session lifecycle hardening; `web-security` for cookies, CSRF, CORS, clickjacking; `secret-configuration-security` for service credentials and signing keys; `logging-error-handling` for audit-safe error and denial messages; `frontend-testing` for permission-state coverage and denied-UI tests; `threat-modeling` for broader privilege-escalation analysis.

# Completion Criteria

The capability is complete when **every protected operation — across UI, API, internal RPC, background jobs, scheduled tasks, bulk imports, admin tools, and support overrides — has explicit identity verification, object-level policy evaluation at a centralized PDP, tenant-scoped query enforcement, deny-by-default fallback, structured audit, invalidation on membership change, and negative-case permission tests**.
