# User Role Identification Benchmarks And Patterns

Use this reference when `user-role-identification` needs more depth than the main `SKILL.md` should carry efficiently. Keep the main body focused on routing, evidence, output, and gates; use this file for actor taxonomy, persona/role separation, service-account governance, support/admin access, external trust contracts, graph/memory/trajectory coupling, and anti-pattern review.

## Contents

- [Benchmark Anchors](#benchmark-anchors)
- [Actor Type Classification Matrix](#actor-type-classification-matrix)
- [Persona Versus Authorization Role](#persona-versus-authorization-role)
- [Data Visibility And Denied Action Matrix](#data-visibility-and-denied-action-matrix)
- [Service Account And Automation Governance](#service-account-and-automation-governance)
- [Support, Admin, And Operator Access](#support-admin-and-operator-access)
- [External Actor Trust Contracts](#external-actor-trust-contracts)
- [Graph, Memory, And Execution Coupling](#graph-memory-and-execution-coupling)
- [Role Risk Decision Tree](#role-risk-decision-tree)
- [Review Checklist](#review-checklist)
- [Anti-Patterns To Reject](#anti-patterns-to-reject)
- [Handoff Boundaries](#handoff-boundaries)

## Benchmark Anchors

- NIST RBAC and ABAC practice: roles, attributes, separation of duties, and least-privilege permissions must be explicit.
- NIST access-control controls: account management, access enforcement, and least privilege require named subject, scope, and review.
- NIST digital identity guidance: identity and authentication assurance levels help classify actor trust.
- OAuth 2.0 and OpenID Connect: delegated clients, machine callers, scopes, and trusted claims must be modeled separately from human users.
- OWASP ASVS identity and access-control requirements: actor identity is the basis for access-control verification.
- OWASP Broken Access Control and API BOLA: object-level and function-level authorization failures often start with collapsed actor models.
- IAM least-privilege practice: service accounts need owner, purpose, credentials, scope, rotation, and monitoring.
- UX persona practice: personas describe behavior and motivation; they do not grant permissions.

## Actor Type Classification Matrix

| Actor type | Trust level | Authentication | Data visibility scope | Primary risk |
| --- | --- | --- | --- | --- |
| Unauthenticated visitor | None | None | Public data only | Accidental exposure of private routes or metadata |
| Authenticated end user | Low to medium | Session, JWT, or passkey | Own objects in own tenant | IDOR, overbroad self-service access |
| Role-differentiated user | Medium | Session plus role or group claim | Role-scoped objects | Role expansion without object scope |
| Support agent | High operational | SSO plus MFA and purpose binding | Diagnostic data for assigned case | Mutation, export, or privacy overreach |
| Administrator | Highest human | SSO plus MFA, approval, break-glass audit | Tenant or platform configuration as scoped | Unbounded override or privilege escalation |
| Privileged operator | Critical operational | SSO plus MFA, runbook, audit | Production operations and recovery surfaces | Manual correction without evidence |
| Service account | High machine | Workload identity, mTLS, token, or key | Defined resource and action scope | Lateral movement if over-scoped |
| Background job or cron | Medium to high machine | Scheduled identity | Batch/job/run data scope | Broad scans, duplicate side effects |
| External partner API | Variable external | OAuth, mTLS, API key, signed request | Contracted partner data | Trusting external claims or replay |
| Identity provider | Federated critical | OIDC or SAML | Identity and group claims | Claim mapping error or unsigned token trust |
| Payment or financial webhook | External limited | HMAC signature, mTLS, or OAuth | Transaction status claims | Forged event, duplicate delivery, money movement |

## Persona Versus Authorization Role

| Dimension | Persona | Authorization role |
| --- | --- | --- |
| Purpose | Explains motivation, context, skill level, and goals. | Defines access, authority, data scope, and denied actions. |
| Example | "Mobile-first small business owner reconciling receipts." | "Tenant billing admin can view invoices and initiate refund requests in own tenant." |
| Evidence | Research, support notes, analytics, interviews. | Policy, route, service, data model, contract, tenant rules, compliance needs. |
| Changes when | User behavior, market segment, or workflow expectation changes. | Permission, role grant, ownership, tenant, state, or trust boundary changes. |
| Failure if confused | UX misses context or permission model is absent. | Access control is based on demographics or vague behavior. |

Use persona context to inform flows and content. Use authorization role to inform permissions, tests, audit, and enforcement handoffs.

## Data Visibility And Denied Action Matrix

| Question | Required answer |
| --- | --- |
| What objects can the actor read? | Object type, owner, tenant, lifecycle state, and relationship scope. |
| What fields can the actor read? | Sensitive fields, raw secrets, financial data, PII, internal notes, and derived values. |
| What aggregates can the actor read? | Whether totals, counts, exports, or analytics can reveal hidden records. |
| What related objects can the actor traverse? | Parent, child, attachment, audit, payment, identity, and support records. |
| What writes are allowed? | Create, update, delete, approve, refund, export, import, grant, revoke, override. |
| What writes are denied? | Cross-tenant, wrong-owner, irreversible, regulated, financial, admin-only, or support-only actions. |
| Where must the boundary be enforced? | Backend service, policy engine, repository query, job scope, consumer handler, or provider verifier. |

## Service Account And Automation Governance

| Governance field | Professional expectation |
| --- | --- |
| Owner | Named team and operational contact. |
| Purpose | One job or integration purpose, not broad platform use. |
| Authentication | Workload identity, mTLS, signed token, or managed secret with rotation. |
| Scope | Minimum resources, actions, tenants, environments, and runtime. |
| Review | Rotation or access review cadence with owner. |
| Audit | Actor identity, job/run ID, tenant, resources, action, decision, request/correlation ID. |
| Anomaly signal | Unexpected tenant, volume spike, off-hours use, denied action, or new endpoint. |
| Handoff | Permission modeling, secret configuration, idempotency, integration, observability, and release gates as needed. |

Do not collapse service accounts into "system". A machine actor row must let reviewers understand blast radius if the credential leaks or the worker misbehaves.

## Support, Admin, And Operator Access

| Access pattern | Default stance | Escalation trigger |
| --- | --- | --- |
| Diagnostic read | Allow only purpose-bound, least-privilege, audited access. | Reads regulated, cross-tenant, financial, identity, or private support data. |
| Mutation | Deny unless a separate elevated flow, approval, and audit are defined. | Refund, cancel, delete, lifecycle change, role grant, or data correction. |
| Impersonation | Avoid; use constrained support views where possible. | User-session impersonation, production write capability, or customer-visible side effects. |
| Break-glass | Time-bound, approved, monitored, and reviewed after use. | Platform-wide, tenant-wide, or compliance-relevant intervention. |
| Bulk export | Deny by default for support; require explicit business and audit justification. | PII, financial data, regulated records, or cross-tenant export. |

Support, admin, and operator actors often need different rows. "Admin" cannot stand for customer admin, tenant owner, platform admin, support manager, and incident operator at the same time.

## External Actor Trust Contracts

| Contract field | Professional expectation |
| --- | --- |
| Authentication | HMAC signature, mTLS, OAuth/OIDC token, SAML assertion, API key, or signed file. |
| Trusted claims | Claims the system accepts after verification, such as issuer, subject, audience, event ID, or tenant mapping. |
| Rejected claims | Caller-supplied tenant, owner, price, status, role, or entitlement values not trusted without local verification. |
| Replay handling | Event ID, idempotency key, nonce, timestamp tolerance, duplicate response. |
| Failure behavior | Malformed payload, expired signature, unknown tenant, stale schema, duplicate delivery, retry exhaustion. |
| Consumer/producer contract | Schema, version, compatibility, ownership, support path, and validation evidence. |

Treat webhooks, identity providers, payment processors, partner APIs, and file consumers as actors because they assert or consume state that changes system behavior.

## Graph, Memory, And Execution Coupling

| Evidence input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | It points to current routes, jobs, services, policies, tests, docs, or contracts that were inspected. | Graph proximity is treated as proof that actor coverage is complete. |
| Project memory | It names actor behavior with freshness tied to unchanged source or recent validation. | It predates role, route, tenant, policy, schema, or integration changes. |
| Execution trajectory | The command or validation ran after the latest relevant edit and covers actor-specific behavior. | Output is stale, happy-path-only, or from a different surface. |
| Incident/support signal | It maps to a current actor, tenant, resource, date range, and reproducible behavior. | It is anecdotal, unresolved, or cannot be tied to current source. |

Strong outputs state which evidence was accepted, rejected, stale, unknown, and how that affects downstream risk.

## Role Risk Decision Tree

```text
For each actor:
  Can the actor read another actor's data, another tenant's data, hidden fields, or bulk exports?
    YES -> mark object-level authorization and privacy risk; hand off to permission-boundary-modeling.

  Can the actor trigger money movement, deletion, compliance record changes, role grants, overrides, or legal state?
    YES -> require audit, approval or step-up when appropriate, and scenario validation.

  Is the actor a service account, worker, scheduled job, migration, webhook, or event consumer?
    YES -> require owner, scope, credential lifecycle, audit, replay/duplicate handling, and integration handoff.

  Can the actor impersonate, break glass, operate cross-tenant, or bypass business invariants?
    YES -> escalate to security/privacy and permission modeling with explicit exception rules.

  Does evidence come from memory, graph, or old execution only?
    YES -> confirm current source or mark evidence not verified.
```

## Review Checklist

- Actor rows cover human, support/admin/operator, machine, external, identity-provider, webhook, and system processes where relevant.
- Each actor has precise name, type, trust level, authentication mechanism, tenant/object boundary, visible data, hidden data, allowed actions, and denied actions.
- Persona context is separate from authorization role.
- Support/admin/operator authority is split into diagnostic read, mutation, impersonation, override, export, delete, role grant, break-glass, and audit needs.
- Service accounts and jobs have owner, purpose, scope, credential lifecycle, audit, and anomaly review.
- External actors have authentication, trusted/rejected claims, replay/idempotency, and failure behavior.
- Repository graph, project memory, and execution trajectory are source-confirmed or marked stale/unknown.
- Role rows map to permission-boundary and scenario-validation handoffs.
- Evidence limits state what was not inspected or not proven.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| All actors are named "User". | Support, admin, worker, and external behavior disappears. | Create typed actor taxonomy with trust and data scope. |
| Persona is used as a permission model. | Demographics or behavior become access rules. | Keep persona context separate from role authority. |
| Service account is "trusted internal". | Leaked credential or worker bug has broad blast radius. | Owner, scope, credential lifecycle, audit, and least privilege. |
| Support can "do anything to help". | Unbounded mutation, privacy exposure, and audit gaps. | Diagnostic read by default; elevated mutation needs approval and audit. |
| External webhook is a background event. | Forged events or replay can change state. | Model as external actor with signature, claims, duplicate handling, and failure behavior. |
| Tenant boundary is UI filtering. | API, job, or export can leak cross-tenant data. | State query/service/job enforcement handoff. |
| Old project memory becomes current truth. | Retired routes, renamed roles, or changed policies are reused. | Confirm current source or mark stale. |

## Handoff Boundaries

- Use `permission-boundary-modeling` for subject/resource/action/condition predicates, enforcement points, denial semantics, and audit events.
- Use `scenario-decomposition` for valid, alternate, denied, abuse, recovery, support, and operational actor paths.
- Use `use-case-modeling` or `user-flow-modeling` when actor goals or path order need UX depth.
- Use `authentication-security` when identity proof, session, token, MFA, OIDC, SAML, or credential mechanics are primary.
- Use `integration-change-builder` for partner APIs, webhooks, file exchange, and external contract behavior.
- Use `idempotency-retry-design` when machine or external actors can duplicate events, retries, imports, exports, or side effects.
- Use `security-privacy-gate` or `threat-modeling` when actor authority creates privilege escalation, insider threat, data exposure, or adversarial misuse.
- Use `quality-test-gate` when role rows need executable validation strategy and coverage evidence.
