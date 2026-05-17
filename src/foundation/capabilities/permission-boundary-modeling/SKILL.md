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

# Non-Negotiable Rules

- **Backend enforcement is the only authoritative authorization control.** Frontend role checks, UI hiding, and API gateway scope filters are defense-in-depth — not primary controls. Every protected mutation, read of sensitive data, and privileged operation must be enforced at the application service boundary with server-side ownership and tenant data. OWASP ASVS V4.1.3: "Verify that application enforces access control rules on a trusted service layer." An API that hides a button in the UI but exposes the endpoint without a backend check is an IDOR vulnerability.
- **Every authorization check must include object-level scope, not only role membership.** `user.role === 'editor'` allows the user to edit ANY document — including documents they do not own and belong to other tenants. Correct check: `user.role === 'editor' AND document.ownerId === user.id AND document.tenantId === user.tenantId`. OWASP API Security A01:2023 (Broken Object Level Authorization) — object-level authorization is the most commonly exploited API vulnerability.
- **Deny behavior must never reveal whether a restricted resource exists.** Returning HTTP 403 with message "You do not have access to order #12345" confirms that order #12345 exists — this is information disclosure. Correct: return HTTP 404 for resources the user cannot see (resource enumeration protection); return HTTP 403 only for resources the user can confirm exist but cannot act on. The choice between 403 and 404 must be explicit and consistent per resource type.
- **Service accounts and background jobs must follow least privilege.** A service account that can read, write, and delete all records "because it's easier" violates the principle of least privilege. Define: which resources the service account can access; which actions (read-only vs write vs admin); which tenants (single-tenant job vs multi-tenant admin job — different risk profiles). Document in the permission matrix; review on service account rotation.
- **Bulk operations must authorize each object individually, not only the collection.** An API endpoint that accepts `DELETE /orders?ids=[1,2,3,4,5]` and checks `user.role === 'admin'` without verifying that each order ID belongs to the user's tenant has a cross-tenant bulk deletion vulnerability. Every object in a bulk operation must be checked against the caller's tenant and ownership context.
- **Support and admin roles must separate diagnostic visibility from mutation authority.** A support agent who can read user data for diagnosis must not be able to modify it without an explicit elevated-privilege flow with its own audit event. Support access must be: time-bounded (not permanent); purpose-bounded (linked to a ticket or support session ID); least-privilege scoped (read-only unless mutation is explicitly required); fully auditable (every support access logs the support agent ID, ticket reference, and resource accessed).
- **Authorization decisions must be auditable.** Every authorization decision that grants or denies access to sensitive data or privileged actions must emit an audit log event: `who (subjectId, role, tenantId)`, `what (resource type, resource ID, action)`, `when (timestamp, requestId)`, `result (allowed/denied)`, `condition evaluated`. Audit logs must be append-only and protected from modification by the service that writes them (NIST SP 800-92; SOC 2 CC6.1).
- **Conditions on authorization must be evaluated server-side with trusted data.** A permission condition that evaluates `order.status === 'open'` must read `order.status` from the database — not from a client-supplied field in the request body. Any condition evaluated against data the caller controls is a permission bypass vulnerability.

# Industry Benchmarks

Anchor against: **OWASP ASVS V4 (Application Security Verification Standard)** — V4.1 General Access Control; V4.2 Operation-Level Access Control; V4.3 Other Access Control; object-level checks (V4.2.1), deny-by-default (V4.1.2), least privilege (V4.1.3), backend enforcement (V4.1.3). **OWASP API Security Top 10** — API1:2023 Broken Object Level Authorization (BOLA/IDOR); API5:2023 Broken Function Level Authorization; API6:2023 Unrestricted Access to Sensitive Business Flows. **NIST SP 800-162 "Guide to Attribute Based Access Control (ABAC)"** — ABAC policy structure: subject attributes, resource attributes, action, environment conditions; policy enforcement point (PEP) and policy decision point (PDP) separation. **Google Zanzibar** — relationship-based access control (ReBAC); `(user, relation, object)` tuple model; ACL evaluation at global scale; inspired **OpenFGA** and **SpiceDB** open-source implementations. **AWS IAM** — explicit deny overrides allow; policy evaluation order; condition keys (aws:RequestedRegion, aws:PrincipalTag); resource-based policies; least privilege principle documented in IAM Best Practices. **RBAC vs ABAC Decision** (NIST SP 800-162 §5): RBAC for stable role sets with predictable permission sets; ABAC for dynamic conditions (time-of-day, resource classification, geographic restriction, MFA strength); most real systems require hybrid. **CWE-639** (Authorization Bypass Through User-Controlled Key); **CWE-862** (Missing Authorization); **CWE-284** (Improper Access Control).

### Authorization Model Classification

| Authorization Model | Best For | Limitation | Common Tooling |
| --- | --- | --- | --- |
| RBAC (Role-Based) | Stable roles, well-defined function boundaries | Doesn't express resource ownership; role explosion at scale | Auth0, Keycloak, AWS IAM roles |
| ABAC (Attribute-Based) | Dynamic conditions (time, classification, geography) | Complex policy authoring; hard to audit | AWS IAM conditions, OPA (Open Policy Agent) |
| ReBAC (Relationship-Based) | Resource ownership, sharing, fine-grained delegation | Requires relationship graph; latency at scale | OpenFGA, SpiceDB (Zanzibar-inspired) |
| PBAC (Policy-Based) | Complex cross-system policy enforcement | Policy versioning and testing overhead | OPA / Rego, AWS Cedar |
| ACL (Access Control List) | Per-resource explicit grants | Doesn't scale; maintenance burden at > 1K resources | File system ACLs, legacy platforms |

### Permission Matrix Template

```
Subject:    { type: "user", role: "editor", tenantId: "t-123", userId: "u-456" }
Resource:   { type: "document", resourceId: "doc-789", ownerId: "u-456", tenantId: "t-123",
              status: "draft", classification: "internal" }
Action:     UPDATE
Conditions: [
  user.tenantId === resource.tenantId,      // tenant isolation
  resource.ownerId === user.userId           // ownership
    OR user.role IN ['admin','team-editor'], // OR delegated role
  resource.status NOT IN ['locked','archived'], // lifecycle state
  NOT resource.classification === 'restricted'  // unless user has clearance
]
Decision:   ALLOW
Enforcement: DocumentService.updateDocument() — server-side query filter includes tenantId
Denial:     Return 404 (resource not visible) if tenantId mismatch;
            Return 403 (forbidden) if tenantId matches but role/ownership fails
Audit:      Emit authorization_event{ subjectId, resourceId, action, decision, requestId }
```

### Authorization Enforcement Decision Tree

```
Is the request accessing a resource that belongs to a user or tenant?
  YES → Object-level authorization required:
         SELECT resource WHERE id = ? AND tenantId = requestContext.tenantId
         DO NOT pass tenantId from client request body as the filter value

Is the request a bulk operation (multiple resource IDs)?
  YES → Check EACH resource individually against ownership and tenant scope
         Reject the entire batch if any resource fails; or
         Return partial success with explicit failure list

Is the caller a service account or background job?
  YES → Does it need access to ALL tenants or just ONE?
         Single tenant → scope service account to that tenantId at token level
         All tenants → document reason; restrict to minimum required actions;
                       log every cross-tenant access with job ID + run ID

Is the condition evaluated from client-supplied data?
  YES → STOP — read condition values from server-side source (database)
         Never evaluate: if (requestBody.status === 'open') allow
         Must evaluate:  if (db.getOrder(id).status === 'open') allow

Does the resource exist but the caller cannot access it?
  Caller cannot confirm resource existence → return 404
  Caller can confirm resource existence but lacks permission → return 403

Does the action require audit?
  HIGH risk (delete, export, admin override, support access) → emit audit event
  MEDIUM risk (create, update sensitive field) → emit audit event
  LOW risk (read, list own resources) → standard access log sufficient
```

# Selection Rules

Select this capability when **authorization boundary design and object-level access control enforcement** are the primary concern. Route elsewhere when: **authentication-security** is primary (credential verification, session token design, MFA enforcement, JWT validation); **user-role-identification** is primary (identifying which actor types exist and their behavioral purpose); **multi-tenant-isolation-design** is primary (data storage isolation strategy for SaaS tenants — storage-level separation, row-level security); **backend-change-builder** is primary (implementing the authorization checks in service code after the model is defined).

# Risk Escalation Rules

Escalate when: any permission crosses tenant boundaries (e.g., a shared resource accessible to multiple tenants — every consumer must be enumerated and approved); a service account is granted write or delete access on production data without time-bounding; a support or impersonation workflow enables mutation without separate audit; an authorization condition reads from a client-controlled field; bulk operations are authorized at collection level without per-object checks; or a change affects GDPR/CCPA right-to-erasure scope (deleting a user must delete only their data — not other tenants' data associated by shared keys).

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

# Output Contract

Return a permission model with:

- `permission_matrix` (per action × resource type: subject type, role/attribute conditions, object-level conditions, tenant isolation rule, lifecycle state conditions, allow/deny decision)
- `enforcement_points` (per action: service method and file; query filter for object-level scope; tenant filter strategy)
- `denial_semantics` (per resource type: 404 vs 403 decision; error message policy — no resource existence disclosure)
- `audit_events` (per high-risk action: event name, logged fields: subjectId, role, tenantId, resourceId, action, decision, requestId)
- `service_account_permissions` (per service account / job: resources, actions, tenant scope, time-bounded or permanent)
- `support_access_model` (diagnostic read scope; mutation elevation flow; ticket binding; audit requirement)
- `bulk_operation_authorization` (per bulk endpoint: per-object ownership check; partial success handling; cross-tenant rejection)
- `jwt_claim_validation` (signature validation confirmed; claim fields used for authorization; trusted issuer list)
- `test_cases` (per permission boundary: authorized access case, unauthorized access case (expected 403/404), cross-tenant access attempt, service account scope test)
- `ror_escalation_triggers` (conditions requiring security-privacy-gate review)

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

# Used By

- domain-impact-modeler
- security-privacy-gate
- backend-change-builder

# Handoff

Hand off to `backend-change-builder` for enforcement implementation in service code; `security-privacy-gate` for high-risk authorization review (cross-tenant, admin override, regulated data); `user-flow-modeling` for mapping permission states to user journey branches and error screens; `authentication-security` for token validation implementation and session management rules.

# Completion Criteria

The capability is complete when **every protected action has a backend enforcement point with explicit object-level scope, denial semantics do not leak resource existence, service accounts and support roles follow least privilege, all high-risk actions emit auditable events, and the model is verified by tests that confirm unauthorized access is rejected — not only that authorized access succeeds**.
