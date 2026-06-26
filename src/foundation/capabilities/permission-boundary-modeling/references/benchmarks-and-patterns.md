# Permission Boundary Modeling Benchmarks And Patterns

Use this reference when `permission-boundary-modeling` needs more detail than the main `SKILL.md` should carry. Keep the main body focused on selection, evidence, output, and quality gates; use this file for authorization models, permission matrix construction, enforcement placement, denial/audit design, service-account/support patterns, and anti-pattern review.

## Benchmark Anchors

- **OWASP ASVS V4:** trusted service-layer access control, deny-by-default, least privilege, and operation-level/object-level access checks.
- **OWASP API Security Top 10:** API1 Broken Object Level Authorization, API5 Broken Function Level Authorization, and API6 sensitive business-flow abuse.
- **CWE-639, CWE-862, CWE-284, CWE-200, CWE-807:** user-controlled keys, missing authorization, improper access control, information disclosure, and untrusted input in security decisions.
- **NIST SP 800-162:** ABAC structure across subject, resource, action, environment, and policy decision/enforcement separation.
- **Google Zanzibar, OpenFGA, SpiceDB:** relationship-based authorization and tuple graph evidence for ownership, sharing, and delegation.
- **AWS IAM and Cedar:** explicit deny precedence, least privilege, condition keys, policy versioning, and policy-as-code evaluation.
- **OPA/Rego and XACML concepts:** auditable policy decision point, policy information point, and policy administration point boundaries.
- **Database row-level security:** PostgreSQL RLS or equivalent as defense-in-depth for tenant/resource filtering, not a replacement for application authorization modeling.
- **SOC 2 CC6 and NIST SP 800-92:** access-control audit evidence and tamper-resistant log expectations.

## Authorization Model Selection

| Model | Best fit | Watchout | Evidence required |
| --- | --- | --- | --- |
| RBAC | Stable roles and predictable function-level permissions. | Does not express ownership or sharing by itself. | Role-to-action matrix and object-level companion rule. |
| ABAC | Conditions depend on subject/resource/environment attributes. | Policy complexity can become hard to audit. | Attribute source, trusted data path, and policy tests. |
| ReBAC | Ownership, sharing, hierarchy, teams, folders, delegated access. | Relationship graph freshness and latency matter. | Tuple source, relationship owner, graph consistency, negative cases. |
| PBAC | Cross-cutting compliance or centrally authored policy. | Versioning, rollout, and policy testing overhead. | Policy artifact, version, owner, CI policy tests. |
| ACL | Small number of explicit per-resource grants. | Maintenance burden and drift at scale. | Grant owner, cleanup path, and audit of stale grants. |

Most mature products combine RBAC for coarse roles, ReBAC for object sharing, and ABAC for context guards such as tenant, classification, lifecycle state, MFA freshness, or purpose.

## Permission Matrix Template

```text
Subject:
  type: user | service_account | support_agent | system | anonymous
  attributes: role, userId, tenantId, group, clearance, auth_time, purpose

Resource:
  type: document | invoice | export | account | job | policy
  attributes: resourceId, tenantId, ownerId, lifecycleState, classification

Action:
  read | list | create | update | delete | export | approve | impersonate | administer

Conditions:
  - subject.tenantId == resource.tenantId
  - subject.userId == resource.ownerId OR subject has delegated relation
  - resource.lifecycleState allows action
  - subject factor/auth_time satisfies step-up requirement
  - support/admin action is bound to ticket/purpose and approval

Decision:
  allow | deny | require_step_up | require_approval

Enforcement:
  controller/service/repository/policy/job/event boundary and query-time tenant/owner filter

Denial:
  404 when resource existence is not visible; 403 when visible but action is forbidden

Audit:
  subject, resource, action, decision, reason code, tenant, request/job/run id, purpose
```

## Enforcement Placement Decision Tree

```
Does the action touch a specific resource?
  yes -> require object-level authorization.
         Load or filter the resource using server-derived tenant/owner scope.
         Reject client-supplied tenant/owner/role/status as authorization input.

Does the endpoint list, search, or export resources?
  yes -> filter at query/source boundary by visibility predicate.
         Do not fetch broadly and filter in application code.

Does the operation accept multiple IDs or a broad predicate?
  yes -> authorize each object or define an all-or-nothing/partial failure contract.
         Audit failures and successes without leaking invisible resource existence.

Is the caller a service account, worker, webhook, or scheduled job?
  yes -> model system identity separately from human identity.
         Scope by tenant/action/resource/run and audit every privileged access.

Is this support/admin/impersonation/break-glass?
  yes -> require purpose, ticket, time box, step-up or approval, and immutable audit.

Is denial observable by a less-privileged caller?
  yes -> choose 404 vs 403 consistently and use safe reason codes in logs/audit.
```

## Boundary Evidence Patterns

- Endpoint/mutation: current route, service method, repository filter, policy function, DTO/mapper, tests, and denial semantics inspected.
- List/search/export: query predicate proves visible set is restricted before pagination/count; timing/count leakage is considered.
- Bulk operation: each requested ID has an authorization decision; partial success contract and audit behavior are defined.
- Support/admin flow: diagnostic read and mutation authority are separated; ticket/purpose and step-up/approval evidence are named.
- Service account/job: credential owner, tenant scope, action list, job/run identity, and audit event are named.
- Event consumer/webhook: tenant/source validation, idempotency/replay risk, and system identity are modeled.
- Policy change: old/new matrix preserves legitimate access and closes only the intended permission gap.

## Graph, Memory, And Trajectory Coupling

Permission boundaries are often discovered through repository graph and project memory. Treat both as routing hints until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, services, repositories, policy files, jobs, and tests are inspected. | Graph proximity is used as proof that every entry point is protected. |
| Project memory | Prior incident, audit finding, or accepted policy matrix has timestamp and unchanged paths. | Memory predates role, tenant, route, schema, support, or service-account changes. |
| Execution trajectory | Validator or security test ran after the final permission edit. | Output predates final edit or covers only one positive path. |
| Generated clients/contracts | Contract diff confirms no new resource/action surface. | Generated artifacts were not regenerated or inspected. |
| Audit/log evidence | Denial and allow events have stable reason codes and safe fields. | Logs include raw resource names, PII, secrets, or unbounded IDs as metrics labels. |

Strong outputs state which memory/graph evidence was accepted, which was rejected, and which entry points remain unknown.

## Denial And Audit Patterns

Denial semantics:

- Return 404 when the caller is not allowed to know the resource exists.
- Return 403 when the resource is already visible but the action is forbidden.
- Return 401 only for missing or invalid authentication, not for authorization denial.
- Avoid messages that include invisible resource names, tenant names, customer names, emails, or IDs.
- Use stable machine-readable reason codes internally; map to safe client messages.

Audit fields:

- subject id/type, acting user id for impersonation, service account id, tenant id;
- resource type/id, action, decision, reason code;
- request id, trace id, job id, run id, ticket/purpose id when applicable;
- policy version or rule id when policy-as-code is used;
- timestamp and source IP/device context when relevant and privacy-approved.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Role-only check on object endpoint. | Any role holder can act on every object of that type. |
| Client-provided `tenant_id`, `owner_id`, `role`, or `status` drives authorization. | Caller controls the policy condition. |
| List endpoint queries all rows then filters in app. | Leaks count/timing, wastes memory, and risks accidental exposure. |
| Bulk delete/export checks only collection permission. | Unauthorized objects can be mutated or exported. |
| Support impersonation logs only the impersonated user. | Audit cannot identify the privileged actor. |
| Service account has all-tenant write/delete because it is convenient. | Credential leak or job bug has platform-wide blast radius. |
| Inconsistent 403/404 behavior. | Attackers can enumerate private resources. |
| Policy logic duplicated in controllers, repositories, and UI. | Drift makes some paths weaker than others. |
| Project memory treated as current policy proof. | New routes/jobs/support tools bypass the remembered control. |
| Negative tests only check "not logged in". | Wrong tenant, wrong owner, insufficient scope, and service-account misuse remain untested. |

## Handoff Boundaries

- Use `authentication-security` for credential, session, token, MFA, and step-up lifecycle.
- Use `authentication-authorization` for implementation-wide identity-to-action enforcement planning.
- Use `backend-change-builder` for service/repository/controller enforcement implementation.
- Use `api-contract-design` for public denial semantics, pagination/list contracts, and bulk partial-success contracts.
- Use `failure-contract-design` for safe error taxonomy and retry/terminal distinctions.
- Use `logging-error-handling` for audit-safe logging fields, redaction, and log-vs-audit boundaries.
- Use `security-privacy-gate` for high-risk, regulated, cross-tenant, support/admin, or service-account review.
- Use `quality-test-gate` for positive, denied, wrong-tenant, wrong-owner, bulk, and service-account test obligations.
