# Broker Delivery And Recovery Evidence

**Load when:** broker-specific acknowledgement, delivery, ordering, deduplication, retry, terminal failure, outbox, or replay behavior is material.

**Do not load when:** the task is synchronous retry without message/job delivery, or current broker configuration already proves the bounded behavior.

Use current broker/provider documentation and deployed configuration, actual processing time/failure classes, ordering and duplicate consequences, vendor quotas/limits, business recovery objective, and named recovery owner. Only when retry is selected, derive attempts, delay, backoff, jitter, visibility windows, and caps from current evidence; example values are non-normative.

## Broker Decision Questions

1. What delivery guarantee is effective for the configured producer/consumer path, and where do acknowledgement, offset, visibility/lock renewal, retention, and redelivery occur relative to the durable side effect?
2. What partition, message-group, session, key, or queue topology defines ordering, and what happens to later messages when one item fails or is paused?
3. What is the real scope and lifetime of broker deduplication or transactional guarantees, and which downstream side effects still require application idempotency or reconciliation?
4. Which failures are transient, permanent, malformed, unauthorized, dependency-limited, or poison? Select retry or no-retry first; only for a selected retry derive attempts/delay/backoff/jitter from failure duration, provider guidance, rate limits, processing objective, ordering impact, and overload risk.
5. Once the configured broker path classifies a failure as terminal—immediately for a non-retryable class or after its evidence-derived retry policy is exhausted—record an observable, policy-permitted disposition and accountable recovery owner. DLQ/dead-letter topic, quarantine/table, pause, reject/drop where policy permits, manual repair, compensating action, or controlled replay are candidates; DLQ is not universal.
6. When business state and publish intent must commit together, evaluate a supported coordination mechanism using relay-duplication, lag, schema-governance, and recovery proof rather than an assumed exactly-once effect.

## Replay And Failure Outcomes

- Projection/cache rebuild may use deterministic overwrite or upsert when source-of-truth and load protection are proven.
- Notification, webhook, entitlement, inventory, payment, or ledger effects require consequence-specific duplicate and reconciliation controls before replay.
- Manual commit/ack is selected only when automatic behavior can acknowledge work before the required durable outcome; verify the actual client/broker mode.
- When retry amplification can exhaust consumers or block an ordered partition, derive backpressure from observed overload and ordering risk. When the configured path reaches its selected terminal disposition, expose the outcome through an owned signal and operating procedure.

## Evidence Outcomes

- Inspect broker/topic/queue, producer acknowledgement, consumer group/subscription, ordering, retention, visibility/lock, delivery count, terminal routing, and replay configuration actually deployed.
- Select tests from paths triggered by the actual broker, topology, and effects: duplicate/redelivery, crash before/after effect and acknowledgement, poison/malformed item, ordering blockage, lag/overload, broker outage, replay, and version skew.
- State provider-limit, production-lag, regional-failover, large-replay, and operator-recovery proof limits of local tests with their owner.
