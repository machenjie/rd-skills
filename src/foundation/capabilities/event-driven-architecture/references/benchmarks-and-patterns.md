# Event-Driven Architecture Benchmarks And Patterns

Use this reference when `event-driven-architecture` needs more than routing-level guidance. Keep the main `SKILL.md` focused on selection, evidence, and handoff rules; use this file for delivery semantics, saga choices, replay safety, lag/backpressure, outbox/inbox flow, and operational anti-pattern review.

## Benchmark Anchors

- **Kafka, Pulsar, Pub/Sub, SQS, RabbitMQ, NATS JetStream:** delivery semantics, ordering scope, consumer groups, retries, retention, replay, and DLQ behavior.
- **CloudEvents v1.0:** portable event metadata such as `id`, `source`, `type`, `specversion`, and `time`.
- **AsyncAPI:** event-driven API documentation for channels, messages, bindings, and servers.
- **Transactional Outbox and Inbox:** reliable publish-after-commit and at-least-once consumer deduplication.
- **CQRS and Event Sourcing:** read model ownership, projection rebuild, event stream history, and snapshot/replay limits.
- **Saga Pattern:** choreography and orchestration for long-running cross-service workflows with compensation.
- **Debezium and CDC:** database log capture for deriving events from committed changes.
- **Schema Registry:** Avro, JSON Schema, or Protobuf compatibility enforcement and version governance.
- **KEDA and consumer-lag autoscaling:** backlog-driven scaling and backpressure design.
- **OpenTelemetry messaging semantics:** trace propagation through producer, broker, and consumer boundaries.

## Delivery Guarantee Comparison

| Broker or config | Delivery guarantee | Ordering scope | Architecture implication |
| --- | --- | --- | --- |
| Kafka default consumer | At-least-once. | Per partition. | Idempotent consumer required; partition key decides aggregate ordering and max parallelism. |
| Kafka transactional producer/EOS | Exactly-once within Kafka transactions. | Per partition. | Does not make external DB/API/email/payment side effects exactly-once. |
| RabbitMQ quorum queue | At-least-once. | Depends on queue/consumer concurrency. | Manual ack, DLX, retry, and poison-message handling remain application obligations. |
| SQS Standard | At-least-once. | No ordering guarantee. | Use only where consumers tolerate duplicate and reordered delivery. |
| SQS FIFO | Deduplicated within broker window. | Per message group. | Broker dedupe window is finite; replay still needs durable application dedupe. |
| EventBridge | At-least-once routing. | No ordering guarantee. | Good for fan-out/routing; consumers still own idempotency and DLQ. |
| Google Pub/Sub | At-least-once. | Optional ordering key. | Ordering key can reduce parallelism and create hot-key risk. |
| HTTP webhook | At-least-once when provider retries. | Provider-specific, usually none. | Treat as external integration with signature, idempotency, retry, and reconciliation. |

## Saga Pattern Selection

| Criterion | Choreography saga | Orchestration saga |
| --- | --- | --- |
| Coupling | Lower direct coupling; services react to events. | Orchestrator knows all steps. |
| Visibility | Harder to inspect end-to-end without tracing and saga state. | Central state gives clearer diagnosis and manual recovery. |
| Compensation | Each service emits or handles its compensation. | Orchestrator emits compensation commands. |
| Fit | Simple, stable flows with few steps and clear ownership. | Complex, long-running, user-visible, or high-value workflows. |
| Primary risk | Event loops, missing compensation, hidden ordering assumptions. | Orchestrator bottleneck, single point of workflow failure. |
| Evidence required | Event graph, trace propagation, compensation coverage, loop prevention. | Orchestrator state model, timeout policy, compensation log, runbook. |

Selection checks:

- If the workflow has more than three material steps, requires manual intervention, or has user-visible status, prefer orchestration unless choreography observability is strong.
- If each step has independent owners and simple compensation, choreography may be sufficient.
- If compensation failure causes financial, entitlement, or inventory corruption, require transaction-consistency review and explicit operator recovery.
- If neither pattern can preserve the invariant, revisit the service/data boundary before introducing events.

## Consumer Lag And Backpressure

Consumer lag is the difference between latest produced offset and committed consumer offset, or the equivalent backlog age/count for non-Kafka brokers. Treat lag as product latency, not only infrastructure health.

Suggested starting thresholds, to be calibrated per business SLA:

| Level | Signal | Architecture response |
| --- | --- | --- |
| Warning | Lag age exceeds normal processing window or backlog grows for two intervals. | Inspect consumer health, dependency latency, and partition skew. |
| Alert | Lag violates product freshness target or DLQ depth becomes non-zero for critical flow. | Page or ticket owner based on severity; stop accepting non-critical work if needed. |
| Critical | Lag grows faster than consumers can drain, or replay/recovery ETA violates SLA. | Scale consumers up to partition limit, throttle producers, activate backpressure, or shed low-priority work. |

Backpressure options:

- throttle producers or admission-control non-critical commands;
- prioritize critical event classes into separate topics/queues;
- scale consumers up to the partition, session, or message-group parallelism limit;
- apply circuit breaker or degraded user state when read model freshness is below product tolerance;
- pause low-priority replay/backfill while live traffic drains;
- route poison messages to DLQ instead of blocking ordered partitions.

## Replay Safety Classification

| Consumer operation | Replay-safe without durable dedupe? | Required protection |
| --- | --- | --- |
| Projection upsert keyed by aggregate ID and version. | Usually yes. | Sequence or version guard. |
| Cache invalidation. | Usually yes. | Safe repeated invalidation; source-of-truth read on refill. |
| Analytics write. | Sometimes. | Event ID dedupe or downstream idempotent insert. |
| Append-only DB insert. | No. | Unique event ID or natural idempotency key. |
| Email, SMS, push, or webhook send. | No. | Sent log keyed by event ID and receiver. |
| Payment capture, refund, ledger, entitlement, or inventory mutation. | Never by default. | Durable idempotency key, reconciliation, compensation/runbook, and restricted replay mode. |
| External API write. | No. | Provider idempotency key or local sent-operation ledger plus reconciliation. |

Replay procedure must state which consumers run, which are disabled, which are dedupe-gated, and which require manual approval.

## Outbox, Inbox, And CDC Flow

Use transactional outbox when a service owns the state change and must publish a fact after commit:

1. Write domain state and outbox event in the same local transaction.
2. Relay reads unpublished outbox rows in bounded batches.
3. Relay publishes with event ID as dedupe key and trace/correlation context.
4. Relay marks published only after broker acknowledgement.
5. Consumer writes an inbox/deduplication record before or atomically with its side effect.
6. Consumer acknowledges or commits offset only after durable side effect succeeds.

CDC can replace polling relay when database log capture is supported and operational ownership is clear. CDC still needs schema ownership, ordering expectations, consumer idempotency, replay rules, and lag observability.

Reject direct dual-write `save(); publish();` patterns unless the event is explicitly best-effort, non-critical, and not used for state propagation.

## Schema Evolution And Consumer Impact

Event schema changes need consumer inventory, compatibility class, and rollout plan.

Compatibility rules:

- Add optional field with default: usually backward-compatible; update registry and docs.
- Add required field: breaking unless all consumers already tolerate absence.
- Remove or rename field: breaking; require new event version or migration window.
- Change type or semantic meaning: breaking even when field name stays the same.
- Change partition key or ordering key: architecture behavior change; requires replay and lag review.
- Change event name from fact to command-like intent: reject or route to domain-event-modeling.

Evidence should include schema diff, active consumer list, generated contract impact, registry compatibility result, and rollback/cutover plan.

## Observability And Trace Propagation

Minimum event-flow signals:

- produced events per topic/channel and producer;
- consumed events per consumer group;
- consumer lag count and age;
- DLQ depth and oldest DLQ message age;
- processing latency and end-to-end event latency;
- consumer error rate by bounded error class;
- replay progress and ETA;
- outbox relay backlog and publish failure rate;
- trace propagation from producer through message headers to consumer spans.

Metric labels must be bounded. Do not label metrics with event ID, aggregate ID, customer ID, user ID, raw topic names with tenant IDs, or payload values. Put high-cardinality values in logs/traces with privacy review.

## Evidence Patterns

A strong event-driven architecture handoff includes:

- current producers, consumers, schemas, topic/channel config, registry, outbox/relay, and generated artifacts inspected;
- async justification and rejected simpler alternative;
- event topology map with owners;
- delivery guarantee and ordering scope per consumer;
- source-of-truth, consistency window, and stale-read product decision;
- transaction/outbox/inbox boundary and side-effect ordering;
- replay-safe and replay-unsafe consumer classification;
- schema compatibility and consumer impact report;
- lag, DLQ, replay, error, and end-to-end latency observability;
- duplicate, out-of-order, DLQ, replay, lag/backpressure, and schema-compat validation;
- evidence limits and next gate.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Async chosen only because synchronous call feels slow. | Adds temporal complexity without proving product consistency or reliability benefit. |
| Producer writes DB then publishes outside a transaction. | Broker failure loses the event; rollback after publish creates a ghost event. |
| Consumer side effect has no durable dedupe. | Duplicate delivery or replay repeats payments, emails, ledger writes, or inventory changes. |
| Exactly-once broker semantics used to justify no application idempotency. | Broker guarantees do not cover external side effects. |
| Random or convenience partition key. | Per-aggregate ordering is lost and state machines can corrupt. |
| DLQ exists with no alert owner or replay procedure. | Failures accumulate silently and recovery is improvised during incidents. |
| Replay all topics through all consumers by default. | Irreversible side effects may run again. |
| Breaking schema change in-place. | Active consumers fail or silently calculate with missing fields. |
| Event payload contains broad PII or secrets. | Durable fan-out expands privacy and breach surface. |
| Consumer lag metric has no product freshness threshold. | Backlog can violate user-facing behavior while infrastructure looks healthy. |
| Prior repository memory accepted as event topology proof. | Hidden current consumers, generated contracts, or retired topics can be missed. |
