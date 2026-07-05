# Transaction Consistency Benchmarks And Patterns

Use this reference when the main skill selects deep isolation, locking, outbox, saga, reconciliation, compensation, or graph-memory-execution review. Treat it as guidance, not proof; closure still requires current source and fresh validation.

## Benchmark Anchors

- ACID: atomicity, consistency, isolation, and durability define the local transaction baseline.
- ANSI SQL isolation: Read Uncommitted, Read Committed, Repeatable Read, Serializable; each trades anomaly prevention for concurrency cost.
- MVCC systems: PostgreSQL, MySQL/InnoDB, SQL Server, and Oracle differ in default isolation and lock behavior; verify the target datastore.
- Designing Data-Intensive Applications: dirty read, non-repeatable read, phantom read, lost update, write skew, serializable snapshot isolation, and compare-and-swap.
- Optimistic concurrency control: version column, compare-and-swap, conflict detection at commit, and explicit conflict response.
- Pessimistic locking: `SELECT ... FOR UPDATE`, lock ordering, lock timeout, deadlock retry, and `SKIP LOCKED` work claiming.
- Transactional Outbox and Inbox: local atomicity with at-least-once delivery and idempotent consumers.
- Saga pattern: forward local transactions with compensating actions, persisted step state, and operator-visible failure.
- Two-Phase Commit/XA: distributed atomicity with availability coupling and coordinator failure risk; use only with explicit justification.
- SRE recovery practice: reconciliation, drift detection, runbook ownership, and freshness SLOs close eventual consistency risk.

## Isolation Anomaly Matrix

| Anomaly | Failure shape | Prevention choice | Validation signal |
| --- | --- | --- | --- |
| Dirty read | Reads uncommitted data that later rolls back. | Read Committed or stronger. | Transaction fixture proves rolled-back data is invisible. |
| Non-repeatable read | Same row changes between reads. | Repeatable Read, explicit lock, or re-read semantics. | Concurrent update fixture shows stable or intentionally refreshed value. |
| Phantom read | Range query changes after concurrent insert/delete. | Serializable, predicate lock, constraint, or explicit range lock. | Concurrent range/insert fixture preserves invariant. |
| Lost update | Two writers overwrite each other. | Version check, row lock, conditional update, or serializable retry. | Concurrent writer test leaves one accepted outcome or one conflict. |
| Write skew | Two writers read same set and update disjoint rows to violate a set invariant. | Serializable, constraint, aggregate row lock, or remodel. | Write-skew fixture fails one transaction or preserves set invariant. |
| Deadlock | Transactions acquire locks in opposite order. | Consistent lock order, short scope, timeout, retry. | Deadlock simulation or lock-order review with retry behavior. |

## Consistency Pattern Decision

```text
Is the invariant local to one authoritative datastore?
  yes -> use a local transaction with the minimum isolation and lock scope needed.
  no  -> can ownership be remodeled so the invariant is local?
           yes -> remodel and avoid distributed consistency.
           no  -> choose outbox, saga, reconciliation, or justified 2PC.

Does the transaction call a remote provider or slow side effect?
  yes -> write intent, commit, release locks, then call externally; record result or compensate.

Can eventual consistency be tolerated?
  yes -> outbox/inbox plus idempotent consumer and reconciliation.
  no  -> saga with explicit compensation, or block until invariant can be localized.
```

## Locking And Conflict Patterns

- Prefer database constraints for uniqueness and invariant enforcement when a constraint can express the rule.
- Use optimistic locking when conflicts are uncommon and user or worker retry is acceptable.
- Use pessimistic row locks when conflict is common, the critical section is short, and lock order is controlled.
- Use Serializable when set-based invariants cannot be protected with a simpler constraint or lock.
- Treat serialization failures and deadlocks as expected retryable states with bounded retry and visible terminal behavior.
- Avoid lock expansion through ORM lazy loading, callbacks, logging hooks, or remote calls inside transaction scope.

## Outbox, Saga, And Reconciliation

| Pattern | Use when | Required evidence |
| --- | --- | --- |
| Transactional outbox | Local state change must publish an event after commit. | Source row and outbox row commit atomically; relay is monitored; consumer is idempotent. |
| Inbox/dedupe table | Consumer may receive duplicate events. | Processed key is recorded before ack/offset commit; duplicate replay is harmless. |
| Saga orchestration | Multiple local transactions need ordered compensation. | Step log, compensation log, retry policy, stuck-saga alert, manual runbook. |
| Reconciliation job | Derived/external state may drift. | Drift query, SLA, owner, remediation command, and idempotent repair. |
| 2PC/XA | True atomicity across participants is mandatory and availability cost is accepted. | Failure-mode analysis, timeout behavior, coordinator recovery, rollback limits. |

## Graph, Memory, And Execution Coupling

- Use repository graph to find handlers, service methods, repositories, ORM callbacks, migrations, event publishers, outbox relays, consumers, retry wrappers, and affected tests.
- Use project memory only as a lead for known fragile transaction paths, deadlocks, lost updates, or incident history.
- Reject prior validation when transaction boundaries, lock order, migrations, queue topics, consumers, retry wrappers, or side-effect adapters changed after the run.
- Compare same-pattern write paths before changing one transaction; sibling services often share the same lost-update or event-before-commit risk.
- Link every closure claim to current source paths and fresh command output; do not infer production lock or replica behavior from unit tests alone.

## Validation Matrix

| Consistency concern | Example validation |
| --- | --- |
| Named invariant | Unit or integration test that fails when invariant protection is removed. |
| Lost update | Concurrent requests or transactions leave one success/one conflict or exact expected aggregate. |
| Write skew or phantom | Concurrent range/set update fixture preserves the set invariant. |
| Deadlock or timeout | Lock-order review plus bounded retry/timeout test where practical. |
| Remote call placement | Source review or integration fixture proves provider call happens after commit/release. |
| Outbox atomicity | Transaction rollback removes both source row and outbox row; commit persists both. |
| Consumer idempotency | Duplicate event/message creates one durable side effect. |
| Saga compensation | Failure at each step records and runs compensator in reverse order. |
| Reconciliation | Drift fixture is detected and repaired or marked for manual owner action. |
| Validation freshness | Final edit occurs before targeted and full validators used for handoff. |

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| One broad transaction around validation, DB writes, provider call, event publish, cache update, and response formatting. | Locks remain open across slow work and unrelated operations, creating contention and unclear rollback. |
| `catch OptimisticLockException {}` or retry forever. | Lost update is hidden or contention is amplified without terminal behavior. |
| Publish event before commit because "it usually works." | Consumers observe rolled-back state after transaction failure. |
| Use 2PC because two services write in one use case. | Availability coupling and coordinator failure are accepted without proving atomicity is required. |
| Saga compensation reads current mutable state instead of persisted compensation parameters. | Compensation can fail or undo the wrong value after later changes. |
| Unit-only proof for a database isolation claim. | Isolation, locks, deadlocks, and phantoms require datastore-aware evidence or explicit limits. |
