# Transaction Consistency Patterns And Evidence

Load for a named anomaly, remote-ordering, outbox, saga, compensation, reconciliation, or distributed-atomicity mechanism decision. Use current datastore, ORM, isolation, replica, protocol, contention, invariant, and recovery facts.

## Local Mechanism Selection

| Risk | Candidate outcomes | Required evidence |
| --- | --- | --- |
| Lost update | Constraint, conditional update, version check, row lock, serialization, or remodel. | Colliding writers, conflict outcome, and current store support. |
| Write skew or phantom | Constraint, aggregate/range lock, serializable execution, or remodel. | Set invariant and datastore/query behavior. |
| Deadlock or contention | Stable order, shorter scope, optimistic conflict, or work claim. | Acquisition, workload, timeout, retry, and idempotent outer boundary. |
| Stale or replica read | Primary read, version/watermark, bounded stale result, or retry. | Read routing, lag, and read-after-write requirement. |
| Duplicate side effect | Idempotency, inbox/dedupe, reconciliation, or compensation. | Crash/redelivery window and durable effect identity. |

## Remote Ordering Selection

| Boundary | Select only with | Required proof |
| --- | --- | --- |
| Remote call while locked | The invariant requires a held transaction or lock. | Bounded latency/timeout, exhaustion, deadlock, cancellation, duplicate call, and rollback. |
| Commit before remote | Durable intent and post-commit recovery. | Crash recovery, dedupe, result persistence, terminal handling, and unknown-outcome owner. |
| Remote success before commit | The effect is identifiable and repairable. | Local-rollback recovery, replay safety, and cancellation, compensation, or reconciliation. |
| Cross-participant mechanism | Atomic boundaries and availability cost justify outbox, inbox, saga, reconciliation, reservation, conditional write, or 2PC/XA. | Identity, recovery, timeout, participant failure, and rollback limits without an exactly-once claim. |

## Pattern Boundary

| Pattern | Valid boundary | Proof outcome |
| --- | --- | --- |
| Local transaction | One datastore owns the invariant. | Commit/rollback and triggered anomaly proof. |
| Outbox/inbox | State and delivery intent/effect need coupling. | Atomic record, observable relay/consumer, duplicate-safe effect. |
| Saga/compensation | Multiple owned steps can be repaired. | Persisted steps/reversal inputs, stuck owner, and failed-compensation path. |
| Reconciliation | External or derived state may drift within a bound. | Drift detection, freshness, idempotent correction, and manual owner. |
| 2PC/XA | Atomicity outweighs availability coupling. | Coordinator recovery, timeout, participant failure, and rollback limits. |

The checklist owns transaction, retry, and failure-path selection. Evidence patterns own current artifacts, freshness, tool authority, inspected/skipped boundaries, and proof limits.
