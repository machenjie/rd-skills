---
name: event-driven-architecture
description: Designs event-driven flows with idempotency, ordering, retry, dead-letter, replay, backpressure, observability, and consistency rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "22"
changeforge_version: 0.1.0
---

# Mission

Design event-driven flows that remain **correct, observable, and operationally recoverable** under every adverse delivery condition: duplicate messages, delayed messages, out-of-order messages, replayed messages, poison messages, consumer failures, backpressure, and broker outages — so that eventual consistency is a deliberate product decision with explicit failure semantics, not an optimistic engineering shortcut.

# When To Use

Use this capability when a change: introduces pub-sub, stream processing, or message-queue consumers; adds new event producers that fan out to multiple consumers; designs projections, read models, or CQRS query-side updates driven by events; implements workflow choreography or saga patterns; adds webhooks, change-data-capture (CDC) flows, or external integration events; introduces eventual consistency between two bounded contexts; or changes delivery guarantees, consumer group topology, or partition strategy on existing flows.

# Do Not Use When

Do not convert a synchronous dependency to asynchronous without a clear reason: user-visible latency reduction, fault isolation from downstream failure, throughput decoupling, or explicit eventual consistency acceptance by the product. Asynchrony that is added for convenience without these reasons introduces operational complexity with no return. Do not use this capability for in-process event bus (e.g., Spring ApplicationEventPublisher scoped to a single service transaction) — that is a domain-event modeling concern, not an architecture concern.

# Non-Negotiable Rules

- **Every consumer side effect must be idempotent.** At-least-once delivery (the default for Kafka, RabbitMQ, SQS, Pulsar) guarantees duplicates. Every operation a consumer performs — database write, external API call, email send, ledger debit — must be safe to execute more than once. Idempotency key strategy must be defined per consumer.
- **Ordering guarantees must be declared, not assumed.** Kafka guarantees ordering within a partition (not across partitions). RabbitMQ classic queues do not guarantee ordering under parallel consumers. FIFO queues (SQS FIFO, RocketMQ) guarantee ordering within a message group. If consumers require per-aggregate ordering, the partition key (Kafka) or message group ID (SQS FIFO) must equal the aggregate ID.
- **Dead-letter queues are mandatory.** Every consumer must define a DLQ (dead-letter queue or dead-letter topic). A message that fails maximum retries must be routed to the DLQ, not discarded. DLQ events must generate an alert when depth exceeds threshold. DLQ ownership, inspection tooling, and replay procedure must be assigned to a named team.
- **Replay must not repeat irreversible side effects.** Event replay is a critical operational procedure (projection rebuild, incident recovery). Before enabling replay: identify all consumers that perform irreversible operations (payment capture, email send, webhook fire, ledger entry). Mark those operations as deduplication-gated: replay only if idempotency key has not been processed.
- **Backpressure is defined, not hoped for.** Producers must not outpace consumer processing capacity indefinitely. Define: consumer lag threshold (e.g., > 10,000 messages = alert), lag growth rate threshold, consumer scaling trigger (KEDA, Kubernetes HPA based on Kafka consumer lag), and circuit-breaker behavior when lag is critical.
- **Schema evolution follows compatibility contracts.** Event schemas consumed by multiple consumers cannot be changed without compatibility analysis. Backward-compatible changes (add optional field) require only a schema version bump. Breaking changes (remove field, rename, type change) require a new topic/channel and a migration period with dual-publishing.
- **Observability is not optional.** Every event flow must emit: event throughput (events/second per topic/partition), consumer processing rate, consumer lag, DLQ depth, error rate per consumer group, and end-to-end event latency (from produce time to consumer commit time). Without these signals, operational diagnosis is guesswork.

# Industry Benchmarks

Anchor against: **Apache Kafka** — dominant distributed event streaming platform; partition-based ordering; consumer groups; log compaction; exactly-once semantics (EOS) via idempotent producer + transactional API (Kafka 0.11+); Kafka Streams for stateful stream processing. **Apache Pulsar** — multi-tenancy; built-in geo-replication; tiered storage; subscription types (exclusive, shared, failover, key-shared for per-key ordering). **AWS SQS / SNS / EventBridge** — managed cloud messaging; SQS FIFO for ordering; EventBridge for event routing and schema registry; SQS visibility timeout as implicit retry. **RabbitMQ** — AMQP 0-9-1; exchanges (direct, fanout, topic, headers); dead-letter exchanges; quorum queues for HA. **NATS JetStream** — lightweight at-least-once persistent messaging; consumer groups; stream replay. **Google Pub/Sub** — managed GCP messaging; at-least-once; ordering keys for per-key ordering; dead-letter topics. **CloudEvents v1.0** (CNCF) — portable event metadata standard: `id`, `source`, `type`, `specversion`, `time`; supported by EventBridge, Azure Event Grid, Knative Eventing. **AsyncAPI 3.0** — event-driven API specification; documents channels, messages, bindings, servers; OpenAPI equivalent for async systems. **Saga Pattern** (Richardson, 2018; Microservices Patterns) — distributed long-running transaction coordination; Choreography Saga (events trigger compensating events) vs Orchestration Saga (central coordinator). **Outbox Pattern** — Transactional Outbox for reliable post-commit event publication; inbox pattern for at-least-once consumer deduplication. **CQRS + Event Sourcing** (Fowler, Young) — command and query model separation; events as source of truth; projection rebuild via replay. **Debezium** — CDC (Change Data Capture) via database WAL; Kafka connector for DB-to-topic CDC. **KEDA** (Kubernetes Event-Driven Autoscaler) — Kafka consumer lag–driven pod autoscaling. **OpenTelemetry** — distributed trace context propagation across event producer/consumer; `traceparent` in CloudEvents extensions. **Google SRE Book** (ch. 26) — on-call for distributed event systems; runbook requirements for DLQ and replay. **Confluent Schema Registry** — Avro/JSON/Protobuf schema management; compatibility enforcement (BACKWARD, FORWARD, FULL); schema fingerprint lookup.

### Delivery Guarantee Comparison

| Broker / config | Delivery guarantee | Ordering | Idempotency required? | Use when |
| --- | --- | --- | --- | --- |
| Kafka (default consumer) | At-least-once | Per-partition | Yes, always | High-throughput event streaming |
| Kafka EOS (idempotent producer + transactions) | Exactly-once (within Kafka) | Per-partition | No for broker; yes for external side effects | Kafka-to-Kafka stream processing |
| RabbitMQ quorum queue | At-least-once | Per consumer (not guaranteed parallel) | Yes | Task queues; routing by type |
| SQS Standard | At-least-once | Not guaranteed | Yes, always | High-throughput; order not critical |
| SQS FIFO | Exactly-once (dedup window) | Per message group | No (within window) | Order-sensitive; < 300 msg/s per group |
| AWS EventBridge | At-least-once | Not guaranteed | Yes | Event routing; multi-target fan-out |
| Google Pub/Sub | At-least-once | Per ordering key | Yes (without ordering key) | GCP-native fan-out |
| NATS JetStream | At-least-once | Per stream | Yes | Low-latency; lightweight |
| HTTP Webhook | At-least-once (with retry) | Not guaranteed | Yes | External integrations; notifications |

### Saga Pattern Selection

| Criterion | Choreography Saga | Orchestration Saga |
| --- | --- | --- |
| Coupling | Low — no central coordinator | Higher — orchestrator knows all steps |
| Visibility | Hard — flow distributed across events | Clear — orchestrator holds full state |
| Debugging | Difficult — trace across many services | Easier — one place for saga state |
| Compensation | Each service handles its own rollback events | Orchestrator emits compensation commands |
| Suitable for | Simple, stable flows (≤ 3 steps) | Complex flows; multi-step; long-running |
| Risk | Cyclic event loops; missing compensation | Orchestrator becomes bottleneck; SPOF |
| Examples | OrderPlaced → ReserveInventory → CapturePayment | Temporal.io, AWS Step Functions, Conductor |

### Consumer Lag Management

```
Consumer Lag = (Latest Offset in Topic) - (Consumer Group Committed Offset)

Thresholds (configurable per use case):
  Warning:  lag > 1,000 messages  OR  lag age > 1 minute
  Alert:    lag > 10,000 messages OR  lag age > 5 minutes
  Critical: lag > 100,000 messages OR lag age > 15 minutes → trigger scale-out

Monitoring (Kafka):
  kafka.consumer_group.lag (per group, topic, partition)
  via: Prometheus JMX exporter, Confluent Control Center, Datadog Kafka integration

Auto-scaling trigger (KEDA example):
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: order-processor-group
        topic: orders
        lagThreshold: "1000"

Backpressure options (when auto-scaling insufficient):
  1. Slow down producer (send-side rate limiting)
  2. Apply credit-based flow control at broker
  3. Activate circuit breaker: stop accepting new inbound requests until lag clears
  4. Shed load: move to DLQ immediately when lag > critical threshold (last resort)
```

### Replay Safety Classification

| Consumer operation | Replay-safe without deduplication? | Required protection |
| --- | --- | --- |
| Database upsert (update-or-insert by ID) | ✅ Yes | Use `ON CONFLICT DO UPDATE` or equivalent |
| Database insert (append-only) | ❌ No | Idempotency key; check before insert |
| Payment capture / charge | ❌ Never | Idempotency key mandatory; per-payment-intent |
| Email send / notification | ❌ No | Dedup window; check sent log by event ID |
| Webhook POST to external service | ❌ No | Idempotency key in header; check sent log |
| Ledger / accounting entry | ❌ Never | Idempotency key; double-entry check |
| Read model / projection update | ✅ Yes (if idempotent upsert) | Use event sequence number as version guard |
| Cache invalidation | ✅ Yes | Multiple invalidations are safe |
| Analytics event write | ✅ Usually | Deduplicate by event ID in analytics store |

# Selection Rules

Select this capability when **asynchronous multi-service event flow design** is primary. Adjacent routing:

- Prefer `domain-event-modeling` when event payload semantics, producer/consumer contracts, and event naming are primary.
- Prefer `message-queue-design` when broker infrastructure selection, queue topology, consumer group configuration, and binding design are primary.
- Prefer `async-job-design` when the concern is background job execution (workers, queues, cron) rather than domain fact communication.
- Prefer `transaction-consistency` when distributed transaction coordination and saga compensation logic are the main concern.
- Prefer `reliability-observability-gate` for production SLO/SLA review of event-driven flows.

# Risk Escalation Rules

Escalate when: event loss, duplication, or replay would cause a financial debit, customer notification, or inventory change to happen twice; an out-of-order event would corrupt a state machine (e.g., `OrderCancelled` before `OrderPlaced`); consumer lag is growing in production and no auto-scaling policy is defined; a schema change would break active consumers with no migration window; a DLQ has been accumulating events for > 1 hour with no acknowledged owner; a saga has no compensation events defined for any failure path.

# Critical Details

Event-driven systems trade synchronous coupling for temporal complexity. Precision failures:

- **"Fire and forget" without DLQ.** A producer publishes an event; the consumer fails; there is no DLQ; the event is lost. This is not eventual consistency — this is data loss. DLQ is not optional infrastructure.
- **Replay re-fires payment.** A replay job rebuilds a projection by re-processing all events from the beginning. The `PaymentCaptured` event passes through a consumer that calls Stripe Capture API again. The customer is charged twice. Every replay procedure must audit which consumers perform non-idempotent external operations and gate them behind deduplication.
- **Partition-key mistake.** A Kafka producer uses `customerId` as partition key. Two events for the same `orderId` but different `customerId` (e.g., a reassigned order) land on different partitions. The consumer processes `OrderShipped` before `OrderCreated`. State machine transitions to invalid state.
- **Exactly-once illusion.** Kafka EOS (exactly-once semantics) guarantees exactly-once delivery within Kafka. It does NOT guarantee exactly-once execution of external side effects (database writes, HTTP calls). Application-level idempotency is still required for any consumer that touches an external system.
- **Consumer group over-parallelism.** A consumer group has 20 parallel consumers on a topic with 6 partitions. 14 consumers are idle (Kafka assigns max 1 consumer per partition per consumer group). Partition count drives maximum parallelism; scale consumers to match partition count.
- **Stale projection read with no disclosure.** A user creates an order; the projection updates 500ms later; the user is redirected to an order list page that reads the stale projection; their new order is not visible. The product must decide: (1) use read-your-writes consistency for this flow; (2) show a "refreshing" state; or (3) use synchronous read from the command side. "It'll catch up soon" is not a product decision.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Consumer performs `INSERT` without idempotency key | Replay or duplicate delivery creates duplicate records |
| DLQ defined but no alert on DLQ depth | Failures accumulate silently for days; data loss discovered late |
| Kafka partition key = `Math.random()` | No ordering guarantee for any aggregate; state machine corruption |
| Saga with no compensation events | Business transaction permanently stuck on partial failure; no rollback path |
| `acks=0` Kafka producer (fire and forget) | Events lost on broker failure; no durability |
| Consumer lag not monitored | Production lag grows to 2M messages; service appears healthy; events hours old |
| Schema field removed without consumer registry check | Active consumer deserializes null; calculation fails silently |
| Exactly-once Kafka claimed = no idempotency needed | External DB write still duplicated; Kafka EOS only covers broker-side |

# Failure Modes

- Consumer duplicate delivery creates two payment charges; customer charged twice; refund required; SLA breach.
- DLQ accumulates 50,000 messages over 48 hours; no alert; orders in permanent "processing" state; mass customer escalation.
- Partition key assigned to random UUID; `OrderCancelled` arrives before `OrderCreated`; state machine error; order stuck.
- Replay rebuilds read model; payment capture consumer re-fires; 10,000 duplicate charges; production incident P0.
- Consumer lag reaches 500,000 messages; auto-scaling not configured; service processes events 3 hours old; financial totals stale; compliance SLA violated.
- Saga no compensation path: inventory reserved, payment fails, no `ReleaseInventory` compensation event defined; inventory permanently locked.
- Schema field renamed: `price` → `unitPrice`; consumers read null; order total = $0.00; passed validation; financial loss.
- `acks=0` on critical payment event topic; broker restart during peak; 200 events lost; payment status unknown.

# Output Contract

Return an event architecture plan with:

- `producers` (service, event name, emission trigger, transaction boundary, outbox mechanism)
- `consumers` (service, event name, processing logic, idempotency key, DLQ destination, owner)
- `event_schemas` (CloudEvents-compatible; schema version; registry location; compatibility mode)
- `delivery_guarantee` (at-least-once / exactly-once per consumer; broker and config)
- `ordering_requirement` (per-aggregate / per-partition / none guaranteed; partition key strategy)
- `retry_policy` (max retries, backoff algorithm, retry delay, DLQ threshold)
- `dlq_policy` (topic name, alert threshold, owner team, replay procedure, runbook)
- `replay_safety` (per-consumer classification; deduplication gate for non-idempotent operations)
- `consistency_model` (eventual; read-your-writes exception; stale read disclosure strategy)
- `backpressure_behavior` (lag threshold, auto-scaling config, circuit-breaker, load-shedding)
- `saga_design` (if applicable: steps, compensation events, orchestrator/choreography, timeout)
- `observability` (metrics: throughput, lag, DLQ depth, error rate, end-to-end latency)
- `schema_evolution_plan` (compatibility matrix; breaking change migration procedure)
- `tests` (idempotency test, out-of-order test, DLQ routing test, replay dedup test, lag alarm test)

# Quality Gate

The architecture design is complete only when:

1. Every consumer side effect is classified as idempotent or has a documented idempotency mechanism.
2. Ordering guarantees declared per-consumer; partition key strategy specified where ordering required.
3. DLQ defined for every consumer; alert threshold, owner, and replay procedure assigned.
4. Replay safety classification completed per consumer; non-idempotent operations gated by deduplication.
5. Schema compatibility mode declared in registry; breaking change migration procedure documented.
6. Consumer lag thresholds defined; auto-scaling trigger configured; backpressure strategy documented.
7. All saga failure paths have compensation events defined; orchestrator or choreography pattern chosen.
8. Observability metrics listed: throughput, lag, DLQ depth, error rate, end-to-end latency.
9. Eventual consistency impact on product UX documented (stale read disclosure or read-your-writes exception).
10. Tests cover: duplicate delivery, out-of-order, DLQ routing, replay deduplication, consumer group lag.

# Used By

- architecture-impact-reviewer
- integration-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `domain-event-modeling` for event payload and schema design; `message-queue-design` for broker topology and infrastructure; `transaction-consistency` for saga compensation and distributed rollback; `reliability-observability-gate` for production SLO review; `data-migration-design` for projection rebuilds during event schema migrations.

# Completion Criteria

The capability is complete when **asynchronous flow correctness is explicit across idempotency, ordering, retries, DLQ ownership, replay safety, backpressure, schema evolution, and observability** — with no optimistic "it'll be fine" assumptions about delivery guarantees, no DLQ without an owner, and no eventual consistency without a product-acknowledged disclosure strategy.
