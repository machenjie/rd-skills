---
name: domain-event-modeling
description: Models domain events as durable past-tense facts with explicit producer, transaction boundary, payload contract, schema version, idempotency key, ordering expectation, retry behavior, and audit impact.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "17"
changeforge_version: 0.1.0
---

# Mission

Define every domain event as a **durable, named, past-tense fact** with a precise producer, transaction boundary, payload contract, schema version, idempotency key, ordering expectation, retry policy, dead-letter strategy, audit significance, and validation path, so asynchronous consumers can reconstruct what happened without querying mutable state or trusting stale project memory.

# When To Use

Use this capability when a change emits a new event from a domain aggregate, bounded context, or service; changes an existing event name, payload, schema version, or compatibility promise; adds a producer, consumer, projection, read model, event-sourced aggregate, saga step, audit record, or integration event; defines outbox-based durable publication; or changes retry, replay, ordering, DLQ, privacy, or consumer ownership rules for a domain fact.

# Do Not Use When

Do not use this capability for incidental logs, metrics, traces, analytics clicks, pageviews, in-process callbacks without durability, notification payload formatting without domain state meaning, broker topology alone, or background job execution alone. Use `message-queue-design` for broker mechanics, `async-job-design` for worker execution, `event-driven-architecture` for multi-service flow topology, and `state-machine-modeling` when the transition that produces the event is not yet defined.

# Stage Fit

Use during planning when domain facts may cross an aggregate, service, bounded context, or audit boundary. Use during coding and refactoring when producers, outbox writes, event schemas, generated contracts, consumer handlers, idempotency stores, partition keys, or DLQ policies change. Use during debugging, bug-fix, code-review, testing, and release review when duplicate delivery, out-of-order delivery, schema compatibility, replay, privacy fan-out, or lost-event rollback risk needs evidence. Hand off when queue infrastructure, transaction consistency, security review, release rollout, or observability readiness becomes the primary decision.

# Non-Negotiable Rules

- **Events are named as past-tense facts, not commands.** `OrderPlaced` and `InvoicePaid` are facts. `PlaceOrder` and `ProcessPayment` are commands and must not be published as events.
- **Publish only after the originating state change commits.** Direct dual-write patterns such as `save(); publish();` are rejected unless a reviewed exception proves equivalent durability. Prefer transactional outbox, CDC, or another post-commit relay.
- **Consumers are idempotent by design.** Each consumer needs a durable idempotency key, duplicate handling rule, and validation evidence for duplicate delivery or replay.
- **Payload carries stable identifiers and self-describing facts.** Required fields include event id, event type, aggregate type, aggregate id, occurred-at timestamp, schema version, producer, and domain-meaningful facts. Payloads that contain only an id force mutable callback reads and are incomplete.
- **Schema evolution is explicit.** Additive compatible changes need a version bump and registry update; breaking changes need a new major version, migration window, consumer inventory, and rollback path.
- **Ordering assumptions are declared.** Per-aggregate ordering requires a partition/message-group key aligned to the aggregate boundary. Global ordering must not be assumed.
- **Every consumer owns retry, DLQ, replay, and alert behavior.** A failing consumer must not drop the event or block the main flow indefinitely.
- **Sensitive payload data is minimized and authorized.** Durable fan-out can expose PII, financial, health, credential, tenant, or object identifiers to consumers that should not receive them.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New domain event | New event name, producer, aggregate fact, integration event, audit event, projection trigger, or event-sourced fact. | Prove the fact meaning, producer boundary, payload contract, consumer need, and durable publication path. | Transition source, producer method/command, event name rationale, outbox/commit boundary, initial consumer inventory. | `domain-impact-modeler`, `state-machine-modeling`, `transaction-consistency` | Skip broker tuning and worker scaling until the fact contract is stable. |
| Event schema evolution | Field added, removed, renamed, retyped, repurposed, versioned, or moved between topics/channels. | Preserve old producers, old consumers, generated contracts, replay, and rollback behavior. | Old/new schema diff, compatibility class, registry mode, consumer inventory, migration and rollback plan. | `version-compatibility`, `contract-testing`, `consumer-impact-analysis` | Skip in-place breaking edits without dual publish or new event type. |
| Producer transaction boundary | State write plus event publish, outbox row, CDC relay, unit-of-work hook, or post-commit handler changes. | Prevent ghost events, lost events, hidden side effects, and rollback mismatch. | Transaction boundary, outbox/relay ownership, failure path, retry/duplicate behavior, lost-event recovery test. | `transaction-consistency`, `data-side-effect-flow-tracing`, `event-driven-architecture` | Skip direct publish from domain mapper, controller, or best-effort hook. |
| Consumer safety and replay | New consumer, projection rebuild, DLQ replay, retry policy, idempotency key, partition key, or handler side effect changes. | Make duplicate, delayed, replayed, and out-of-order delivery harmless or explicitly blocked. | Consumer side-effect map, dedupe store, replay-safe classification, ordering rule, DLQ owner and runbook. | `idempotency-retry-design`, `quality-test-gate`, `message-queue-design` | Skip "consumer will handle it" claims without a durable dedupe rule. |
| Saga or audit event | Event participates in workflow choreography, compensation, audit retention, compliance, or immutable history. | Protect compensation semantics, audit integrity, temporal ordering, and retention commitments. | Saga role, timeout/compensation event, audit fields, retention owner, reconciliation path. | `transaction-consistency`, `reliability-observability-gate`, `release-rollback` | Skip if the transition itself is still undefined; route first to `state-machine-modeling`. |
| Sensitive event payload | Event contains tenant, object, permission, PII, financial, health, credential, or regulated audit fields. | Minimize payload, restrict consumers, preserve authorization boundaries, and state residual risk. | Data classification, allowed consumers, redaction/tokenization decision, retention, privacy validation. | `security-privacy-gate`, `permission-boundary-modeling`, `quality-test-gate` | Skip fan-out of raw sensitive fields unless every consumer is authorized and named. |

# Industry Benchmarks

Anchor against Domain-Driven Design and Event Storming for fact discovery, Transactional Outbox and CDC for post-commit durability, Saga and CQRS/Event Sourcing for workflow and projection semantics, CloudEvents and AsyncAPI for event contracts, Apache Avro or schema registry compatibility for evolution, Kafka/Pulsar/NATS/SQS delivery semantics for ordering and replay, and OWASP API Security plus privacy-by-design constraints for fan-out data exposure. Keep this body focused on routing, evidence, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for event type classification, outbox SQL, schema evolution, idempotency, retry/DLQ, ordering, privacy, graph-memory-execution coupling, and validation matrices.

# Selection Rules

Select this capability when **domain fact semantics and event contracts** are primary. Adjacent routing:

- Prefer `state-machine-modeling` when the state transition that produces the event is not defined.
- Prefer `event-driven-architecture` when topology, asynchronous flow, replay operations, lag, or cross-service consistency is primary.
- Prefer `message-queue-design` when broker, topic, queue, binding, consumer group, or partition infrastructure is primary.
- Prefer `async-job-design` when the concern is background execution rather than domain fact communication.
- Prefer `transaction-consistency` when distributed transaction coordination, outbox correctness, or saga rollback is primary.
- Prefer `integration-change-builder` when implementing a cross-service consumer is the main work.

# Risk Escalation Rules

Escalate when duplicate events can cause payment, ledger, entitlement, notification, inventory, or order state to happen twice; out-of-order events can corrupt a projection or state machine; a lost event can leave a saga stuck; a schema change has unknown consumers or no migration path; an event payload fans out sensitive data without authorization; DLQ depth or event age exceeds the operational threshold; audit retention, tenant boundary, or object permission semantics are unclear.

# Proactive Professional Triggers

- **Signal:** event name is imperative, future-tense, or ambiguous. **Hidden risk:** consumers treat unconfirmed intent as a durable fact. **Required professional action:** rename to a past-tense fact or route to command/state modeling. **Route to:** `state-machine-modeling`, `domain-impact-modeler`. **Evidence required:** producing transition and fact semantics.
- **Signal:** producer saves state and publishes outside the same commit boundary. **Hidden risk:** ghost event on rollback or lost event on broker failure. **Required professional action:** require outbox, CDC, post-commit relay, or documented equivalent. **Route to:** `transaction-consistency`, `data-side-effect-flow-tracing`. **Evidence required:** transaction boundary, relay owner, failure-path validation.
- **Signal:** payload contains only an id or requires consumer callback to current state. **Hidden risk:** consumers reconstruct the wrong historical fact after state changes. **Required professional action:** make payload self-describing or document a safe exception. **Route to:** `dto-schema-design`, `contract-testing`. **Evidence required:** payload field semantics, examples, compatibility check.
- **Signal:** schema changes or consumer additions rely on memory, diagrams, or graph assumptions without current source confirmation. **Hidden risk:** hidden consumers break or stale topology drives the wrong migration. **Required professional action:** inspect current producers, consumers, schemas, generated artifacts, tests, and registry/config. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected memory, inspected paths, unknown consumers.
- **Signal:** consumer retry, DLQ, replay, or idempotency is described but no owner or validation exists. **Hidden risk:** permanent stuck events, repeated side effects, or unrecoverable poison messages. **Required professional action:** define durable dedupe, DLQ owner, replay runbook, and tests. **Route to:** `idempotency-retry-design`, `quality-test-gate`, `reliability-observability-gate`. **Evidence required:** duplicate/replay/DLQ validation and residual risk.
- **Signal:** payload includes tenant, object, permission, PII, financial, audit, health, or credential data. **Hidden risk:** durable fan-out leaks data or violates authorization boundaries. **Required professional action:** classify data, minimize payload, restrict consumers, and record residual privacy risk. **Route to:** `security-privacy-gate`, `permission-boundary-modeling`. **Evidence required:** allowed consumer list, redaction/tokenization decision, retention rule.

# Critical Details

Domain events are not log messages, notifications, or commands. Precision failures:

- **Dual-write without outbox.** If the database commits and broker publish fails, the event is lost; if the broker publish succeeds and the database rolls back, consumers observe a ghost fact.
- **Payload minimalism.** `{ "orderId": "123" }` is not a complete historical fact when consumers need amount, status, actor, tenant, or previous value semantics.
- **Schema drift.** A field added without versioning or registry compatibility can fail strict consumers or silently corrupt lenient ones.
- **Ordering not partition-aligned.** Per-order ordering cannot hold when the partition key is a random event id or unrelated customer id.
- **Replay without side-effect classification.** Projection rebuilds must not resend emails, recapture payment, duplicate ledger entries, or grant entitlements again.
- **Audit event without retention/actor.** A durable audit fact without actor, subject, source, timestamp, or retention owner is not an audit record.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `publish(event)` inside `try { db.save(); publish(); }` without outbox | Ghost events on rollback; lost events on broker failure |
| Event named `CreateOrder` | Command, not a fact; consumers act on unconfirmed intent |
| Payload only contains `orderId` | Consumer must query mutable state and loses historical context |
| No idempotency key | Duplicate delivery can charge, notify, or write twice |
| Schema field renamed without version bump | Consumers deserialize wrong data or nulls |
| Notification event carries full SSN or raw account number | Durable data fan-out to unauthorized consumers |
| DLQ not defined or unowned | Saga or projection can remain stuck indefinitely |
| Partition key unrelated to aggregate id | Events for one aggregate arrive out of order |

# Failure Modes

- Duplicate `PaymentCaptured` event processed twice because the consumer has no durable idempotency record.
- `OrderCancelled` arrives before `OrderPlaced` due to partition-key mismatch and projection state becomes invalid.
- Producer emits `InvoiceIssued.v1` before transaction commit; rollback leaves downstream accounting with a non-existent invoice.
- Producer commits state but broker publish fails; saga waits forever for an event that was never emitted.
- Field `amount` is renamed to `totalAmount` without versioning; consumers calculate zero or reject the message.
- PII in event payload reaches analytics, logs, or low-trust consumers outside the permission boundary.
- DLQ accumulates unprocessed events for days because no owner, alert, or replay tool exists.
- Event-sourced aggregate replay takes unacceptable time because snapshot and replay constraints were not designed.
- Saga compensation event is missing; payment capture succeeds while inventory reservation fails permanently.
- Previous project memory names an old consumer, but the current repository contains a new hidden consumer not included in compatibility review.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, boundaries, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete event catalog, producer change, consumer addition, schema evolution, outbox path, idempotency rule, ordering policy, retry/DLQ policy, replay plan, or audit/privacy classification. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when event type classification, outbox SQL, CloudEvents/AsyncAPI shape, schema compatibility, idempotency strategy, retry/DLQ matrix, ordering/partition design, saga/audit/privacy detail, graph-memory-execution coupling, or event-to-validation mapping is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing, metadata-only edits, or event-free changes.

# Output Contract

Return an event catalog with:

- `mode_selected`: new domain event, event schema evolution, producer transaction boundary, consumer safety and replay, saga or audit event, or sensitive event payload.
- `boundaries_inspected`: producer paths, consumer paths, schemas, registry/config, outbox/relay, generated contracts, tests, runbooks, docs, and prior memory accepted or rejected.
- `source_evidence`: current-source observations that prove the event topology and contract; do not rely on diagrams or memory alone.
- `graph_memory_trajectory_judgment`: repository graph, project memory, and execution trajectory facts accepted, rejected, or left unknown with freshness limits.
- `event_catalog`: event name, event type, aggregate, producer, consumers, owner, and lifecycle status.
- `event_name` / `event_type`: past-tense PascalCase name and namespaced versioned type such as `billing.invoice.InvoiceIssued.v1`.
- `fact_semantics`: what happened, when it becomes true, and which command/transition confirms it.
- `producer`: service, aggregate, method/command, owner, and emission trigger.
- `commit_boundary`: same transaction outbox, CDC, post-commit relay, or documented exception plus failure behavior.
- `payload_schema`: fields, types, required/optional status, examples, semantics, stable identifiers, tenant/object identifiers, and sensitive data classification.
- `schema_version`: current version, compatibility mode, registry location, old/new behavior, and migration or rollback path.
- `consumer_inventory`: known consumers, subscription mechanism, side effects, owner, idempotency method, DLQ owner, and unknown consumer risk.
- `idempotency_key`: producer event id, aggregate sequence, natural dedupe key, or consumer-specific key and storage boundary.
- `ordering_expectation`: none, per aggregate, per partition, or stronger exception with partition/message-group key strategy.
- `retry_policy` and `dead_letter_strategy`: max retries, backoff, poison-message handling, DLQ topic, alert threshold, replay tool, and owner.
- `replay_safety`: replay-safe, replay-gated, or replay-blocked classification per consumer.
- `audit_impact` and `privacy_classification`: retention, actor/source fields, regulated data, redaction/tokenization, and allowed consumers.
- `saga_role`: none, trigger, step, compensation, timeout, reconciliation, or audit checkpoint.
- `event_to_validation_map`: each producer, schema, consumer, idempotency rule, ordering rule, retry/DLQ policy, replay path, and privacy decision mapped to validation.
- `reuse_and_placement_rationale`: existing event/schema/outbox/consumer reused or rejected; why no speculative event or new service was added.
- `behavior_preservation`: old producers, old consumers, old schemas, old topics/channels, old replay behavior, and old runbooks that remain valid.
- `validation_evidence`: commands, tests, validators, reports, fixtures, contract checks, replay checks, or explicit not-verified disclosure with exit code or artifact.
- `handoff_boundaries`: decisions moved to queue design, event-driven architecture, transaction consistency, security/privacy, reliability, release, or human review.
- `evidence_limits`: what evidence proves, what it does not prove, unknown consumers, untested replay scale, residual risk, owner, and next gate.

# Evidence Contract

Close a domain event plan only when these answers are concrete:

- **Boundaries inspected:** name the producer files, consumer files, schema files, registry/config, outbox/relay, generated artifacts, tests, docs, runbooks, and project memory checked. If no implementation exists, say so.
- **What evidence proves:** state which current-source facts prove the event meaning, commit boundary, schema, consumer inventory, idempotency, ordering, retry/DLQ, replay, audit, and privacy decisions.
- **What evidence does not prove:** call out unknown consumers, production broker behavior, large replay, partition skew, privacy fan-out outside inspected code, generated artifact drift, or untested rollback.
- **Validation evidence:** include command names, validator names, tests, reports, fixtures, artifacts, and exit code/result. Do not claim event readiness from design reasoning alone.
- **Reuse / placement rationale:** identify the existing event, schema, outbox, consumer, registry, or reference reused; justify any new event type or new file placement.
- **Behavior preservation:** state how old producers, old consumers, old schemas, old replay/DLQ procedures, and rollback behavior remain valid or are migrated.
- **Residual risk:** name the remaining event-loss, duplicate, ordering, compatibility, privacy, audit, or operational risk and its owner.
- **Next gate:** route unresolved broker mechanics, transaction consistency, consumer implementation, security/privacy, reliability/observability, release rollout, or human domain approval to the correct gate.

# Benchmark Coverage

This capability covers domain-event naming, fact semantics, producer commit boundary, outbox/CDC durability, payload contract, schema versioning, consumer inventory, idempotency, ordering, retry/DLQ, replay safety, saga/audit role, privacy fan-out, and event-to-validation mapping. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for the detailed benchmark matrix and implementation patterns.

# Routing Coverage

Routes from `domain-impact-modeler`, `state-machine-modeling`, `event-driven-architecture`, `data-side-effect-flow-tracing`, `version-compatibility`, `consumer-impact-analysis`, `dto-schema-design`, `nosql-database`, and `use-case-modeling` should arrive here when event fact semantics or event contract evidence is primary. Route away when infrastructure, implementation, transaction, security, reliability, release, or state-transition ownership is primary.

# Quality Gate

The event catalog is complete only when:

1. Mode selected, inspected boundaries, source evidence, graph-memory-trajectory judgment, and evidence limits are recorded.
2. All event names are past-tense domain facts with explicit fact semantics and no command disguised as an event.
3. Producer, owner, triggering transition, and commit boundary are identified; outbox/CDC/equivalent durability is specified.
4. Payload is self-describing with stable identifiers, schema version, examples, and no unexplained mutable callback requirement.
5. Schema registry or compatibility mode is declared; breaking changes have migration, dual-publish/new-type, and rollback behavior.
6. Consumer inventory includes side effects, owners, subscription mechanism, idempotency strategy, DLQ owner, and unknown consumer risk.
7. Idempotency key and durable dedupe behavior are specified per consumer.
8. Ordering expectation and partition/message-group key are declared, or "none guaranteed" is explicit.
9. Retry, backoff, poison-message, DLQ, alert, replay tool, and runbook are assigned.
10. Replay safety is classified for every consumer, especially notifications, payments, ledgers, entitlements, webhooks, and audit sinks.
11. Saga role, compensation event, timeout, reconciliation, and audit retention are defined where applicable.
12. Tenant, object, permission, PII, financial, health, credential, and audit data are classified and restricted to allowed consumers.
13. Existing producers, consumers, schemas, topics/channels, replay procedures, and rollback behavior are preserved or migrated.
14. Event-to-validation map covers duplicate delivery, out-of-order delivery, schema compatibility, DLQ routing, replay, privacy, and rollback.
15. Handoff boundaries and residual risk owner are explicit before release.

# Used By

- domain-impact-modeler
- integration-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `state-machine-modeling` when transition semantics are undefined; `event-driven-architecture` for cross-service topology, replay operations, lag, and eventual-consistency UX; `integration-change-builder` for consumer implementation; `message-queue-design` for broker topology and infrastructure; `transaction-consistency` for outbox/saga correctness; `security-privacy-gate` for sensitive payload and permission-boundary review; `reliability-observability-gate` for production readiness; and `release-rollback` when schema or consumer rollout needs staged release control.

# Completion Criteria

The capability is complete when every domain event has a past-tense name, fact semantics, current-source evidence, producer and post-commit publication path, self-describing schema version, consumer inventory, idempotency key, ordering guarantee, retry and DLQ owner, replay classification, audit/privacy classification, validation map, behavior-preservation statement, residual-risk owner, and next gate for unresolved work, with no payload minimalism, no unreviewed dual-write pattern, no unknown sensitive fan-out, and no unowned DLQ.
