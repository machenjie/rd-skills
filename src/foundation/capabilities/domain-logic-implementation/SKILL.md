---
name: domain-logic-implementation
description: Implements domain invariants near the domain model or domain service and prevents duplicated inconsistent rules across layers.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "39"
changeforge_version: 0.1.0
---

# Mission

Implement domain logic at the authority that owns the business rule: aggregate, entity, value object, domain policy, or domain service. The goal is to make invalid states unrepresentable or rejected before persistence, keep calculations and lifecycle transitions consistent across entry points, and prevent controllers, UI code, repositories, tests, or application services from becoming competing rule engines.

# When To Use

Use this capability when a change adds or modifies domain objects, aggregate behavior, invariants, calculations, lifecycle transitions, value object construction, domain policies, domain services, rule authority, or cleanup of duplicated business rules across layers.

# Do Not Use When

Do not use this capability to design application-service orchestration, transaction sequencing, authorization-first workflow, or external effects; use `service-business-logic` for that. Do not use it while rules are still being discovered from messy requirements or legacy code; use `business-rule-extraction` first. Do not use it as a reason to scatter rules across controllers, UI code, SQL scripts, tests, repositories, generic helpers, or unrelated services.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release preparation, and incident repair for backend/domain behavior. Treat this capability as the stage selection and launch guard for rule authority, invariant placement, value object validity, lifecycle transition enforcement, calculation contract, and layer cleanup decisions. In planning, name the rule authority, failure outcomes, current source paths, repository graph slice, project-memory verdict, and validation signal before code. During coding, keep domain logic pure from transport, persistence, framework, network, cache, queue, clock, and UI concerns unless an explicit domain service boundary owns the policy. During review, reject anemic domain objects, duplicate guards, direct field mutation, stale "existing rule covers it" claims, and tests that only prove the happy path; hand off with the unresolved boundary and next gate when orchestration, persistence, transaction, API contract, security, or release owns the remaining question.

# Non-Negotiable Rules

- **Each rule has one domain authority.** An invariant belongs to the aggregate/entity/value object/policy/domain service that can enforce it for every caller, not to the controller, UI, repository, migration, or test fixture.
- **Every mutating entry point goes through the authority.** If imports, admin screens, background jobs, API handlers, or tests can bypass the domain method and mutate fields directly, the invariant is not implemented.
- **Invalid state is rejected before persistence.** Lifecycle transitions, quantity/money/date boundaries, ownership constraints, terminal states, and cross-field invariants must fail before save/commit, not after database cleanup or UI hiding.
- **Domain code stays persistence and transport independent.** Domain objects must not accept DTOs, ORM entities, HTTP requests, framework validators, database sessions, UI models, raw rows, cache clients, message clients, or external API responses as their native inputs.
- **Value objects enforce validity at construction.** A money, date range, email, percentage, interval, identifier, quantity, or domain-specific code object cannot exist in a partially valid state.
- **Domain services are for real domain policies.** Use a domain service when a rule spans multiple domain objects or policies and no single aggregate owns the decision; do not use one as a procedural dumping ground for field mutation.
- **Calculations expose basis and version.** Pricing, eligibility, score, balance, quota, entitlement, deadline, and status derivations must state inputs, rounding/timezone/currency rules, effective date, and failure cases.
- **Side effects stay outside pure domain behavior.** Domain methods can decide and emit domain events or outcomes; application services/adapters perform persistence, network calls, queueing, email, payment, cache invalidation, logging, and metrics.
- **Persistence constraints reinforce, not replace, domain rules.** Database constraints, unique indexes, check constraints, and foreign keys provide defense in depth; readable domain behavior remains the primary authority.
- **Tests exercise public domain behavior.** Cover allowed behavior, denied behavior, boundary values, transition matrix rows, calculation boundaries, and failure outcomes without depending on private helpers.

# Mode Matrix

Select the domain implementation mode before choosing aggregate method, value object, domain service, policy/specification, transition table, calculation object, or layer cleanup mechanics.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Aggregate or entity invariant | Mutating behavior, lifecycle rule, terminal state, direct field writes, anemic model. | Put the invariant on the aggregate/entity method that owns the state. | Authority, entry points, invariant, allowed/denied cases, rejection outcome. | `domain-object-identification`, `state-machine-modeling`, `unit-testing` | Generic service guard only. |
| Value object validity | Money, range, quantity, email, percentage, identity, timezone, currency, precision. | Make invalid values unconstructable and keep equality/format rules local. | Constructor/factory rules, boundary values, equality semantics, serialization boundary. | `domain-object-identification`, `i18n-timezone-money-safety` | Raw primitive propagation. |
| Domain service or policy | Rule spans objects, pricing/eligibility/entitlement policy, externalized policy table. | Place a pure domain decision outside orchestration while preserving domain vocabulary. | Objects read, policy inputs, no side effects, failure reasons, tests. | `business-rule-extraction`, `service-business-logic` | God service or helper bag. |
| Lifecycle transition enforcement | Status/state transitions, approvals, cancellation, fulfillment, subscription, workflow terminal states. | Enumerate allowed transitions and reject forbidden ones at the domain boundary. | State matrix, guard conditions, actor/policy inputs, terminal-state tests. | `state-machine-modeling`, `transaction-consistency` | UI-only disablement. |
| Calculation or derivation | Price, balance, quota, due date, score, SLA, availability, eligibility, allocation. | Centralize formula, rounding, effective-date, and partial-data behavior. | Formula basis, precision/time rules, version/effective date, edge tests. | `business-rule-extraction`, `test-strategy` | Unnamed number/string return. |
| Layer cleanup | Same rule in UI/controller/service/SQL/tests, repository returns domain data bags, test-only rule. | Pick one authority and leave other layers as callers, projections, or defense in depth. | Duplicate scan, selected authority, removed/kept checks, regression proof. | `implementation-structure-design`, `code-review` | Cosmetic deduplication. |

# Proactive Professional Triggers

- **Signal:** A controller, UI component, SQL script, repository, or test fixture contains the only check for a business rule. **Hidden risk:** another entry point persists invalid state. **Required professional action:** move or duplicate-as-defense the rule to the domain authority and scan other entry points. **Route to:** `domain-logic-implementation`, `repository-context-map`, `regression-testing`. **Evidence required:** authority method, bypass scan, denied-case test.
- **Signal:** A service mutates domain fields directly or branches on `status` instead of calling a domain operation. **Hidden risk:** anemic domain model, transition drift, and missed terminal-state protection. **Required professional action:** add or use a domain operation with typed rejection outcome. **Route to:** `service-business-logic`, `state-machine-modeling`. **Evidence required:** before/after caller flow and transition tests.
- **Signal:** A domain object imports an ORM, HTTP request, framework validator, DTO, cache client, queue client, or API client. **Hidden risk:** dependency-direction break makes domain behavior untestable and couples rules to infrastructure. **Required professional action:** introduce mapping at the adapter/service boundary and keep domain inputs persistence-neutral. **Route to:** `implementation-structure-design`, `repository-persistence`. **Evidence required:** import boundary, mapper location, pure-domain test.
- **Signal:** A calculation returns a primitive with no named failure, precision, timezone, currency, effective-date, or version policy. **Hidden risk:** silent formula drift or externally visible contract mismatch. **Required professional action:** name the calculation contract and edge cases. **Route to:** `business-rule-extraction`, `data-api-contract-changer` when externally exposed. **Evidence required:** formula basis, boundary table, contract impact.
- **Signal:** Persistence constraints are the only protection for uniqueness, quantity, range, lifecycle, or ownership. **Hidden risk:** users see late storage errors and domain objects can carry invalid state in memory. **Required professional action:** enforce in domain first and retain constraints as defense in depth. **Route to:** `repository-persistence`, `data-model-design`. **Evidence required:** domain rejection test and persistence constraint rationale.
- **Signal:** A rule spans multiple aggregates inside one synchronous write. **Hidden risk:** hidden distributed consistency or locking assumption. **Required professional action:** select aggregate authority, transaction boundary, or explicit eventual-consistency design before implementation. **Route to:** `domain-object-identification`, `transaction-consistency`, `idempotency-retry-design`. **Evidence required:** consistency boundary, concurrency/retry behavior, compensation or outbox decision.

# Industry Benchmarks

Anchor against Domain-Driven Design tactical patterns, aggregate consistency boundaries, value object validation, domain service and specification/policy placement, Clean Architecture dependency rules, state machine transition discipline, ubiquitous language, property/boundary testing, and persistence constraints as defense in depth. Keep the body focused on route-time decisions, output evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for authority matrices, graph/memory/trajectory coupling, validation maps, and anti-pattern review.

# Selection Rules

Select this capability when the primary question is where and how a business invariant, transition, policy, calculation, or value constraint is enforced in domain code. Prefer `service-business-logic` when orchestration, authorization order, repositories, transaction scope, or external effects dominate. Prefer `business-rule-extraction` when rules are not yet understood. Prefer `state-machine-modeling` when transition discovery is the main work. Prefer `repository-persistence` when mapping, query, ORM, storage errors, or transaction mechanics are primary.

# Risk Escalation Rules

Escalate when domain rules affect money, inventory, entitlement, permissions, compliance, lifecycle terminal states, cross-aggregate consistency, irreversible transitions, data retention, audit trails, or calculations used by external contracts. Escalate when concurrency can violate an invariant, when retry can apply a rule twice, when a policy change needs a migration or backfill, or when old and new rule versions must coexist during rollout.

# Critical Details

- **Rule authority beats caller convenience.** Controllers and application services may precheck for UX or early denial, but they never become the last line of defense for a core invariant.
- **Domain inputs are domain concepts.** Convert DTOs, raw rows, request parameters, external API payloads, and UI models into domain commands, value objects, or primitives at the boundary before invoking domain behavior.
- **Typed failures are part of the model.** Use domain results or typed errors that name `AlreadyCanceled`, `InsufficientBalance`, `InvalidDateRange`, `TerminalStateTransitionDenied`, or equivalent domain language; avoid `null`, generic boolean failure, swallowed exceptions, and infrastructure exception leakage.
- **Concurrency is not solved by a method name.** Aggregates define consistency boundaries, but optimistic locking, unique constraints, idempotency keys, and transaction isolation may still be needed to protect invariants under concurrent writes.
- **Domain events are decisions, not delivery.** A domain operation may produce a domain event as part of the decision; event persistence, outbox publishing, and external integration remain application/infrastructure responsibilities.
- **Versioned rules need explicit coexistence.** When old orders, subscriptions, contracts, or invoices keep old rule semantics, the domain model must name the effective rule version rather than silently applying today's formula to historical state.
- **Tests should fail for the right reason.** A denied-case test must assert the domain rejection outcome, not merely a controller status code or database exception.

# Reference Loading Policy

The body carries the decision-critical rules for normal L1/L2 use. Load [references/checklist.md](references/checklist.md) for L2+ implementation planning, review, repair, or any change touching money, permissions, terminal states, cross-aggregate consistency, rule cleanup, or unclear rule authority. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when authority selection, calculation/versioning, graph/memory/trajectory reuse, validation mapping, or anti-pattern detail needs more depth than this body should carry. Use [examples/example-output.md](examples/example-output.md) only when the expected domain implementation contract shape is unclear. Do not load references for trivial local wording changes where the inline quality gate is sufficient.

# Failure Modes

- **Divergent duplicate rule:** the same rule exists in frontend, controller, service, and database with different edge cases.
- **Anemic domain mutation:** domain objects are passive data bags while services mutate fields directly.
- **UI-only transition guard:** invalid lifecycle transitions persist because only UI controls were hidden.
- **Persistence-coupled domain:** domain code accepts ORM objects and becomes tied to storage behavior.
- **Happy-path-only proof:** tests prove happy paths but miss denied transitions and boundary values.
- **Invalid value object:** a value object allows invalid construction and relies on later service validation.
- **Formula drift:** a calculation is copied into reporting, billing, and UI code with different rounding.
- **God domain service:** a domain service becomes a procedural god object that both decides and performs side effects.
- **Late storage failure:** persistence constraints throw late generic errors that leak through the API as domain behavior.
- **Unowned consistency boundary:** cross-aggregate rules are implemented synchronously with no transaction, lock, retry, outbox, or eventual-consistency decision.

# Output Contract

Return a Domain Implementation Contract with:

- **Mode selected:** aggregate/entity invariant, value object validity, domain service/policy, lifecycle transition, calculation/derivation, or layer cleanup.
- **Domain owner:** aggregate root, entity, value object, domain policy, or domain service that owns the rule.
- **Rule authority map:** invariants, calculations, lifecycle transitions, policy rules, effective dates/versions, and the one authority for each.
- **Entry points and bypass scan:** callers that can mutate or derive the behavior, rejected bypasses, and layers allowed only to precheck or project.
- **Operations:** domain methods/factories/policies, inputs, output/result type, side-effect classification, and dependency boundary.
- **Allowed and rejected transitions:** source state, command, actor/policy input, target state, rejection outcome, and terminal-state handling.
- **Value objects:** construction rules, equality/format semantics, boundary values, and serialization/mapping boundary.
- **Domain service needs:** objects/policies read, why no single aggregate owns the rule, and proof it stays pure.
- **Failure outcomes:** typed domain errors/results, user-facing mapping owner, and no infrastructure exception leakage.
- **Persistence reinforcement:** constraints/indexes/locks/idempotency or transaction requirements that reinforce domain behavior.
- **Tests:** allowed cases, denied cases, boundary/property cases, transition matrix, concurrency or retry cases when relevant.
- **Handoff:** service, repository, transaction, API contract, or state-machine work that remains outside this capability.
- **Graph memory trajectory judgment:** accepted, rejected, stale, or not verified for prior rule authority, duplicated-rule, caller, transition, and validation claims.
- **Changed rule to validation map:** every invariant, value rule, transition, calculation, failure outcome, bypass path, and non-authoritative check mapped to validator, owner review, or residual risk.
- **Evidence limits:** what source reads, graph scans, project memory, tests, owner review, and validation prove and do not prove.
- **Next gate and rollback/reroute:** where to continue when authority, transaction, API contract, release, security, or historical-data evidence is partial.

# Evidence Contract

Close a domain-logic change only when the handoff states the selected mode, source files and boundaries inspected, related entry points inspected, same-pattern or bypass scan, selected domain authority and rejected placement alternatives, graph/memory/trajectory judgment, behavior preserved for existing callers, validation commands run with outcomes, what the evidence proves, what the evidence does not prove, validation freshness after the final material edit, untested concurrency/versioning/backfill risk, rollback or reroute note, residual risk, and next gate. A prose-only domain plan without denied-case or boundary evidence is not sufficient.

# Quality Gate

1. **Single authority:** every invariant has exactly one authority in the domain; it is not duplicated across controller, service, SQL, and frontend.
2. **Pre-persistence rejection:** invalid states are rejected as close to the domain as possible, before persistence, not after.
3. **Transition completeness:** each allowed and each forbidden state transition is enumerated, with the rejection outcome for forbidden ones.
4. **Denied-case proof:** tests prove both allowed behavior and forbidden behavior, not just the happy path.
5. **Value construction safety:** value objects enforce their own validity at construction; no partially-valid value object can exist.
6. **Dependency direction:** domain logic does not import controller, transport, ORM, or UI concerns; dependency direction points inward.
7. **Persistence reinforcement:** persistence constraints reinforce the invariants rather than being the only place they are enforced.
8. **Typed failure outcomes:** failure outcomes are explicit domain results or typed errors, not silent nulls or swallowed exceptions.
9. **Entry-point coverage:** all mutating entry points invoke the same domain authority, including imports, admin paths, jobs, and tests.
10. **Pure domain services:** domain services contain pure domain decisions and do not perform persistence, network, queue, cache, log, metric, email, or payment effects.
11. **Calculation contract:** calculations state precision, rounding, timezone, currency, effective-date/version, and externally visible contract impact when relevant.
12. **Consistency handoff:** cross-aggregate, concurrent, retry, or eventual-consistency risks have a transaction/idempotency/outbox/compensation decision or explicit handoff.
13. **Duplicate-rule scan:** implementation has a same-pattern scan for duplicated rules and a plan for removing or demoting non-authoritative checks.
14. **Public behavior tests:** public behavior tests cover the domain API and failure outcomes without importing private helpers.
15. **Evidence freshness:** validation commands, graph scans, source reads, owner reviews, and manual artifacts state outcome, what evidence proves, what evidence does not prove, and whether evidence is fresh after the final material edit.
16. **Handoff limits:** handoff boundaries, evidence limits, rollback or reroute note, residual risk, and next gate are explicit so domain implementation is not over-claimed as orchestration, persistence, transaction, API, release, or security approval.

# Used By

- backend-change-builder
- domain-impact-modeler

# Handoff

Hand off to `business-rule-extraction` for unclear rules; `domain-object-identification` for unclear aggregate/entity/value ownership; `state-machine-modeling` for complex lifecycle discovery; `service-business-logic` for orchestration, authorization order, transactions, and external effects; `repository-persistence` for mapping and constraints; `transaction-consistency` or `idempotency-retry-design` for concurrency, retries, and distributed consistency; `data-api-contract-changer` when externally visible calculation or failure contracts change.

# Completion Criteria

The capability is complete when each domain rule has one enforceable authority, invalid states are rejected before persistence, domain behavior is persistence/transport independent, value objects and transitions are explicit, side effects are kept outside pure domain decisions, critical constraints reinforce the domain model, and tests cover allowed, denied, boundary, transition, and relevant concurrency/versioning cases.
