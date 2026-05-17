---
name: domain-event-modeling
description: Models domain events with producer, consumer, payload, idempotency, ordering, retry behavior, and audit impact.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "17"
changeforge_version: 0.1.0
---

# Mission

Define every domain event as a **durable, named, past-tense fact** with a precise producer, transaction boundary, payload contract, schema version, idempotency key, ordering expectation, retry policy, dead-letter strategy, and audit significance — so that asynchronous consumers can always reconstruct what happened without querying mutable state.

# When To Use

Use this capability when a change: emits a new event from a domain aggregate, bounded context, or service; changes an existing event's name, payload, or schema version; adds a new consumer to an existing event stream; defines retry or dead-letter handling for an integration event; designs an outbox-based durable event emission; implements a projection, read model, or event-sourced aggregate; designs an event-driven saga or process manager; or models audit-significant state transitions.

# Do Not Use When

Do not use this capability for: incidental application log messages that are not domain facts; user analytics events (click, pageview, funnel step) that have no domain state meaning; metric counters or telemetry spans; internal in-process callbacks or pub-sub with no durability; or transport infrastructure design without a business fact being communicated — use `message-queue-design` for broker topology.

# Non-Negotiable Rules

- **Events are named as past-tense facts, not commands.** `OrderPlaced` ✓, `InvoicePaid` ✓. `PlaceOrder` ✗, `ProcessPayment` ✗. An event describes what happened, after it happened. A command names intent before the fact is confirmed.
- **An event is published only after the originating state change commits.** Publishing before commit creates ghost events — the consumer acts on something that may be rolled back. Use the Transactional Outbox Pattern: write the event to an outbox table in the same transaction as the state change; a relay process reads the outbox and publishes. No direct publish inside `try { save(); publish(); }` blocks.
- **Consumers must be idempotent.** Every consumer must handle duplicate delivery of the same event without corrupting state. The idempotency key must be specified in the event schema (`eventId` UUID + aggregate `type` + `aggregateId` forms a natural key). Consumers must use upsert, conditional update, or event-log deduplication.
- **Payload carries stable identifiers and self-describing facts.** Consumers must not be forced to call back to the producer to understand what happened. Required payload fields: `eventId` (UUID), `eventType` (namespaced string), `aggregateType`, `aggregateId`, `occurredAt` (ISO 8601 UTC), `schemaVersion`, and domain-meaningful fields. Avoid payload minimalism ("only the ID") — consumers that need the previous state have no way to get it after the fact.
- **Sensitive data is excluded or encrypted in payloads.** Events are durable and fan out to multiple consumers. PII, financial account numbers, health data, and credentials must not be in event payloads in cleartext. Tokenize or reference; include only what consumers legitimately need.
- **Schema versioning follows additive-only evolution for minor versions.** Adding optional fields is backward-compatible. Removing fields, renaming fields, or changing field semantics is a breaking change requiring a new major version. Consumers must be designed to handle forward-compatible payloads (`additionalProperties` ignored). Use CycloneDX Schema Compatibility or **Apache Avro / Confluent Schema Registry** with compatibility mode `FORWARD`.
- **Ordering assumptions are declared explicitly.** Per-aggregate ordering (all events for one `orderId` are ordered) can be provided by a Kafka partition key on `aggregateId`. Global ordering cannot be guaranteed at scale. If a consumer requires per-aggregate ordering, the partition key strategy must be specified. If ordering is not guaranteed, consumers must be designed to handle out-of-order delivery.
- **Dead-letter queues are defined for every event consumer.** A consumer that fails must not drop the event and must not block the main queue forever. Define: max retry count, retry backoff policy, dead-letter queue (DLQ) destination, and alerting threshold for DLQ depth. DLQ events require manual inspection, replay tooling, and an ownership process.

# Industry Benchmarks

Anchor against: **Domain-Driven Design (Evans, 2004; Vernon, 2013)** — domain events as first-class modeling artifacts; aggregate as consistency boundary for event emission. **Event Storming (Brandolini, 2013)** — collaborative workshop technique for discovering domain events, commands, policies, read models, and aggregates. **Transactional Outbox Pattern (Microservices.io)** — canonical solution for reliable event publication after database commit. **Saga Pattern** — distributed transaction coordination via event-driven choreography or orchestration; Microservices Patterns (Richardson, 2018). **Apache Kafka** — de-facto standard for high-throughput event streaming; partition-key-based ordering; consumer groups; log compaction for entity events. **Apache Pulsar** — multi-topic subscriptions, built-in geo-replication, tiered storage. **NATS JetStream** — lightweight, at-least-once persistent messaging. **CloudEvents v1.0** (CNCF) — open specification for event metadata: `id`, `source`, `type`, `specversion`, `time`, `datacontenttype`, `dataschema`. Widely adopted for event interoperability. **Apache Avro / Confluent Schema Registry** — binary event serialization with schema evolution enforcement; compatibility modes: BACKWARD, FORWARD, FULL. **AsyncAPI 3.0** — OpenAPI equivalent for event-driven APIs; documents channels, messages, bindings, and schema. **CQRS + Event Sourcing (Fowler, 2005; Young, 2010)** — complete event history as source of truth; projection rebuilds; temporal queries. **Debezium** — change data capture (CDC) for database-to-event stream conversion. **OWASP API Security Top 10** — events are APIs; A01 Broken Object Level Authorization applies to event payload access. **ISO 8601** — all event timestamps in UTC, full precision (`2024-01-15T09:30:00.000Z`).

### Domain Event Type Classification

| Event class | Description | Durability | Fan-out | Schema contract |
| --- | --- | --- | --- | --- |
| **Domain Event** | Fact within a bounded context; internal to domain | High (outbox) | Internal consumers | Versioned, stable |
| **Integration Event** | Fact shared across bounded context boundaries | High (message broker) | External consumers | Public, versioned, backward-compatible |
| **Notification Event** | Triggers a user or operator notification; no state change | Medium (MQ/webhook) | Notification service | Payload minimal; PII-sensitive |
| **Audit Record** | Immutable compliance record (who did what, when, from where) | Highest (append-only store) | Audit log | Immutable; no delete |
| **Analytics Event** | Funnel/behavioral tracking; no domain state | Low-medium | Analytics platform | Schema flexible; separate pipeline |
| **CDC Event** | Database change captured by Debezium/binlog | Medium | Data warehouse, search | Auto-generated; schema from DB |
| **Saga Step Event** | Intermediate saga state; compensating transaction trigger | High | Saga orchestrator/coordinator | Tied to saga schema version |
| **Command** (not an event) | Intent before a fact is confirmed | N/A — rejected | N/A | Never publish as "event" |

### Outbox Pattern Implementation

```sql
-- Outbox table (co-located in the same transactional database as the domain state):
CREATE TABLE outbox_events (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type   TEXT        NOT NULL,           -- e.g. 'order.placed.v1'
  aggregate_id TEXT        NOT NULL,           -- partition key candidate
  payload      JSONB       NOT NULL,           -- full CloudEvents-compatible body
  occurred_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at TIMESTAMPTZ,                    -- NULL = not yet published
  attempts     INT         NOT NULL DEFAULT 0
);

-- State change + event written atomically (no dual-write):
BEGIN;
  UPDATE orders SET status = 'PLACED', updated_at = now() WHERE id = $1;
  INSERT INTO outbox_events (event_type, aggregate_id, payload)
    VALUES ('order.placed.v1', $1, $payload);
COMMIT;

-- Relay process (polling or WAL-based CDC):
SELECT * FROM outbox_events WHERE published_at IS NULL ORDER BY occurred_at LIMIT 100;
-- Publish to Kafka / Pulsar / SNS → on success:
UPDATE outbox_events SET published_at = now() WHERE id = $event_id;
```

### Idempotency Key Design

| Strategy | Suitable when | Implementation |
| --- | --- | --- |
| `eventId` UUID (producer-assigned) | All cases; canonical key | Consumer: `INSERT ... ON CONFLICT (event_id) DO NOTHING` |
| `aggregateId` + `eventSequenceNumber` | Event-sourced aggregates with monotonic sequence | Consumer: reject events with lower or equal sequence |
| `aggregateId` + `eventType` + `occurredAt` | CDC / low-frequency events | Risky for high-frequency; clock skew can cause duplicates |
| Correlation ID passed from upstream | Saga compensation events | Must be preserved through all downstream events |

### Schema Evolution Rules

| Change type | Compatibility | Required action |
| --- | --- | --- |
| Add optional field with default | ✅ Backward-compatible | Minor version bump; update schema registry |
| Add required field | ❌ Breaking | New major version; migrate producers + consumers |
| Remove field | ❌ Breaking | New major version; deprecation period (≥ 2 sprints) |
| Rename field | ❌ Breaking | New major version; alias old name in transition period |
| Change field type | ❌ Breaking | New major version |
| Reorder fields (Avro binary) | ❌ Breaking | New major version |
| Change field semantics (same name, new meaning) | ❌ Breaking — most dangerous | New event type name; do not reuse the name |

### Retry and Dead-Letter Policy

```
Consumer retry policy (example: Kafka consumer group):

Max retries: 3 (configurable per event type and criticality)
Backoff: exponential with jitter: 1s, 4s, 16s
After max retries:
  → Publish to dead-letter topic: <original-topic>.DLQ
  → Emit alert when DLQ depth > threshold (e.g. > 10 msgs, or > 5 mins age)
  → DLQ events require:
      - Manual inspection workflow (runbook link in event metadata)
      - Replay tooling that re-publishes from DLQ to original topic
      - Ownership assignment (which team owns the DLQ for this event type)

Permanent failures (schema mismatch, deserialization error):
  → Move to <topic>.POISON queue immediately (no retries)
  → Alert immediately
  → Do NOT retry deserialization errors — they will always fail
```

# Selection Rules

Select this capability when **domain facts cross aggregate or service boundaries, drive asynchronous behavior, or require durable publication**. Adjacent routing:

- Prefer `state-machine-modeling` when the state transitions that produce events are not yet defined.
- Prefer `message-queue-design` when broker topology, queue mechanics, consumer group design, and infrastructure are primary.
- Prefer `async-job-design` when asynchronous work execution (jobs, queues, workers) is primary rather than domain fact communication.
- Prefer `integration-change-builder` for the implementation of cross-service event consumers.
- Prefer `transaction-consistency` when distributed transaction coordination and rollback strategies are the main concern.

# Risk Escalation Rules

Escalate when: duplicate events can cause a payment, notification, ledger entry, or order to be processed twice; out-of-order events can produce incorrect projections or stale read models; a lost event would leave a saga stuck without a compensating transaction trigger; a schema change would break consumers with no migration path and no consumer registry; an event payload contains PII or financial data that fans out to consumers without authorization controls; DLQ depth is growing and events older than 24 hours are unprocessed; a Saga step has no compensation event defined.

# Critical Details

Domain events are not log messages, not notifications, and not commands. Precision failures:

- **Dual-write without outbox.** `save(); publish();` — if the network call to the broker fails after the database commit, the event is lost. If the broker call succeeds but the database commit fails (rolled back), the event is a ghost. The Outbox Pattern is not optional for reliable event-driven architectures.
- **Payload minimalism anti-pattern.** Emitting only `{ eventId, aggregateId }` and expecting consumers to fetch current state loses the historical fact. By the time the consumer fetches the state, it may have changed again. Event payloads must carry enough facts to make the event self-describing.
- **Event as command.** `ProcessRefund` as an "event" is not a fact — it's a command disguised as an event. When published on an event bus, every subscriber treats it as a fact that happened. If the refund has not yet been processed, the event is misleading. Domain events communicate what did happen, not what should happen.
- **Schema drift.** A producer adds a new field without incrementing `schemaVersion`. Consumers that deserialize strictly fail. Consumers that deserialize leniently silently ignore the new field. Neither is correct. Every schema change, even "just a new optional field," must be accompanied by a `schemaVersion` increment and registry update.
- **Ordering not partition-aligned.** A Kafka producer using a non-`aggregateId` partition key sends events for the same order to different partitions. Consumers receive `OrderShipped` before `OrderPlaced`. The consumer's state machine breaks. Partition key must equal the aggregation boundary for per-entity ordering.
- **Event sourcing without snapshot strategy.** If an aggregate has 100,000 events, replaying all 100,000 to reconstruct current state on every command is unacceptable. Snapshot after N events or periodic snapshots are required for long-lived aggregates.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `publish(event)` inside `try { db.save(); publish(); }` without outbox | Ghost events on rollback; lost events on broker failure |
| Event named `CreateOrder` | Command, not a fact; consumers act on unconfirmed intent |
| Payload: `{ "orderId": "123" }` only | Consumer must call back to producer; loses historical context |
| No idempotency key; consumer processes duplicate event | Payment processed twice; ledger corrupted |
| Schema field renamed without version bump | Consumers silently deserialize wrong field; data corruption |
| Notification event contains full PII: name, email, SSN | Data fan-out to all consumers; GDPR Article 5 violation |
| DLQ not defined; consumer failure drops event silently | Saga stuck permanently; order never fulfills |
| Avro Kafka event, partition key = random UUID | Events for same order on different partitions; out-of-order delivery |

# Failure Modes

- Dual-write: broker publish succeeds, DB rollback follows — ghost event causes downstream system to allocate inventory for a non-existent order.
- Dual-write: DB commits, broker down — event lost; saga stuck; order never ships.
- Duplicate payment event processed twice because consumer has no idempotency check; user charged twice.
- `OrderCancelled` arrives before `OrderPlaced` due to partition key mismatch; consumer state machine in invalid state.
- Schema field renamed from `amount` to `totalAmount` without version bump; consumers deserialize null; calculation fails silently.
- PII in event payload fans out to analytics event pipeline; GDPR audit finds customer SSN in data warehouse logs.
- DLQ not monitored; 500 stuck events accumulate over 72 hours; customer orders permanently in limbo.
- Event-sourced aggregate with 200,000 events, no snapshot; replay takes 45 seconds; system unusable under load.
- Saga compensation event not defined; payment captured but inventory reservation failed; no rollback path; inconsistent state permanent.
- Schema registry not enforced in CI; producer publishes schema-incompatible event; all consumers start throwing deserialization errors.

# Output Contract

Return an event catalog with:

- `event_name` (past-tense, PascalCase), `event_type` (namespaced: `domain.subdomain.EventName.v1`)
- `producer` (service/aggregate name, method/command that triggers emission)
- `commit_boundary` (same transaction as state change via outbox? or separate publish?)
- `payload_schema` (all fields: name, type, required/optional, semantics, example values)
- `schema_version` (current; evolution history; registry location)
- `consumers` (list of known consumers; subscription mechanism; DLQ owner per consumer)
- `idempotency_key` (field(s) forming natural deduplication key)
- `ordering_expectation` (per-aggregate via partition key? Global? None guaranteed? — with partition strategy)
- `retry_policy` (max retries, backoff, DLQ topic, alert threshold)
- `dead_letter_strategy` (DLQ topic, owner, replay tool, runbook)
- `audit_impact` (immutable record required? regulatory retention period?)
- `privacy_classification` (PII fields? tokenized? restricted consumers?)
- `saga_role` (none / trigger / step / compensation; linked saga name)
- `tests` (consumer idempotency test, schema compatibility test, out-of-order handling test, DLQ routing test)

# Quality Gate

The event catalog is complete only when:

1. All event names are past-tense domain facts; no commands disguised as events.
2. Outbox pattern (or equivalent durable handoff) is specified for each emitting producer.
3. Payload is self-describing; no payload-minimalism; PII excluded or tokenized.
4. `schemaVersion` present; schema registered in registry; compatibility mode declared.
5. Idempotency key defined; consumer deduplication logic specified.
6. Ordering expectation declared with partition key strategy (or "none guaranteed" explicitly stated).
7. Retry policy and DLQ destination defined for every consumer.
8. DLQ ownership, alerting threshold, and replay tooling identified.
9. Saga compensation events defined wherever an event participates in a distributed workflow.
10. Tests cover: duplicate delivery, out-of-order delivery, schema forward-compatibility, DLQ routing.

# Used By

- domain-impact-modeler
- integration-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `state-machine-modeling` when transition semantics are undefined; `integration-change-builder` for cross-service consumer implementation; `message-queue-design` for broker topology and infrastructure; `transaction-consistency` for distributed saga coordination; `data-model-design` for event store or outbox table schema.

# Completion Criteria

The capability is complete when every domain event has a **past-tense name, a self-describing schema version, a durable post-commit publication path, a defined idempotency key, an explicit ordering guarantee, a retry policy, a DLQ owner, an audit classification, and tests covering duplicate and out-of-order delivery** — with no payload-minimalism, no dual-write pattern, and no unowned DLQ.
