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

Also use it when repository graph, project memory, or execution traces show a new read/write path, job worker, support tool, export, list query, cache layer, or downstream integration that can bypass the normal user-facing authorization route.

# Do Not Use When

Do not use this capability to treat authentication as authorization (the most common breach class), to enforce protected actions only through hidden UI controls, to add a single role check at the controller and call it complete, or to replace `authentication-security` (token/session/credential lifecycle hardening) and `permission-boundary-modeling` (policy matrix design before code).

# Stage Fit

- **Planning / design:** map subjects, actions, resources, tenants, privileged paths, and deny semantics before APIs or data access are finalized.
- **Implementation / repair:** place enforcement at every entry point and keep policy evaluation centralized enough to review, test, and audit.
- **Review:** reject changes that add a protected operation without object-level rules, negative permission tests, and audit evidence.
- **Release / migration:** verify rollout keeps existing denials, invalidates stale claims/caches, and preserves audit continuity across old and new paths.

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
- Authorization claims must be backed by **repository graph evidence** (all entry points found), **memory evidence** (known policy decisions and constraints reused or updated), **execution evidence** (commands/tests proving enforcement paths), and **validation evidence** (permission tests or explicit gaps).

# Industry Benchmarks

Anchor against OWASP API Security Top 10 2023 (BOLA/BFLA), OWASP ASVS V1/V4/V8, OAuth/OIDC/JWT/SAML security BCPs, NIST 800-63B and 800-162, XACML PEP/PDP concepts, OPA/Rego or Cedar policy-as-code, Zanzibar-style ReBAC systems, AWS IAM least privilege, GDPR Art. 32, SOC 2 CC6, and ISO/IEC 27001 A.9. Use these as review anchors, not as a requirement to reproduce every standard in the skill body.

### Access Control Model Selection

| Model | Pick when | Avoid when | Standard reference |
| --- | --- | --- | --- |
| **RBAC** (roles → permissions) | Small set of well-known roles; user-to-role mapping is stable | Many resources with per-object sharing; complex ownership trees | NIST RBAC, INCITS 359 |
| **ABAC** (attributes + rules) | Decisions depend on subject/resource/env attributes (department, classification, time, location) | Simple role checks are sufficient; policy author skill is limited | NIST SP 800-162, XACML |
| **ReBAC** (relationship graph) | Per-object sharing, hierarchies (folders, orgs, teams), invite/share flows like Google Drive / GitHub | No relationship semantics; flat role world | Google Zanzibar; OpenFGA |
| **PBAC / Policy-as-code** | Cross-cutting compliance rules; auditable policy authored separately from code | Tiny app; OPA/Cedar operational cost not justified | OPA, Cedar |
| **Capability-based** | Distributed services where possession of an unforgeable reference grants the capability | Centralized revocation matters more than decentralization | Tahoe-LAFS, macaroons |

Most real systems combine: **RBAC for coarse roles + ReBAC for object sharing + ABAC for context guards**. The pure form is rarely sufficient.

# Mode Matrix

| Mode | Minimum professional output |
| --- | --- |
| Plan | subject/action/resource matrix, tenant boundary, policy model, privileged paths, and known bypass paths |
| Implement | PDP/PEP placement, repository filters, object checks, denial taxonomy, audit event schema, and negative tests |
| Review | diff-to-entry-point map, stale claim/cache risk, missing object checks, mass-assignment checks, and denied-path evidence |
| Repair | verified failed enforcement path, root cause, same-pattern scan, regression test, and rollback note |
| Release | compatibility of existing policies, cache/token invalidation plan, audit continuity, and migration/backfill safety |

# Selection Rules

Select this capability when **identity-to-action enforcement** is primary. Adjacent routing:

- Prefer `permission-boundary-modeling` for policy matrix and ownership modeling **before** implementation.
- Prefer `authentication-security` for credential, session, token lifecycle hardening.
- Prefer `web-security` for browser-specific concerns (cookies, CSRF, CORS, clickjacking).
- Prefer `secret-configuration-security` for API keys, service credentials, signing keys storage.
- Prefer `threat-modeling` when the question is broader account/privilege threat surface.
- Use **with** `logging-error-handling` for audit-safe denial logging.
- Use **with** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the work must prove all entry points, prior decisions, executed checks, and validation evidence are coupled.

# Proactive Professional Triggers

- **Signal:** A new endpoint, resolver, worker, webhook, scheduled job, admin/support script, export, import, or bulk action reads or mutates protected data. **Hidden risk:** alternate entry point bypasses object-level authorization and becomes privilege escalation or cross-tenant leak. **Required professional action:** map every entry point, subject/action/resource/tenant context, PDP/PEP check, and allow/deny tests. **Route to:** `authentication-authorization`, `repository-graph-analysis`, `permission-boundary-modeling`. **Evidence required:** entry-point graph, changed-operation-to-policy map, and positive/negative permission test output.
- **Signal:** Resource, tenant, owner, account, document, or asset id moves through a path, query, body, event, queue message, cache key, or downstream service call. **Hidden risk:** BOLA/IDOR or tenant confusion lets a caller guess, replay, or reuse identifiers. **Required professional action:** verify ownership and tenant scope at repository/query boundary and policy decision. **Route to:** `authentication-authorization`, `data-side-effect-flow-tracing`, `repository-persistence`. **Evidence required:** same-pattern identifier scan and denied cross-tenant/wrong-owner regression output.
- **Signal:** Roles, groups, scopes, policy files, sharing links, invites, impersonation, delegation, service accounts, or machine-to-machine calls change. **Hidden risk:** authentication claim is mistaken for authorization, stale privilege survives demotion, or delegated actor loses audit accountability. **Required professional action:** separate identity proof from authorization decision, bound claim/cache freshness, and record real actor plus effective subject. **Route to:** `authentication-authorization`, `authentication-security`, `logging-error-handling`. **Evidence required:** policy matrix, invalidation rule, actor/effective-subject audit schema, and denied stale-claim test.
- **Signal:** A list, search, report, aggregation, pagination, cache, or export path returns protected rows. **Hidden risk:** filtering after fetch, pagination, aggregation, serialization, or cache reuse leaks invisible records through rows, counts, timing, or exports. **Required professional action:** enforce tenant/visibility predicates before pagination, aggregation, export, or cache write. **Route to:** `authentication-authorization`, `indexing-query-optimization`, `search-analytics-design`. **Evidence required:** query predicate, list/export fixture, and denied invisible-row regression result.
- **Signal:** Denial behavior, audit events, policy cache, tenant suspension, role demotion, support override, or privileged step-up changes. **Hidden risk:** denials reveal resource existence, privileged actions lack accountability, or revoked authority remains usable. **Required professional action:** define denial taxonomy, immutable audit fields, privileged re-auth/dual-control rules, and cache invalidation triggers. **Route to:** `authentication-authorization`, `security-privacy-gate`, `validation-broker`. **Evidence required:** denial contract, audit sample, invalidation test, and residual-risk owner.

# Risk Escalation Rules

Escalate when access decisions affect: sensitive personal data (PII/PHI/financial), cross-tenant boundaries (the highest-impact bug class in multi-tenant SaaS), administrative actions, service account scope expansion, exports (data exfiltration risk), billing/payments, destructive operations (bulk delete, account close), public APIs, OAuth scope additions to existing clients, impersonation/support-as-user flows, third-party app authorization, or any access path that bypasses normal flow (admin SQL console, support scripts, batch jobs). Escalate any deviation from deny-by-default. Escalate any caching of authorization decisions beyond 5 minutes for mutable membership.

# Reference Loading Policy

- **L1:** Read this `SKILL.md` only for ordinary route, plan, review, or small implementation work.
- **L2:** Read `references/checklist.md` when producing a concrete implementation/review checklist or checking denial, audit, cache, tenant, and test completeness.
- **L3:** Read `examples/example-output.md` when the user needs a structured auth plan or when output shape is underspecified.
- **Do not load adjacent skills by default.** Load `permission-boundary-modeling`, `authentication-security`, `threat-modeling`, or `secret-configuration-security` only when the task crosses into policy design, credential lifecycle, broader abuse analysis, or key/secret handling.

# Critical Details

Role checks are rarely enough for resource-specific operations. A user with role `editor` may still lack access to **this** specific document, folder, project, or tenant. Apply these refinements:

- **Boundary placement:** record controller/resolver, service, repository/query, worker, consumer, and support/admin enforcement points; absence in the current graph is a finding.
- **Object and tenant scope:** every resource id in a path, query, body, event, cache key, or downstream call needs subject-resource relationship and tenant predicate proof.
- **Mutable field allowlist:** correct OLA still fails if PATCH accepts `owner_id`, `tenant_id`, `role`, or `is_admin`; allowlist mutable fields per action.
- **Safe denial:** pick and apply a consistent 403/404 existence-leak policy with client-safe messages and audit-safe reason codes.
- **List, search, export, and bulk:** filter at data source before pagination, aggregation, serialization, cache write, or export; authorize each object in bulk operations.
- **PDP/PEP split:** centralize policy decisions in one auditable PDP while distributing enforcement at every entry point; reject scattered inline role checks.
- **Privileged and support paths:** step-up, impersonation, support-as-user, service accounts, delegation chains, and background jobs need scoped identity, real actor, time box, and immutable audit.
- **Freshness and invalidation:** token claims, permission caches, tenant suspension, role demotion, and ownership changes need bounded TTL and invalidation proof.
- **GraphQL and event consumers:** enforce field-level and tenant-scope checks inside resolvers/consumers, not only at gateway or producer.

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

Return an `authentication_authorization_plan` with:

- `mode_selected` (plan, implement, review, repair, or release)
- `authorization_decision` (approved, approved with conditions, blocked, or requires policy owner)
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
- `graph_memory_execution_validation` (entry points inspected, prior decisions reused/updated, commands/tests run, explicit evidence gaps)
- `changed_authz_to_validation_map` (each changed protected operation mapped to object rule, deny behavior, audit event, and positive/negative tests)
- `evidence_limits` (uninspected entry points, stale memory, missing generated clients, unrun permission tests, unsupported policy assumptions)
- `tests` (positive + at least: unauthenticated, insufficient scope, wrong tenant, wrong owner, expired credential, mass-assignment attempt, list-endpoint cross-tenant)
- `residual_risks` and `owner`

# Evidence Contract

An acceptable answer names:

- **Basis:** selected mode, protected subject/action/resource/tenant set, policy model, denial decision, and security benchmark or incident class.
- **Repository evidence:** files, routes, resolvers, workers, consumers, repositories, support/admin tools, exports, caches, policy files, tests, and generated contracts inspected or explicitly unavailable.
- **Memory evidence:** prior policy decisions, tenant rules, deny semantics, exceptions, migration constraints, incident notes, and stale claims accepted, rejected, or marked not verified.
- **Graph evidence:** upstream callers, downstream services, resource ownership paths, query filters, list/export/cache paths, event/job paths, and bypass-capable entry points.
- **Execution evidence:** validation commands, permission tests, same-pattern scans, failing reproduction when repairing, audit samples, and any unrun checks with reason.
- **Authorization proof:** object rule, server-derived tenant/owner source, PDP/PEP placement, denial semantics, audit event, cache invalidation, and positive/negative validation for each protected action.
- **What evidence does not prove:** uninspected entry points, production policy state, generated clients not rebuilt, stale tokens already issued, privileged manual controls, third-party IdP behavior, or future policy changes.
- **Handoff evidence:** adjacent capability needed next, owner of unresolved policy decisions, rollback/kill-switch path, residual risk, and validation freshness limit.

# Benchmark Coverage

- **Security:** OWASP API1/API5, OWASP ASVS access-control requirements, least privilege, auditability, and abuse-resistant denial behavior.
- **Architecture:** explicit PDP/PEP split, policy source of truth, tenant-aware data access, and bounded cache/claim freshness.
- **Testing:** positive and negative permission tests across object, tenant, list/search/export, privileged, background, and support paths.
- **Operations:** immutable audit events, alertable suspicious patterns, cache/token invalidation, rollout compatibility, and rollback notes.

# Routing Coverage

This capability should route from prompts involving authentication, authorization, object-level access, roles, scopes, tenant isolation, denial behavior, service accounts, impersonation, exports, bulk operations, admin/support tools, background jobs, GraphQL resolvers, list/search filtering, and access-decision audits. Pair it with `permission-boundary-modeling`, `authentication-security`, `threat-modeling`, `secret-configuration-security`, or `logging-error-handling` only when their owned concern is explicitly present.

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
12. List/search/report/export paths filter by tenant and visibility before pagination, aggregation, caching, or serialization.
13. Admin/support/impersonation paths name the real actor, scoped authority, time box, user-visible indication where applicable, and dual-control requirement.
14. Cache and claim freshness are bounded and invalidated on membership, ownership, role, tenant, and policy changes.
15. Repository graph, memory, execution, and validation evidence are present or explicitly marked as gaps with an owner.

# Used By

- backend-change-builder
- security-privacy-gate

# Handoff

Hand off to `permission-boundary-modeling` for policy matrix design; `authentication-security` for credential, token, session lifecycle hardening; `web-security` for cookies, CSRF, CORS, clickjacking; `secret-configuration-security` for service credentials and signing keys; `logging-error-handling` for audit-safe error and denial messages; `frontend-testing` for permission-state coverage and denied-UI tests; `threat-modeling` for broader privilege-escalation analysis.

# Completion Criteria

The capability is complete when **every protected operation — across UI, API, internal RPC, background jobs, scheduled tasks, bulk imports, admin tools, and support overrides — has explicit identity verification, object-level policy evaluation at a centralized PDP, tenant-scoped query enforcement, deny-by-default fallback, structured audit, invalidation on membership change, and negative-case permission tests**.
