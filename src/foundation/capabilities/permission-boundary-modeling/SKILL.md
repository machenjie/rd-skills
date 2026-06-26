---
name: permission-boundary-modeling
description: Models authorization as subject, resource, action, and condition rules with object-level scope, backend enforcement, auditable denial behavior, tenant isolation, and privilege-escalation resistance.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "16"
changeforge_version: 0.1.0
---

# Mission

**Model authorization as explicit subject × resource × action × condition rules with object-level scope, backend enforcement, and auditable denial behavior** — preventing privilege escalation, cross-tenant data leakage, IDOR vulnerabilities, and overly broad service account permissions by ensuring every protected action has an authoritative server-side enforcement point and every denial is semantically safe.

# When To Use

Use this capability when a change: introduces or modifies user roles, permission grants, or resource ownership rules; adds an API endpoint, mutation, or bulk operation that operates on user-owned or tenant-scoped data; grants a service account, background job, or external system access to resources; adds a support or admin workflow with elevated access; changes a multi-tenant boundary where one tenant's data must never be accessible to another; modifies a lifecycle state that changes authorization rules (e.g., "submitted" orders cannot be deleted; "locked" accounts cannot be transferred); or is flagged in security review for missing object-level authorization checks.

# Do Not Use When

Do not use this capability to: model authentication mechanisms (credential verification, session management, MFA — use `authentication-security`); define frontend role-based UI rendering as the primary control (frontend role checks are UX, not security; backend enforcement is the control); model user identity claims without resource scope (use `user-role-identification` when actor taxonomy is primary); or define network perimeter access controls (firewalls, VPCs, security groups — those are infrastructure scope).

# Stage Fit

Use during domain modeling when a feature introduces protected subjects, resources, actions, ownership, tenant scope, lifecycle-gated behavior, support/admin access, service-account access, or cross-tenant sharing. Use during implementation review when authorization checks, query filters, denial behavior, audit events, bulk operations, background jobs, or policy exceptions are added or changed. Use during testing when allowed, denied, cross-tenant, wrong-owner, bulk, service-account, support/admin, and resource-existence cases need explicit proof. Repository graph, project memory, and previous incident notes may suggest permission-sensitive paths, but current source, current routes, policy definitions, tests, and generated contracts must confirm the active boundary before the model treats that evidence as authoritative.

# Non-Negotiable Rules

- **Backend enforcement is the only authoritative authorization control.** Frontend role checks, UI hiding, and API gateway scope filters are defense-in-depth — not primary controls. Every protected mutation, read of sensitive data, and privileged operation must be enforced at the application service boundary with server-side ownership and tenant data. OWASP ASVS V4.1.3: "Verify that application enforces access control rules on a trusted service layer." An API that hides a button in the UI but exposes the endpoint without a backend check is an IDOR vulnerability.
- **Every authorization check must include object-level scope, not only role membership.** `user.role === 'editor'` allows the user to edit ANY document — including documents they do not own and belong to other tenants. Correct check: `user.role === 'editor' AND document.ownerId === user.id AND document.tenantId === user.tenantId`. OWASP API Security A01:2023 (Broken Object Level Authorization) — object-level authorization is the most commonly exploited API vulnerability.
- **Deny behavior must never reveal whether a restricted resource exists.** Returning HTTP 403 with message "You do not have access to order #12345" confirms that order #12345 exists — this is information disclosure. Correct: return HTTP 404 for resources the user cannot see (resource enumeration protection); return HTTP 403 only for resources the user can confirm exist but cannot act on. The choice between 403 and 404 must be explicit and consistent per resource type.
- **Service accounts and background jobs must follow least privilege.** A service account that can read, write, and delete all records "because it's easier" violates the principle of least privilege. Define: which resources the service account can access; which actions (read-only vs write vs admin); which tenants (single-tenant job vs multi-tenant admin job — different risk profiles). Document in the permission matrix; review on service account rotation.
- **Bulk operations must authorize each object individually, not only the collection.** An API endpoint that accepts `DELETE /orders?ids=[1,2,3,4,5]` and checks `user.role === 'admin'` without verifying that each order ID belongs to the user's tenant has a cross-tenant bulk deletion vulnerability. Every object in a bulk operation must be checked against the caller's tenant and ownership context.
- **Support and admin roles must separate diagnostic visibility from mutation authority.** A support agent who can read user data for diagnosis must not be able to modify it without an explicit elevated-privilege flow with its own audit event. Support access must be: time-bounded (not permanent); purpose-bounded (linked to a ticket or support session ID); least-privilege scoped (read-only unless mutation is explicitly required); fully auditable (every support access logs the support agent ID, ticket reference, and resource accessed).
- **Authorization decisions must be auditable.** Every authorization decision that grants or denies access to sensitive data or privileged actions must emit an audit log event: `who (subjectId, role, tenantId)`, `what (resource type, resource ID, action)`, `when (timestamp, requestId)`, `result (allowed/denied)`, `condition evaluated`. Audit logs must be append-only and protected from modification by the service that writes them (NIST SP 800-92; SOC 2 CC6.1).
- **Conditions on authorization must be evaluated server-side with trusted data.** A permission condition that evaluates `order.status === 'open'` must read `order.status` from the database — not from a client-supplied field in the request body. Any condition evaluated against data the caller controls is a permission bypass vulnerability.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New permission surface | New endpoint, mutation, export, admin/support action, role, service account, tenant-sharing rule, or lifecycle-gated action. | Define subject, resource, action, condition, decision, enforcement point, denial, and audit before implementation. | Permission matrix, current resource ownership source, backend enforcement boundary, negative-test obligations. | `authentication-authorization`, `threat-modeling`, `quality-test-gate` | Frontend-only role rendering as security proof. |
| Existing boundary evolution | Role grant changes, ownership transfer, tenant filter, resource state rule, support flow, or policy exception changes. | Preserve old legitimate access while preventing broader access. | Old/new matrix, affected callers, behavior preservation, regression cases. | `regression-testing`, `security-privacy-gate` | Broad policy rewrite without consumer/user impact review. |
| Object-level access review | Resource IDs, tenant IDs, owner IDs, scopes, role, or claims are accepted from request input. | Prevent BOLA/IDOR, tenant leak, mass assignment, and existence disclosure. | Server-derived identity/scope, query-time filter, denial semantics, same-pattern scan. | `input-validation`, `api-contract-design`, `model-boundary-mapping` | Controller role-only check. |
| Bulk, job, service, or event authorization | Bulk IDs, imports, exports, background jobs, message consumers, scheduled tasks, service accounts, or webhooks. | Authorize each object or event with scoped system identity and auditable least privilege. | Per-object check, service-account scope, tenant/job/run ID, audit and replay/duplicate risk. | `idempotency-retry-design`, `message-queue-design`, `data-side-effect-flow-tracing` | Collection-level allow for all objects. |
| Privileged/support/admin access | Impersonation, break-glass, support diagnosis, admin override, role grant, export, delete, or regulated data. | Separate diagnostic visibility from mutation authority and require step-up/approval/audit. | Ticket/purpose binding, time box, elevated-flow approval, audit fields, deny cases. | `authentication-security`, `security-privacy-gate`, `logging-error-handling` | Permanent broad admin access. |

# Industry Benchmarks

Anchor against OWASP ASVS V4 access-control requirements, OWASP API Security API1/API5, CWE-639/CWE-862/CWE-284, NIST SP 800-162 ABAC, policy-enforcement/decision point separation, Google Zanzibar/ReBAC patterns, AWS IAM explicit-deny and least-privilege policy evaluation, OPA/Cedar policy-as-code practice, PostgreSQL RLS defense-in-depth, and SOC 2/NIST log-management expectations for access auditability. Keep this body focused on routing, evidence, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for authorization-model matrices, permission-matrix templates, enforcement decision trees, denial/audit patterns, service-account/support access, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when **authorization boundary design and object-level access control enforcement** are the primary concern. Route elsewhere when: **authentication-security** is primary (credential verification, session token design, MFA enforcement, JWT validation); **user-role-identification** is primary (identifying which actor types exist and their behavioral purpose); **multi-tenant-isolation-design** is primary (data storage isolation strategy for SaaS tenants — storage-level separation, row-level security); **backend-change-builder** is primary (implementing the authorization checks in service code after the model is defined).

# Risk Escalation Rules

Escalate when: any permission crosses tenant boundaries (e.g., a shared resource accessible to multiple tenants — every consumer must be enumerated and approved); a service account is granted write or delete access on production data without time-bounding; a support or impersonation workflow enables mutation without separate audit; an authorization condition reads from a client-controlled field; bulk operations are authorized at collection level without per-object checks; or a change affects GDPR/CCPA right-to-erasure scope (deleting a user must delete only their data — not other tenants' data associated by shared keys).

# Proactive Professional Triggers

- **Signal:** endpoint, query, event, job, or policy accepts `user_id`, `tenant_id`, `owner_id`, `resource_id`, role, group, scope, status, or classification from caller-controlled input. **Hidden risk:** IDOR, tenant spoofing, mass assignment, or client-controlled policy condition. **Required professional action:** derive subject and scope from trusted session/token/server-side state and prove object-level query filtering. **Route to:** `input-validation`, `authentication-authorization`, `security-privacy-gate`. **Evidence required:** source of truth, denied wrong-tenant/owner case, same-pattern scan.
- **Signal:** protected operation is authorized by role/function only, with no resource relationship or tenant predicate. **Hidden risk:** role holder can act on every object of that type. **Required professional action:** add object-level rule to permission matrix and define enforcement point. **Route to:** `authentication-authorization`, `backend-change-builder`. **Evidence required:** subject-resource-action-condition row, query/filter location, positive and negative tests.
- **Signal:** list/search/export filters after fetching broad data, or bulk operation checks only collection permission. **Hidden risk:** cross-tenant leakage, timing/count leak, or partial unauthorized mutation. **Required professional action:** filter at query/source boundary and define per-object authorization/partial-failure semantics. **Route to:** `api-contract-design`, `repository-persistence`, `quality-test-gate`. **Evidence required:** query-time predicate, bulk failure contract, cross-tenant test.
- **Signal:** support/admin/impersonation flow grants mutation, export, billing, role grant, delete, or regulated-data access without purpose, step-up, time box, or audit. **Hidden risk:** privileged access becomes unbounded and unauditable. **Required professional action:** split diagnostic read from elevated mutation and require audit/approval. **Route to:** `authentication-security`, `logging-error-handling`, `security-privacy-gate`. **Evidence required:** ticket/purpose binding, step-up/approval rule, audit fields, denial cases.
- **Signal:** service account, worker, migration, webhook, or message consumer runs as broad `system`/admin. **Hidden risk:** leaked credential or bug has platform-wide blast radius. **Required professional action:** scope machine identity by action/resource/tenant/run and add replay/duplicate safeguards when applicable. **Route to:** `secret-configuration-security`, `message-queue-design`, `idempotency-retry-design`. **Evidence required:** service-account matrix, credential owner, tenant/run scope, audit.
- **Signal:** denial behavior returns inconsistent 403/404, reveals existence, or uses verbose resource names in errors/logs. **Hidden risk:** resource enumeration or privacy leakage. **Required professional action:** define denial taxonomy and safe diagnostics. **Route to:** `failure-contract-design`, `logging-error-handling`. **Evidence required:** denial semantics per resource, user-facing message policy, audit-safe reason code.
- **Signal:** project memory, repository graph, or prior security note says permission checks exist but current routes/policies/tests were not inspected. **Hidden risk:** stale memory hides new entry points or retired policy locations. **Required professional action:** confirm with current source, policy files, routes, tests, generated clients, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** inspected paths, accepted/rejected memory, unknown entry points, validation gap.

# Critical Details

- **IDOR (Insecure Direct Object Reference) is the most common API authorization vulnerability.** The pattern: `GET /api/orders/12345` — if the backend returns the order without checking `order.userId === request.user.id`, any authenticated user can read any order by incrementing the ID. Defense: never use sequential integer IDs for resources in public APIs (use UUIDs); always filter by tenant/owner in the database query, not in application code after fetching.
- **JWT claims must be verified server-side; custom claims must not be trusted blindly.** A JWT with `role: "admin"` in the payload only proves that role if the JWT was signed by a trusted issuer and the signature is validated. A service that reads `jwt.claims.tenantId` without verifying the JWT signature has an authorization bypass. Never trust claims from a JWT without validating the signature and expiration.
- **Row-level security (PostgreSQL RLS, MySQL VPD) provides defense-in-depth.** Application-level tenant filters are the primary control. Database-level row-level security (PostgreSQL `CREATE POLICY`) is defense-in-depth: even if application code has a bug that omits the tenant filter, RLS prevents cross-tenant data leakage at the database level. Recommended for high-sensitivity multi-tenant SaaS.
- **Permission changes are schema changes.** Adding a new role or changing which actions a role can perform may break existing user workflows. Permission changes must be communicated to affected users, tested against existing permission matrix cases, and rolled back safely if they produce unexpected access denials in production.

### Anti-examples

| Anti-pattern | Problem | CWE | Fix |
| --- | --- | --- | --- |
| `GET /documents/{docId}` — no tenant filter; returns any document by ID | Cross-tenant data read; IDOR (CWE-639) | CWE-639 | Filter: `WHERE id=? AND tenantId=request.tenantId` |
| `DELETE /batch?ids=[...]` — checks `user.role === 'admin'`; no per-object tenant check | Cross-tenant bulk delete; admin of Tenant A deletes Tenant B records | CWE-862 | Verify each ID belongs to caller's tenant before delete |
| HTTP 403 with message "Order #12345 does not belong to you" | Confirms resource #12345 exists; information disclosure | CWE-200 | Return 404 if resource not visible to caller |
| Service account `data-pipeline` has full read/write/delete on all tables | Blast radius if credentials are leaked or script has a bug | CWE-284 | Scope to minimum: `SELECT` on source tables, `INSERT` on destination only |
| Authorization condition: `if (req.body.isAdmin === true) allowDelete()` | Caller controls the condition; trivial bypass by setting `isAdmin: true` in body | CWE-807 | Read authorization attributes from server-side session / database, not request body |
| Support tool allows agents to update user payment method "for convenience" | Support mutation without elevated-privilege gate or audit event | CWE-862 | Read-only support access; separate elevated flow with ticket ID + approval for mutations |
| JWT `tenantId` claim trusted without signature validation | JWT forgery attack allows tenantId spoofing | CWE-347 | Always validate JWT signature and expiration before reading claims |

# Failure Modes

- IDOR on `GET /invoices/{id}` — no tenantId filter; any authenticated user can download any invoice by guessing ID; discovered in security penetration test 6 months post-launch.
- Bulk export `POST /export?userIds=[...]` — checks `canExport` role; does not verify that each userId belongs to caller's tenant; cross-tenant PII export.
- Support agent impersonation tool grants full write access — support ticket resolves billing dispute by directly modifying payment record; no audit trail; discovered in SOC 2 audit.
- Background job `recalculate-invoices` runs with `admin` service account — due to a bug, overwrites invoices for ALL tenants when given a single tenant's job ID; blast radius is total platform.
- Soft-deleted resource still returned in list — `status !== 'deleted'` filter missing; permission check passes for a resource that should be inaccessible; deleted users' data visible to others.
- Permission change adds `viewer` role without updating bulk export guard — `viewer` role users gain export access because `canExport` check was `role !== 'guest'` (not `role === 'exporter'`); logical flaw in deny-by-exception design.
- Frontend-only permission check — React component hides delete button for non-admins; the API endpoint has no backend check; curl DELETE as a non-admin succeeds.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 permission-boundary routing, non-negotiable rules, and output requirements. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete permission matrix, endpoint, job, bulk operation, support/admin flow, service account, or denial/audit behavior. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when authorization-model choice, permission matrix detail, enforcement placement, denial semantics, audit fields, service-account/support access, or graph/memory/trajectory evidence needs more depth. Use [examples/example-output.md](examples/example-output.md) only when the expected matrix shape is unclear. Do not load references for pure routing or metadata-only edits with no permission model output.

# Output Contract

Return a permission model with:

- `mode_selected` (new permission surface, existing boundary evolution, object-level access review, bulk/job/service/event authorization, or privileged/support/admin access)
- `boundaries_inspected` (routes, controllers, services, repositories, policy files, schemas, DTOs, generated clients, jobs, event consumers, support/admin tools, existing tests, audit logs, registry/project memory, and skipped boundaries with reason)
- `source_evidence` (current source, route map, policy definition, repository graph, project memory, execution trajectory, test report, or security finding inspected with freshness limits)
- `permission_matrix` (per action × resource type: subject type, role/attribute conditions, object-level conditions, tenant isolation rule, lifecycle state conditions, allow/deny decision)
- `enforcement_points` (per action: service method and file; query filter for object-level scope; tenant filter strategy)
- `denial_semantics` (per resource type: 404 vs 403 decision; error message policy — no resource existence disclosure)
- `audit_events` (per high-risk action: event name, logged fields: subjectId, role, tenantId, resourceId, action, decision, requestId)
- `service_account_permissions` (per service account / job: resources, actions, tenant scope, time-bounded or permanent)
- `support_access_model` (diagnostic read scope; mutation elevation flow; ticket binding; audit requirement)
- `bulk_operation_authorization` (per bulk endpoint: per-object ownership check; partial success handling; cross-tenant rejection)
- `jwt_claim_validation` (signature validation confirmed; claim fields used for authorization; trusted issuer list)
- `test_cases` (per permission boundary: authorized access case, unauthorized access case (expected 403/404), cross-tenant access attempt, service account scope test)
- `changed_permission_to_validation_map` (each role, action, resource, condition, enforcement point, denial, service account, support/admin path, or bulk path mapped to validator/test/manual review or residual risk)
- `reuse_and_placement_rationale` (existing policy module, repository filter, service boundary, audit schema, test harness, and reference files reused; rejected frontend-only or duplicated policy locations)
- `behavior_preservation` (old legitimate access, old denials, tenant isolation, service account scope, support/admin audit, and client-visible denial behavior preserved or intentionally changed)
- `validation_evidence` (commands, reports, negative tests, security review artifacts, exit codes, freshness, or not-verified disclosure)
- `handoff_boundaries` (authentication lifecycle, implementation, API contract, failure contract, logging, security review, or release work that belongs elsewhere)
- `evidence_limits` (what was not inspected, unknown entry points/consumers, untested tenant data, generated clients, production policy state, or manual controls)
- `risk_escalation_triggers` (conditions requiring security-privacy-gate, backend-change-builder, data-api-contract-changer, or release handoff)

# Evidence Contract

Close permission-boundary modeling only when these answers are concrete:

- **Boundary basis:** selected mode, protected subject/resource/action/condition set, policy model, and security benchmark or incident class the decision rests on.
- **Current boundaries inspected:** routes, services, repositories, policy files, schemas, jobs, event consumers, support/admin tools, tests, audit paths, registry/project memory, and repository graph accepted or rejected for freshness.
- **Placement rationale:** why each enforcement point belongs at controller/service/repository/policy/job/event boundary and why frontend-only, gateway-only, client-supplied, duplicated, or list-then-filter placement is rejected.
- **Authorization proof:** object-level rule, tenant/owner source, server-side condition source, denial semantics, audit event, service-account/support scope, and bulk/object-by-object behavior named for each protected action.
- **Validation proof:** each changed permission rule maps to positive, denied, wrong-tenant/wrong-owner, service-account, support/admin, or bulk validation evidence, with freshness and what evidence does not prove.
- **Behavior preservation and residual risk:** legitimate old access and safe denials are preserved or intentionally changed; remaining unknown entry points, stale memory, untested clients, manual approvals, or audit gaps have owner and next gate.

# Quality Gate

The model is complete only when:

1. Every API endpoint and mutation has an identified enforcement point with object-level scope.
2. Object-level checks use server-side ownership and tenant data — not client-supplied values.
3. Denial semantics are explicit: 404 for resource not visible; 403 for visible but forbidden.
4. Bulk operations authorize each object individually.
5. Service accounts are scoped to minimum required resources and actions.
6. Support access is read-only unless mutation elevation flow with audit is defined.
7. JWT claims are validated (signature + expiration) before being used for authorization decisions.
8. Audit events defined for all high-risk actions.
9. Test cases cover unauthorized access and cross-tenant access attempts — not only happy path.
10. Deny-by-default confirmed: new resource types without explicit allow rules are inaccessible.
11. Current-source, repository graph, project memory, and prior incident evidence are freshness-scoped; inferred permission coverage is marked not verified.
12. List/search/export and bulk operations authorize at the data-source or per-object boundary, not after broad fetch.
13. Support/admin/impersonation and service-account access have purpose, scope, audit, and expiry or review owner.
14. Every changed rule, enforcement point, denial semantic, and privileged path maps to validation evidence or named residual risk.

# Used By

- domain-impact-modeler
- security-privacy-gate
- backend-change-builder

# Handoff

Hand off to `backend-change-builder` for enforcement implementation in service code; `security-privacy-gate` for high-risk authorization review (cross-tenant, admin override, regulated data); `user-flow-modeling` for mapping permission states to user journey branches and error screens; `authentication-security` for token validation implementation and session management rules.

# Completion Criteria

The capability is complete when **every protected action has a backend enforcement point with explicit object-level scope, denial semantics do not leak resource existence, service accounts and support roles follow least privilege, all high-risk actions emit auditable events, and the model is verified by tests that confirm unauthorized access is rejected — not only that authorized access succeeds**.
