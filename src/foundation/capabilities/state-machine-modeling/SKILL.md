---
name: state-machine-modeling
description: Models lifecycle states, allowed transitions, illegal transitions, guards, and side effects for orders, payments, subscriptions, approvals, assets, jobs, and workflows.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "14"
changeforge_version: 0.1.0
---

# Mission

**Model every domain object with meaningful lifecycle as an explicit finite state machine** - enumerating all states, all allowed transitions, all illegal transitions, every transition's guard conditions, side effects, emitted events, and audit impact - so lifecycle behavior is enforceable in the authoritative domain layer, untestable implicit status logic is eliminated, and impossible states become structurally unrepresentable rather than defended by scattered conditional checks.

# When To Use

Use this capability when: a domain object (order, payment, subscription, job, document, approval, asset, request, ticket) has more than one meaningful lifecycle state and the allowed transitions between states carry business rules, side effects, authorization constraints, or audit obligations; a change adds a new state, new transition, or new guard to an existing lifecycle; a production incident was caused by an illegal transition or unexpected state (e.g., double-charging, duplicate fulfillment, stuck job); or a multi-step workflow requires recovery, cancellation, and timeout to be explicitly designed as first-class transitions rather than discovered in production.

# Do Not Use When

Do not use this capability for: simple display-only status labels that control no behavior, no persistence, no authorization, no events, and no side effects (a color badge on a card is not a state machine); UI-only loading/error/empty states that are local to a single component and map to no domain concept (use `interaction-state-modeling`); domain event consumers that react to transitions but do not own the transition logic (use `domain-event-modeling`).

# Stage Fit

Use during domain discovery when lifecycle ownership is unclear; during implementation planning when transition authority, guards, side effects, persistence, events, authorization, or recovery behavior must be designed; during review when a diff adds status values, scattered conditionals, new actors, or external side effects; and during repair when incidents trace to illegal transitions, stuck records, duplicate side effects, stale migration assumptions, or missing regression coverage. Hand off when the primary question is object identity, detailed rule cataloging, event transport, storage migration sequencing, or executable test implementation.

# Non-Negotiable Rules

- **States must be mutually exclusive and exhaustive for the lifecycle.** A domain object must be in exactly one state at any point in time. Overlapping states ("PROCESSING and also PENDING"), implicit states ("no status field means PENDING"), and undeclared states discovered by reading boolean flags in combination are design defects. The state machine must enumerate all states including terminal states and error/failed states.
- **Allowed transitions must be explicit, and all unlisted transitions are illegal by default.** Any code path that attempts to transition from state A to state B must be validated against the allowed transition table. Unlisted transitions must throw a domain exception, not silently fail or succeed.
- **Every transition must name its actor or trigger, guard conditions, side effects, emitted events, and audit record.** A transition row without a guard, side effect policy, or audit record is incomplete.
- **Side effects must be tied to committed transitions, not attempted transitions.** Pattern: transition and persist, commit, emit event, then downstream handlers execute external effects asynchronously.
- **Retry and idempotency must be designed for every transition that triggers an external effect.** A retry caused by timeout, network error, or at-least-once delivery must not double-charge, double-ship, duplicate a ledger entry, or re-run a destructive action.
- **Recovery, cancellation, and timeout must be first-class transitions, not afterthoughts.** Every in-progress state must have an explicit exit to failure, timeout, cancellation, or operator recovery with trigger, actor, guard, and side effects.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New lifecycle model | New domain object, workflow, job, approval, asset, request, or ticket with meaningful states. | Define source of truth, state list, legal/illegal transitions, ownership, terminal states, recovery exits, and validation plan before implementation. | Object owner, state source, transition table, illegal-transition policy, terminal/failure states, diagram or table, tests. | `domain-object-identification`, `business-rule-extraction`, `quality-test-gate` | Modeling UI-only loading/error states. |
| Transition or guard change | New status value, transition, actor, guard, cancellation path, or lifecycle rule. | Preserve existing valid paths while proving new and old paths cannot create impossible states. | Current transition graph, changed rows, guard owner, actor authority, backward/forward compatibility, migration impact. | `business-rule-extraction`, `permission-boundary-modeling`, `version-compatibility` | Editing a status enum without graph review. |
| Incident or illegal transition repair | Stuck record, duplicate charge, duplicate fulfillment, invalid cancel, silent transition failure, or failed recovery. | Reproduce the illegal path and add regression evidence for the exact recurrence surface. | Incident path, current state, attempted transition, missing guard or lock, repair transition, red/green or compensating evidence. | `failure-diagnosis`, `regression-testing`, `concurrency-control` | Treating repair as a one-off data patch. |
| External side-effect transition | Transition triggers payment, shipment, email, webhook, event, ledger, inventory, or integration call. | Bind side effects to committed transitions and make retries idempotent. | Commit boundary, outbox/event plan, idempotency key, duplicate handling, ordering expectation, audit fields. | `domain-event-modeling`, `idempotency-retry-design`, `transaction-consistency` | Direct side effects before persistence commit. |
| Migration or versioned state change | State is renamed, removed, split, merged, or added for objects with stored records or consumers. | Keep old records, old code, new code, events, reports, and rollback behavior coherent. | Record counts, mapping plan, expand/contract or bridge, rollback behavior, consumer impact, validation query. | `data-migration-design`, `version-compatibility`, `delivery-release-gate` | Assuming enum changes are code-only. |
| Review and test evidence | PR review, architecture review, or release gate asks whether lifecycle behavior is safe. | Map every state/transition/risk to executable or documented validation evidence. | Changed-state-to-validation map, invalid transition tests, timeout/recovery tests, event/audit checks, evidence limits. | `quality-test-gate`, `ai-code-review-refactor`, `validation-broker` | Approving from diagram shape alone. |

# Industry Benchmarks

Anchor against UML State Machine Diagrams, Harel Statecharts, XState, Fowler State Pattern, Event Sourcing and CQRS, BPMN 2.0, DORA change-failure analysis, and IEEE/ISTQB state transition testing. Keep this body focused on lifecycle ownership and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for transition-table templates, guard-validation patterns, testing coverage matrices, detailed benchmark anchors, and anti-pattern review.

# Selection Rules

Select this capability when **state transitions carry business rules, authorization constraints, external side effects, or audit obligations**. Route elsewhere when: UI loading/empty/error states are the primary concern (use `interaction-state-modeling`); domain events consumed by downstream handlers are the primary concern (use `domain-event-modeling`); business rule guards need detailed extraction from existing code (use `business-rule-extraction`); the implementation of state transition enforcement needs design (use `domain-logic-implementation`).

Select `business-semantic-control-plane` with this capability when workflow states, allowed/forbidden transitions, guard rules, stale memory, or business golden cases must be represented in a task-scoped Business Semantic Pack.

# Risk Escalation Rules

Escalate immediately when: an illegal transition can cause a double charge, duplicate fulfillment, duplicate shipment, inventory corruption, ledger corruption, or regulated-record corruption; a transition can be triggered by an actor who should not have authority; a state has no recovery/failure exit; a transition involves deletion, export, retention, or privacy-relevant behavior; or a state machine change requires a data migration for existing records in states that no longer exist.

# Proactive Professional Triggers

- **Signal:** A status or enum field is added without a transition table. **Hidden risk:** the enum becomes a bag of labels and illegal transitions stay implicit. **Required professional action:** require states, legal transitions, illegal transitions, and enforcement source before code review. **Route to:** `state-machine-modeling`, `domain-object-identification`. **Evidence required:** source of truth, owner, state list, transition table, validation command or report, and rejected display-only interpretation.
- **Signal:** Lifecycle behavior is scattered across services, controllers, jobs, SQL, support scripts, or tests. **Hidden risk:** each entry point enforces a different state model. **Required professional action:** scan writer paths and centralize transition authority or document delegated command boundaries. **Route to:** `business-rule-extraction`, `domain-logic-implementation`, `repository-graph-analysis`. **Evidence required:** writer scan output, delegated caller map, enforcement layer, same-pattern review, and residual bypass risk.
- **Signal:** Project memory or a previous state machine is reused for a new object. **Hidden risk:** stale lifecycle assumptions override current source, migrations, events, or actors. **Required professional action:** verify current code, data, events, tests, and owner before reuse. **Route to:** `project-memory-governance`, `repository-context-map`. **Evidence required:** accepted/rejected memory map, inspected path list, graph freshness, validation output, and unverified areas.
- **Signal:** A transition emits an event or external side effect. **Hidden risk:** retries, rollback, or dual-write failures produce duplicate or ghost effects. **Required professional action:** require committed-state side-effect binding and idempotency design. **Route to:** `domain-event-modeling`, `idempotency-retry-design`, `transaction-consistency`. **Evidence required:** commit boundary, outbox/event handoff, deduplication key, failure-behavior test, and what the test does not prove.
- **Signal:** A state is renamed, removed, split, merged, or newly terminal for stored records. **Hidden risk:** old data, reports, consumers, and rollback cannot interpret the lifecycle. **Required professional action:** require migration and compatibility review. **Route to:** `data-migration-design`, `version-compatibility`, `delivery-release-gate`. **Evidence required:** record mapping, compatibility window, rollback behavior, and validation query.

# Critical Details

- **The most dangerous state machine defect is a missing failure/recovery exit.** A `PROCESSING` state with no `FAILED` or `TIMED_OUT` exit will produce permanently stuck records when the external dependency fails. Every in-progress state must have a timeout trigger and a failure state.
- **Guard evaluation order matters for concurrent transitions.** If two concurrent actors can both trigger a transition, guard evaluation must happen after acquiring the row-level lock or the transition must use optimistic concurrency control.
- **Terminal states require irreversibility enforcement beyond caller convention.** A domain object in a terminal state must not be modifiable by any actor except an explicit, audited recovery or correction workflow.
- **State machine diagrams and transition tables must be versioned alongside the domain code.** The transition table is the authoritative specification and must evolve with implementation, tests, migrations, and events.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 lifecycle routing, ownership, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete state model. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when transition-table shape, guard implementation, all-state/all-transition testing, or benchmark detail is needed. Use [examples/example-output.md](examples/example-output.md) only as an output-shape example, not as a domain template. Do not load references for trivial display-status wording or pure routing work where the output contract is enough.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `if order.status == 'PENDING' or order.status == 'PROCESSING': allow_cancel()` scattered in 6 files | Inconsistent cancellation rules; one file updated, others not; illegal cancel allowed | Single domain method `order.cancel()` enforces the guard; all callers delegate |
| `PROCESSING` state with no `FAILED` or `TIMED_OUT` exit | Stuck records when payment gateway times out; manual DB surgery required | Add `FAILED` state; add scheduler timeout trigger; add support recovery transition |
| Side effect called before transaction commit | External action succeeds while DB rolls back | Emit a post-commit event or outbox record; downstream handler performs the side effect |
| Transition has no guard or audit record | Any actor can trigger it and nobody can reconstruct why | Guard with reasoned denial; audit actor, trigger, old state, new state, and evidence |
| External call retried without idempotency key | Duplicate charge, shipment, notification, or ledger write | Use stable idempotency key tied to transition identity and external effect |
| State machine stored as magic integer | Values lose domain meaning and break when reordered | Store named state values and enforce through domain transition authority |

# Failure Modes

- **Double charge:** `PENDING -> PROCESSING` transition is retried without an idempotency key; the payment provider charges twice while the aggregate records one transition.
- **Stuck in-progress state:** `PROCESSING` has no timeout or failure exit; an external dependency outage leaves records permanently in progress until manual database edits.
- **Illegal terminal transition:** `SHIPPED -> CANCELLED` is not rejected; refund and delivery both complete because terminal-state enforcement lives only in caller convention.
- **Concurrent duplicate side effect:** two actors read the same old state and execute duplicate shipments, charges, or notifications without a row lock or optimistic version check.
- **Swallowed illegal transition:** invalid transition attempts return success or no-op, leaving the object unchanged with no audit event, denial reason, or operator-visible failure.
- **Missing state migration:** a new state is added but existing records, reports, consumers, exports, or old code cannot interpret it during rollout or rollback.
- **Stale graph reuse:** project memory copies a similar workflow's transition table after actors, event consumers, support tools, or migration assumptions changed.
- **Audit/privacy gap:** a privileged deletion, retention, or export transition lacks actor authority, audit fields, and privacy classification, so regulated evidence cannot be reconstructed.

# Output Contract

Return a state machine model with:

- `mode_selected` (new lifecycle, transition change, incident repair, external side effect, migration/versioned state change, or review/test evidence)
- `source_evidence` (domain object source, current code/docs/tests/registry, writer paths, repository graph, project memory, and freshness limits)
- `lifecycle_owner` (business owner, technical owner, aggregate or workflow owner, mutation authority)
- `state_source_of_truth` (field/table/event stream/aggregate state, storage representation, authoritative enforcement layer)
- `states` (all states: name, meaning, terminal/non-terminal)
- `transition_table` (per transition: from, to, trigger, actor, guard, side effects, emitted event, audit record)
- `transition_authority` (which command, service, aggregate method, job, or operator workflow may execute each transition)
- `guard_evidence` (rule owner, input facts, reason codes, ordering, and denied behavior)
- `illegal_transitions` (explicitly listed; enforcement method)
- `timeout_triggers` (per in-progress state: duration, actor, resulting state, side effects)
- `recovery_transitions` (per failure/stuck state: trigger, actor, resulting state)
- `side_effect_commit_boundary` (when persistence commits, when events/outbox publish, and when downstream side effects run)
- `event_and_audit_contract` (event names, payload/audit fields, privacy classification, retention or compliance note when relevant)
- `idempotency_design` (per transition with external effect: idempotency key, deduplication method)
- `concurrency_controls` (row-level lock vs. optimistic concurrency; where applied)
- `migration_and_versioning` (existing record mapping, compatibility window, rollback behavior when states change)
- `state_machine_diagram` (textual notation or Mermaid stateDiagram-v2)
- `graph_and_memory_decisions` (current writers/consumers confirmed, reused patterns accepted or rejected, stale memory caveats)
- `business_semantic_workflow_record` when BSP is selected: workflow id, states, allowed/forbidden transitions, guard rule ids, actor authority, evidence classes, memory/graph selector limits, and residual semantic risk
- `changed_state_to_validation_map` (each state, transition, guard, event, migration, and side effect mapped to a validator/test or residual risk)
- `handoff_boundaries` (what belongs to object identification, business rules, events, idempotency, permissions, migration, release, or testing)
- `evidence_limits` (uninspected code paths, data, migrations, events, runtime behavior, tests not run, or graph freshness limits)

## BSP.workflows Write Contract

When BSP is selected, each workflow must be writable to `BSP.workflows` with:

- workflow id, object or aggregate owner, and source of truth
- `states`, allowed transitions, and forbidden transitions
- guard rule ids, actor or mutation authority, side effects, emitted events, and audit fields
- source paths, evidence class, graph/memory selector status, and freshness limits
- `validation_map` entries for allowed transitions, forbidden transitions, guard rules, side effects, and migration/compatibility claims
- residual risk for uninspected writers, stored-record compatibility, or missing owner review

State modeling consumes BSP task intent, business objects, business rules, code mapping, memory projection, graph selectors, validation map, and context control when present. Missing states, forbidden transitions, guard rule ids, actor authority, or writer coverage blocks workflow closure unless recorded as residual risk with owner/test handoff; graph and memory remain selector evidence, not BSP `FACT`.

# Evidence Contract

- **Repository evidence:** name the domain files, models, services, jobs, SQL, event schemas, tests, docs, registry entries, and support/admin tools inspected; if no concrete implementation exists, state that the output is a design contract rather than verified source behavior.
- **Graph evidence:** identify state writers, readers, event producers/consumers, job triggers, support tools, migration scripts, and any same-pattern lifecycle code that could bypass the transition authority.
- **Memory evidence:** project memory, prior state machines, and previous agent trajectories are suggestions only until current source, tests, data, and owners confirm they still apply.
- **Execution evidence:** map lifecycle decisions to unit, integration, state-transition, invalid-transition, timeout/recovery, migration, event/audit, concurrency, or regression tests, or explicitly mark unrun validation and residual risk.
- **Boundary evidence:** every transition states what it owns and what it hands off to rules, authorization, idempotency, events, migrations, release, or test execution.
- **Closure evidence:** name boundaries inspected, validation commands or report artifacts with exit codes, what evidence proves, what evidence does not prove, validation freshness, residual risk, rollback or reroute note, and the next handoff gate.

# Benchmark Coverage

Professional state-machine modeling covers state exhaustiveness, transition legality, actor authority, guard rule ownership, side-effect commit boundaries, event/audit contracts, idempotency, concurrency, timeout/recovery, migration/compatibility, repository graph freshness, memory freshness, and validation mapping. A diagram or enum update without enforcement and evidence is incomplete.

# Routing Coverage

Route here when the primary question is lifecycle state authority, allowed/illegal transition design, recovery/cancel/timeout behavior, or state-change side effects. Hand off to `domain-object-identification` for object and aggregate ownership, `business-rule-extraction` for guard details, `permission-boundary-modeling` or `authentication-authorization` for actor authority, `domain-event-modeling` for event contracts, `idempotency-retry-design` and `transaction-consistency` for retry/commit safety, `data-migration-design` and `version-compatibility` for persisted state changes, `quality-test-gate` or `regression-testing` for executable proof, and `delivery-release-gate` when production rollout or rollback is affected.

# Quality Gate

The state machine model is complete only when:

1. All states are enumerated including terminal and failure/recovery states.
2. Transition table has actor, guard, side effect, event, and audit record for every transition.
3. All illegal transitions are explicitly listed with enforcement mechanism.
4. Every in-progress state has at least one timeout/failure exit.
5. Every transition with an external effect has an idempotency key design.
6. Side effects are tied to committed transitions (post-commit, not pre-commit).
7. Concurrency control is specified for states that multiple actors can transition concurrently.
8. Transition table is versioned alongside the domain code.
9. Test plan covers: all states, all valid transitions, all invalid transitions, timeout paths, recovery paths.
10. Data migration plan exists if new states are added to objects with existing production records.
11. A new or changed status/enum without forbidden transition coverage blocks closure; allowed-path tests alone do not prove workflow safety.
11. Selected mode, source evidence, lifecycle owner, source of truth, and transition authority are explicit.
12. Repository graph, project memory, and prior execution trajectory evidence are confirmed against current source or marked stale/not verified.
13. Every changed state, transition, guard, side effect, event, audit field, migration, and permission branch maps to validation evidence or named residual risk.
14. Handoff boundaries and evidence limits are stated so lifecycle modeling is not over-claimed as full rule extraction, event implementation, migration execution, release approval, or test certification.

# Used By

- domain-impact-modeler
- backend-change-builder
- quality-test-gate

# Handoff

Hand off to `domain-object-identification` when object, aggregate, or lifecycle ownership is unresolved; `business-rule-extraction` for guard condition detail; `permission-boundary-modeling` or `authentication-authorization` for actor authority; `domain-event-modeling` for event and audit contracts; `domain-logic-implementation` and `backend-change-builder` for enforcement implementation; `idempotency-retry-design`, `transaction-consistency`, or `concurrency-control` for retry, commit, and concurrent transition safety; `data-migration-design` and `version-compatibility` for persisted state changes; `quality-test-gate` and `regression-testing` for validation evidence; `security-privacy-gate` when transitions affect regulated data or privileged actions; and `delivery-release-gate` when rollout, rollback, or production migration is affected.

# Completion Criteria

The capability is complete when **every state, legal transition, illegal transition, guard, actor authority, side effect, event, audit record, timeout exit, recovery transition, idempotency design, migration/versioning impact, and validation obligation is explicit, evidence-limited, and implementable without scattered conditional status checks**.
