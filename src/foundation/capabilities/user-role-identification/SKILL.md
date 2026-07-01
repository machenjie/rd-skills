---
name: user-role-identification
description: Identifies actors, roles, personas, support and admin users, system users, service accounts, external systems, and role-specific risks for a change.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "03"
changeforge_version: 0.1.0
---

# Mission

**Build a complete, typed role inventory before behavior, permission, workflow, or test design begins** so that every human actor, privileged operator, machine actor, external system, tenant boundary, trust level, data visibility rule, and role-specific risk is explicit before downstream capabilities design access, scenarios, or implementation.

# When To Use

Use this capability when a change affects user journeys, role-specific feature visibility, data access, authorization rules, administrative or support workflows, service-to-service calls, webhooks, background jobs, notifications, exports, audit trails, tenant isolation, or any surface where "the user" may hide multiple actors with different trust, authority, or data scope.

# Do Not Use When

Do not use this capability to create marketing personas unrelated to system behavior; replace `permission-boundary-modeling` for enforcement predicates; replace `authentication-security` for credential, session, token, or MFA design; replace `scenario-decomposition` for path coverage; or perform detailed threat modeling after the actor taxonomy is already known.

# Stage Fit

Use during the intake stage when actor identity, authority, data scope, tenant boundary, support/admin involvement, automation, or external caller assumptions are unclear. Use during design when repository graph, project memory, or previous execution suggests actor patterns that must be confirmed against current source, docs, tests, policy files, or registry evidence. Use during coding when an implementation branch, API route, job, event handler, export, or support tool implies a hidden actor. Use during code-review when a change says "user", "admin", "system", "internal", "partner", "support", "worker", or "webhook" without naming the actual subject, trust level, and denied actions. Use during testing and release review to verify role rows map to denied-path, support, automation, and external-actor validation evidence. Handoff is allowed once the role inventory is precise enough for permission, scenario, flow, test, security, implementation, and release gates.

# Non-Negotiable Rules

- **"User" is never a final actor type.** Classify every subject as unauthenticated visitor, authenticated end user, role-differentiated user, support agent, administrator, privileged operator, service account, background job, scheduled task, external system, identity provider, webhook caller, or system process.
- **Support, admin, operator, and machine actors must be discovered even when the request only names end users.** Checkout, billing, export, onboarding, deletion, and recovery flows usually involve support tools, admin consoles, scheduled jobs, and external callbacks.
- **Persona and role are separate artifacts.** A persona explains motivation and context; a role explains authorization, data scope, business authority, audit obligations, and denied actions. Do not use persona traits as permission rules.
- **Every actor needs explicit data visibility.** State what they can see by object, field, tenant, aggregate, export, and related object, plus what they must never see.
- **Tenant, ownership, and object boundaries must be stated per actor.** "Admin can see orders" is incomplete; "Org admin can see orders in own tenant only, enforced at query boundary" is actionable.
- **Service accounts and background jobs need owner, scope, credential lifecycle, audit, and least-privilege justification.** "Internal" or "trusted" is not a permission model.
- **Support and admin roles do not bypass business invariants by default.** Diagnostic read, mutation, impersonation, override, refund, export, delete, and role-grant authority must be separately justified and audited.
- **External systems are actors with trust contracts.** Identity providers, payment webhooks, partner APIs, event publishers, and file consumers need authentication, trusted claims, duplicate/replay handling, and failure behavior.
- **Memory, graph, and execution evidence must be freshness-scoped.** Repository graph, project memory, previous role inventories, and old validation runs can guide discovery, but current source and current change context decide the inventory.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New actor surface | New feature, API, workflow, job, event, support/admin path, or integration mentions a broad "user/system/admin". | Build initial taxonomy with data scope, denied actions, and downstream model needs. | Brief, route/surface, actor source, role names, tenant/object boundary. | `requirement-structuring`, `use-case-modeling`, `permission-boundary-modeling` | Permission predicates until actors are stable. |
| Existing role evolution | Role, support/admin authority, tenant access, service account, partner contract, or feature visibility changes. | Preserve legitimate access while preventing silent privilege expansion. | Old/new role inventory, current source/tests/docs, consumer or support impact. | `regression-testing`, `security-privacy-gate`, `consumer-impact-analysis` | Broad role rewrite without preservation evidence. |
| Permission-sensitive discovery | Actor can read/write others' data, cross tenant, export, impersonate, approve, refund, delete, grant roles, or trigger irreversible effects. | Mark enforcement depth and escalation before design continues. | Subject/resource/action/scope, data source, audit need, denied case. | `permission-boundary-modeling`, `threat-modeling`, `quality-test-gate` | Treating role name alone as authorization proof. |
| Machine/external actor modeling | Service account, worker, cron, webhook, message consumer, OAuth/OIDC/SAML provider, partner API, or file exchange appears. | Treat non-human callers as scoped subjects with trust and replay boundaries. | Owner, credential/auth method, scope, token/secret lifecycle, retry/duplicate behavior. | `integration-change-builder`, `idempotency-retry-design`, `authentication-security` | Collapsing machine callers into generic system actor. |
| Reuse and memory validation | Previous inventory, project memory, repository graph, support note, incident, or execution output suggests actors. | Accept only source-confirmed current evidence and record stale or unknown paths. | Inspected files, tests, docs, graph edges, memory freshness, rejected assumptions. | `repository-context-map`, `repository-graph-analysis`, `project-memory-governance` | Copying old role inventories without current-source checks. |

# Industry Benchmarks

Anchor against NIST RBAC/ABAC and access-control guidance, NIST digital identity assurance, OWASP ASVS identity/access-control requirements, OWASP Broken Access Control and API BOLA risks, OAuth 2.0 and OIDC delegation/client patterns, IAM least-privilege and service-account governance, and UX persona practice that separates behavioral personas from authorization roles. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for actor taxonomies, persona/role separation, service-account governance, support/admin access patterns, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when the primary question is **who participates, what identity/trust they carry, what they can do, what data they can see, and which downstream models must use that actor set**. Route to `permission-boundary-modeling` when enforcement predicates are primary, `scenario-decomposition` when actor-specific paths need coverage, `use-case-modeling` when a single actor goal needs flow structure, `authentication-security` when identity proof and session/token mechanics are primary, and `security-privacy-gate` or `threat-modeling` when adversarial misuse is the dominant risk.

# Risk Escalation Rules

Escalate when an actor crosses tenant or ownership boundaries; can read or export regulated, financial, private, or cross-actor data; can mutate money, legal, compliance, identity, subscription, deletion, or role-grant state; can impersonate or elevate; uses a broad service account; depends on unsigned or unauthenticated external claims; or relies on stale project memory, UI-only filtering, or "internal system" trust without current-source proof.

# Proactive Professional Triggers

- **Signal:** Change brief, route, job, policy file, support note, integration contract, or UI/API text uses only generic actor labels such as "user", "admin", "support", "system", "internal", "partner", "webhook", or "service".
  **Hidden risk:** Hidden actors produce missing authorization, audit, support, scenario validation, and wrong downstream handoffs.
  **Required professional action:** Split and classify actor types, trust levels, data visibility, denied actions, and role-specific validation needs before design.
  **Route to:** `requirement-structuring`, `permission-boundary-modeling`, `scenario-decomposition`.
  **Evidence required:** Actor source map, inspected path list, validation or report link, and denied-action notes.
- **Signal:** Repository graph, project memory, previous execution output, incident note, or generated summary names an actor pattern or says a role already exists.
  **Hidden risk:** Stale memory preserves retired roles, renamed routes, changed tenant boundaries, or unverified support/admin access.
  **Required professional action:** Inspect current source, docs, tests, registry, or execution output; verify, downgrade, or reject each prior actor claim before reuse.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`.
  **Evidence required:** Accepted/rejected memory map, inspected paths, freshness date or window, validation report or command, and unknown surfaces.
- **Signal:** Service account, worker, cron, migration, webhook, or event consumer participates. **Hidden risk:** broad machine identity creates lateral movement, duplicate side effects, or unowned credentials. **Required professional action:** require owner, credential/auth method, scope, tenant/job/run boundary, audit, and replay/duplicate handoff. **Route to:** `permission-boundary-modeling`, `integration-change-builder`, `idempotency-retry-design`. **Evidence required:** machine actor row, credential owner, scope, and downstream integration/idempotency route.
- **Signal:** Support/admin/operator can diagnose, mutate, impersonate, export, refund, delete, grant roles, or override business rules. **Hidden risk:** privileged access becomes unaudited mutation or privacy exposure. **Required professional action:** separate read-only diagnostic access from elevated mutation and mark audit/approval needs. **Route to:** `permission-boundary-modeling`, `security-privacy-gate`, `quality-test-gate`. **Evidence required:** support/admin model, purpose binding, denied actions, audit requirement, and permission handoff.
- **Signal:** Persona language is being used as permission language. **Hidden risk:** demographics or behavioral context become access-control rules. **Required professional action:** split behavioral context from authorization role and preserve both when they matter. **Route to:** `use-case-modeling`, `user-flow-modeling`, `permission-boundary-modeling`. **Evidence required:** persona-role split, source of persona context, authorization role, and denied actions.
- **Signal:** Actor-specific behavior affects scenarios or tests. **Hidden risk:** valid alternate paths, denied paths, abuse, recovery, and operational behavior are collapsed into happy-path testing. **Required professional action:** map roles to valid, denied, abuse, recovery, and operational scenario coverage. **Route to:** `scenario-decomposition`, `acceptance-standard-definition`, `quality-test-gate`. **Evidence required:** role-to-scenario validation map, validation method, residual risk, and next gate.

# Critical Details

- **Role inventories are source-of-truth inputs, not implementation proof.** They inform permission, scenario, flow, and test work; they do not prove enforcement exists.
- **Data visibility must include negative visibility.** Explicitly name data, fields, tenants, exports, aggregates, and related records the actor cannot access.
- **Machine actors have blast radius.** A leaked credential or flawed worker can bypass UI, sessions, and human approval. Scope and audit them as rigorously as human roles.
- **Support/admin exceptions are product and compliance decisions.** If an override is needed, name the invariant exception, approval path, audit event, and downstream validation.

# Failure Modes

- Single "User" actor hides support, admin, service-account, external, or tenant-specific behavior until authorization gaps appear in implementation.
- Persona traits are reused as permission rules, leaving no object, tenant, or denied-action boundary for enforcement.
- Service accounts and workers are treated as trusted internals, creating broad credential blast radius and weak audit evidence.
- Support or admin roles can mutate, export, impersonate, refund, delete, or override without purpose binding, approval, or audit.
- External webhooks, IdPs, partner APIs, or file consumers are modeled as background events, so authentication, trusted claims, replay, and failure behavior are omitted.
- Repository graph, project memory, or old execution output is copied without current-source confirmation, preserving stale role assumptions.
- **Validation gap:** role rows do not map to validator, test, report, or manual review evidence, so planning cannot prove coverage.
- **Behavior drift:** existing legitimate access and existing safe denials are not preserved or intentionally changed with owner approval.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, mode, routing, evidence, output, and quality gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete role inventory, role change, support/admin path, service account, webhook, external integration, or role-to-scenario map. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when actor taxonomy, persona/role separation, service-account governance, support/admin access, trust contracts, graph/memory/trajectory reuse, or anti-pattern detail needs more depth. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on source evidence, repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, or role-to-validation mapping. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording work where this body is enough.

# Output Contract

Return a role inventory with:

- `mode_selected` (new actor surface, existing role evolution, permission-sensitive discovery, machine/external actor modeling, or reuse and memory validation)
- `role_inventory_scope` (change surface, actor source, affected tenants, protected resources, excluded/non-goal actors, and release boundary)
- `source_evidence` (current brief, source files, routes, jobs, policy files, docs, tests, registry, repository graph, project memory, execution trajectory, incidents, or support signals inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, and unknown graph/memory/execution evidence)
- `actor_taxonomy` (per actor: name, actor type, human/machine/external classification, trust level, authentication mechanism, owner, tenant scope, and lifecycle)
- `persona_role_split` (behavioral persona context kept separate from authorization role, or explicit statement that persona context is not needed)
- `data_visibility_matrix` (per actor: visible data, hidden data, field/export/aggregate limits, related-object scope, tenant/object ownership boundary)
- `allowed_denied_actions` (per actor: allowed actions, denied actions, irreversible actions, privilege escalation limits, and business-invariant exceptions)
- `service_account_governance` (owner, purpose, credentials, rotation/review cadence, scope, audit, and anomaly monitoring for each machine actor)
- `external_actor_trust_contract` (auth method, claims trusted, claims rejected, idempotency/replay needs, failure behavior, and consumer/producer contract)
- `support_admin_operator_model` (diagnostic read, mutation authority, impersonation, break-glass, approval, purpose binding, time box, and audit obligations)
- `role_to_permission_boundary_map` (actors and actions that require `permission-boundary-modeling`, with subject/resource/action/scope hints)
- `role_to_scenario_validation_map` (valid, denied, abuse, recovery, operational, and support scenarios that each role must cover)
- `downstream_models_required` (permission, scenario, flow, authentication, security, test, integration, reliability, release, or documentation handoffs)
- `handoff_boundaries` (what this inventory does not prove: enforcement, threat depth, executable tests, auth implementation, runbook completeness, or production policy state)
- `evidence_limits` (uninspected actors, stale memory, unknown consumers, generated clients, live IdP/provider state, production permissions, manual controls, or missing validation)

# Evidence Contract

Close role identification only when these answers are concrete:

- **Scope basis:** selected mode, change surface, actor source, non-goal actors, protected resources, tenant/object boundary, and release boundary.
- **Current evidence:** source, docs, tests, routes, jobs, integrations, policy files, registry, repository graph, project memory, execution trajectory, incidents, or support signals inspected and freshness-scoped.
- **Actor proof:** every human, support/admin/operator, service account, background job, external system, identity provider, webhook, and system process is represented or explicitly excluded with reason.
- **Authority proof:** trust level, authentication mechanism, data visibility, denied actions, business invariant exceptions, service-account scope, and support/admin access are explicit.
- **Coupling proof:** repository graph, project memory, and execution trajectory are accepted, rejected, stale, or unknown, and role rows map to permission and scenario validation handoffs.
- **Validation proof:** validation command, validator, test, report, artifact, output, and exit code are named when available; state what evidence proves, what evidence does not prove, residual risk, next gate, reuse and placement rationale, and behavior preservation.
- **Limits:** enforcement, authentication implementation, detailed threat model, test execution, production policy state, and manual operational controls are not over-claimed.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak role work collapses actors into "user", merges personas with authorization roles, forgets support/admin/machine/external actors, omits negative visibility, trusts project memory without source checks, or lacks downstream handoff maps. Improved outputs name selected mode, source evidence, graph/memory/trajectory judgment, typed actor taxonomy, visibility and denied actions, service/external governance, support/admin model, permission/scenario maps, and evidence limits while keeping deep benchmark detail in references.

# Routing Coverage

Route here when actor taxonomy and role inventory are the primary work. Hand off when enforcement predicates (`permission-boundary-modeling`), actor path coverage (`scenario-decomposition`), actor-goal flow (`use-case-modeling`), credential/session design (`authentication-security`), adversarial depth (`security-privacy-gate` or `threat-modeling`), executable verification (`quality-test-gate`), or integration/reliability/release work becomes primary. Do not let this capability become runtime authorization implementation.

# Quality Gate

The role inventory is complete only when:

1. Every relevant actor type is represented or explicitly excluded with a reason.
2. No actor remains named only as "user", "admin", "system", "internal", or "partner".
3. Persona context and authorization role are separated.
4. Every actor has authentication mechanism, trust level, owner where applicable, tenant/object boundary, and data visibility.
5. Hidden data, denied actions, and business-invariant exceptions are explicit.
6. Service accounts, workers, jobs, and system processes have owner, scope, credential lifecycle, audit, and review obligations.
7. External actors have trust contract, accepted/rejected claims, replay/idempotency needs, and failure behavior.
8. Support/admin/operator access separates diagnostic read from mutation, impersonation, override, export, delete, and role-grant authority.
9. Repository graph, project memory, and execution trajectory evidence are source-confirmed or marked stale/unknown.
10. Actors that cross tenant, owner, regulated-data, financial, or irreversible-action boundaries are escalated.
11. Every role that affects enforcement maps to `permission-boundary-modeling`.
12. Every role that affects path coverage maps to `scenario-decomposition` or validation evidence.
13. Handoff boundaries and evidence limits prevent the inventory from being mistaken for enforcement, threat model, or completed tests.

# Used By

- change-intake-compiler
- experience-impact-modeler
- security-privacy-gate

# Handoff

Hand off to `permission-boundary-modeling` for enforcement predicates and access-control rules; `scenario-decomposition` for role-specific valid, denied, abuse, recovery, and operational paths; `use-case-modeling` or `user-flow-modeling` for actor-goal flow detail; `authentication-security` for identity/session/token mechanics; `security-privacy-gate` or `threat-modeling` for adversarial role misuse; and `quality-test-gate` for verification strategy.

# Completion Criteria

The capability is complete when **every relevant human, privileged, machine, external, and system actor is typed; trust, visibility, denied actions, tenant/object boundaries, support/admin authority, service-account governance, graph/memory/trajectory judgment, downstream handoffs, and evidence limits are explicit; and no hidden permission assumption can propagate into implementation planning**.
