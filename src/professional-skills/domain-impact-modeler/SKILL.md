---
name: domain-impact-modeler
description: "Use this skill when implementing, reviewing, planning, or validating product or code changes that need domain impact analysis across entities, value objects, aggregates, business rules, invariants, state machines, permissions, domain events, lifecycle transitions, and consistency boundaries."
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
metadata:
  changeforge.profile: recommended
  changeforge.skill_type: professional
---

# Domain Impact Modeler

## Mission
Identify, map, and reason about the full business domain impact of a proposed change — across bounded contexts, aggregate boundaries, domain events, ownership rules, and invariants — so that implementation decisions are grounded in domain model correctness, not technical convenience, and cross-domain side effects are discovered before they become production incidents.

## Stage Ownership
Own the DDD slice for ChangeForge process traces: domain terms, entity and value-object ownership, domain/application service boundaries, invariants, side-effect boundaries, and existing code ownership. Use `development-process-orchestrator` when DDD must map forward into SDD and TDD evidence.

## When To Use
- A change creates, modifies, or deletes an entity, aggregate, or value object in a domain model.
- A change adds, renames, or removes a domain event that other bounded contexts may consume.
- A change crosses a bounded context boundary or introduces a new integration point between domains.
- Ownership of a concept or aggregate is ambiguous or contested between services.
- Ubiquitous language is being extended, changed, or reused with different meaning across contexts.
- Business rules or invariants are being modified, relaxed, or enforced differently.
- A refactoring changes domain model structure without visible feature change — the impact is hidden in the semantics.

## Do Not Use When
- The change is purely technical infrastructure with no domain model implications.
- The change affects a single bounded context with no shared domain events and no cross-context ownership questions.
- The impact analysis is already captured in a change intake document with an approved domain model review.

## Adjacent Skill Conflict Resolution

For `domain-impact-modeler`, keep this skill primary only when domain objects, aggregates, business rules, invariants, state machines, permissions, domain events, or lifecycle transitions decide the next action. Hand API/schema compatibility to `data-api-contract-changer`, storage/query/migration concerns to `data-middleware-change-builder`, security/privacy decisions to `security-privacy-gate`, reliability/observability decisions to `reliability-observability-gate`, release/rollback readiness to `delivery-release-gate`, and documentation contract updates to `change-documentation-gate`. Domain extensions add risk-specific addenda after the primary owner is selected; record skipped plausible owners when the routing choice affects handoff or validation.

## Required Context / Missing Information Policy

Before `domain-impact-modeler` plans or closes work, collect current behavior, desired behavior, non-goals, affected surface, owner module, validation signal, existing conventions, and material data/API/security/release boundaries. Ask or block only when the missing fact can change public contract, data model, authorization, tenant behavior, migration/rollback, irreversible operation, or domain semantics; otherwise proceed with explicit reversible assumptions.

## Critical Gotchas

- `domain-impact-modeler` must inspect the owning source, tests, configs, docs, and generated-artifact boundaries before planning material engineering work.
- `domain-impact-modeler` must select only risk-changing references, capabilities, gates, or domain extensions; do not load nearby material because it exists.
- `domain-impact-modeler` must close with fresh validation evidence, evidence limits, residual risk, and next owner or gate when work remains.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `domain-impact-modeler` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- **Bounded context boundaries must be explicit**: every aggregate has one owning context; no aggregate is shared or mutated by two contexts simultaneously.
- **Domain events are contractual commitments**: once a domain event is published and consumed, its shape is as binding as a public API — changes require versioning, consumer notification, and migration.
- **Ubiquitous language changes propagate everywhere the term is used**: renaming a concept in code without updating the language in documentation, team vocabulary, and consumer schemas creates two models that drift apart.
- **Invariants must be enforced at the aggregate boundary**: invariants enforced only at the application layer will be violated by any path that bypasses that layer (batch jobs, admin scripts, direct database writes).
- **Cross-domain side effects must be designed, not discovered**: every domain event that crosses a context boundary must have an explicit consumer list, delivery guarantee, and failure handling strategy.
- **Anti-corruption layers are required at context boundaries**: never let the model of one bounded context bleed into another — translate at the boundary.
- **Domain ownership ambiguity is a design defect**: if it's unclear which context owns an entity, resolve the ambiguity before implementation, not during.
- **Do not encode domain decisions only in UI or client code**: business rules validated only at presentation layer are invisible to batch jobs, APIs, admin tools, and integrations.
- **Relaxed invariants cannot be re-tightened without data cleanup**: once a constraint is removed, records violating it may already exist — design for forward invariant tightening from day one.

## Industry Benchmarks
- **Domain-Driven Design (Evans)**: Bounded contexts, ubiquitous language, aggregates, value objects, domain events, repositories, anti-corruption layers. Foundational model for domain impact analysis.
- **Implementing Domain-Driven Design (Vernon)**: Aggregate design rules — small aggregates, reference by identity, eventual consistency between aggregates. The authoritative guide to aggregate sizing and boundaries.
- **Event Storming (Brandolini)**: Collaborative domain modeling that surfaces domain events, commands, aggregates, and bounded context boundaries before code is written. Use to validate domain impact scope.
- **Team Topologies (Skelton, Pais)**: Domain ownership maps to team topology — stream-aligned teams own domains; platform teams provide capabilities. Cross-domain changes require inter-team coordination.
- **Context Mapping Patterns (Evans Chapter 3)**: Published Language, Shared Kernel, Customer/Supplier, Conformist, Anti-Corruption Layer, Open Host Service — each pattern has different impact propagation risk and coordination overhead.

### Context Mapping Risk Matrix

| Relationship Pattern | Impact Propagation Risk | Required Coordination |
|---|---|---|
| Shared Kernel | Critical — both contexts must agree on all changes | Joint review; both teams must approve any model change |
| Customer/Supplier | High — supplier changes affect all customer teams | Change notification + migration guide + agreed timeline |
| Conformist | Medium — consumer conforms to upstream model | Consumer must audit impact before each release |
| Published Language | High — changes affect all consuming contexts | Versioning required; all consumers notified and migrated |
| Anti-Corruption Layer | Low — ACL absorbs external model changes | ACL translation must be updated; internal model protected |
| Separate Ways | None — contexts are fully independent | No coordination required |

## Technical Selection Criteria
Evaluate the domain impact against:
- **Bounded context scope**: Which contexts does this change touch? What are their ownership rules and relationship patterns?
- **Aggregate integrity**: Does the change respect aggregate boundaries? Does it enforce invariants at the aggregate root?
- **Domain event impact**: Are existing domain events modified, replaced, or deprecated? Who consumes them? What is the versioning strategy?
- **Ubiquitous language consistency**: Does the change introduce, modify, or reuse terms in a way that conflicts with the existing language in any bounded context?
- **Context relationship pattern**: What is the relationship (Shared Kernel, Customer/Supplier, ACL, etc.) between affected contexts? What coordination is required?
- **Cross-context side effects**: What actions in other contexts are triggered by this change? Are they designed, tested, and handled in failure?
- **Invariant enforcement location**: Are invariants enforced at the aggregate root or dispersed into application/service layers?
- **Eventual consistency design**: If this change introduces eventual consistency between aggregates, is the compensation mechanism defined (saga, process manager, outbox pattern)?
- **State machine validity**: Does the change preserve all valid state transitions? Are illegal state transitions blocked at the domain model level?
- **Permission and ownership model**: Does the change alter who can perform what action on which entity? Is authorization enforced at the domain boundary?

## Mode Selection
Select the domain mode before modeling impact.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Entity/value change | Entity, value object, aggregate, ownership, identity, or lifecycle term changes. | Identify system-of-record, aggregate boundary, invariant owner, and language impact. | Entity/value map, owning context, invariant list, persistence/API/event surfaces. | `domain-object-identification`, `business-rule-extraction` | Architecture split unless ownership or coupling is unclear. |
| Business rule/invariant change | Rule relaxed/tightened, permission rule changes, money/status limit, or validation moves. | Locate authoritative rule enforcement and invalid historical state risk. | Rule source, allowed/denied cases, enforcement boundary, data cleanup implication. | `business-rule-extraction`, `permission-boundary-modeling` | UI-only validation as sufficient evidence. |
| State machine change | Status, lifecycle transition, workflow gate, cancellation, approval, or compensation changes. | Preserve valid transitions and block illegal transitions across all entry points. | State diagram delta, transition table, forbidden transition tests, event side effects. | `state-machine-modeling`, `regression-testing` | Persistence schema work until transitions are approved. |
| Domain event change | Event added, renamed, deprecated, shape changed, or consumer unknown. | Treat events as contracts with versioning, consumers, and delivery semantics. | Event schema, producer/consumer list, version plan, replay/upcaster/compatibility evidence. | `domain-event-modeling`, `data-api-contract-changer` | Consumer migration assumptions without owner. |
| Cross-context ownership | Shared concept, service split, ACL, reporting projection, or team ownership boundary appears. | Keep one business rule authority and prevent model leakage between contexts. | Context map, relationship pattern, ACL/translation point, owner approval. | `architecture-impact-reviewer`, `integration-change-builder` | Direct database sharing or shared mutable aggregate. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A request renames or reuses a business term like account, order, customer, tenant, status, balance, or entitlement. **Hidden risk:** ubiquitous-language drift creates two meanings for one concept. **Required professional action:** audit affected contexts and define owning language. **Route to:** `domain-object-identification`, `change-documentation-gate`. **Evidence required:** term map, affected contexts, old/new name boundary, docs/API/event impact.
- **Signal:** A rule is added in controller, UI, SQL, or validation layer without domain owner. **Hidden risk:** invariant bypass through batch jobs, APIs, admin tools, or events. **Required professional action:** move or route enforcement to aggregate/domain policy owner. **Route to:** `business-rule-extraction`, `backend-change-builder`. **Evidence required:** enforcement location, bypass paths scanned, allowed/forbidden tests.
- **Signal:** A new status or lifecycle transition is added without a full transition table. **Hidden risk:** illegal state paths become reachable and downstream events misfire. **Required professional action:** model state machine before implementation. **Route to:** `state-machine-modeling`, `quality-test-gate`. **Evidence required:** transition delta, forbidden transitions, side effects, regression tests.
- **Signal:** A domain event changes shape, required field, name, or meaning with unknown consumers. **Hidden risk:** event contract break or replay incompatibility. **Required professional action:** version event or enumerate consumers before merge. **Route to:** `domain-event-modeling`, `contract-testing`. **Evidence required:** consumer list, schema diff, version/migration plan, replay or upcaster note.
- **Signal:** Two modules/services can write the same entity, permission, balance, status, or entitlement. **Hidden risk:** business rule authority is split and consistency depends on timing. **Required professional action:** assign one owner and mediate other writes through contract/event/ACL. **Route to:** `architecture-impact-reviewer`, `transaction-consistency`. **Evidence required:** writer scan, owner decision, dependency direction, compensation/consistency model.

### Decision Tree: Domain Model Change Depth

```
Does the change modify an aggregate's identity, ownership, or invariants?
├── Yes → Full domain model review required; bounded context impact analysis
Does the change add or modify a domain event?
├── Yes → Consumer enumeration required; event versioning if consumers exist
Does the change rename or redefine a domain concept?
├── Yes → Ubiquitous language audit across all affected bounded contexts
Does the change cross a bounded context boundary?
├── Yes → Context relationship pattern must be declared; ACL/translation layer assessed
Does the change alter authorization or permission semantics?
├── Yes → Permission model audit; RBAC/ABAC policy review
Change within single context with no shared events?
└── Lightweight domain review sufficient
```

## Risk Escalation
- Escalate when a change violates the Single Responsibility Principle of bounded context ownership — when two teams would need to coordinate on every subsequent change.
- Escalate when a domain event change breaks existing consumers who have not been notified or migrated.
- Escalate when an aggregate invariant is being relaxed to accommodate a new use case — relaxed invariants cannot be re-tightened without data cleanup.
- Escalate when a Shared Kernel modification is proposed — this affects two teams simultaneously and requires joint approval.
- Escalate when the proposed implementation would introduce a distributed monolith pattern — tight runtime coupling between contexts through synchronous cross-domain calls on the critical path.
- Escalate when the domain model change creates a cyclic dependency between bounded contexts.
- Escalate when business rule changes affect regulatory, financial, or compliance invariants — these require stakeholder and legal/compliance sign-off.
- Escalate when a state machine change allows new state transitions that were previously illegal — the downstream behavioral consequences must be fully analyzed.

## Critical Details
- **Aggregate size discipline**: Vernon's rule — aggregates should be as small as possible. Large aggregates create lock contention and high write conflict rates under concurrent load. Split the aggregate before adding the feature.
- **Event versioning**: Domain events are immutable historical records. A changed event is a new event version, not an update. Support both v1 and v2 simultaneously during the migration window; upcasters translate old events to new schema at read time.
- **Saga vs. process manager**: A saga is a sequence of local transactions with compensating transactions for rollback. A process manager has state and reacts to events. Use sagas for linear flows, process managers for complex multi-step business processes with branching.
- **Repository vs. domain service**: A Repository retrieves and persists aggregates. It does not contain business logic. Business logic that belongs to no single aggregate is a domain service.
- **Value object equality**: Value objects are defined by their attributes, not identity. Two `Money(100, USD)` objects are equal. Mutation creates a new value object; the old one is discarded.
- **Outbox pattern for reliable event publishing**: Write domain events to an outbox table in the same transaction as the aggregate state change; a background worker publishes them to the event bus — prevents event loss on process crash.
- **Anti-corruption layer location**: The ACL lives at the boundary of the consuming context, not the providing context. It translates the upstream model into the consuming context's language without polluting the internal model.

### Anti-Examples

| Domain Pattern | Problem | Corrected Approach |
|---|---|---|
| Two services share the `Order` aggregate with direct DB access | Shared mutable aggregate violates bounded context isolation | Each context owns its own `Order` projection; domain events propagate state changes |
| Domain event `OrderPlaced` modified to add required `taxAmount` | Breaks all consumers that don't populate `taxAmount` | Publish `OrderPlacedV2` with `taxAmount`; deprecate `OrderPlaced` with sunset timeline |
| Business rule "Order cannot exceed credit limit" enforced in REST controller only | Bypassed by batch job, admin script, or direct DB write | Enforce at aggregate root `Order.place()` method; return domain exception |
| Term "Account" reused with different meaning in billing and identity contexts | Language ambiguity causes cross-team confusion and silent bugs | Define `BillingAccount` and `UserAccount` as distinct bounded context terms |
| Saga has no compensating transactions | Failure midway creates permanently inconsistent state | Every saga step has a defined compensating transaction; test compensation paths |

## Failure Modes
For `domain-impact-modeler`, state symptom, impact, and detection.
State repair and evidence before closure.

- **Hidden cross-context coupling**: A change to the `User` aggregate causes the `Billing` context to receive malformed events — the two contexts were implicitly coupled through a shared database table.
- **Invariant bypass in production**: An admin script inserts an `Order` record directly into the database, bypassing the aggregate root — an illegal state is created that the application cannot handle.
- **Domain event explosion**: A domain event change cascades through 12 consuming services — each needs a migration, none were notified, and the release is blocked for weeks.
- **Ubiquitous language drift**: After a rename from `Client` to `Customer`, the old term continues in API docs, team discussions, and legacy code modules — two conflicting models coexist.
- **Over-sized aggregate creates write bottleneck**: An aggregate with 50 child entities locks the entire aggregate root on every write — concurrency degrades under high load.
- **Saga without compensation**: A multi-step business process has no compensating transactions — a failure midway creates permanently inconsistent state with no automated recovery.
- **Permission bypass through domain event**: An unauthorized action is blocked at the API layer but the domain event that would trigger the same effect is accessible to a queue consumer with elevated permissions.
- **Business semantic claim without source evidence**: A rule, workflow, term, or owner is marked as fact from memory or graph proximity only; implementation planning proceeds on an unverified domain assumption.

## Reference Loading Policy
Do not load every reference by default. For L1 `domain-impact-modeler` work, use this body unless selected risk requires more detail.
For L2, L3, L4, and L5 `domain-impact-modeler` work, read `references/capabilities/index.md` only to locate selected capability references; load selected files at `references/capabilities/<capability-id>-<capability-name>.md`, then add [references/checklist.md](references/checklist.md), [references/evidence-patterns.md](references/evidence-patterns.md), [references/business-semantic-pack.md](references/business-semantic-pack.md), or domain references only when route risk requires them. Load `references/checklist.md` for aggregate/rule/event surface review, `references/evidence-patterns.md` when closure depends on rule-to-test mapping, event consumer proof, owner acknowledgement, or historical data cleanup evidence, and `references/business-semantic-pack.md` when BSP source-backed facts, memory/graph selector limits, or structured BSP skip rationale decide whether implementation planning can continue.

## Execution Procedure

For `domain-impact-modeler`: confirm activation and role; classify missing context; inspect relevant source/test/config/doc evidence; select mode, complexity, risk, and minimal references; execute or review only the owned surface; validate with concrete commands, diffs, tests, evals, or not-run limits; route repair through the owner; hand off with residual risk and next gate.

## Output Contract
Return a domain impact model with:
- **Mode selected**: Domain mode and trigger signal that selected it.
- **Bounded context map**: Which contexts are affected, with relationship patterns and coordination requirements.
- **Aggregate impact**: Which aggregates are modified, with invariant list and enforcement location.
- **Domain event impact**: Events added, changed, or deprecated — with consumer list, versioning strategy, and migration plan.
- **Ubiquitous language delta**: Terms added, renamed, or redefined — with cross-context audit results.
- **State machine delta**: State transitions added, modified, or removed — with validity analysis.
- **Permission model impact**: Authorization rules affected by the change — with enforcement location.
- **Cross-domain side effects**: Actions triggered in other contexts — with delivery guarantee, failure handling, and compensation.
- **Risk classification**: Per-context risk level with escalation triggers identified.
- **Team coordination required**: Named teams or owners that must review or approve before implementation proceeds.
- **Boundaries inspected**: entities, value objects, aggregates, policies, state machines, events, permissions, repositories, APIs, and context maps inspected.
- **Professional judgment**: authoritative business rule owner, invariant enforcement decision, hidden coupling ruled out, and domain risks still possible.
- **Business semantic control**: BSP trigger decision, task-scoped business intent/vocabulary/object/rule/workflow evidence, source-backed FACT status, memory/graph selector limits, selected/skipped references, and residual semantic risk when business semantics are in scope.
- **Reuse and placement rationale**: existing aggregate, policy, domain service, event, or ACL reused; new concept placement justified.
- **Behavior preservation statement**: old allowed/forbidden transitions, event semantics, permission rules, and invariants preserved or intentionally changed.
- **Validation evidence**: domain tests, transition tests, consumer/schema checks, language audit, or not-verified disclosure.
- `domain_change_to_validation_map`: each affected entity, invariant, state transition, permission rule, domain event, BSP claim, or cross-context side effect mapped to test, validator/report artifact, source/owner evidence, freshness, what is proved, what is not proved, residual risk, and next owner.
- **Evidence limits**: what the domain evidence proves and does not prove about downstream consumers, historical data, replay, or compliance.
- `business_semantic_pack_delta`: when BSP is selected, summarize sections changed, source-backed facts, assumptions that must not be treated as FACT, open questions, and residual business risk; load [references/business-semantic-pack.md](references/business-semantic-pack.md) for the full field contract.
- **Residual risk and next gate**: unverified side effect, event migration, data cleanup, or owner approval with handoff.

## Business Semantic Pack Coupling
DDD owns the BSP domain slices when a business semantic trigger is present. It writes or updates `business_vocabulary`, `business_objects`, `business_rules`, `workflows`, and `data_and_signal_semantics`, then maps each claim into `validation_map` or residual risk.

When a business semantic trigger, missing BSP, source-backed FACT decision, or memory/graph selector limit decides the next action, load [references/business-semantic-pack.md](references/business-semantic-pack.md).

## Evidence Contract
Close a domain impact model only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the business rule, invariant, and ubiquitous-language term the model rests on.
- **Files and boundaries inspected**: the aggregates, value objects, domain services, policies, state machines, and domain events examined, and the bounded-context boundary each change sits within.
- **Placement rationale**: why each rule and invariant has exactly one enforcement owner in the domain, and confirmation that no business rule leaks into a controller, SQL query, frontend validator, or test mock.
- **Validation commands**: the tests proving both allowed and forbidden transitions, and the cross-context language audit, each with its outcome.
- **Domain judgment and evidence limits**: mode selected, behavior preservation, authoritative owner, what evidence proves, what it does not prove, residual risk, and next gate.
- **Residual risk**: the cross-domain side effect, event-versioning gap, or compensation path that remains unverified, with the named owner.
- **BSP evidence**: graph and memory are selectors only; any business semantic `FACT` requires current source, owner review, user-provided source, or validation evidence.

## Quality Gate
1. Every aggregate affected has an identified owning bounded context with explicit ownership rules.
2. Aggregate invariants are enforced at the aggregate root, not only in the application layer.
3. All domain events that cross context boundaries have a versioning strategy and consumer list.
4. Ubiquitous language changes are audited across all affected bounded contexts.
5. Context relationship patterns are declared for all cross-context integrations affected by the change.
6. Cross-domain side effects have explicit delivery guarantees and failure handling.
7. No cyclic dependencies between bounded contexts are introduced.
8. Sagas or process managers are defined for multi-step business processes that span aggregate boundaries.
9. All teams that own affected bounded contexts have been notified and acknowledged the impact.
10. Domain model changes do not violate regulatory or compliance invariants without explicit stakeholder approval.
11. Business Semantic Pack domain claims are mapped to source-backed evidence, validation, owner review, or explicit residual risk.
12. When a business semantic trigger is present, DDD output maps affected vocabulary, object, rule, workflow, signal, and validation claims into BSP or records structured BSP skipped rationale before implementation planning.

## Handoff
- **architecture-impact-reviewer** — when domain model changes affect architectural boundaries, team topology, or system-of-record ownership.
- **backend-change-builder** — for aggregate and domain service implementation details.
- **integration-change-builder** — when cross-context integration contracts or event delivery mechanisms are affected.
- **data-api-contract-changer** — when domain event schema evolution requires API versioning or consumer migration.
- **change-impact-analyzer** — when the domain model change has upstream business process or downstream reporting impact.
- **task-dag-planner** — to sequence team coordination, migration, and implementation tasks with proper inter-team dependencies.

## Completion Criteria
Domain impact analysis is complete when all affected bounded contexts are identified with relationship patterns, aggregate invariants are enumerated and enforcement locations confirmed, domain event changes have versioning strategies and consumer notifications planned, ubiquitous language changes are audited and propagated, cross-domain side effects are explicitly designed with failure handling, and all owning teams have acknowledged the impact before implementation begins.
