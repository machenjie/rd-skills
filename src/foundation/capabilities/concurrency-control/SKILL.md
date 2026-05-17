---
name: concurrency-control
description: Designs race, duplicate-submit, lock, optimistic concurrency, deadlock, and worker parallelism controls with deterministic conflict behavior.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "67"
changeforge_version: 0.1.0
---

# Mission

Prevent **lost updates, phantom reads, duplicate effects, deadlocks, and race-dependent invariant violations** by identifying every shared resource and its invariant, choosing the right concurrency control mechanism per conflict profile, and producing deterministic, documented conflict behavior that survives parallel workers, retries, and duplicate submissions.

# When To Use

Use this capability when a change involves: concurrent writes to a shared resource (database rows, counters, balances, inventory, quotas, slots, seats, leases), duplicate-submit risk (double-click, network retry, message redelivery), background workers or job queues with parallel consumers, distributed locks or leases, optimistic locking / versioning (ETags, `row_version`, event stream position), compare-and-swap or atomic operations, queue partition design, shared in-memory state across threads or goroutines/coroutines, cross-service reservation workflows, or any path where the same mutation can be triggered from more than one actor simultaneously.

# Do Not Use When

Do not use this capability to add broad table locks without identifying the specific invariant they protect — that inflates contention unnecessarily. Do not use it to hide unsafe side effects behind retry loops. Do not conflate atomicity (which belongs to `transaction-consistency`) with concurrency control. Concurrency control protects an invariant under simultaneous access; transaction atomicity ensures all-or-nothing commit.

# Non-Negotiable Rules

- **Name the invariant** before choosing a mechanism. "Inventory never goes below zero," "balance never exceeds credit limit," "each job executes exactly once per trigger." Without a named invariant, the choice of mechanism is guesswork.
- **Choose the narrowest scope of control.** Row-level locking beats table-level; atomic increment beats read-modify-write; partition-level queue routing beats global lock.
- **Define conflict behavior explicitly**: the system either retries (idempotent safe path), rejects with an actionable message, applies a merge/CRDTs strategy, or escalates to human. "Undefined" is not a behavior.
- **Timeout and release every lock and lease.** Unbounded locks cause permanent stalls and cascading service failures. Maximum hold time must be documented and enforced.
- **Lock ordering is deterministic.** When multiple resources are locked in sequence, the order is the same across all code paths. Inversion = deadlock.
- **Fencing tokens for distributed leases.** After acquiring a lease, attach a monotonic fence token (e.g., etcd revision, ZooKeeper zxid) to every operation within the lease window; reject operations from older tokens. Prevents stale-leader writes after lease expiry.
- **Idempotency keys for duplicate-submit protection.** Any action that can be retried or redelivered must carry a client-supplied idempotency key; the server must deduplicate within the retention window. (See also `idempotency-retry-design`.)
- **Optimistic concurrency must return a useful conflict response.** HTTP 409 with instructions on how to re-read and retry is acceptable; HTTP 500 is not. The version/ETag must identify what changed.
- **Queue workers must be idempotent, not just de-duplicated at enqueue.** Messages are delivered at-least-once in all major brokers (Kafka, SQS, RabbitMQ, Pub/Sub); assume re-delivery.
- **Concurrency tests are mandatory for high-risk paths.** Serial unit tests do not exercise races. At minimum: a concurrent-execution test with N goroutines/threads; for critical financial paths, a stress/chaos test under realistic load.
- **Never use `SELECT ... FOR UPDATE` on a full table scan.** Combined with a concurrent transaction doing the same scan → guaranteed deadlock.
- **Publish domain events or side effects only after the invariant is committed.** Publish-before-commit = inconsistent event stream on rollback. Outbox pattern required.
- **Document contention characteristics.** Hot rows, hot partition keys, hot counters require specialized strategies (sharded counters, eventual-aggregate, approximate count) or they become latency bottlenecks.

# Industry Benchmarks

Anchor against: **Herlihy & Shavit — "The Art of Multiprocessor Programming"** for lock-free and wait-free algorithm foundations. **Gray & Reuter — "Transaction Processing: Concepts and Techniques"** for isolation levels and locking theory. **ANSI/ISO SQL-92** isolation levels (Read Uncommitted / Read Committed / Repeatable Read / Serializable). **PostgreSQL row-level locking** (`SELECT FOR UPDATE`, `FOR NO KEY UPDATE`, `FOR SHARE`, `FOR KEY SHARE`), advisory locks, and `SKIP LOCKED` for queue patterns. **MySQL InnoDB gap locks and next-key locks** (source of many accidental deadlocks). **MVCC (Multi-Version Concurrency Control)** — Postgres, Oracle, CockroachDB, Spanner use MVCC to give readers consistent snapshots without blocking writers; understand snapshot vs serializable isolation. **Optimistic locking patterns**: ETag / `If-Match` (RFC 7232), `row_version` / `xmin`, event-stream position. **Google Spanner** external consistency model. **CockroachDB Serializable Snapshot Isolation (SSI)**. **Martin Kleppmann — "Designing Data-Intensive Applications"** Ch. 7 (transactions) and Ch. 9 (consistency and consensus) for linearizability, causal consistency, and two-generals awareness. **Leslie Lamport — "Time, Clocks, and the Ordering of Events"** for logical clocks. **Fencing tokens** pattern (Kleppmann 2016 blog). **Redis SETNX / SET NX EX** for distributed mutex; Redis Redlock and its documented limitations (split-brain, clock drift). **ZooKeeper / etcd / Consul** leases for distributed locks with linearizable guarantee. **Kafka consumer group partition assignment** for queue worker concurrency without locking. **AWS SQS visibility timeout + approximate deduplication** for at-least-once message processing. **CRDT (Conflict-free Replicated Data Types)** — Shapiro et al. 2011 — for eventual-consistent multi-master without coordination. **Sharded counter pattern** (write to N shards, aggregate asynchronously) for hot counters. **"Two-Phase Locking (2PL)"** and **"Serializable Snapshot Isolation (SSI)"** for database-level concurrency theory. **OWASP Concurrency Testing** guide (TOCTOU attacks, race conditions in authentication).

### Concurrency Control Mechanism Selection

| Scenario | Preferred mechanism | Avoid |
| --- | --- | --- |
| Financial balance update | `SELECT ... FOR UPDATE` (pessimistic row lock) or Serializable isolation | Optimistic (too many conflicts under high load) |
| Inventory decrement | Atomic `UPDATE SET qty = qty - 1 WHERE qty > 0` + row affected check | Read-then-write (TOCTOU) |
| Idempotent resource creation | `INSERT ... ON CONFLICT DO NOTHING` + idempotency key | Separate SELECT then INSERT (race window) |
| Read-mostly resource with rare write | Optimistic locking (ETag / row_version), retry on conflict | Pessimistic lock (blocks all readers in some DBs) |
| Distributed task deduplication | Idempotency key table with `UNIQUE` + expiry | In-memory dedup (lost on restart) |
| Distributed leader election / lease | etcd/ZooKeeper/Consul lease + fencing token | Redis SETNX without expiry or Redlock in split-brain environment |
| Hot counter (page views, rate limit) | Sharded counter (N DB rows) or Redis INCR | Single row `UPDATE` under high concurrency (hot row bottleneck) |
| Worker queue parallelism | Kafka partition key = resource id (natural partitioning) | Global consumer lock |
| Multi-resource reservation (seat + payment) | Saga (choreography/orchestration) with compensating transactions | Distributed 2PC (too fragile in microservices) |
| Collaborative editing | CRDT (Yjs, Automerge) or OT (Operational Transformation) | Last-write-wins (silent data loss) |
| Cache-backed counter | Redis INCR + periodic flush to DB with compare-and-swap | Cache as source of truth (data loss on eviction) |

### Deadlock Avoidance Decision Tree

```
Does the operation lock more than one resource?
├─ No  → Deadlock risk is low; ensure timeout.
└─ Yes →
    Is the locking order consistent across all code paths?
    ├─ No  → DEADLOCK RISK: enforce canonical order (e.g., by primary key ascending).
    └─ Yes →
        Do any locks span a network call (to external service, queue, user input)?
        ├─ Yes → Extremely high deadlock/stall risk:
        │         Release lock before network call, OR
        │         Use optimistic approach (no lock; detect conflict on write).
        └─ No  →
            Are lock durations bounded with hard timeout?
            ├─ No  → Add timeout + monitoring for stuck lock holders.
            └─ Yes → Proceed; monitor lock wait histogram.
```

### Race Condition (TOCTOU) Decision Tree

```
Does the code read a value, then make a decision, then write?
(Read-Check-Act pattern)
├─ No  → Low TOCTOU risk.
└─ Yes →
    Is the check + act atomic (e.g., UPDATE WHERE condition, CAS, INSERT ON CONFLICT)?
    ├─ Yes → Safe.
    └─ No  → TOCTOU race:
              Option A: Collapse read+check+act into a single atomic statement.
              Option B: Acquire pessimistic lock before read.
              Option C: Use optimistic version check; reject on mismatch.
              Option D: Use serializable isolation (all reads re-verified at commit).
```

### Distributed Lease / Fencing Token Pattern

```
1. Acquire lease: etcd/ZooKeeper grant with revision R.
2. Attach fence token R to every write operation in the lease window.
3. Storage / downstream service: REJECT any write with token < max_seen_token.
4. On lease expiry: client must stop writes and re-acquire.
5. Split-brain: two processes both believe they hold the lease —
   fencing ensures only the newer token's writes succeed.
```

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `if balance >= amount: balance -= amount` without lock | Two concurrent requests both read 100, both see ≥ 50, both deduct → balance goes negative |
| `SELECT ... FOR UPDATE` on full-table scan in two concurrent txns | Guaranteed deadlock; DB kills one txn; unpredictable behavior under load |
| Redis SETNX with no expiry | Holder crashes; lock held forever; service stalls indefinitely |
| Idempotency key checked in application but not unique-indexed | Race between two identical requests at DB layer both pass in-app check → duplicate record |
| Publish event before commit | Transaction rolls back; event already delivered; consumer processed a phantom operation |
| Worker retries message without idempotency; handler sends email | Duplicate email on each retry/redelivery |
| Optimistic lock returns HTTP 500 on conflict | Caller cannot distinguish server error from conflict; cannot implement correct retry |
| `SKIP LOCKED` used in queue but side effect not idempotent | Row reprocessed after failure; duplicate charge |
| Distributed lock held across external API call | External API slow/unreachable; lock held for minutes; all other workers stall |
| Sharded counter not used for high-traffic page-view counter | Single row hot-spot; writes serialize; response time degrades linearly with load |

# Selection Rules

Select this capability when **simultaneous execution is the primary risk**. Adjacent routing:

- Prefer `transaction-consistency` when atomicity (all-or-nothing commit) and isolation level selection are primary.
- Prefer `idempotency-retry-design` when duplicate execution, message redelivery, and retry strategies dominate.
- Prefer `async-job-design` when worker lifecycle, queue design, and job state management are primary.
- Prefer `profiling` when lock contention, hot-row, or throughput measurement is primary.
- Use **with** `transaction-consistency` for serializable isolation and 2PL interactions.
- Use **with** `idempotency-retry-design` for idempotency key lifecycle.

# Risk Escalation Rules

Escalate when races affect: money or financial balances, inventory or reservation slots, quotas or rate limits, permissions or account ownership, scheduled job deduplication, distributed worker fan-out, cross-service reservation workflows, high-traffic endpoints (> a few hundred TPS on a shared row), or any path where conflict recovery is undocumented. Escalate any distributed lock that requires fencing tokens but does not have them (Redlock on clock-drift-sensitive systems). Escalate any optimistic-conflict handling that returns a non-actionable error to the caller.

# Critical Details

Concurrency control is about **preserving a named invariant under overlap**. The mechanism choice is derived from the invariant and the conflict rate, not from habit. Key refinements:

- **TOCTOU (Time of Check / Time of Use) is everywhere.** Any `read → decide → act` sequence without atomicity is a TOCTOU race. SQL `UPDATE WHERE condition` collapses all three atomically and is the default weapon.
- **At-least-once delivery is not a footnote.** Kafka, SQS, RabbitMQ, Google Pub/Sub all guarantee at-least-once. Exactly-once delivery requires idempotent handlers and idempotency key deduplication at the consumer — not just at the producer.
- **Optimistic locking conflict rate matters.** If a resource is updated by 10 concurrent writers and the retry on conflict retries up to 3 times, contention escalates non-linearly. Pessimistic locking is more efficient when conflict rate > ~20%.
- **Deadlocks are preventable, not just detectable.** Canonical lock order (e.g., always lock by `id ASC`) eliminates lock-order inversions. Lock-wait graphs and `pg_locks` / `SHOW ENGINE INNODB STATUS` are investigative tools for when prevention fails.
- **The outbox pattern closes the publish-before-commit gap.** Write the event as a row in an outbox table within the same transaction; a separate process reads the outbox and publishes. Guarantees at-least-once event publication without split commitment.
- **Leaky time window in optimistic locking.** MVCC snapshot isolation allows two transactions to each read the same version and both write conflicting updates; only serializable isolation (SSI) fully prevents write-skew anomalies.
- **Sharded counters.** A single row updated by thousands of requests per second becomes a hot-row bottleneck. Write to N shards in parallel (shard = hash(writer_id) % N); aggregate asynchronously. Redis `INCR` on a distributed key is an alternative.
- **Queue partition routing.** Kafka partition key = resource id ensures all events for a given resource are processed by the same consumer in order, eliminating the need for distributed locks for per-resource serialization.
- **Redis Redlock limitations.** Redlock (multi-node Redis quorum lock) has known failure modes under clock drift and network partition. For correctness-critical locks (financial, inventory) use etcd or ZooKeeper with linearizable guarantees + fencing tokens. Redis `SETNX NX EX` is acceptable for advisory locks (cache warming, background dedup) where silent loss is tolerable.
- **Stale read and read-your-writes.** After a write, the writer may read from a replica that has not yet caught up. Cache invalidation and read-your-writes guarantees need explicit handling.
- **Concurrency at the application layer.** Multiple threads / goroutines / async tasks sharing in-process state without a mutex or channel = data race. Go race detector, Java `-ea` assertions, Python threading lock, Rust's ownership system — use the language's tooling.
- **Testing.** `go test -race`, JUnit `@RepeatedTest` with `ExecutorService`, `asyncio.gather` storm tests, property-based testing (Hypothesis) with shrinking, Jepsen for database-level correctness verification. Serial tests do not expose races.

# Failure Modes

- Two concurrent withdrawals both pass the balance check; both succeed; balance goes negative.
- Duplicate form submission creates two orders for one intended purchase; no idempotency key.
- Lock ordering inconsistent across two code paths; infrequent but reproducible deadlock under load.
- Redis distributed lock has no expiry; service crashes holding lock; all workers stall permanently.
- Worker retries a message; handler side effects (email, charge, webhook) fire on every retry without idempotency.
- Event published before transaction commits; transaction rolls back; consumer receives a phantom event.
- Optimistic lock conflict returns 500; caller cannot retry correctly; data left in stale state.
- `SKIP LOCKED` queue worker re-fetches a failed row; non-idempotent handler causes duplicate billing.
- Distributed lock acquired but no fencing token; stale leader writes after lease expiry; split-brain data corruption.
- Sharded counter not used; single hot row serializes writes; p99 latency degrades 10× under load.
- Serializable isolation not used for read-modify-write; write-skew anomaly allows two concurrent operations to each read consistent but together produce a forbidden state.
- Saga compensation not implemented; reservation succeeds, payment fails, inventory permanently reserved.
- Test only runs operations serially; race never triggered in CI; ships to production.
- Lease held across external API call; external API times out; lease held for minutes; all other lease seekers queue.

# Output Contract

Return a concurrency design with, per shared resource or invariant:

- `resource` (name, system, key/row scope)
- `invariant` (the property that must hold under concurrent access)
- `actors` (who can mutate: services, workers, user-initiated, scheduled jobs, migrations)
- `race_scenarios` (enumerated: specific scenario → consequence if unprotected)
- `mechanism` (optimistic / pessimistic row lock / atomic SQL / CAS / advisory lock / distributed lease / queue partition / CRDT / sharded counter)
- `lock_scope` (row / partition / queue topic / in-process / distributed)
- `lock_ordering` (if multiple; canonical order)
- `max_lock_duration` (ms; timeout enforcement mechanism)
- `fencing` (fencing token source and enforcement — for distributed leases)
- `conflict_behavior` (retry with backoff / reject with 409 and instructions / merge / escalate; documented per actor)
- `duplicate_submit_handling` (idempotency key source, storage, dedup window, scope)
- `event_publish_safety` (outbox / transactional outbox / post-commit hook; no publish-before-commit)
- `deadlock_risk` (analysis; ordering controls)
- `hot_spot_risk` (contention profile; sharding strategy if needed)
- `observability` (lock wait time, conflict rate, deadlock count, idempotency hit rate, queue depth)
- `tests` (concurrent-execution test, idempotency test, conflict-response test, deadlock stress test)

# Quality Gate

The concurrency design passes only when:

1. Every shared resource has a named invariant.
2. Mechanism is justified against conflict rate and failure consequence (not default choice).
3. All locks and leases have bounded duration with timeout enforcement.
4. Lock ordering is canonical across all code paths; deadlock scenario analyzed.
5. Distributed leases use fencing tokens; rejection of stale tokens enforced at storage.
6. Duplicate-submit paths have idempotency keys with unique-indexed server-side storage.
7. Queue workers are idempotent for at-least-once delivery; side effects verified.
8. Events published via outbox or post-commit hook; never before commit.
9. Hot rows/counters have sharding or atomic operations; contention profile documented.
10. Conflict behavior returns actionable error; callers can implement correct retry/resolve.
11. Concurrency tests (not just serial tests) exist for high-risk invariants.
12. Observability: lock wait, conflict rate, deadlock alert wired.

# Used By

- reliability-observability-gate
- backend-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `transaction-consistency` for isolation level selection and atomicity; `idempotency-retry-design` for retry strategies and idempotency key lifecycle; `async-job-design` for queue worker lifecycle; `profiling` for lock contention and hot-row measurement; `observability` for lock-wait and deadlock alerting.

# Completion Criteria

The capability is complete when **every concurrency-sensitive path has a named invariant, a justified control mechanism, bounded lock duration, deterministic conflict behavior, duplicate-submit protection, event-publish safety via outbox, and concurrent-execution test evidence** — with no hidden races or silent invariant violations under parallel load.
