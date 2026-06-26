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

# Stage Fit

Own concurrency design during planning, implementation review, testing, and repair when simultaneous execution can break an invariant, duplicate a side effect, deadlock, starve a worker pool, or make conflict handling nondeterministic. In planning, turn current source, transaction boundaries, queues, workers, locks, repository graph, project memory, execution trajectory, and validation history into a scoped concurrency plan before implementation. In review, reject stale memory about "safe" locks, serial-only tests, lock choices without named invariants, hidden side effects before commit, unbounded fan-out, and conflict behavior that callers cannot act on. Hand off when the unresolved question is transaction atomicity, retry/idempotency lifecycle, async worker state, profiling, observability, or language-specific runtime safety.

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

# Mode Matrix

Select the concurrency mode before choosing locks, versions, queue routing, leases, or worker parallelism.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Shared-resource invariant | Concurrent writes to row, counter, balance, inventory, quota, slot, seat, or reservation. | Preserve named invariant with narrow control scope and deterministic conflict handling. | Resource/invariant map, actor list, race scenarios, mechanism rationale. | `transaction-consistency`, `quality-test-gate` | Distributed lease unless resource crosses process/service boundary. |
| Duplicate effect prevention | Double-submit, retry, message redelivery, webhook replay, worker reprocessing, or side-effecting command. | Ensure repeated execution produces one committed effect or one replayed result. | Idempotency key scope, dedupe store, payload fingerprint, retention, duplicate test. | `idempotency-retry-design`, `regression-testing` | Broad lock if unique constraint or idempotency store is enough. |
| Worker parallelism and ordering | Parallel consumers, partition keys, fan-out, queue claims, `SKIP LOCKED`, or worker pool changes. | Bound concurrency and preserve per-resource ordering without global bottlenecks. | Partition/claim strategy, idempotent handler, backpressure, queue depth/lag evidence. | `async-job-design`, `message-queue-design`, `reliability-observability-gate` | Exactly-once claims without handler idempotency. |
| Distributed lease or leader | Distributed lock, lease, leader election, ownership handoff, cache warming, or singleton worker. | Prevent stale-owner writes and permanent stalls. | Lease provider guarantee, TTL, fencing token, stale-token rejection, timeout/release test. | `language-performance-safety`, `low-level-systems-extension` when runtime primitives matter | Redis/Redlock for correctness-critical ownership without risk acceptance. |
| Contention and deadlock repair | Deadlock, hot row, lock wait, race detector failure, pool starvation, or throughput cliff. | Verify cause, reduce lock scope, define order, measure contention, add regression/stress evidence. | Repro, lock-wait evidence, same-pattern scan, before/after stress or profile. | `profiling`, `failure-diagnosis`, `reliability-observability-gate` | Blind retry or wider lock as the first fix. |

# Industry Benchmarks

Anchor against multiprocessor correctness, SQL isolation and MVCC, row-level/advisory locks, optimistic locking (`ETag`, `row_version`, event position), linearizable lease systems, fencing-token discipline, at-least-once broker semantics, CRDT/OT collaboration patterns, sharded counters, and OWASP race-condition/TOCTOU testing. Keep this body focused on selection, routing, evidence, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for mechanism matrices, deadlock and TOCTOU decision trees, lease/fencing patterns, graph/memory/trajectory coupling, validation evidence patterns, and anti-pattern detail.

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

# Proactive Professional Triggers

- **Signal:** project memory, repository graph, or prior execution says a path is "already locked", "idempotent", "single worker", or "safe to retry" without current source/test confirmation. **Hidden risk:** stale concurrency assumptions preserve a race introduced after the remembered design. **Required professional action:** confirm current lock, idempotency store, worker topology, tests, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, current-source proof, and freshness limits.
- **Signal:** code reads state, decides, then writes (`read-check-act`) under possible overlap. **Hidden risk:** TOCTOU race or lost update. **Required professional action:** collapse check-and-act into atomic statement, lock before read, or add optimistic version conflict handling. **Route to:** `transaction-consistency`, `data-middleware-change-builder`. **Evidence required:** atomic SQL/CAS/version check and concurrent test.
- **Signal:** duplicate-submit, retry, redelivery, `SKIP LOCKED`, or worker reprocessing can repeat a side effect. **Hidden risk:** duplicate charge, duplicate email, duplicate order, or replayed webhook. **Required professional action:** require durable idempotency and handler-level duplicate safety. **Route to:** `idempotency-retry-design`, `async-job-design`. **Evidence required:** unique-indexed dedupe, payload fingerprint, duplicate/replay test, DLQ or terminal state.
- **Signal:** multiple resources are locked, lock ordering is implicit, or a lock spans network/storage/user I/O. **Hidden risk:** deadlock, pool starvation, or cascading latency under load. **Required professional action:** define canonical lock order, shorten critical section, add timeout, and measure lock waits. **Route to:** `language-performance-safety`, `profiling`, `reliability-observability-gate`. **Evidence required:** lock-order map, timeout, contention metric, deadlock/stress test.
- **Signal:** distributed lock, leader election, or lease controls correctness, ownership, singleton work, or cross-process mutation. **Hidden risk:** stale leader writes after lease expiry or split-brain. **Required professional action:** use linearizable lease or document advisory-only risk; require fencing-token enforcement for correctness-critical writes. **Route to:** `low-level-systems-extension`, `security-privacy-gate` when privilege or data exposure is in scope. **Evidence required:** provider guarantee, fence token source, stale-token rejection test.
- **Signal:** hot counter, quota, rate limit, pool, queue, or partition key is shared by high traffic. **Hidden risk:** hot row/partition serializes throughput and hides as latency. **Required professional action:** model contention and choose sharding, partition routing, atomic operation, or approximate aggregate. **Route to:** `performance-budgeting`, `profiling`, `observability`. **Evidence required:** conflict rate, p95/p99 lock wait, queue depth, benchmark/profile or not-verified limit.

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

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 concurrency selection, invariant, mechanism, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete concurrency plan, when invariant/lock/idempotency/deadlock/test coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when mechanism choice, TOCTOU/deadlock/lease/fencing patterns, hot-row contention, worker partitioning, graph/memory/trajectory reuse, or anti-pattern detail needs depth. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Output Contract

Return a concurrency design with, per shared resource or invariant:

- `mode_selected` (shared-resource invariant, duplicate effect prevention, worker parallelism and ordering, distributed lease or leader, contention and deadlock repair)
- `concurrency_evidence` (current source paths, transaction boundaries, locks, queues, worker topology, idempotency stores, tests, repository graph, project memory, execution trajectory, and freshness limits inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each graph/memory/trajectory concurrency claim)
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
- `changed_concurrency_to_validation_map` (each resource, invariant, mechanism, lock, lease, idempotency, queue, and event-publish decision mapped to validator or residual risk)
- `handoff_boundaries` (what belongs to transaction consistency, retry/idempotency, async jobs, profiling, observability, runtime safety, security, or no-next-gate rationale)
- `evidence_limits` (what was not verified, such as all scheduler interleavings, production contention, broker redelivery behavior, replica lag, clock drift, or hidden automation)

# Evidence Contract

Close a concurrency design only when the output names selected mode, current concurrency evidence inspected, graph/memory/execution reuse judgment, each shared resource and invariant, overlap scenarios, chosen mechanism and rejected alternatives, lock/lease scope and timeout, conflict behavior, duplicate-submit handling, event-publish safety, deadlock/hot-spot analysis, changed-concurrency-to-validation map, handoff boundaries, residual risk, and evidence limits. A lock choice or "add idempotency" statement is not sufficient evidence.

# Benchmark Coverage

Improved concurrency plans should reject common weak patterns: read-check-act without atomicity, full-table `SELECT FOR UPDATE`, Redis lock without expiry, correctness-critical lease without fencing, app-only idempotency without unique storage, event publish before commit, serial-only tests for race-sensitive paths, lock held across I/O, and hot counters on a single row. Detailed matrices and examples belong in references so this body stays efficient.

# Routing Coverage

Route here when the primary work is simultaneous execution safety: races, duplicate submit, optimistic conflict, pessimistic lock, lease, lock order, worker parallelism, queue partitioning, hot-row contention, or deterministic conflict behavior. Hand off when the primary concern is transaction atomicity (`transaction-consistency`), retry/DLQ lifecycle (`idempotency-retry-design`), worker state and scheduling (`async-job-design`), runtime race tooling and lock scope (`language-performance-safety`), contention measurement (`profiling`), production telemetry (`observability` or `reliability-observability-gate`), or security impact of races (`security-privacy-gate`).

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
13. Repository graph, project memory, and execution trajectory inputs are current-source confirmed or marked not verified before they shape concurrency decisions.
14. Every resource, invariant, mechanism, lock, lease, idempotency, worker, and event-publish decision maps to validation evidence or named residual risk.
15. Handoff boundaries and evidence limits are explicit so concurrency design is not over-claimed as transaction atomicity, idempotency lifecycle, async worker readiness, production observability, or language runtime proof.

# Used By

- reliability-observability-gate
- backend-change-builder
- data-middleware-change-builder

# Handoff

Hand off to `transaction-consistency` for isolation level selection and atomicity; `idempotency-retry-design` for retry strategies and idempotency key lifecycle; `async-job-design` for queue worker lifecycle; `profiling` for lock contention and hot-row measurement; `observability` for lock-wait and deadlock alerting.

# Completion Criteria

The capability is complete when **every concurrency-sensitive path has a named invariant, a justified control mechanism, bounded lock duration, deterministic conflict behavior, duplicate-submit protection, event-publish safety via outbox, and concurrent-execution test evidence** — with no hidden races or silent invariant violations under parallel load.
