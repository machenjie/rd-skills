---
name: transaction-consistency
description: Designs minimal transaction boundaries that preserve named business invariants while avoiding avoidable distributed transactions, remote calls inside locks, over-broad contention, and mismatched consistency patterns.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "48"
changeforge_version: 0.1.0
---

# Mission

**Design the minimal transaction boundary that preserves every named business invariant — while avoiding distributed transactions, slow remote calls inside locks, and over-broad transactions that create contention — by choosing the right isolation level, concurrency control mechanism, and cross-service consistency pattern for each consistency requirement**.

# When To Use

Use this capability when: a change involves multi-step writes to a shared resource and partial application of those writes would violate a business invariant (e.g., transferring money between two accounts must be atomic); a change involves concurrent access to a record by multiple actors and lost updates, dirty reads, or phantom reads would produce incorrect behavior; a change involves a cross-service write that cannot be made atomic (two independent databases, or a database write plus an external API call) and a consistency pattern (Outbox, Saga, compensation) must be designed; or optimistic or pessimistic locking is being added to handle concurrent edit conflicts.

# Do Not Use When

Do not use this capability for: read-only queries where consistency is not a concern; single-row single-table writes with no concurrency risk and no invariant to protect; designing the message broker or queue topology (use `message-queue-design`); designing idempotency keys and retry behavior (use `idempotency-retry-design`).

# Non-Negotiable Rules

- **Start with the invariant, not the mechanism.** Every transaction boundary must be justified by a named invariant: "the account balance must never go below zero" (debit must check and update atomically); "a subscription must not exist in both ACTIVE and CANCELLED state simultaneously" (status update must be atomic with any side-effect records). A transaction that exists "because we always wrap things in transactions" with no named invariant is a transaction that creates contention without protecting anything.
- **Define isolation level explicitly and justify the choice.** The four SQL isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) exist because stronger isolation reduces concurrency and throughput. The design must name the isolation anomaly being prevented and the isolation level required to prevent it. Default to Read Committed (the PostgreSQL default). Upgrade to Repeatable Read for transactions that require consistent re-reads of the same rows. Use Serializable only for transactions that require prevention of phantom reads or serialization anomalies — and design for the serialization failure retry.
- **Never perform a slow remote call while holding a database lock.** A transaction that opens a database row-level lock, calls an external payment API (latency: 200ms–5s; failure rate: 0.1%–5%), then commits or rolls back based on the API response will hold the lock for the entire duration of the API call. Under load, this blocks all other transactions attempting to lock the same row. The pattern causes lock contention cascades and can bring down a service under moderate traffic. Fix: execute the local transaction first to record intent; release the lock; make the external call; use an outbox or compensation pattern to handle the external call's result.
- **Prefer local transaction plus event (Transactional Outbox) over distributed transactions for cross-service consistency.** A distributed transaction (2PC across two databases, or XA transactions) creates availability coupling: if either participant fails to respond, both are blocked. The Transactional Outbox pattern: write the business record and the outbox event in the same local transaction; a background relay reads the outbox and publishes to the message broker; the downstream service consumes and applies idempotently. This provides at-least-once delivery with local atomicity, without distributed coordination.
- **Optimistic locking requires explicit conflict handling that users or background workers can recover from.** Optimistic locking (version column or `updated_at` timestamp check) detects conflicts at commit time, not at read time. A conflict means two concurrent writers attempted the same update; one succeeds, one gets a `OptimisticLockException` or equivalent. The design must specify: who handles the exception (the caller retries? the user is shown a conflict warning?); what the retry strategy is (immediate retry, exponential backoff, user-prompted merge); and what happens if the conflicting update was from a different field (fine-grained or coarse-grained conflict detection).
- **Saga compensation must be designed as a first-class workflow, not an afterthought.** A Saga is a sequence of local transactions, each with a compensating transaction. If Step 3 fails, Steps 2 and 1 must be compensated in reverse order. The compensation design must specify: what data the compensation step needs (compensation log must be written before the forward step is executed); whether the compensation is synchronous or asynchronous; what happens if the compensation itself fails (retry with backoff; alert; manual intervention runbook); and whether partial compensation produces a consistent state or a temporarily inconsistent state that a reconciliation job must resolve.

# Industry Benchmarks

Anchor against: **ACID Properties (Atomicity, Consistency, Isolation, Durability)** — the foundational transaction guarantees; isolation levels per ANSI SQL (Read Uncommitted, Read Committed, Repeatable Read, Serializable). **Martin Kleppmann — Designing Data-Intensive Applications** — isolation anomalies (dirty read, non-repeatable read, phantom read, write skew, lost update); serializable snapshot isolation; compare-and-swap. **Two-Phase Commit (2PC) / XA Transactions** — distributed atomicity; coordinator failure risk; availability coupling. **Transactional Outbox Pattern (Chris Richardson, microservices.io)** — local transaction atomicity + at-least-once message delivery without 2PC. **Saga Pattern (Hector Garcia-Molina, 1987)** — sequence of local transactions; compensating transactions for rollback; choreography vs. orchestration. **Optimistic Concurrency Control (Jim Gray)** — version column; lost update prevention; conflict detection at commit time. **Pessimistic Locking (SELECT FOR UPDATE)** — row-level lock; deadlock detection; lock timeout. **PostgreSQL documentation** — MVCC; isolation level behavior; advisory locks; `FOR UPDATE SKIP LOCKED` for queue-style processing. **Two Generals Problem / CAP Theorem (Eric Brewer)** — consistency vs. availability trade-offs in distributed systems.

### Isolation Anomaly and Level Selection Matrix

| Anomaly | Description | Isolation Level to Prevent | Use Case Example |
| --- | --- | --- | --- |
| Dirty Read | Read uncommitted data from a concurrent transaction that may roll back | Read Committed | Rarely acceptable; avoid in financial systems |
| Non-Repeatable Read | Read same row twice; concurrent UPDATE changes it between reads | Repeatable Read | Inventory check-then-reserve patterns |
| Phantom Read | Read a range; concurrent INSERT adds a row to the range | Serializable | Unique constraint enforcement in application code |
| Lost Update | Two concurrent updates; one overwrites the other | Optimistic lock or `SELECT FOR UPDATE` | Balance update; stock decrement |
| Write Skew | Two concurrent transactions read a set; each updates based on what it read; combined result is invalid | Serializable | "At most one doctor on-call" constraint |

### Consistency Pattern Decision Tree

```
Is the invariant local to a single database?
  YES → Use a single local transaction with the minimum isolation level required.
        Is there concurrent write risk (multiple actors updating same record)?
          YES → Add optimistic lock (version column) or pessimistic lock (SELECT FOR UPDATE)
          NO  → Read Committed isolation is sufficient
  NO → Is the invariant across two services with independent databases?
        YES → Can you tolerate eventual consistency (minutes of inconsistency)?
              YES → Transactional Outbox + at-least-once delivery (preferred)
              NO  → Saga with compensation (more complex; requires compensation design)
                    Can you avoid the cross-service write entirely by re-modeling?
                      YES → Preferred — redesign to move both writes to one service
                      NO  → Saga or Outbox; document consistency window and monitoring

Does the consistency boundary include an external API call (payment, email)?
  YES → NEVER hold a DB lock during the external call
  → Pattern: (1) write intent to DB (PENDING state); commit; release lock
             (2) make external call
             (3) update DB based on result (CONFIRMED or FAILED)
             (4) if update fails after external success: compensate via Outbox/job
```

# Selection Rules

Select this capability when **consistency requirements, invariant protection, or concurrency control are the primary design question**. Route to `relational-database` for schema constraint design (unique indexes, check constraints, foreign keys). Route to `message-queue-design` for asynchronous message delivery and broker topology. Route to `idempotency-retry-design` when duplicate execution prevention is the primary concern. Route to `async-job-design` for compensation worker and reconciliation job design.

# Risk Escalation Rules

Escalate when: the invariant involves money movement, inventory, quota enforcement, or account ownership (financial/operational risk — requires peer review of the transaction boundary design); a distributed transaction (2PC) is proposed (availability risk — must evaluate Outbox/Saga alternatives first and document why they are insufficient); a remote call is proposed inside a database transaction (lock contention risk — must redesign before implementation); a Saga compensation step has no design for compensation failure (if compensation fails, the system is left in a permanently inconsistent state — must specify retry and runbook); or the lock scope covers multiple rows or tables under concurrent write load (deadlock risk — must review for lock ordering and timeout).

# Critical Details

- **The most common transaction design mistake: over-broad transaction scope.** A developer wraps a payment processing flow in a single transaction: (1) read account balance, (2) call payment gateway API (2s latency), (3) write charge record, (4) update account balance. The transaction holds a database lock on the account row for 2+ seconds. Under load, 50 concurrent payments for the same account queue up waiting for the lock; response times degrade from 200ms to 100s; the service appears to hang. Fix: execute the payment API call outside the transaction; use optimistic locking on the account row; handle the payment result in a separate short transaction.
- **Write skew is the hardest anomaly to detect and the most dangerous for business invariants.** Write skew occurs when: Transaction A reads a set of rows satisfying a condition; Transaction B reads the same set; both decide to insert/update based on the condition; after both commit, the condition is violated. Example: "at most 2 doctors on-call at once." Transaction A (reads: 1 doctor on-call; decides: safe to add) and Transaction B (reads: 1 doctor on-call; decides: safe to add) both commit; result: 3 doctors on-call. Prevention: Serializable isolation, or explicit `SELECT FOR UPDATE` on the set rows, or a unique constraint.
- **Compensating transactions must record their compensation data before the forward step executes.** A Saga that attempts to compensate step 2 by looking up the data that step 2 inserted will fail if step 2's data has been modified by a subsequent operation. The compensation log must capture the pre-step state (or the compensation action parameters) atomically with the forward step. Pattern: in the same local transaction as the forward step, write a compensation record to a `saga_log` table.
- **`FOR UPDATE SKIP LOCKED` enables safe queue-style processing without lock contention.** Traditional `SELECT FOR UPDATE` on a work queue causes all workers to compete for the same lock. `SELECT FOR UPDATE SKIP LOCKED` (PostgreSQL 9.5+, MySQL 8.0+) allows each worker to acquire the first unlocked row, skipping rows locked by other workers. This is the correct pattern for job queues, task dispatchers, and claim-check processors.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Payment API call inside DB transaction | Lock held for 2s during API call; 50 concurrent users queue on lock; service degrades | Write PENDING intent; commit; call API; update result in second short transaction |
| `BEGIN TRANSACTION; UPDATE balance; COMMIT` with no isolation level or concurrency control | Two concurrent balance decrements both read balance=100; both write balance=100-50=50; net result: 50 instead of 0 (lost update) | `SELECT balance FOR UPDATE` inside transaction; or optimistic lock with version check |
| `OptimisticLockException` silently caught and ignored | Conflict silently discarded; one writer's update is lost; invariant violated | Explicit conflict handling: retry with re-read, or return 409 Conflict to caller |
| Saga compensation step with no `saga_log` record | Step 3 fails; compensation tries to reverse step 2 using data that has been overwritten; compensation fails; system permanently inconsistent | Write compensation parameters to `saga_log` atomically with each forward step |
| Distributed 2PC across two databases | If participant B is unavailable, coordinator blocks participant A indefinitely; availability coupling | Replace with Transactional Outbox; participant A writes outbox event; relay delivers to B |
| Transaction wraps 5 tables including a reporting aggregate | Lock contention on reporting table during peak load; unrelated reads blocked | Move aggregate update to async job; transaction covers only the core invariant tables |

# Failure Modes

- Payment charged but account record not updated: lock timeout during step 3; partial completion; financial discrepancy.
- Lost update: two concurrent stock decrements both pass the `stock > 0` check; stock goes negative; oversold.
- Deadlock: Transaction A locks rows 1 then 2; Transaction B locks rows 2 then 1; deadlock; one transaction aborted.
- Stuck Saga: compensation step fails; no retry or runbook; system left in partial state indefinitely.
- Phantom booking: two users book the last seat concurrently; both pass the `seats > 0` check at Read Committed; both succeed; negative seat count.
- Outbox relay not running: forward transaction succeeds; outbox event never published; downstream service never notified; silent inconsistency.

# Reference Loading Policy

Read `references/checklist.md` when the change touches multi-step writes, money/inventory/quota/account invariants, distributed consistency, saga/outbox behavior, or concurrent writers. Do not load it for a single-row write with no named invariant, no concurrency risk, and no cross-service side effect.

# Output Contract

Return a consistency design with:

- `invariants` (per invariant: name, data scope, violation condition, business impact)
- `transaction_boundaries` (per transaction: tables touched, isolation level, concurrency control, lock type, timeout)
- `isolation_anomaly_analysis` (per anomaly type: present/absent; prevention mechanism)
- `cross_service_consistency` (pattern: Outbox/Saga/2PC; justification; consistency window)
- `saga_design` (if applicable: steps, compensation steps, compensation log, failure handling)
- `outbox_design` (if applicable: event schema, relay mechanism, at-least-once guarantees, idempotency on consumer)
- `optimistic_lock_design` (version column, conflict handling, retry strategy)
- `remote_call_placement` (confirmation that no remote calls are inside DB transactions)
- `concurrency_tests` (concurrent write simulation; lost update test; deadlock stress test)
- `reconciliation_job` (if eventual consistency: detection of inconsistencies; resolution process; SLA)

# Evidence Contract

Close consistency design only when the output names each invariant, transaction boundary, isolation level, lock/concurrency control, remote-call placement, compensation/outbox path, validation commands, what concurrency evidence proves, what it does not prove under production load, residual consistency risk, and next gate.

# Quality Gate

The consistency design is complete only when:

1. Every transaction boundary is justified by a named invariant.
2. Isolation level is explicitly stated and anomaly protection is verified.
3. No remote API calls occur inside database transactions.
4. Cross-service consistency uses Outbox or Saga with explicit compensation design.
5. Saga compensation records are written atomically with forward steps.
6. Optimistic lock conflicts have an explicit handling strategy.
7. Deadlock prevention (consistent lock ordering, short lock scope, timeout) is addressed.
8. A reconciliation job or monitoring signal detects eventual consistency violations.
9. Concurrency tests cover lost update, phantom read (if applicable), and deadlock scenarios.
10. Lock scope is the minimum required to protect the invariant.

# Used By

- data-middleware-change-builder
- backend-change-builder

# Handoff

Hand off to `relational-database` for constraint and schema design; `message-queue-design` for asynchronous event delivery; `idempotency-retry-design` for retry safety; `async-job-design` for compensation and reconciliation workers.

# Completion Criteria

The capability is complete when **every named business invariant is protected by a minimal, correctly-isolated transaction or a compensatable consistency pattern — and no remote call occurs inside a database lock**.
