---
name: message-queue-design
description: Designs queue consumers for duplicate, delayed, failed, and out-of-order messages with idempotency, retry, dead letter, backpressure, and observability.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "50"
changeforge_version: 0.1.0
---

# Mission

Design **message queues and consumers that remain correct under duplicate delivery, delay, failure, retry, dead-letter accumulation, backpressure, replay, and out-of-order processing** — ensuring at-least-once delivery semantics are compensated by idempotent consumers, bounded retry policies, dead-letter ownership, and observable consumer lag before any message-driven flow reaches production.

# When To Use

Use this capability when a change: adds a new queue, topic, exchange, or stream; adds a producer that publishes messages (commands, events, or notifications); adds or modifies a consumer (worker, subscriber, handler); defines or modifies retry policies, dead-letter queues, backpressure settings, or consumer group configuration; introduces ordering guarantees or partition key logic; or is flagged in review for "duplicate processing", "poison message blocking partition", "no dead-letter queue", or "consumer lag growing unbounded."

# Do Not Use When

Do not use this capability to design synchronous RPC patterns as queues (use `api-contract-design`), to handle queue infrastructure provisioning without also designing consumer behavior and failure handling, or to assume exactly-once delivery semantics in any general-purpose queue or broker without explicit transactional outbox + idempotency infrastructure.

# Non-Negotiable Rules

- **Consumers must be idempotent.** Every mainstream queue (RabbitMQ, Kafka, SQS, Pub/Sub, Azure Service Bus) provides at-least-once delivery. A consumer must produce the same observable side effect whether it processes a message once or ten times. Idempotency key must be carried in message attributes/headers — not just message body — so it is accessible without deserializing the payload.
- **Acknowledgement must occur AFTER durable side effects complete.** Ack before persistence = lost work on consumer crash. Ack after exception = duplicate processing on retry. The correct model: execute side effect → commit to durable store → ack. For Kafka: commit offset only after processing + storing the result (or use transactional producers with `exactly_once_semantics`). For SQS: delete message only after successful write.
- **Dead-letter queues (DLQ) are mandatory for all non-trivial consumers.** Every queue that processes business-critical messages (orders, payments, notifications, state changes) must have a DLQ configured. DLQ messages must have: original message + headers, failure reason, attempt count, original topic/queue, timestamp. DLQ must have an alert on non-zero depth and a documented replay procedure.
- **Poison messages must not block a partition.** A message that causes a consumer to crash on every attempt (deserialization failure, null pointer, missing reference) will block all subsequent messages on the same partition/key in ordered queues. Policy: after `maxDeliveryAttempts` (default 3–5), move to DLQ unconditionally. Never `NACK` a poison message back to the main queue with immediate requeue.
- **Retry policies must be bounded and use exponential backoff with jitter.** Unbounded retries + immediate requeue = retry storm. Formula: `delay = min(base * 2^attempt + jitter(0..base), maxDelay)`. Define `maxAttempts` (suggest 3–5 for transient failures), `maxDelay` (suggest 300s), `jitter` (±20–50%). Non-retryable errors (schema validation failure, business rule rejection, permanent 4xx) must go directly to DLQ on first attempt — do not retry.
- **Ordering guarantees must be stated explicitly with the partition/key scope.** In Kafka: ordering is guaranteed within a partition, not globally. SQS standard: no ordering. SQS FIFO: ordering per message group ID. Define: which messages require ordering (e.g., events for the same `orderId` must be ordered), what the partition key is, and the tradeoff (smaller key space → hot partitions; larger key space → lower ordering guarantees).
- **Consumer lag must be monitored and alert on threshold breach.** Consumer lag (messages produced − messages consumed) growing unbounded indicates a consumer that is slower than the producer, stuck in a retry loop, or dead. Alert when: lag exceeds a business-latency SLO threshold (e.g., > 10,000 messages OR > 5-minute processing delay for payment events); DLQ depth > 0; consumer group has no active members. Expose lag via metrics: Kafka `consumer_lag_sum`, SQS `ApproximateNumberOfMessagesNotVisible`, RabbitMQ `messages_ready + messages_unacknowledged`.
- **Backpressure must slow producers or shed non-critical work before lag becomes an outage.** Consumers that cannot keep up will eventually exhaust memory, crash, or block critical paths. Options: producer rate limiting (token bucket); priority queues (shed low-priority messages first); separate queues by criticality (payment events on dedicated high-priority topic); consumer horizontal scaling (add consumer instances up to partition count). Never let lag grow indefinitely without a shedding or scaling mechanism.

# Industry Benchmarks

Anchor against: **Apache Kafka Documentation** — partition ordering, consumer groups, offset commit semantics, `isolation.level=read_committed` for transactional producers, `enable.auto.commit=false` (manual offset commit required for correctness). **AWS SQS/SNS Best Practices** — visibility timeout ≥ max processing time; `ApproximateReceiveCount` for retry detection; DLQ `maxReceiveCount` 3–5; SQS FIFO for ordering per group ID. **RabbitMQ Dead Letter Exchanges (DLX)** — `x-dead-letter-exchange`, `x-message-ttl`, `x-max-retries`; `nack(requeue=false)` to route to DLX. **Gregor Hohpe & Bobby Woolf "Enterprise Integration Patterns"** (2003) — Dead Letter Channel, Message Store, Idempotent Receiver, Competing Consumers, Message Expiration. **Microservices Patterns — Chris Richardson** — Transactional Outbox Pattern: write message to `outbox` table in same DB transaction as business data; relay process reads and publishes; ensures no message lost on crash; polling publisher or CDC (Debezium). **NATS JetStream** — at-least-once + exactly-once (with `MsgId` deduplication within 2-minute window). **Azure Service Bus** — `MaxDeliveryCount` per queue/topic (default 10); `ScheduledEnqueueTimeUtc` for delayed retry; sessions for FIFO ordering; `DeadLetterReason` property. **Google Cloud Pub/Sub** — `ack_deadline_seconds`; `minimum_backoff + maximum_backoff` for subscription retry; snapshot/seek for replay.

### Message Delivery Guarantee Comparison

| Broker | Default Guarantee | Exactly-Once? | Ordering Scope | DLQ Built-in? |
| --- | --- | --- | --- | --- |
| Kafka | At-least-once (manual offset commit) | Yes (transactional producer + `read_committed`) | Per partition | No (manual DLQ topic) |
| SQS Standard | At-least-once | No | None | Yes (maxReceiveCount) |
| SQS FIFO | At-least-once (exactly-once 5-min dedup window) | Yes (dedup ID) | Per MessageGroupId | Yes |
| RabbitMQ | At-least-once (manual ack) | No | Per queue (single consumer) | Yes (DLX) |
| Azure Service Bus | At-least-once | No (sessions for ordering) | Per session | Yes (MaxDeliveryCount) |
| Google Pub/Sub | At-least-once | No | Per key (ordering key) | No (manual) |

### Retry Policy Configuration Matrix

| Message Class | Max Attempts | Initial Delay | Backoff Factor | Max Delay | Jitter | On Exhaustion |
| --- | --- | --- | --- | --- | --- | --- |
| Transient (DB timeout, 503) | 5 | 1s | 2× | 300s | ±25% | DLQ |
| Downstream dependency (3rd-party API) | 3 | 5s | 2× | 300s | ±30% | DLQ + alert |
| Non-retryable (schema error, 4xx) | 1 | — | — | — | — | DLQ immediately |
| Ordering-sensitive (FIFO stream) | 3 | 2s | 2× | 60s | ±20% | DLQ (preserve order) |
| Background / low-priority | 3 | 30s | 2× | 600s | ±50% | DLQ (no alert) |

### Transactional Outbox Pattern

```
Problem: Producer publishes to queue AFTER committing to DB →
         if queue publish fails, event is lost permanently.

Solution (Transactional Outbox):

  BEGIN TRANSACTION
    UPDATE orders SET status = 'confirmed' WHERE id = :id
    INSERT INTO outbox (id, topic, payload, status)
      VALUES (:event_id, 'order.confirmed', :payload, 'PENDING')
  COMMIT

  Relay process (separate):
    LOOP:
      SELECT * FROM outbox WHERE status = 'PENDING' ORDER BY created_at LIMIT 100
      FOR each row:
        PUBLISH to message broker (idempotently — event_id as dedup key)
        UPDATE outbox SET status = 'PUBLISHED' WHERE id = :row.id

Guarantees:
  - Event is NEVER lost (committed to DB before queue publish)
  - At-least-once delivery (relay retries on broker failure)
  - Exactly-once semantics if consumer checks idempotency key = event_id

Options:
  - Polling Relay: simple, adds DB load, ~1s latency
  - CDC + Debezium: capture changes from DB WAL → Kafka; near-real-time; no polling
```

# Selection Rules

Select this capability when: queue topology, delivery semantics, consumer correctness under duplicate delivery, or retry/DLQ policy is the primary concern. Route elsewhere when: **async-job-design** is primary (job lifecycle, progress tracking, status reporting); **event-driven-architecture** is primary (event schema design, event routing, publisher/subscriber topology across bounded contexts); **idempotency-retry-design** is primary (idempotency key schema and at-application-layer duplicate detection); **observability** is primary (consumer lag metrics, alerting configuration).

# Risk Escalation Rules

Escalate when: messages carry financial transactions (payments, ledger updates, inventory), regulated personal data (HIPAA, GDPR, PCI), or security-sensitive operations (permission changes, authentication events); the change removes DLQ configuration or reduces `maxDeliveryAttempts`; a consumer does not have idempotency protection and processes irreversible side effects (email, SMS, charge); consumer lag is expected to exceed business SLO under normal load; or the proposed ordering guarantee scope (partition key) is insufficient to prevent out-of-order processing for a stateful workflow.

# Critical Details

- **Kafka `enable.auto.commit=false` is mandatory for correctness.** Auto-commit periodically commits the highest offset regardless of whether processing succeeded. A consumer that processes and auto-commits, then crashes mid-batch, will skip messages whose offsets were committed but effects not applied. Always use manual commit (`commitSync` after processing + storing the result).
- **Consumer visibility timeout (SQS) / lock timeout (Service Bus) must exceed max processing time.** If processing takes 25 seconds and visibility timeout is 20 seconds, the message becomes visible again and a second consumer picks it up — causing a duplicate. Rule: `visibilityTimeout ≥ p99 processing time × 2`. Extend visibility timeout for long-running consumers programmatically.
- **Deduplication window is finite.** SQS FIFO deduplication window: 5 minutes. NATS JetStream `MsgId` deduplication: configurable (default 2 minutes). Messages replayed outside this window will be re-processed. Consumer idempotency must not rely solely on broker-level deduplication for events that may be replayed hours or days later (replay from DLQ, disaster recovery).
- **Partition key selection determines ordering AND load distribution.** `orderId` as partition key: ordering guaranteed per order; hot partition risk if one order generates high volume. `customerId` as partition key: ordering per customer; more balanced load. `random` / no key: maximum throughput, no ordering. For stateful workflows that require strict ordering, the partition key must be the entity ID whose state is being mutated.
- **Consumer group rebalance causes pause — design for it.** When a consumer joins or leaves a Kafka consumer group, partitions are reassigned (rebalance). During rebalance, no consumer is processing. Sessions that hold locks or DB connections during rebalance may time out. Use `CooperativeStickyAssignor` (incremental rebalance) to minimize pause. Commit offsets before processing to minimize reprocessing on rebalance.

### Consumer Implementation Checklist

```
Before processing:
  [ ] Extract idempotency key from message header/attribute (not body)
  [ ] Extract correlationId / traceparent from message header
  [ ] Bind correlationId to logging context (MDC / contextvars / AsyncLocalStorage)
  [ ] Check: has this idempotency key been processed? (idempotency store lookup)

Processing:
  [ ] Deserialize + validate schema (→ DLQ immediately on validation failure; do not retry)
  [ ] Execute business logic
  [ ] Write side effects to durable store (DB commit / API call)
  [ ] Record idempotency key as processed in idempotency store

After processing:
  [ ] Acknowledge / commit offset (only after durable write succeeds)
  [ ] Log at INFO with correlationId, message type, processing duration

On failure:
  [ ] Catch exception
  [ ] Determine: retryable? (transient) or non-retryable? (schema, business rule)
  [ ] Non-retryable: NACK with requeue=false → DLQ immediately
  [ ] Retryable: NACK with requeue=false + delay → let broker retry policy handle
  [ ] Never: NACK with requeue=true (poison message loop risk)
  [ ] Log at ERROR with exception type, attempt count, correlationId
```

# Failure Modes

- Consumer does not check idempotency key — duplicate delivery creates duplicate payment charges, duplicate emails, or duplicate inventory deductions.
- Ack before DB commit — consumer crashes after ack but before commit; message is lost; event never processed; no alert.
- Poison message `NACK` with `requeue=true` — message immediately requeued; consumer crashes again; thousands of attempts per minute; CPU spike; downstream DB overwhelmed; other messages on partition blocked.
- No DLQ configured — after `maxDeliveryAttempts`, message is silently dropped; no recovery path; data loss undetected.
- Kafka `enable.auto.commit=true` — periodic offset commit marks messages as processed before processing completes; consumer crash between auto-commit and processing completion skips messages permanently.
- SQS visibility timeout shorter than processing time — message becomes visible to second consumer mid-processing; duplicate processing; idempotency failure if not implemented.
- Consumer lag grows to millions of messages with no alert — 4-hour message processing backlog on payment events; customers receive payment confirmations hours late; SLO breach.
- Retry storm: retryable error causes immediate requeue without backoff — 500 messages retry at 100/second; downstream dependency receives 50,000 req/min; cascading failure.
- Transactional outbox not used: queue publish outside DB transaction — DB commit succeeds; queue publish fails; event permanently lost; downstream service never receives state change; data inconsistency.
- Partition key set to constant value — all messages route to one partition; one consumer handles 100% of load; other consumers idle; throughput capped at single consumer capacity.

# Output Contract

Return a queue design with:

- `producers` (service name, message type, schema, idempotency key, correlation ID header, transactional outbox: yes/no)
- `topics_queues` (name, broker, ordering guarantee, partition key, retention, consumer groups)
- `message_schema` (fields: idempotency_key, correlation_id, event_type, payload, schema_version; no secrets in payload)
- `delivery_guarantee` (at-least-once; idempotency compensation strategy)
- `consumer_steps` (per-consumer: idempotency check → deserialization → business logic → durable write → ack)
- `acknowledgement_point` (after or before durable write — must be AFTER)
- `retry_policy` (initial delay, backoff formula, max attempts, jitter, max delay, retryable vs non-retryable classification)
- `dead_letter_policy` (DLQ name, max attempts before DLQ, DLQ alert threshold, replay procedure)
- `backpressure` (consumer scaling policy, rate limiting, priority queue design)
- `ordering_guarantee` (partition key, scope, tradeoffs, handling of out-of-order arrival)
- `observability` (consumer lag metric + alert threshold, DLQ depth alert, consumer group health alert, processing latency P99 SLO)
- `test_strategy` (assert: duplicate message → idempotent; poison message → DLQ after N attempts; consumer crash mid-processing → no message lost; lag alert fires when threshold exceeded)

# Quality Gate

The design is complete only when:

1. Every consumer has an explicit idempotency strategy with idempotency key in message header.
2. Acknowledgement / offset commit is performed AFTER durable side effects are committed.
3. DLQ configured for every topic/queue with business-critical messages; DLQ alert defined.
4. Retry policy specifies max attempts, backoff formula with jitter, max delay, and non-retryable classification.
5. Poison message handling routes to DLQ after max attempts without requeue to main topic.
6. Consumer lag metric defined with SLO-based alert threshold.
7. Ordering guarantee scope documented with partition key and business justification.
8. Transactional outbox pattern or equivalent used for producer-side exactly-once durability.
9. Backpressure mechanism defined (consumer scaling, rate limiting, or priority queues).
10. Consumer visibility timeout / lock duration validated against p99 processing time.

# Used By

- backend-change-builder
- event-driven-architecture
- integration-change-builder

# Handoff

Hand off to `event-driven-architecture` for cross-bounded-context event routing and schema registry design; `async-job-design` for job lifecycle and status tracking; `idempotency-retry-design` for application-level idempotency key schema; `observability` for consumer lag dashboard and alert threshold configuration.

# Completion Criteria

The capability is complete when **all consumers are idempotent, acknowledgement occurs after durable writes, DLQ with ownership and replay procedure exists for every critical queue, retry policies are bounded with exponential backoff and jitter, consumer lag is monitored with SLO-based alerting, and all behaviors are verified by automated tests including duplicate delivery and poison message scenarios**.
