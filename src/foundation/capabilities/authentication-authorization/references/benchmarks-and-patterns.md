# Authentication Authorization Benchmarks And Patterns

Load this reference when `authentication-authorization` needs more detail than the main `SKILL.md` should carry: access-control model choice, PDP/PEP placement, bypass path review, cache/claim invalidation, support/service-account flows, complex protected-operation matrices, or benchmark-backed review.

## Benchmark Anchors

- **OWASP API Security 2023 API1/API5:** object-level and function-level authorization failures are primary API abuse paths.
- **OWASP ASVS V4:** access control is enforced on the trusted service layer and denied by default.
- **CWE-639, CWE-862, CWE-284, CWE-200, CWE-807:** user-controlled keys, missing authorization, improper access control, information disclosure, and untrusted input in security decisions.
- **NIST SP 800-162:** ABAC subject/resource/action/environment structure for condition-rich decisions.
- **XACML / OPA / Cedar:** separable policy decision, enforcement, information, and administration points.
- **Google Zanzibar / OpenFGA / SpiceDB:** relationship graph evidence for ownership, sharing, delegation, inheritance, and tuple freshness.
- **AWS IAM explicit deny:** deny precedence, least privilege, condition keys, and policy versioning discipline.
- **SOC 2 CC6 and NIST SP 800-92:** access-decision auditability, retention, and tamper-resistance expectations.

Use benchmarks to change a rule, evidence requirement, denial decision, audit field, or validation map. Do not cite a benchmark as proof by itself.

## Access-Control Model Pattern

| Model | Use when | Watchout | Evidence |
| --- | --- | --- | --- |
| RBAC | Coarse roles map to stable action groups. | Role alone does not prove access to this object. | Role-action matrix plus object/tenant companion rule. |
| ABAC | Rules depend on subject, resource, tenant, lifecycle, classification, MFA freshness, time, device, or purpose. | Attribute source can become caller-controlled or stale. | Trusted attribute source and negative tests per condition. |
| ReBAC | Ownership, sharing, org/team hierarchy, delegation, folder/project inheritance, or invite flows drive access. | Relationship graph consistency, latency, and stale tuples matter. | Tuple source, relationship owner, graph freshness, wrong-owner tests. |
| PBAC / policy-as-code | Cross-cutting policy needs central authoring, review, and audit. | Versioning and rollout can break existing legitimate access. | Policy artifact, version, owner, CI policy tests, rollback plan. |
| Capability token | A delegated unforgeable reference grants a narrow action. | Revocation and leakage are harder than central policy checks. | Scope, expiry, revocation story, audit binding, misuse tests. |

Most production systems combine RBAC for broad job functions, ReBAC for object sharing, ABAC for context guards, and policy-as-code for cross-cutting compliance rules.

## PDP / PEP Placement

```
Can the operation touch protected data or action?
├─ Yes: PEP must run on the trusted backend path before side effect or data return.
│  ├─ Object-specific? Load/filter by server-derived tenant/owner/relationship.
│  ├─ List/search/export? Predicate must apply before pagination, aggregation, cache, serialization, and export.
│  ├─ Worker/job/event? Assign scoped system identity, tenant/run context, and audit reason.
│  └─ Support/admin? Require purpose, step-up/approval, time box, and real-actor audit.
└─ No: document why no protected subject/action/resource exists.
```

Reject frontend-only, gateway-only, list-then-filter, client-supplied owner, duplicated inline role checks, and broad `system` enforcement for protected operations.

## Protected Operation Matrix

Use this shape when a decision crosses multiple resources or entry points:

| Operation | Subject | Resource/tenant source | Object rule | Enforcement point | Denial | Audit | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `project.settings.update` | user/support/service account | project repository by server tenant | owner or tenant admin; support requires purpose | route + service + repository predicate | 404 when invisible; 403 when visible forbidden | allow/deny with real actor and policy version | owner allowed, viewer denied, wrong tenant denied, stale role denied |

## Cache, Claim, And Invalidation Patterns

- Keep authorization caches short-lived and keyed by subject, tenant, resource type, resource id, action, and policy version when needed.
- Invalidate on role/group/scope change, membership change, ownership transfer, tenant suspension, resource visibility change, policy update, service-account rotation, and support override expiry.
- Treat token claims as identity and routing hints, not final authorization, when roles or tenant membership can change during token lifetime.
- For materialized visibility tables or search indexes, document update trigger, lag tolerance, deny behavior during lag, and stale-result tests.

## Support And Service-Account Patterns

- Support-as-user logs both real actor and effective subject, ticket/purpose, time box, approval, resource, action, decision, and policy version.
- Diagnostic read and mutation authority are separate permissions; regulated mutation may require dual control.
- Service accounts are scoped by action/resource/tenant/run, not broad human-superuser roles.
- Background jobs and exports need job/run identity, source tenant, replay/idempotency context, and allow/deny audit where sensitive.

## Anti-Patterns To Reject

| Anti-pattern | Failure |
| --- | --- |
| `isAuthenticated()` before object read. | Authentication is mistaken for authorization. |
| Role-only check on `/{resourceId}`. | Any role holder can access every object of that type. |
| Caller-provided `tenant_id`, `owner_id`, `role`, `scope`, or `is_admin` drives policy. | Caller controls the authorization condition. |
| List/search/export filters after broad fetch. | Count/timing/export leaks and accidental exposure. |
| Policy logic duplicated in UI, gateway, controller, service, and repository. | Drift weakens one path. |
| Permission tests cover only unauthenticated users. | Wrong-owner, wrong-tenant, stale-claim, mass-assignment, and service-account misuse remain untested. |
