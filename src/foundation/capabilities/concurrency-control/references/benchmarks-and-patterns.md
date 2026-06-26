# Concurrency Control Benchmarks And Patterns

Use this reference when `concurrency-control` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, invariants, evidence, output, and gates; use this file for mechanism matrices, deadlock and TOCTOU decision trees, lease/fencing patterns, worker partitioning, graph/memory/trajectory coupling, validation evidence, and anti-pattern review.

## Benchmark Anchors

- Herlihy and Shavit, "The Art of Multiprocessor Programming": lock-free and wait-free algorithm foundations.
- Gray and Reuter, "Transaction Processing": isolation levels, locking, deadlock, and transaction-processing theory.
- ANSI/ISO SQL isolation levels, MVCC, two-phase locking, serializable snapshot isolation, and database-specific lock modes.
- PostgreSQL row-level/advisory locks, `SKIP LOCKED`, and MySQL InnoDB gap/next-key locks.
- Optimistic locking patterns: ETag / `If-Match`, `row_version`, `xmin`, and event-stream position.
- Lamport logical clocks, Google Spanner external consistency, CockroachDB SSI, and Kleppmann consistency/consensus guidance.
- ZooKeeper, etcd, and Consul leases with linearizable guarantees and fencing-token discipline.
- Kafka consumer group partitioning, SQS visibility timeout, and at-least-once broker semantics.
- CRDT and Operational Transformation for coordination-free collaborative updates.
- OWASP concurrency testing for TOCTOU and race-condition abuse paths.

## Mechanism Selection Matrix

| Scenario | Preferred mechanism | Avoid |
| --- | --- | --- |
| Financial balance update | Pessimistic row lock or Serializable isolation. | Optimistic-only design under high conflict. |
| Inventory decrement | Atomic `UPDATE ... WHERE qty > 0` and affected-row check. | Read-then-write TOCTOU. |
| Idempotent resource creation | Unique constraint plus idempotency key. | Separate SELECT then INSERT. |
| Read-mostly resource with rare write | Optimistic locking with actionable conflict response. | Broad pessimistic lock by default. |
| Distributed task dedupe | Durable idempotency table with unique key and expiry. | In-memory dedupe lost on restart. |
| Distributed leader or lease | Linearizable lease plus fencing token. | Redis lock for correctness-critical ownership without risk acceptance. |
| Hot counter or quota | Sharded counter, atomic increment, or approximate aggregate. | Single hot row at high write rate. |
| Worker queue parallelism | Partition key by resource ID or deterministic claim strategy. | Global consumer lock. |
| Multi-resource reservation | Saga/outbox with compensation and idempotent consumers. | Distributed 2PC in ordinary microservice workflows. |
| Collaborative editing | CRDT or OT with merge semantics. | Last-write-wins when data loss is unacceptable. |

## Deadlock Decision Tree

```text
Does the operation lock more than one resource?
  No:
    Deadlock risk is lower, but require timeout and lock-release proof.
  Yes:
    Is the lock order canonical across every code path?
      No:
        Define a stable order such as resource type then primary key ascending.
      Yes:
        Does any lock span network, storage, queue, or user I/O?
          Yes:
            Redesign to release before I/O or use optimistic conflict detection.
          No:
            Bound lock duration, emit lock-wait metric, and stress test.
```

## TOCTOU Decision Tree

```text
Does the code read a value, decide, then write?
  No:
    Lower TOCTOU risk.
  Yes:
    Is check-and-act atomic?
      Yes:
        Verify the atomic statement, CAS, unique constraint, or serializable transaction.
      No:
        Choose one:
        - collapse into atomic SQL / CAS;
        - lock before read;
        - use optimistic version check and 409 conflict;
        - use Serializable isolation and retry serialization failures.
```

## Distributed Lease And Fencing

Correctness-critical leases need a monotonic token that downstream storage enforces.

1. Acquire a lease from a linearizable coordinator; record revision or zxid.
2. Attach the token to every write in the lease window.
3. Storage rejects writes with a token lower than the highest accepted token.
4. On expiry or failed refresh, stop writes before attempting reacquisition.
5. If two actors believe they hold the lease, fencing lets only the newer owner mutate.

Redis `SET NX EX` can be acceptable for advisory work where duplicated work is tolerable. It is not sufficient for correctness-critical financial, inventory, permission, or ownership writes without a documented residual-risk owner.

## Worker Parallelism Patterns

| Pattern | Fit | Required evidence |
| --- | --- | --- |
| Partition by resource ID | Per-resource ordering matters and partition count can absorb load. | Partition key, rebalance behavior, lag metric, idempotent handler. |
| Claim rows with `SKIP LOCKED` | Database-backed work queue with many workers. | Claim transaction, visibility/timeout, handler idempotency, retry/DLQ. |
| Sharded locks | Hot resource needs bounded local serialization. | Shard function, skew analysis, lock metric, collision behavior. |
| Bounded worker pool | Fan-out or I/O parallelism needs a ceiling. | Pool size, queue depth, backpressure, cancellation, saturation metric. |
| Single-flight | Many requests compute same expensive result. | Key scope, timeout, error propagation, stampede test. |

## Graph, Memory, And Trajectory Coupling

Treat repository graph, project memory, and execution trajectory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current transaction code, lock usage, idempotency tables, queue workers, tests, and callers are inspected. | Graph proximity is treated as proof that all mutation paths share the same guard. |
| Project memory | Prior lock/idempotency design still matches current source, schema, queue topology, and worker count. | Memory predates a schema, broker, worker, retry, or service split change. |
| Execution trajectory | Race/stress/validator output ran after the final concurrency edit. | Validation predates the current lock/idempotency/worker change. |
| Incident or flake history | Signature maps to current resource, actor, worker, and test name. | "Flaky" or "intermittent" is used without reproducible overlap scenario. |
| Generated artifacts | Migrations, generated clients, queue schemas, or docs were refreshed after the change. | Generated contract still describes old conflict behavior. |

Strong outputs state which graph, memory, and trajectory inputs were accepted, rejected, or left unknown.

## Validation Evidence Patterns

- Atomic update proof: concurrent test where exactly one update succeeds and invariant holds.
- Optimistic conflict proof: stale version update returns conflict and actionable retry/refresh guidance.
- Idempotency proof: duplicate key returns replay/in-flight response; same key with different payload is rejected.
- Queue worker proof: redelivery/retry does not duplicate side effects; DLQ or terminal state is observable.
- Deadlock proof: two or more lock-order paths are stress-tested with canonical order and timeout.
- Lease proof: stale fencing token write is rejected after a newer token succeeds.
- Hot-row proof: lock-wait/conflict metric, benchmark/profile, or explicit not-verified production contention limit.
- Publish safety proof: event is written outbox/post-commit and no event is delivered after rollback.
- Runtime proof: race detector, sanitizer, stress, or language-specific concurrency tool output where applicable.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| `if balance >= amount: balance -= amount` without lock or atomic write. | Two concurrent requests both pass and overdraw. | Atomic SQL, row lock, or serializable transaction. |
| Full-table `SELECT ... FOR UPDATE` under concurrent workers. | Wide lock contention and deadlock. | Narrow predicate, ordered row locks, partitioned worker claims. |
| Redis lock with no expiry. | Holder crashes and stalls all workers. | TTL, release path, watchdog, or coordinator lease. |
| App-only idempotency check without unique index. | Two requests pass before insert. | Unique constraint or atomic insert. |
| Publish event before commit. | Consumer sees phantom event after rollback. | Outbox in same transaction or post-commit hook. |
| Worker handler sends external side effect on every retry. | Duplicate email, charge, webhook, or notification. | Handler-level idempotency and terminal state. |
| Optimistic conflict returns 500. | Caller cannot distinguish retryable conflict from server fault. | 409 with version/refresh guidance. |
| `SKIP LOCKED` without idempotent side effect. | Row is reprocessed after failure. | Idempotent handler, checkpoint, retry/DLQ. |
| Lock held across external API call. | Slow dependency stalls every waiting actor. | Commit intent, release lock, call external API, reconcile result. |
| Single hot counter row at high traffic. | Writes serialize and p99 grows with load. | Sharded counter or approximate aggregate. |
| Serial-only test for overlap-sensitive path. | CI never exercises race. | Deterministic parallel/stress test. |

## Handoff Boundaries

- Use `transaction-consistency` when the unresolved decision is isolation level, transaction scope, atomicity, outbox, or saga compensation.
- Use `idempotency-retry-design` when duplicate effect prevention, payload fingerprint, DLQ, or retry policy is primary.
- Use `async-job-design` when worker lifecycle, scheduling, state transitions, retries, or reconciliation jobs dominate.
- Use `message-queue-design` when broker topology, partitions, retention, DLQ, or replay semantics dominate.
- Use `language-performance-safety` when race detector, sanitizer, thread pool, event-loop, cancellation, unsafe/FFI, or runtime-specific synchronization matters.
- Use `profiling` when measured contention, hot row, lock wait, pool saturation, or throughput cliff is primary.
- Use `observability` or `reliability-observability-gate` when production metrics, alerts, dashboards, or runbook ownership are unresolved.
