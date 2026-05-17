---
name: user-role-identification
description: Identifies actors, roles, personas, support and admin users, system users, service accounts, external systems, and role-specific risks for a change.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "03"
changeforge_version: 0.1.0
---

# Mission

**Build a complete, typed role inventory before any behavior, permission, or workflow design begins** — making every human actor (end user, support agent, administrator), privileged operator (incident responder, data admin), system actor (service account, background job, cron), external actor (partner API, OAuth provider, payment webhook), and tenant/organizational boundary explicitly visible, so that authorization models, access controls, data visibility rules, audit requirements, and actor-specific risks are never designed with hidden assumptions about who can act.

# When To Use

Use this capability when a change affects: user journeys, feature visibility, or data access for any actor class; authorization rules, permission gates, or role-based feature flags; administrative, support, or operational workflows; service-to-service API calls, webhook receivers, or event consumers; notifications, exports, or audit trails where actor identity determines scope; multi-tenant systems where data isolation depends on actor role; or any change where one actor type might be implicitly assumed to be the only actor.

# Do Not Use When

Do not use this capability to: invent fictional personas for a brainstorming exercise unrelated to the change; create marketing personas that have no bearing on system authorization or behavior; replace `permission-boundary-modeling` (which specifies enforcement rules for the identified roles); or replace `threat-modeling` (which identifies adversarial use of roles and trust boundary violations).

# Non-Negotiable Rules

- **Distinguish actor types explicitly.** A "user" is not a type — it is a placeholder. Every actor must be classified: end user (authenticated vs. unauthenticated), role-differentiated user (e.g., Customer, Employee, Partner), support agent, administrator, privileged operator, service account, background job, scheduled task, external system (partner API, identity provider, payment provider, webhook), or system-level process. Mixing these types in a single "user" label hides authorization differences that become security gaps.
- **Identify support, admin, background, and system actors even when the request mentions only end users.** A product change to "the checkout flow" will be exercised by: the end customer, the fraud review agent (support), the order operations admin, the inventory restock scheduled job, and the payment webhook. All 5 must be identified, not just the customer. Missing actors at design time means missing authorization checks, missing audit log entries, and missing operational runbooks at production time.
- **Capture data visibility scope per actor.** Each actor must have an explicit statement of: what data they can see (by object, field, tenant), what data is never visible to them (even through aggregated queries or bulk exports), and whether visibility extends to related objects (e.g., a support agent can see order details but not payment method raw data). Undeclared data visibility defaults to "all data visible" — which is always wrong.
- **Mark object-level ownership and tenant boundaries for permission modeling.** "Admin can see orders" is insufficient. "Admin can see all orders within their organization's tenant; cross-tenant order access is never permitted; tenant boundary is enforced at query level, not presentation level" is correct. Every actor statement must include the ownership / tenant boundary scope so that `permission-boundary-modeling` can derive enforcement predicates.
- **Service accounts and background jobs require the same rigor as human actors.** A service account that calls the billing API needs: an explicit owner (team + human contact), a defined scope (which endpoints, which data), a rotation policy, audit logging, and least-privilege justification. Treating service accounts as "trusted because they're internal" is the most common source of lateral movement in compromised environments.
- **Do not assume administrative or support roles may bypass business rules.** An admin who can set a user's subscription to ACTIVE without going through the payment flow creates an audit gap and a potential fraud vector. A support agent who can cancel an order without the cancellation window check creates inconsistent business state. Every actor's authority must be bounded by the same business invariants as end users, with explicit exceptions documented and audit-logged.
- **External systems that receive or produce data are actors with trust levels and contracts.** A payment webhook is not a background event — it is an external actor calling your API. It requires: authentication (HMAC signature, API key, OAuth), trust level (what claims can it assert?), idempotency contract (what happens on duplicate delivery?), and failure behavior (what if the payload is malformed?).

# Industry Benchmarks

Anchor against: **NIST SP 800-162 — RBAC and ABAC** — role/attribute-based access control; role assignment; permission assignment; role hierarchy; separation of duties. **NIST SP 800-53 AC-2/AC-3/AC-6** — account management; access enforcement; least privilege. **NIST SP 800-63-3 — Digital Identity Guidelines** — identity assurance levels (IAL1/IAL2/IAL3); authentication assurance levels (AAL1/AAL2/AAL3); relevant for mapping actor trust levels. **OAuth 2.0 (RFC 6749) / OIDC (OpenID Connect Core)** — scope-based delegation; client types; service account credential flows (Client Credentials flow). **OWASP ASVS V2/V4** — identity and access control verification requirements. **OWASP A01:2021 — Broken Access Control** — most common web vulnerability; object-level authorization (IDOR); function-level authorization; privilege escalation. **Nielsen Norman Group — Persona Creation** — behavioral persona vs. authorization role; personas describe motivation, not permissions. **Google Cloud IAM Design Patterns** — least privilege; separation of duties; service account governance; workload identity.

### Actor Type Classification Matrix

| Actor Type | Trust Level | Authentication | Data Visibility Scope | Privilege Risk | Example |
| --- | --- | --- | --- | --- | --- |
| Unauthenticated visitor | None | None | Public data only | Low | Anonymous browsing |
| Authenticated end user | Low-medium | Session / JWT | Own objects in own tenant | Medium | Customer |
| Role-differentiated user | Medium | Session / JWT + role claim | Role-scoped objects | Medium-high | Admin, Editor, Viewer |
| Support agent | High (operational) | SSO + MFA + audit | Diagnostic view of others' data | High | Customer Success rep |
| Administrator | Highest (human) | SSO + MFA + break-glass audit | All tenant data; platform config | Critical | Org Admin, Super Admin |
| Service account | High (machine) | API key / mTLS / Client Credentials | Defined by scope; no UI | Critical if over-scoped | Billing service → Inventory API |
| Background job / cron | Medium (machine) | Scheduled task identity | Data batch it processes | Medium-high | Nightly report generator |
| External partner API | Variable | API key / OAuth / mTLS | Partner's contracted data scope | High (external trust) | Partner inventory feed |
| Identity provider / SSO | Trusted (federated) | SAML / OIDC | Asserts identity claims | Critical (trust chain) | Auth0, Okta, Azure AD |
| Payment / financial webhook | External-limited | HMAC signature | Transaction result data | High (financial) | Stripe webhook |

### Role Risk Assessment Decision Tree

```
For each identified actor, answer:
  1. Can this actor read data belonging to another actor or tenant?
     YES → Mark: Object-level authorization required; IDOR risk; escalate to permission-boundary-modeling
     NO  → Standard ownership check sufficient

  2. Can this actor trigger irreversible financial, legal, or compliance-relevant actions?
     YES → Mark: Dual control or approval workflow required; all actions must be audit-logged
     NO  → Standard audit log

  3. Does this actor operate across tenant boundaries?
     YES → Mark: Tenant boundary enforcement at query layer; cross-tenant data leakage risk
     NO  → Tenant scope = single tenant

  4. Is this actor a service account or automated process?
     YES → Require: owner team, scope definition, rotation policy, least-privilege review
     NO  → Standard session management

  5. Can this actor impersonate another actor or elevate to a more privileged role?
     YES → Mark: Critical privilege escalation risk; requires threat modeling review
     NO  → Standard role boundary
```

# Selection Rules

Select this capability when **the primary question is who participates, what they can do, and what data they can access** for a given change. Route to `permission-boundary-modeling` to define the enforcement predicates and access control rules for the identified roles. Route to `user-flow-modeling` when roles are known and path-level branching by role is the design question. Route to `threat-modeling` when adversarial use of roles (privilege escalation, impersonation, insider threat) is the primary risk. Route to `authentication-authorization` when authentication mechanism selection and identity assurance levels are the primary concern.

# Risk Escalation Rules

Escalate when: any actor can access data belonging to a different actor or tenant (IDOR risk); an actor can trigger money movement, data deletion, or compliance-relevant record modification without audit (financial/regulatory risk); a service account has broader permissions than its defined job function (least-privilege violation — must remediate before release); an external actor's identity is not authenticated and verified server-side (trust boundary violation); or an administrative or support actor can modify data in ways that bypass business rules or leave no audit trail.

# Critical Details

- **"Role" and "persona" are different concepts that must not be conflated.** A persona ("Sarah, a 35-year-old who shops on mobile") describes behavioral motivation and context. A role ("Customer: authenticated, single-tenant, can CRUD own orders, cannot access others' orders") describes authorization boundaries. A product team that works only in persona language produces no authorization model. A development team that works only in role language misses the behavioral context that drives flow design. Both are needed, and they must be kept distinct.
- **Support agents typically need diagnostic access without mutation authority.** A support agent who can read order details, trace transaction history, and view error logs can resolve most customer issues. A support agent who can also modify order state, issue refunds, or change subscription plans is a privileged operator whose every action must be audit-logged to a named user. The default for support roles is read-only diagnostic access; write authority requires explicit justification and enhanced audit controls.
- **Service account credentials must have explicit owners and rotation policies.** A service account with no named owner gets neither renewed nor rotated. When the engineer who created it leaves, the credential lives indefinitely. Minimum requirements per service account: named owning team, named human contact, scope definition (list of endpoints/permissions), rotation cadence (90 days or shorter), monitoring for anomalous usage patterns.
- **Tenant boundary enforcement cannot rely on UI filtering.** A multi-tenant system where the UI only shows the user's own tenant data, but the API accepts any `tenantId` parameter without validating it against the authenticated user's tenant, is not tenant-isolated — it is IDOR-vulnerable. The tenant boundary must be enforced in every query predicate and every write operation at the data layer, not filtered at presentation time.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| All users modeled as a single "User" actor | Support agents, admins, service accounts share one model; authorization gaps appear | Typed actor taxonomy: Customer, Support Agent, Org Admin, Billing Service Account |
| Persona ("Sarah, frequent shopper") used as authorization model | No permission boundaries, data scope, or risk flags in a persona | Separate: behavioral persona (UX) + authorization role (engineering) |
| Service account "trusted because it's internal" | Lateral movement vector if the service is compromised; no audit trail | Define scope, rotate every 90 days, log all calls to named service account identity |
| Admin role exempt from business rules ("admin can do anything") | Audit gap; potential fraud; inconsistent state; no compensating controls | Admin actions subject to same business invariants; exceptions explicitly listed and audit-logged |
| External webhook modeled as "background event" | No authentication check; malicious caller can forge webhook events | External webhook = actor; requires HMAC signature validation or OAuth token verification |
| Tenant boundary enforced only in UI | Any API call with a different `orgId` returns another tenant's data (IDOR) | Tenant predicate enforced in every query: `WHERE tenant_id = :authenticated_tenant_id` |

# Failure Modes

- Support agent role not modeled: no diagnostic read API designed; support creates data-access workarounds via admin console.
- Service account scope not defined: billing service has read access to all user data "because it's easier than restricting it"; used as lateral movement entry point after compromise.
- Tenant boundary enforced only at UI layer: IDOR vulnerability exposes all customers' data through direct API calls.
- Admin bypass of business rules not audited: admin issues refund without payment record; fraud discovered months later with no audit trail.
- External payment webhook not authenticated: attacker POSTs fake `payment_succeeded` events; orders fulfilled without payment.
- Persona treated as authorization model: no explicit data visibility scope; PII visible to actors who should not have access.

# Output Contract

Return a role inventory with per actor:

- `actor_name` (precise, not "user")
- `actor_type` (end user / support / admin / service account / background job / external system / identity provider)
- `goal` (what this actor wants from the system)
- `authentication_mechanism` (session, JWT, API key, HMAC, OIDC, none)
- `trust_level` (none / low / medium / high / critical)
- `data_visibility` (own objects / role-scoped / all-tenant / cross-tenant / defined scope)
- `allowed_actions` (list)
- `denied_actions` (explicit denials, especially cross-tenant and cross-actor)
- `tenant_boundary_scope` (single tenant / own org / platform-wide / n/a)
- `audit_requirement` (every action / privileged actions only / none)
- `role_specific_risks` (IDOR, privilege escalation, lateral movement, data exposure, financial fraud)
- `downstream_models_required` (permission-boundary-modeling, threat-modeling, flow branching)

# Quality Gate

The role inventory is complete only when:

1. Every actor type in the system is represented, not just the primary end user.
2. Every actor has an explicit data visibility scope (not "access as needed").
3. Service accounts have named owners, defined scopes, and rotation policies.
4. External actors have authentication mechanisms and trust levels.
5. Tenant and ownership boundaries are stated per actor.
6. Audit requirements are specified for privileged actors.
7. Risk flags are raised for every actor who can trigger irreversible, cross-tenant, or financial actions.
8. Persona descriptions and authorization roles are maintained as separate artifacts.
9. Admin/support exception rules are explicitly stated, not implied.
10. The inventory is precise enough for `permission-boundary-modeling` to derive enforcement predicates without additional clarification.

# Used By

- change-intake-compiler
- experience-impact-modeler
- security-privacy-gate

# Handoff

Hand off to `permission-boundary-modeling` for enforcement rules and access predicates; `user-flow-modeling` for role-branching flow design; `threat-modeling` for adversarial role misuse; `authentication-authorization` for identity assurance and authentication mechanism selection.

# Completion Criteria

The capability is complete when **every actor type is explicitly identified and typed, data visibility and tenant boundaries are declared, and the inventory is precise enough to prevent hidden permission assumptions from propagating into implementation and authorization design**.
