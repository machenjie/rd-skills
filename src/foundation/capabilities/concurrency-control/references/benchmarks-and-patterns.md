# Concurrency Control Benchmarks And Patterns

Load for a named lost-update, duplicate-work, stale-owner, deadlock, TOCTOU, overlap, or contention mechanism decision. Select from the invariant and current store or protocol.

## Mechanism Selection

| Risk | Candidate control | Required proof and limit |
| --- | --- | --- |
| Unique creation | Unique constraint, conditional insert, or idempotency record. | Concurrent attempts leave one owned result and expose conflict safely. |
| Lost update | Version, CAS, or ETag check. | Conflict preserves caller intent; blind retry cannot overwrite newer state. |
| Read-modify-write | Row, range, advisory lock, serializable behavior, or atomic store primitive. | Current engine, scope, order, timeout, and retry protect the invariant. |
| Multi-resource invariant | Canonical order, atomic primitive, partition, or single authority. | Participating paths for the selected invariant follow one order, with any external wait treated as a bounded, evidence-backed exception. |
| Cross-store workflow | Saga, outbox, compensation, or reconciliation. | Step identity, idempotence, ordering, partial-state owner, and convergence are explicit. |
| Lease ownership | Linearizable claim plus fencing token. | Authoritative writes reject the former owner's stale token; TTL alone is insufficient. |
| Queue overlap | Partition, claim, visibility, inbox, or dedupe matched to the broker/store. | Crash, redelivery, expiry, and duplicate-worker outcomes remain recoverable. |
| Hot aggregate | Atomic update, shard, or explicitly approximate aggregation. | Loss, skew, and reconciliation error are measured. |
| Collaborative edit | CRDT or OT when concurrent intent must converge. | Causality/conflict fixtures reject unacceptable last-write-wins loss. |
| Cache stampede | Single-flight, coalescing, admission bound, or staggered refresh. | Failure and recovery do not synchronize callers or overload the source. |
| Pool or fan-out | Bounded concurrency and backpressure from capacity/deadline. | Connection exhaustion, hidden queues, and unbounded tasks are rejected. |

## Ownership And Proof Limits

- Route isolation to `transaction-consistency`, retries to `idempotency-retry-design`, queue claims to `message-queue-design`, cache coordination to `cache-design`, lifecycle to `dependency-wiring-lifecycle`, and capacity to `performance-budgeting`.
- The checklist owns lock order, cancellation, ABA, time and lifecycle decisions; evidence patterns own overlap, fencing, contention, freshness and proof limits.
