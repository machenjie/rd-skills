---
name: domain-object-identification
description: Identifies entities, value objects, aggregates, resources, ownership, lifecycle, invariants, and relationships for product-domain changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "12"
changeforge_version: 0.1.0
---

# Mission

Establish the domain object inventory that tells a builder where identity, lifecycle, invariants, ownership, permissions, persistence, events, and tests belong. The inventory separates domain concepts from database tables, API resources, DTOs, UI labels, generated schemas, and read models so later implementation work can place behavior on the correct object or boundary instead of copying terms from the nearest layer.

# When To Use

Use this capability when a change introduces, renames, splits, merges, or reuses entities, value objects, aggregate roots, resources, ownership terms, lifecycle states, relationships, identifiers, invariants, read models, or external resource names.

Use it before persistence, permission, API, event, or implementation placement when the domain owner, aggregate boundary, identity source, or lifecycle authority is unclear.

# Do Not Use When

Do not use this capability to mirror database tables without domain reasoning, rename implementation classes for style, create speculative domain objects beyond the approved scope, or force a rich domain model onto simple CRUD with no meaningful invariant or lifecycle.

Do not use it when the objects are already accepted and the current question is rule authority (`business-rule-extraction`), lifecycle transition legality (`state-machine-modeling`), persistence shape (`data-model-design`), API schema shape (`dto-schema-design`), or DTO/domain/persistence boundary mapping (`model-boundary-mapping`).

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release preparation, and incident repair when domain language, identity, ownership, aggregate boundaries, lifecycle, or resource exposure can drift. Treat this capability as the stage launch guard before persistence, permission, API, event, and implementation placement decisions. In planning, name the candidate terms, current source paths, repository graph slice, project-memory verdict, accepted or rejected prior object claims, validation signal, and downstream handoff. During review, reject diffs that change domain language, identity, ownership, aggregate boundaries, writer authority, or exposed resources without updating the object inventory and downstream tests.

# Non-Negotiable Rules

- Distinguish entities, value objects, aggregates, resources, policies, and read models.
- Identify ownership, lifecycle, invariants, and relationship cardinality.
- Define source of identity and equality semantics.
- Identify which object owns each rule and transition.
- Do not let UI labels or storage tables define the domain model by default.
- Do not reuse the same business term across bounded contexts without naming the owning context and translation point.
- Do not expose persistence models, generated schemas, or API DTOs as internal domain objects without an explicit mapping decision.
- Aggregate boundaries must be sized by invariant consistency and transaction authority, not by table joins or screen composition.
- Relationship modeling must name cardinality, optionality, reference direction, and whether references cross aggregate boundaries by identity.
- Every permission, event, persistence, and test implication must have an owner or a downstream handoff.

# Industry Benchmarks

Use domain-driven design tactical modeling, bounded-context and ubiquitous-language review, aggregate consistency review, entity/value-object identity rules, resource modeling, lifecycle analysis, data ownership review, API contract design, event storming, and context-mapping practices as benchmarks. Keep the body focused on route-time selection, output evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for category decision matrices, graph/memory/trajectory coupling, object-to-validation mapping, and anti-pattern review.

# Mode Matrix

Select the object-identification mode before choosing persistence schema, API resource shape, permission owner, event contract, or implementation placement; record skipped adjacent modes and handoff targets when evidence is partial.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Concept inventory | New or reused business term, object, owner, identifier, relationship, or lifecycle term. | Separate domain concept from table, DTO, UI label, resource, and read model. | Term map, category decision, identity/equality rule, owning context, rejected layer-derived names. | `business-rule-extraction`, `use-case-modeling` | Persistence design until object ownership is clear. |
| Aggregate boundary | Invariant, transaction, consistency, lifecycle, or mutation authority crosses objects. | Draw aggregate roots and references so invariants are enforceable without broad locking. | Aggregate root, invariant owner, transaction boundary, relationship cardinality, cross-aggregate identity reference. | `transaction-consistency`, `domain-logic-implementation` | Splitting by table count or screen section. |
| Resource exposure | API resource, event payload, DTO, generated client, or external provider name resembles a domain object. | Prevent resource/schema names from overwriting internal domain language. | Internal object map, external resource map, translation owner, compatibility and event impact. | `dto-schema-design`, `model-boundary-mapping`, `domain-event-modeling` | Directly returning domain objects from API/resource layers. |
| Cross-context ownership | Two modules, services, teams, or actors can define or mutate the same concept. | Assign one source of truth and define translation, ACL, event, or contract boundary. | Context owner, writer scan, mutation authority, conflict policy, documentation impact. | `architecture-impact-reviewer`, `permission-boundary-modeling` | Shared mutable aggregate or direct database sharing. |

# Selection Rules

Select this capability when the main question is what domain concepts exist, which category each concept belongs to, and who owns the concept's behavior. Select it before `business-rule-extraction` when rule owners are unknown. Select it with `repository-context-map` or `repository-graph-analysis` when current code, registry, tests, generated artifacts, or docs already use the term and may contain conflicting meanings.

Select `business-semantic-control-plane` with this capability when object names, owner context, DTO/table confusion, stale memory, or graph-selected evidence must be recorded in a task-scoped Business Semantic Pack. The BSP record carries object claims as source-backed facts, inferences, assumptions, open questions, or memory signals.

Prefer `business-rule-extraction` when objects are known but rules are scattered. Prefer `state-machine-modeling` when lifecycle states and transitions are the primary unknown. Prefer `data-model-design` when persistence structure is the main deliverable. Prefer `implementation-structure-design` when the domain concept is accepted and the remaining question is function, class, file, or module placement.

# Risk Escalation Rules

Escalate when object boundaries affect consistency, tenant ownership, money movement, regulated records, audit history, migration design, external API resources, or event semantics.

Escalate when a rename or reuse of a term can change permission checks, data ownership, API/event meaning, reporting metrics, historical audit interpretation, or cross-service writer authority. Escalate when graph or source search finds the same term used by multiple modules with different lifecycle, identity, or owner semantics.

# Proactive Professional Triggers

- **Signal:** A request uses a broad business term such as account, customer, order, tenant, subscription, balance, status, entitlement, profile, or resource without owner context.
  **Hidden risk:** two bounded contexts reuse one word with different identity, lifecycle, or mutation authority, causing wrong owner decisions.
  **Required professional action:** inspect current source, model a term/context map before implementation, and reject ambiguous meanings.
  **Route to:** `domain-object-identification`, `repository-context-map`.
  **Evidence required:** affected contexts, owning context, old/new term boundary, searched source paths, and rejected ambiguous meanings.
- **Signal:** A table, ORM entity, generated schema, API DTO, event payload, or provider model is treated as the domain object.
  **Hidden risk:** persistence or external contract details become the business model and leak into permissions, tests, and APIs.
  **Required professional action:** compare domain object and boundary model, document the mapping owner, and require mapping tests before placement.
  **Route to:** `model-boundary-mapping`, `dto-schema-design`.
  **Evidence required:** source/target model map, identity/equality decision, mapping tests, and rejected direct reuse.
- **Signal:** A new invariant references multiple entities without naming an aggregate root.
  **Hidden risk:** transaction boundaries cannot enforce the invariant and concurrent writes create inconsistent invalid state.
  **Required professional action:** model aggregate ownership and verify transaction or eventual-consistency design before coding.
  **Route to:** `transaction-consistency`, `domain-logic-implementation`.
  **Evidence required:** invariant owner, consistency boundary, allowed cross-aggregate references, and tests for violating writes.
- **Signal:** Two services, jobs, admin tools, imports, or event consumers can mutate the same object or status.
  **Hidden risk:** ownership is split and behavior becomes inconsistent across timing, retries, or entry point.
  **Required professional action:** scan writer entry points, document mutation authority, and route other writers through contract, command, event, or ACL.
  **Route to:** `architecture-impact-reviewer`, `permission-boundary-modeling`.
  **Evidence required:** writer scan, authority decision, dependency direction, and denied mutation cases.
- **Signal:** A domain event or API resource name changes because an internal object was renamed.
  **Hidden risk:** internal ubiquitous-language cleanup becomes an external contract break.
  **Required professional action:** document the internal rename separately from the resource/event compatibility plan and verify consumers.
  **Route to:** `domain-event-modeling`, `data-api-contract-changer`.
  **Evidence required:** consumer list, compatibility decision, versioning or alias plan, and residual external-contract risk.
- **Signal:** Repository graph or project memory claims an object owner, legacy name, or writer path without current source confirmation.
  **Hidden risk:** stale memory or generated artifacts become semantic proof and send implementation to the wrong owner.
  **Required professional action:** inspect current source, compare memory timestamp, and document accepted or rejected claims.
  **Route to:** `repository-graph-analysis`, `project-memory-governance`.
  **Evidence required:** graph nodes inspected, memory timestamp, accepted/rejected claim, validation freshness, and uninspected paths.

# Critical Details

Entities require stable identity across time. Value objects require equality by attributes and should not hide lifecycle state. Aggregates own invariants that must be transactionally protected. Resources are externally exposed representations and may not equal internal aggregates. Read models optimize queries and must not become write-side authorities. Policies/specifications own decisions that do not naturally belong to one entity but still need a named owner.

Identity evidence includes natural key, surrogate id, tenant scope, external id, uniqueness boundary, and merge/split behavior. Equality evidence includes exact attributes, normalization, precision, timezone, locale, and versioning where those affect value-object comparison.

Ownership includes business owner, data owner, source of truth, tenant scope, mutation authority, and writer entry points. A repository graph or search result can reveal conflicting uses of a term, but it is not semantic proof until current source, tests, docs, or registry context confirms the meaning.

Aggregate boundaries are consistency boundaries: keep references across aggregates by identity, not deep object nesting, unless the object is a child whose lifecycle and invariants are owned by the parent. Cross-aggregate workflows need domain events, process managers, compensating actions, or explicit eventual consistency.

# Failure Modes

- **Table-as-domain shortcut:** database tables are accepted as domain objects without behavior analysis.
- **Hidden identity in values:** value objects gain hidden identity and lifecycle.
- **Oversized aggregate:** aggregate boundaries are too large, creating lock contention and broad transactions.
- **Undersized aggregate:** aggregate boundaries are too small, allowing invariants to be violated.
- **Resource language takeover:** external resource names overwrite internal domain language without review.
- **Same-term drift:** one term is reused across modules with different owner, identity, or lifecycle semantics.
- **Boundary model leak:** API DTOs or ORM entities become domain objects and force contract or storage changes into business behavior.
- **Read-model authority:** read models or reporting projections become write-side authority.
- **Deep cross-aggregate graph:** cross-aggregate references use nested object graphs and bypass aggregate invariants.
- **Ownerless downstream risk:** permission, persistence, event, and test implications are left as "later" and no downstream owner receives them.
- **Stale graph or memory proof:** old project memory, generated clients, or graph proximity are treated as semantic proof without current-source confirmation.

# Output Contract

Return a domain object inventory with, per object:

- `object_name`
- `category` (entity, value object, aggregate root, child entity, domain service, policy/specification, resource, read model)
- `owning_context`
- `identity` and `equality_semantics`
- `business_owner`, `data_owner`, `tenant_scope`, and `mutation_authority`
- `lifecycle` and state-machine handoff if meaningful states exist
- `invariants` and authoritative owner for each invariant
- `relationships` with cardinality, optionality, direction, and aggregate reference rule
- `aggregate_boundary` and consistency/transaction expectation
- `resource_exposure` (API/resource/event/DTO/generated/provider names and mapping owner)
- `persistence_implications`, `permission_implications`, and `event_implications`
- `tests` covering identity, equality, invariant, lifecycle, permission, persistence mapping, and event/resource mapping risks
- `open_questions`, rejected ambiguous meanings, and downstream handoffs
- `graph_memory_trajectory_judgment` for accepted, rejected, stale, or not-verified object claims
- `business_semantic_pack_mapping` when BSP is selected: object id, owning context, evidence class, source paths, memory/graph selector status, selected/skipped references, and residual semantic risk
- `object_to_validation_map` linking identity, equality, ownership, lifecycle, relationship, permission, persistence, and event/resource claims to validator, owner review, or residual risk
- `evidence_limits` naming what source reads, graph scans, project memory, owner review, and validation prove and do not prove
- `next_gate` when rule extraction, state modeling, permission, persistence, API contract, event, transaction, or release evidence remains outside this capability

# Quality Gate

1. Every identified object has an explicit category (entity, value object, aggregate root, domain service, or policy) with a justification.
2. Every entity has a defined identity and lifecycle; every value object is defined by its attributes and has no identity.
3. Each business rule, invariant, and state transition is assigned to exactly one explicit domain owner.
4. Aggregate boundaries are drawn so that each invariant is enforceable within a single aggregate's consistency boundary.
5. Permission, persistence, and event implications are named for each object, not deferred.
6. Relationships and aggregate references use identity, not deep object nesting across aggregate boundaries.
7. External resource and integration names do not overwrite internal domain language without explicit review.
8. No rule, transition, permission, persistence concern, or event is left without an assigned owner.
9. Same-term reuse across modules or contexts is mapped to one owning language or an explicit translation boundary.
10. DTO, ORM, event, generated, and provider models are mapped to or from domain objects rather than silently becoming them.
11. Writer entry points are inventoried when mutation authority is part of the change.
12. Tests or validation obligations are assigned for identity, equality, invariant, lifecycle, permission, persistence, and event/resource mapping risks.
13. Business Semantic Pack object claims are task-scoped, source-backed when marked `FACT`, and never promoted from repository graph or project memory alone.

# Evidence Contract

Close a domain object identification decision only when the handoff states:

- **Basis:** request, domain vocabulary, existing code/docs/tests/registry evidence, and why object identification is the right depth.
- **Boundaries inspected:** source paths, search terms, repository graph slice, project-memory claims, owning contexts, tables/resources/DTOs/events/read models checked, and uninspected areas.
- **Placement rationale:** why each concept is entity, value object, aggregate, resource, read model, policy, or service; rejected table/DTO/UI-label alternatives.
- **Validation evidence:** validator commands, graph scans, owner reviews, or review artifacts run after the final material edit, what they prove, what they do not prove, and any stale/not-run evidence.
- **Residual risk:** ambiguous terms, unresolved owners, stale memory, missing writer scan, unverified consumer/event impact, or open downstream handoff.

# Reference Loading Policy

The body holds high-frequency domain object decisions. Load [references/checklist.md](references/checklist.md) when building or reviewing a full inventory. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when category selection, aggregate/resource boundary, graph/memory/trajectory reuse, validation mapping, or anti-pattern detail needs more depth than this body should carry. Use [examples/example-output.md](examples/example-output.md) only as an output-shape example, not as a domain template. Do not load references for pure routing or trivial wording work where the output contract and quality gate are sufficient.

# Used By

- domain-impact-modeler
- data-api-contract-changer
- backend-change-builder

# Handoff

Hand off to `business-rule-extraction` for invariants, `state-machine-modeling` for lifecycle, `permission-boundary-modeling` for authorization, `data-model-design` for persistence, `dto-schema-design` or `model-boundary-mapping` for external schemas, `domain-event-modeling` for events, and `transaction-consistency` when aggregate ownership depends on concurrency or distributed consistency.

# Completion Criteria

The capability is complete when domain concepts are named with ownership, identity, equality, lifecycle, invariants, relationships, aggregate boundaries, resource mappings, and validation obligations clear enough to guide implementation without leaking database, API, DTO, UI, generated, or external-provider models into the domain language.
