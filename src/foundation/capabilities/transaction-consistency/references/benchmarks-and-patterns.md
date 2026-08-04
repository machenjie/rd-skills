# Transaction Consistency Patterns And Evidence

**Load when:** a transaction decision needs deeper anomaly, locking, remote-side-effect, outbox/saga, compensation, reconciliation, or distributed-atomicity evidence.

**Do not load when:** the root Skill already determines the bounded invariant and proof, or no transaction/consistency boundary changes.

Use the actual datastore/ORM/driver configuration, default isolation, replica behavior, external protocol, workload/contention, failure window, business invariant, and recovery ownership. Pattern names and isolation levels are candidates, not proof.

## Anomaly And Local-Control Questions

| Concern | Decision evidence | Candidate outcomes |
| --- | --- | --- |
| Lost update | Concurrent writers, accepted conflict behavior, current constraint/version support | Conditional update, version check, row lock, serialization, remodel |
| Write skew or phantom | Set/range invariant and target datastore behavior | Constraint, aggregate lock, serializable execution, remodel |
| Deadlock/contention | Effective lock acquisition, scope, workload, timeout/retry behavior | Stable ordering, shorter scope, optimistic conflict, work claiming |
| Stale or replica read | Read routing, lag, read-after-write requirement | Primary read, version/watermark, bounded stale result, retry |
| Duplicate side effect | Crash/redelivery window and durable effect identity | Idempotency, inbox/dedupe, reconciliation, compensation |

Prefer a datastore constraint when it directly expresses the invariant, but verify ORM/migration and error behavior. Select optimistic or pessimistic control from conflict frequency, critical-section duration, user/worker retry semantics, and lock evidence rather than a universal isolation rule.

## Remote Call And Commit Ordering

- When consistency crosses a remote effect and local commit, derive ordering from invariants, protocol, contention, idempotency, uncertainty, reversibility, and available recovery.
- Select a commit-first or open-transaction strategy from that evidence instead of adopting either by default.
- Require ordering-specific proof through either a bounded transaction or lock across remote I/O or durable post-commit recovery, with absence of either treated as an escalation condition.
- If a remote call occurs while a local transaction or lock is open, prove why the invariant requires that ordering. Bound provider latency, timeout, connection/lock exhaustion, deadlock, cancellation, duplicate-call, and rollback behavior under representative concurrency.
- If local intent commits before the remote call, prove crash recovery between commit and call, duplicate suppression, result persistence, retry/terminal handling, compensation or reconciliation, and operator ownership for an unknown provider outcome.
- If the remote call occurs before final local commit, prove how to repair remote success followed by local rollback. Also prove replay safety and state whether reservation/authorization expiry or provider cancellation is available.
- Select outbox, inbox, saga, reconciliation, provider reservation, conditional write, or 2PC/XA from actual atomic boundaries and availability cost without inferring end-to-end exactly-once behavior.

## Pattern Evidence

| Pattern | Use only when | Proof outcome |
| --- | --- | --- |
| Local transaction | One authoritative datastore can protect the invariant | Atomic commit/rollback and relevant concurrent anomaly test |
| Outbox/inbox | Local state and delivery intent/effect need durable coupling | Atomic record, observable relay/consumer, duplicate-safe effect |
| Saga/compensation | Multiple owned steps can be reversed or repaired | Persisted step/compensation inputs, stuck-state owner, failed-compensation path |
| Reconciliation | External or derived state may drift acceptably | Drift detection, bounded freshness, idempotent repair/manual owner |
| 2PC/XA | True participant atomicity outweighs availability coupling | Coordinator recovery, timeouts, participant failure, rollback limits |

## Validation And Limits

- Inspect current service or repository code, ORM callbacks, transaction annotations, migrations, publishers, provider adapters, retry wrappers, and affected tests as effective-behavior evidence beyond annotations alone.
- `analysis-agent` defines the anomaly/failure reproduction and inspects current evidence without execution; only a permitted `task-agent` runs approved checks.
- After identifying the changed invariant and reachable anomaly or uncertainty windows, select tests for applicable concurrent-writer, set/range-anomaly, and deadlock/timeout paths. Also cover applicable provider-success/local-failure, local-success/provider-uncertainty, duplicate-delivery, compensation-failure, or reconciliation-drift paths. An omitted catalog path is acceptable when its non-reachability or scope boundary is recorded.
- State datastore-lock, isolation, replica-lag, provider-timing, production-contention, and operator-recovery proof limits of unit tests.

## Failure Patterns

- Broad transactions hold locks across unrelated work without invariant evidence.
- Event/cache visibility precedes commit, exposing state that later rolls back.
- Retry hides conflict or repeats a non-idempotent provider effect without terminal behavior.
- Compensation reads mutable current state instead of persisted reversal inputs.
- Distributed atomicity is selected without proving its availability and recovery cost.
