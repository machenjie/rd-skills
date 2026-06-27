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

# Stage Fit

Use this capability during planning, coding, review, testing, repair, and release-readiness when a write path must preserve an invariant across concurrent requests, multiple tables, outbox/event publication, compensation, reconciliation, or external side effects. Re-run it after edits that move a transaction boundary, lock acquisition, event publish, idempotency check, retry wrapper, remote call, or validation command because memory and repository graph claims become stale when execution order changes.

Do not let this capability become a general database design review. Hand off to `relational-database` for schema/constraint design, `message-queue-design` for broker delivery topology, `idempotency-retry-design` for duplicate request math, and `data-side-effect-flow-tracing` when the first problem is discovering hidden or misordered side effects.

# Non-Negotiable Rules

- **Start with the invariant, not the mechanism.** Every transaction boundary must be justified by a named invariant: "the account balance must never go below zero" (debit must check and update atomically); "a subscription must not exist in both ACTIVE and CANCELLED state simultaneously" (status update must be atomic with any side-effect records). A transaction that exists "because we always wrap things in transactions" with no named invariant is a transaction that creates contention without protecting anything.
- **Define isolation level explicitly and justify the choice.** The four SQL isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) exist because stronger isolation reduces concurrency and throughput. The design must name the isolation anomaly being prevented and the isolation level required to prevent it. Default to Read Committed (the PostgreSQL default). Upgrade to Repeatable Read for transactions that require consistent re-reads of the same rows. Use Serializable only for transactions that require prevention of phantom reads or serialization anomalies — and design for the serialization failure retry.
- **Never perform a slow remote call while holding a database lock.** A transaction that opens a database row-level lock, calls an external payment API (latency: 200ms–5s; failure rate: 0.1%–5%), then commits or rolls back based on the API response will hold the lock for the entire duration of the API call. Under load, this blocks all other transactions attempting to lock the same row. The pattern causes lock contention cascades and can bring down a service under moderate traffic. Fix: execute the local transaction first to record intent; release the lock; make the external call; use an outbox or compensation pattern to handle the external call's result.
- **Prefer local transaction plus event (Transactional Outbox) over distributed transactions for cross-service consistency.** A distributed transaction (2PC across two databases, or XA transactions) creates availability coupling: if either participant fails to respond, both are blocked. The Transactional Outbox pattern: write the business record and the outbox event in the same local transaction; a background relay reads the outbox and publishes to the message broker; the downstream service consumes and applies idempotently. This provides at-least-once delivery with local atomicity, without distributed coordination.
- **Optimistic locking requires explicit conflict handling that users or background workers can recover from.** Optimistic locking (version column or `updated_at` timestamp check) detects conflicts at commit time, not at read time. A conflict means two concurrent writers attempted the same update; one succeeds, one gets a `OptimisticLockException` or equivalent. The design must specify: who handles the exception (the caller retries? the user is shown a conflict warning?); what the retry strategy is (immediate retry, exponential backoff, user-prompted merge); and what happens if the conflicting update was from a different field (fine-grained or coarse-grained conflict detection).
- **Saga compensation must be designed as a first-class workflow, not an afterthought.** A Saga is a sequence of local transactions, each with a compensating transaction. If Step 3 fails, Steps 2 and 1 must be compensated in reverse order. The compensation design must specify: what data the compensation step needs (compensation log must be written before the forward step is executed); whether the compensation is synchronous or asynchronous; what happens if the compensation itself fails (retry with backoff; alert; manual intervention runbook); and whether partial compensation produces a consistent state or a temporarily inconsistent state that a reconciliation job must resolve.

# Industry Benchmarks

Anchor against ACID, ANSI SQL isolation, MVCC anomaly analysis, transactional outbox, saga compensation, optimistic and pessimistic locking, PostgreSQL/MySQL lock behavior, Two-Phase Commit availability trade-offs, CAP/PACELC consistency choices, and SRE-style reconciliation evidence. Keep this body focused on route selection, closure, and validation; load [references/checklist.md](references/checklist.md) for a lightweight execution checklist, [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for anomaly matrices and pattern decisions, and [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on graph/memory/execution freshness, tool boundaries, or production-evidence limits.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Local invariant transaction | Single database, multi-step write, financial/inventory/quota/state invariant. | Minimal atomic boundary, isolation level, lock strategy, rollback behavior. | Invariant statement, rows/tables touched, isolation choice, concurrency test. | `relational-database`, `repository-persistence` | Single-row write with no named invariant or concurrent writer. |
| Concurrent writer conflict | Lost update, write skew, phantom booking, stale version, lock timeout. | Optimistic/pessimistic control, conflict response, retry budget, deadlock handling. | Conflict simulation, lock order, timeout, retry/409 behavior. | `concurrency-control`, `failure-contract-design` | Sequential-only path with DB constraint proof. |
| Transaction plus side effect | DB write plus event, cache, search, file, webhook, email, payment, or provider call. | No remote call under lock; publish-after-commit, outbox, intent state, or compensation. | Side-effect flow map, outbox/intent decision, partial-failure test. | `data-side-effect-flow-tracing`, `async-job-design` | Pure local transaction with no observable side effect. |
| Cross-service consistency | Independent databases, services, external systems, eventually consistent read model. | Outbox, saga, reconciliation, consistency window, idempotent consumers. | Pattern decision, compensation log, reconciliation SLA, consumer idempotency evidence. | `message-queue-design`, `idempotency-retry-design` | Same-service local transaction sufficient. |
| Release and validation freshness | Migration, refactor, repository graph or memory claim, prior validation before final edit. | Prove current source and command order still match the consistency boundary. | Current paths inspected, accepted/rejected memory, fresh validator output, evidence limits. | `validation-broker`, `plan-execution-consistency` | No boundary, test, config, or execution-order change. |

# Selection Rules

Select this capability when **consistency requirements, invariant protection, or concurrency control are the primary design question**. Route to `relational-database` for schema constraint design (unique indexes, check constraints, foreign keys). Route to `message-queue-design` for asynchronous message delivery and broker topology. Route to `idempotency-retry-design` when duplicate execution prevention is the primary concern. Route to `async-job-design` for compensation worker and reconciliation job design.

# Risk Escalation Rules

Escalate when: the invariant involves money movement, inventory, quota enforcement, or account ownership (financial/operational risk — requires peer review of the transaction boundary design); a distributed transaction (2PC) is proposed (availability risk — must evaluate Outbox/Saga alternatives first and document why they are insufficient); a remote call is proposed inside a database transaction (lock contention risk — must redesign before implementation); a Saga compensation step has no design for compensation failure (if compensation fails, the system is left in a permanently inconsistent state — must specify retry and runbook); or the lock scope covers multiple rows or tables under concurrent write load (deadlock risk — must review for lock ordering and timeout).

# Proactive Professional Triggers

- **Signal:** A write path says "wrap it in a transaction" without naming the business invariant, rows/tables, failure state, or concurrent writer. **Hidden risk:** broad locks reduce throughput while failing to protect the real correctness condition. **Required professional action:** name the invariant, prove the minimal atomic scope, and reject unrelated work inside the transaction. **Route to:** `transaction-consistency`, `relational-database`. **Evidence required:** invariant-to-boundary map, lock scope, isolation choice, and rejected over-broad operations.
- **Signal:** A handler, job, repository, or workflow makes a payment, webhook, email, storage, cache, search, event, or external API call while a DB transaction or row lock is open. **Hidden risk:** lock contention, partial completion, and duplicate side effects during timeout or retry. **Required professional action:** move remote side effects outside the lock and use intent state, outbox, compensation, or reconciliation. **Route to:** `data-side-effect-flow-tracing`, `async-job-design`. **Evidence required:** transaction timeline, remote-call placement, partial-failure path, and no-lock-held proof.
- **Signal:** Cross-service or multi-store consistency is handled by direct writes, 2PC, retry loops, or "best effort" events without an outbox, saga, or reconciliation decision. **Hidden risk:** durable state diverges after one participant succeeds and another fails. **Required professional action:** choose outbox, saga, or remodel-to-one-owner, then define consistency window and consumer idempotency. **Route to:** `message-queue-design`, `idempotency-retry-design`. **Evidence required:** pattern decision, event/inbox key, compensation or reconciliation path, and duplicate-delivery test.
- **Signal:** Optimistic lock, serializable transaction, or deadlock retry catches conflicts but hides them, retries forever, or returns a generic 500. **Hidden risk:** users lose updates, workers amplify contention, and operators cannot distinguish retryable conflicts from system failure. **Required professional action:** define bounded retry, conflict response, lock timeout, and safe failure contract. **Route to:** `failure-contract-design`, `quality-test-gate`. **Evidence required:** retry budget, conflict/timeout response, concurrent-write test, and terminal-state assertion.
- **Signal:** Project memory, repository graph, old migration notes, or previous test output claims the transaction path is safe after repository methods, migrations, queues, retry wrappers, or side effects changed. **Hidden risk:** stale topology hides a new lost-update, ghost-event, or compensation gap. **Required professional action:** inspect current source, compare same-pattern write paths, rerun focused validators, and disclose what remains unverified. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** inspected path list, accepted/rejected prior claim, fresh command outcome, and residual consistency risk.

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

- **Payment charged but account record not updated:** lock timeout during step 3 leaves partial completion and financial discrepancy.
- **Lost update:** two concurrent stock decrements both pass the `stock > 0` check; stock goes negative and inventory is oversold.
- **Deadlock without bounded retry:** Transaction A locks rows 1 then 2 while Transaction B locks rows 2 then 1; one aborts and the caller sees an ambiguous failure.
- **Stuck Saga:** compensation step fails without retry, alert, or runbook, so the system remains in partial state indefinitely.
- **Phantom booking:** two users book the last seat concurrently; both pass the range check at Read Committed and the capacity invariant is violated.
- **Outbox relay not running:** forward transaction succeeds, the outbox event is never published, and downstream state silently diverges.
- **Serialization retry gap:** Serializable or optimistic conflict is caught but lacks bounded retry, terminal response, or operator-visible classification.
- **Stale topology claim:** memory or repository graph says publish-after-commit is safe, but current source moved event publication, retry, cache, or remote-call ordering.
- **Compensation evidence gap:** compensation parameters are reconstructed from mutable current state instead of a durable log written with the forward step.

# Reference Loading Policy

Read `references/checklist.md` when the change touches multi-step writes, money/inventory/quota/account invariants, distributed consistency, saga/outbox behavior, or concurrent writers. Read `references/benchmarks-and-patterns.md` when the decision needs anomaly tables, isolation/locking choices, outbox-vs-saga tradeoffs, compensation failure paths, graph-memory-execution coupling, or validation mapping. Read `references/evidence-patterns.md` when handoff depends on current-source proof, same-pattern write-path scans, accepted or rejected memory/graph claims, tool permission boundaries, or what evidence proves versus what evidence does not prove. Do not load references for a single-row write with no named invariant, no concurrency risk, no side effect, and no stale evidence concern.

# Output Contract

Return a consistency design with:

- `mode_selected` (local invariant transaction, concurrent writer conflict, transaction plus side effect, cross-service consistency, or release/validation freshness)
- `source_evidence` (current handlers, services, repositories, migrations, queue/event publishers, side-effect adapters, tests, graph, memory, and execution trajectory inspected)
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
- `graph_memory_execution_coupling` (repository graph, project memory, generated reports, previous validation, and final execution evidence accepted/rejected/stale/not verified)
- `validation_freshness` (commands run after final material edit, stale validations rejected, and not-run obligations named)
- `tool_permission_boundary` (read-only versus state-mutating tools, sandbox/approval context, dry-run or rollback path, and secret/output redaction rule)
- `evidence_scope` (what concurrency, integration, migration, and validator evidence proves, plus production load/lock/replica/consumer claims left unproven)
- `residual_consistency_risk` (remaining lost-update, deadlock, partial side-effect, replay, compensation, reconciliation, or validation risk)

# Evidence Contract

Close consistency design only when the output names each invariant, the boundaries inspected, current source paths inspected, same-pattern write-path scan, transaction boundary, isolation level, lock/concurrency control, remote-call placement, compensation/outbox path, graph-memory-execution freshness, validation commands, what evidence proves, what evidence does not prove under production load, tool permission/sandbox boundary, residual consistency risk, rollback note, handoff, and next gate.

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
11. Repository graph, project memory, generated reports, and prior validation claims are confirmed against current source or marked stale/not verified.
12. Transaction/event/cache/external side-effect ordering is mapped to validation evidence or residual risk.
13. Validation evidence is fresh for the final material path and states production-load limits.
14. Tool output used as evidence avoids raw secrets, environment dumps, full payloads, and unbounded logs.

# Used By

- data-middleware-change-builder
- backend-change-builder

# Benchmark Coverage

This capability covers ACID, isolation anomalies, lost-update/write-skew prevention, optimistic and pessimistic locking, 2PC availability trade-offs, transactional outbox, saga compensation, reconciliation, lock ordering, current-source graph checks, memory freshness, and validation-to-invariant mapping. Detailed matrices and decision trees live in `references/benchmarks-and-patterns.md` to keep `SKILL.md` efficient.

# Routing Coverage

Route here when transaction atomicity, isolation, lock scope, cross-service consistency, or side-effect ordering is the primary correctness question. Route away to `relational-database` for schema constraints, `message-queue-design` for broker topology, `idempotency-retry-design` for duplicate request guarantees, `data-side-effect-flow-tracing` for hidden effects, and `quality-test-gate` when validation depth is the unresolved issue.

# Handoff

Hand off to `relational-database` for constraint and schema design; `message-queue-design` for asynchronous event delivery; `idempotency-retry-design` for retry safety; `async-job-design` for compensation and reconciliation workers.

# Completion Criteria

The capability is complete when **every named business invariant is protected by a minimal, correctly-isolated transaction or a compensatable consistency pattern — and no remote call occurs inside a database lock**.
