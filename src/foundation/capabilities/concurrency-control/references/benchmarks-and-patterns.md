# Concurrency Control Benchmarks And Patterns

Load this reference when lost update, duplicate work, stale ownership, deadlock, TOCTOU, overlap or contention changes correctness. Select from the actual invariant/anomaly and current store/protocol, not a universal lock or isolation level.

## Mechanism Selection

| Risk | Candidate control | Required proof and danger |
| --- | --- | --- |
| Unique creation/deduplication | Unique constraint, conditional insert or idempotency record. | Concurrent attempts leave one owned result and translate conflict safely. |
| Lost update/stale write | Version/CAS/ETag optimistic check when conflicts are detectable/retryable. | Conflict path preserves user intent; blind retry does not overwrite newer state. |
| Critical read-modify-write | Transactional row/range/advisory lock or serializable behavior when the engine and invariant require it. | Lock scope/order/timeout and retry are current; do not prescribe isolation from domain label alone. |
| Multi-resource invariant | Canonical lock/order, atomic store primitive or redesigned single authority. | Where locks remain the selected control, participating acquisition paths follow one canonical order; provider or network waits stay outside the critical section unless the current protocol proves a bounded, safe exception. |
| Distributed multi-resource workflow | Saga/outbox/compensation and reconciliation when one atomic store cannot own the invariant. | Step/compensator idempotency, ordering and stuck/partial-state owner are explicit. |
| Distributed ownership/lease | Linearizable claim plus fencing token when stale owners can still act. | When correctness relies on a lease and an expired owner can still reach authoritative state, the authoritative write path compares the monotonic fencing token and rejects the former owner's stale token; TTL expiry alone does not prove exclusive authority. |
| Queue/job overlap | Partition/claim/visibility/inbox mechanism matched to broker/store. | Crash, redelivery, lease expiry and duplicate worker fixture remain recoverable. |
| Hot counter/aggregate | Atomic increment, partition/shard or explicitly approximate aggregation according to consistency need. | Read-modify-write loss, skew and reconciliation error are measured. |
| Collaborative editing | CRDT or Operational Transformation when concurrent/offline edits require convergent merge semantics. | Last-write-wins is rejected when lost intent is unacceptable; convergence, causality and conflict fixtures are required. |
| Hot-key/cache stampede | Single-flight, request coalescing, admission/queue bounds or staggered refresh. | Failure/recovery does not synchronize callers or overload source. |
| Resource pool/fan-out | Bounded concurrency and backpressure derived from capacity/deadline. | Unbounded tasks, connection exhaustion or hidden queue growth are rejected. |

## Deadlock, TOCTOU, And Lifecycle Rules

- Make check-and-act atomic at the authoritative boundary; revalidate file/path/permission/state after canonicalization and immediately before effect when the resource can change.
- For multiple locks/resources, publish one canonical order or eliminate the cycle through ownership/partitioning. Capture deadlock victim/retry behavior and ensure retries are idempotent.
- State who creates, renews, fences, releases and observes a lease/lock/claim, plus clock/partition/process-crash behavior. Cleanup on normal paths does not replace expiry/fencing recovery.
- Keep network/provider/user waits outside database or process locks unless the current protocol proves why this is safe and bounded.

## Worker And Contention Evidence

| Concern | Evidence | Proof limit |
| --- | --- | --- |
| Race/invariant | Barrier/interleaving test reproduces competing operations and asserts final invariant/side effects. | One stress run cannot prove every schedule. |
| Conflict/deadlock | Forced version conflict or reversed acquisition reaches bounded retry/terminal result. | Mock locks do not prove store semantics. |
| Lease/fencing | Old owner attempts a write after takeover and is rejected. | Local TTL test does not prove distributed linearizability. |
| Throughput/contention | Representative hot-key/row/load test measures wait, abort/retry, queue and tail latency. | Dev data and averages do not prove production contention. |
| Freshness | Current mutation paths, transactions, workers/jobs, store settings and tests inspected after final edit. | Source graph cannot prove dynamic/manual writers. |

Route database isolation to `transaction-consistency`, duplicate/retry semantics to `idempotency-retry-design`, queue claims to `message-queue-design`, cache coordination to `cache-design`, resource lifecycle to `dependency-wiring-lifecycle`, and capacity/latency to `performance-budgeting`.

Reject non-atomic check-then-write, inconsistent lock order, network calls while locked, optimistic retry without intent preservation, and TTL locks without fencing for critical state. Also reject unbounded fan-out, random sleeps as race proof, and green local stress reported as proof of all production schedules.
