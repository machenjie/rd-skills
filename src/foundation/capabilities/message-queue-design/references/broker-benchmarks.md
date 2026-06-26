# Message Queue Broker Benchmarks

Use this reference when broker-specific delivery behavior, retry defaults, partition/ordering scope, transactional outbox relay choice, or replay safety is material to a queue design. Keep broker guarantees separate from application guarantees: broker deduplication windows and transactional producers do not remove the need for durable consumer idempotency when side effects leave the broker.

## Broker Guarantee Comparison

| Broker | Default Guarantee | Exactly-Once Scope | Ordering Scope | DLQ Support |
| --- | --- | --- | --- | --- |
| Kafka | At-least-once with manual offset commit | Kafka-to-Kafka with transactional producer and `read_committed`; not external side effects | Per partition | Manual DLQ topic |
| SQS Standard | At-least-once | No | None | Built-in redrive policy |
| SQS FIFO | At-least-once plus finite dedup window | Deduplication ID within a 5-minute window | Per `MessageGroupId` | Built-in redrive policy |
| RabbitMQ | At-least-once with manual ack | No | Per queue only under constrained consumer topology | Dead-letter exchange |
| Azure Service Bus | At-least-once | No end-to-end exactly-once | Per session | Built-in dead-letter queue |
| Google Pub/Sub | At-least-once | No | Per ordering key when enabled | Manual dead-letter topic |
| NATS JetStream | At-least-once | Bounded message ID dedupe window | Stream/consumer dependent | Configurable delivery subject |

## Retry Policy Configuration Matrix

| Message Class | Max Attempts | Initial Delay | Backoff | Max Delay | Jitter | Terminal State |
| --- | --- | --- | --- | --- | --- | --- |
| Transient database/network timeout | 5 | 1s | Exponential | 300s | 25% or full jitter | DLQ with diagnostic |
| Downstream dependency 503/429 | 3-5 | Honor `Retry-After` or 5s | Exponential | 300s | 30% or full jitter | DLQ plus alert |
| Schema or validation error | 1 | n/a | none | n/a | none | DLQ immediately |
| Ordering-sensitive FIFO stream | 3 | 2s | Exponential | 60s | 20% | DLQ preserving order impact |
| Background low-priority work | 3 | 30s | Exponential | 600s | 50% | DLQ or dead-letter table |

## Transactional Outbox Flow

```
BEGIN TRANSACTION
  UPDATE orders SET status = 'confirmed' WHERE id = :id
  INSERT INTO outbox (id, topic, payload, status)
    VALUES (:event_id, 'order.confirmed', :payload, 'PENDING')
COMMIT

Relay:
  SELECT pending outbox rows in deterministic order
  PUBLISH with event_id as idempotency/deduplication key
  MARK row as published after broker acknowledgement
```

Guarantees:
- business state and publish intent commit atomically;
- relay retries can publish more than once, so consumers still need idempotency;
- polling relay is simple but adds database load and latency;
- CDC/Debezium reduces polling load but increases platform and schema governance needs.

## Replay Safety Classes

| Consumer Side Effect | Replay Default | Required Control |
| --- | --- | --- |
| Projection rebuild or materialized view update | Safe if idempotent upsert | Unique key or deterministic overwrite |
| Email, SMS, push, webhook POST | Unsafe by default | Deduplication gate and replay-disabled flag unless explicitly approved |
| Payment, refund, ledger, inventory mutation | Unsafe by default | Durable idempotency, reconciliation, and approval before replay |
| Analytics event copy | Usually safe with dedupe | Event ID dedupe and downstream duplication tolerance |
| Cache warm/invalidation | Safe if bounded | Rate limit and source-of-truth fallback |

## Evidence Checklist

- broker config inspected: topic/queue, partition/message group, retention, visibility/lock timeout, max delivery, DLQ/redrive, consumer group;
- producer durability inspected: in-transaction outbox, broker ack mode, relay idempotency, retry policy;
- consumer correctness inspected: idempotency key, dedupe store, payload hash or natural key, ack/offset point, retryable/error classification;
- operations inspected: lag, age, throughput, retry, DLQ, consumer health, replay runbook, owner, alert threshold;
- validation mapped: duplicate delivery, poison message, crash before ack/commit, large replay or declared not verified, lag alert, and broker outage residual risk.
