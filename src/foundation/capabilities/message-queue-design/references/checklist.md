# Message Queue Proof Checklist

- Prove producer, broker or queue, schema and version, consumer, delivery guarantee, ownership or visibility model, and ordering scope from actual configuration.
- Prove acknowledgement, offset, or visibility timing relative to the durable business effect; consider manual commit when automatic behavior can lose required work, and record the broker's actual ownership semantics.
- When handler duration can exceed delivery ownership or visibility, derive extension, renewal, cancellation, and shutdown behavior from broker and workload evidence.
- Treat expiry or rebalance overlap as concurrent delivery.
- Derive ownership checks, fencing, duplicate-safe effects, or reconciliation from the side-effect guarantees.
- For duplicate delivery, redelivery, and replay, select natural idempotence, durable outcome reuse, conditional effects, or reconciliation from business identity, result reuse, and distinguished broker, caller, and handler retry ownership.
- For schema evolution or replay, validate old messages against mixed deployed consumers and current business semantics. When replay can outlive broker or deduplication retention, define duplicate-safe effects and reconciliation without expired deduplication state.
- Select retry or no-retry from classified transient, permanent, malformed, unauthorized, dependency-limited, and poison failures, with attempts, delay, backoff, and jitter derived from provider and workload evidence.
- When failure is terminal or retry is exhausted, name an owned, observable disposition selected from broker semantics and policy.
- Provide retention, repair, or replay evidence when the disposition depends on it.
- When terminal records enter a DLQ or quarantine, derive minimization, redaction, encryption or isolation, access, retention, deletion, audit, inspection, repair, replay, and disposal controls from classified payload, metadata, policy, and authority.
- Prove ordering impact and unblock behavior when a failed message can stall a partition, session, group, or workflow.
- When lag or overload risk is triggered, determine whether partition-key skew or a hot partition contributes. Prove applicable producer or consumer backpressure, lag or age limits, overload or degradation behavior, and telemetry tied to an owned operational action.
- Select tests from paths triggered by the actual broker, topology, and effects. Applicable paths include duplicate, delayed, out-of-order, concurrent-delivery, crash/acknowledgement, poison, terminal, lag, outage, old-schema, late-replay, and version-skew behavior. Name unverified production or provider limits.
