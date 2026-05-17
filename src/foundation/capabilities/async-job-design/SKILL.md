---
name: async-job-design
description: Designs asynchronous jobs with idempotency, retry, timeout, failure handling, observability, cancellation, and compensation where relevant.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "43"
changeforge_version: 0.1.0
---

# Mission

Design asynchronous jobs that execute safely under duplicate delivery, retries, timeouts, cancellation, partial failure, poison messages, operator intervention, and version skew — with bounded resource use, visible status, and recoverable outcomes.

# When To Use

Use this capability when a change adds or modifies: background jobs, queue workers, scheduled/cron jobs, delayed tasks, batch processors, fan-out/fan-in jobs, long-running workflows (Saga / Temporal / Step Functions / Airflow), event consumers with business side effects, data backfills, bulk imports/exports, async webhook senders, periodic cleanup, or compensating transactions.

# Do Not Use When

Do not use this capability to move work out of the request path "to make it fast" without defining ownership, idempotency, retry policy, status visibility, and failure handling — that creates invisible failure. Do not use it to design queue topology (`message-queue-design`), broker selection (`event-driven-architecture`), retry math alone (`idempotency-retry-design`), or schema migration jobs (`data-migration-design`); use those alongside this capability.

# Non-Negotiable Rules

- Jobs must explicitly define: **idempotency key, retry policy with bounded attempts, retry backoff with jitter, per-attempt and total timeout, failure classification (transient vs permanent), dead-letter handling, status model, observability, cancellation, and compensation** where side effects span steps.
- Payloads must contain **stable identifiers** (entity ids, correlation id), **not stale snapshots** unless snapshot semantics are explicit and the snapshot expiry is documented.
- Workers must tolerate **at-least-once delivery, duplicate execution, out-of-order execution, and concurrent execution** unless the queue + worker design provably prevents each.
- Retries must distinguish **transient (retryable)**, **permanent (do-not-retry)**, and **rate-limited (retry with longer backoff)**. Blind retry of permanent failures wastes capacity and hides the bug.
- Operators or users must have visibility into job state when outcomes matter to a human. Silent failure is the worst failure.
- Long-running or externally visible jobs require **cancellation semantics** (cooperative cancellation tokens) and **compensation** for already-committed side effects.
- All side-effecting external calls inside a job must be **idempotent** (via key, conditional write, or natural idempotence) — or the job must guarantee single execution per unit of work.
- Every job emits structured logs with `job_name`, `job_id`, `attempt`, `idempotency_key`, `correlation_id`, plus the metrics: enqueue rate, in-flight, success rate, failure rate by class, latency (queue + execution), retry count, DLQ size, age of oldest in-flight job.
- Each job has a documented **owner**, **runbook**, and **alert** before go-live.
- Jobs that touch money, identity, notifications to users, inventory, or external partners require additional double-check (idempotency + reconciliation).

# Industry Benchmarks

Anchor against: **At-least-once delivery semantics** (Kafka, SQS, RabbitMQ standard mode), **Exactly-once illusion via idempotent consumers** (Kafka transactions are not end-to-end exactly-once across external systems), **Dead-Letter Queue (DLQ)** pattern, **Outbox / Inbox patterns** for transactional messaging (Chris Richardson, microservices.io), **Saga pattern** for distributed transactions (orchestration via Temporal/Cadence/AWS Step Functions, or choreography), **Compensating Transaction** pattern (Garcia-Molina/Salem), **Circuit Breaker** (Nygard, *Release It!*) for downstream protection, **Bulkhead** pattern, **Token Bucket / Leaky Bucket** for rate-limiting downstream, **AWS Well-Architected Reliability Pillar**, **Google SRE Workbook** for error budgets on async work, **CloudEvents 1.0** for event envelope schema, **OpenTelemetry** for distributed tracing across producer→broker→consumer, **Exponential backoff with full jitter** (AWS Architecture Blog, "Exponential Backoff and Jitter"), **Poison message handling**, **Outbox table + CDC** (Debezium) for transactional event emission, **Two-phase / message-relay** alternatives. For workflow engines: **Temporal**, **Cadence**, **Airflow**, **Step Functions**, **Camunda** — pick by replay/versioning needs.

### Runtime Selection Matrix

| Runtime | Pick when | Avoid when | Idempotency burden |
| --- | --- | --- | --- |
| **In-process background task** (e.g., asyncio task, goroutine, thread pool) | Best-effort, OK to lose on restart, short, low value | Loss is unacceptable; observability needed; > seconds | All on the developer |
| **Cron / scheduled job** | Periodic, idempotent-by-design (e.g., reconciliation) | Need to react to events; sub-minute cadence | Per-tick guard |
| **Queue worker** (SQS, RabbitMQ, Redis stream, NATS JetStream) | Decouple producer/consumer; fan-out; back-pressure | Need ordered workflows with branching/compensation | Per-message idempotency key |
| **Event broker** (Kafka, Pulsar, Kinesis) | Replayable log; multiple consumer groups; high throughput | Workflow orchestration; per-item retries; small scale | Per-key idempotency + offset management |
| **Workflow engine** (Temporal, Cadence, Step Functions, Camunda) | Long-running (minutes→months), branching, compensation, retries, versioning, durable timers | Tiny jobs; engine operational cost not justified | Engine handles retries; activities must still be idempotent |
| **Lambda / FaaS triggered by queue/topic** | Spiky, ops-offload, simple jobs | Sustained high volume (cost), > 15 min runtime, cold-start sensitive | Per-invocation idempotency key |

### Retry Policy Selection

| Failure class | Action | Backoff | Max attempts | Termination |
| --- | --- | --- | --- | --- |
| Transient network / 5xx / timeout | Retry | Exponential + **full jitter**: `delay = random(0, min(cap, base * 2^attempt))` | 3–7 typical | Move to DLQ with diagnostic |
| Rate-limited (429 / quota) | Retry with longer backoff or respect `Retry-After` | Honor server hint; otherwise exponential with higher base | 3–10 | DLQ + alert |
| Permanent (4xx validation, business rule violation) | **Do not retry** | n/a | 0 | DLQ immediately with reason |
| Poison message (cannot parse, malformed payload) | Do not retry; quarantine | n/a | 0 | Quarantine queue + alert; **never block the main queue** |
| Downstream circuit open | Pause / requeue with delay | Up to circuit close | Bounded by SLO | DLQ if circuit stays open beyond threshold |
| Optimistic-concurrency conflict (412/409) | Retry after re-read | Short, bounded | 3 typical | Surface as conflict, not silent loss |

### Decision Tree: Idempotency Strategy

```
Does the job have side effects that must occur exactly once per logical unit of work?
├─ No (read-only / naturally idempotent) → No key needed; document why.
└─ Yes →
    Can the side effect be expressed as a conditional write
    (e.g., INSERT with unique key, UPDATE WHERE version=?, PUT-If-None-Match)?
    ├─ Yes → Use natural idempotence; idempotency_key = business unique id; record outcome.
    └─ No  →
        Maintain an idempotency record:
          { idempotency_key, job_name, status, result, expires_at }
          - Lock-then-execute: SELECT FOR UPDATE / INSERT-or-conflict on key
          - On retry with same key → return stored result; do not re-execute side effect
          - Retention ≥ longest possible retry/replay window (≥ 24h; ≥ 7d for money)
          - Different payload + same key → reject with conflict
```

### Saga / Long-Running Workflow Patterns

| Pattern | When | Compensation responsibility |
| --- | --- | --- |
| **Orchestration** (Temporal, Step Functions, Camunda) | Branching, long timers, visible state, versioning of in-flight workflows | Orchestrator records committed steps; calls compensators in reverse order on failure |
| **Choreography** (events trigger next step) | Loose coupling, simple flows, ≤ 3-4 steps | Each step emits compensating event on failure; harder to reason end-to-end |
| **Process Manager** (stateful coordinator inside a service) | Mid-complexity flows scoped to one bounded context | Coordinator persists state and rollbacks |

For workflow engines: pin the workflow **version**; in-flight workflows must complete on the version they started; new versions only for new workflows. Otherwise replay corruption.

# Selection Rules

Select this capability when **background execution lifecycle** (when, where, how, what-if-it-fails) is primary. Adjacent routing:

- Prefer `idempotency-retry-design` when the headline question is duplicate-side-effect math and key design alone.
- Prefer `message-queue-design` when topology, ordering, partitioning, or queue infra selection dominates.
- Prefer `event-driven-architecture` when broker topology + event schema + consumer fan-out dominate.
- Prefer `data-migration-design` for backfills/schema migrations specifically.
- Prefer `degradation-circuit-breaking` for downstream protection patterns specifically.
- Use **with** `logging-error-handling` and `observability` for diagnostics; `reliability-observability-gate` for SLO acceptance.

# Risk Escalation Rules

Escalate when jobs affect: **money** (charges, payouts, refunds), **inventory** (over-sell, under-sell), **customer notifications** (emails, SMS, push — duplicate sends are very visible), **data migrations**, **bulk updates** to user data, **external systems** without their own idempotency, **tenant-wide changes**, **irreversible side effects** (deletes, public posts, third-party API calls), runtimes **> 15 min**, **high fan-out** (one job → thousands of effects), **per-tenant billing**, or workflows that span **regulatory boundaries**. Escalate any job whose failure SLO is unknown.

# Critical Details

Async work fundamentally changes the failure model: **the request may succeed while the job later fails, retries, duplicates, is cancelled, or executes after a code change**. Apply these refinements:

- **Payloads should be durable and minimal.** Pass entity ids + version, not full snapshots, unless snapshot semantics are deliberate. Reason: snapshots go stale; ids re-fetch current state.
- **Snapshot semantics, when used, must include `snapshot_taken_at` and `payload_schema_version`.** Workers must validate and reject expired or unknown versions explicitly.
- **The job is not the request.** Acknowledge the request only after the work is **durably enqueued** (in DB outbox or broker with ack). Otherwise you have lost-update bugs on producer-side failure.
- **Outbox pattern** is the safest producer pattern: write business state + outbox row in one DB transaction; a relay publishes outbox rows to the broker. Avoids dual-write inconsistency.
- **Status model.** Each business-meaningful job has at least: `pending → running → succeeded | failed | cancelled | timed_out | dead_lettered`. Status is queryable by users/operators where outcomes matter to them.
- **Cancellation is cooperative.** Workers must check a cancellation signal at safe points; abrupt termination leaves partial state. Define what cancellation guarantees (e.g., "no new external calls after cancel", "in-flight HTTP call completes").
- **Compensation is a design output, not a runtime hope.** If step 3 of 5 fails, what runs to undo steps 1–2? If it cannot be undone, that is a finding — escalate before shipping.
- **Poison messages.** A single malformed message must not block the queue. Move to a quarantine queue after N attempts and alert.
- **DLQ is not a feature; it is a debugging surface.** A DLQ that no one watches is silent failure. Alert on DLQ size > 0 and on age of oldest message.
- **Bounded concurrency.** Workers must respect downstream concurrency limits (DB connections, external API rate). Unbounded fan-out melts databases and triggers rate-limiting cascades.
- **Backpressure.** Producers must slow down when queue depth > threshold. Otherwise an outage of consumers becomes a producer-side memory/disk crisis.
- **Timeouts everywhere.** Per-attempt timeout < total timeout < lease/visibility timeout (the queue's "in-flight" window). If execution exceeds visibility timeout, the queue redelivers and you have concurrent execution of the same job.
- **Clock skew & scheduling drift.** Cron jobs miss/double-fire across leader elections. Use a distributed scheduler (e.g., quartz with DB lock, K8s CronJob with concurrencyPolicy=Forbid, Temporal schedules).
- **Versioning of in-flight work.** Code changes during the lifetime of a long-running workflow. Either pin workflows to versions (Temporal patches), or design payloads to be forward-compatible, or drain before deploy.
- **Replay storms.** A bug that DLQs many messages followed by a fix causing mass replay can melt downstream systems. Replay at rate-limited speed.
- **Observability minimums.** Tracing across producer → broker → consumer (propagate `traceparent` in message headers). Without it, debugging is hours instead of minutes.
- **Test for failure, not for happy path.** The acceptance test must simulate duplicate delivery, timeout, cancellation, and downstream failure. Otherwise the failure handling is untested code.
- **Tenant isolation.** A single noisy tenant must not starve others. Use per-tenant queues, weighted fair-queueing, or per-tenant concurrency caps.
- **Cost of retries.** Exponential retry of expensive operations (LLM calls, third-party API calls at $0.01/req) can multiply cost during incidents. Budget retry cost.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `fire_and_forget(send_email(user))` from request handler | Lost on restart; no retry; no visibility |
| Retry without idempotency key on `POST /charge` | Duplicate charges |
| Retry permanent 4xx | Wastes capacity; hides the bug |
| Snapshot payload + 3-day retry window + no schema version | Stale data committed days later |
| One queue handling all jobs of all priorities | Bulk import starves transactional jobs |
| DLQ with no alert | Silent failure |
| Worker reads from DB without `SELECT FOR UPDATE` then writes | Lost update under concurrent delivery |
| Cancellation = `process.kill(pid)` | Partial external effects, no compensation |
| Workflow versioned by "latest deploy" with in-flight workflows | Replay corruption |
| Cron with `concurrencyPolicy: Allow` and long-running tick | Drift → 2x concurrent runs → double effects |

# Failure Modes

- Worker retries a non-idempotent side effect (charge, email, webhook) and produces duplicate effects visible to customers.
- Job status is invisible; users keep clicking "submit"; operators cannot answer "did it run?".
- Payload snapshots become stale; the job commits a decision based on data that has since changed.
- Permanent validation failure (4xx from downstream) loops through max retries without useful diagnostics; DLQ piles up with the same error.
- Cancellation stops the worker mid-step; partial external effects remain (e.g., charged but no order, sent webhook but no DB write).
- DLQ accumulates silently; no alert; failures discovered weeks later from customer complaints.
- Poison message blocks the entire queue because retry loops forever on parse failure.
- Worker concurrency unbounded; on incident recovery, queue drains too fast and melts the database.
- Visibility/lease timeout < actual execution time → same job executed twice concurrently.
- Schema change to payload + in-flight jobs of old shape → workers crash on deserialization → DLQ flood.
- Workflow code deployed mid-run; existing workflow replay fails because activity signatures changed.
- One tenant's bulk operation starves all other tenants' jobs.
- Saga step succeeds, compensation step fails on rollback → permanent inconsistency, no alarm.

# Output Contract

Return an async job design containing:

- `job_name` (stable, unique)
- `trigger` (event topic / API endpoint / schedule / manual)
- `runtime` (queue worker / workflow engine / cron / FaaS) with justification vs alternatives
- `payload_schema` (with `payload_schema_version`, identifiers vs snapshot decision, expiry semantics if snapshot)
- `idempotency`: key derivation, scope, storage, retention window, replay semantics, conflict behavior
- `concurrency`: max concurrent attempts, per-tenant cap, downstream rate-limit budget
- `timeouts`: per-attempt timeout, total deadline, queue visibility timeout (must satisfy per-attempt < visibility)
- `retry_policy`: classification (transient/permanent/rate-limited/poison), backoff formula (exponential + full jitter), max attempts, max wall-clock
- `failure_handling`: DLQ destination, quarantine for poison, alert thresholds, runbook link
- `cancellation`: signal mechanism, safe-point contract, guarantees on partial effects
- `compensation`: per-step compensators (for multi-step / saga), ordering, idempotency of compensators
- `status_model`: states, transitions, visibility to users vs operators, query API
- `observability`: metrics (queue depth, in-flight, success/failure by class, latency p50/p95/p99, retry count, DLQ size, oldest-in-flight age), structured log fields, traces with propagated context
- `ownership`: owning team, on-call, runbook
- `tests`: unit (handler logic), integration (queue → handler → side effect), failure-injection (duplicate, timeout, cancellation, downstream fault), load (sustained + spike + backlog drain)
- `versioning`: payload schema evolution rules, in-flight workflow versioning, deploy/drain strategy
- `cost_model`: cost per execution × projected volume; retry cost cap

# Quality Gate

The job design passes only when:

1. Duplicate delivery, retry exhaustion, timeout, cancellation, partial failure, and poison message **each have defined outcomes** with diagnostics.
2. Idempotency is proven (natural idempotence demonstrated, or key + storage + replay semantics specified and tested).
3. Visibility/lease timeout > per-attempt timeout + safety margin; lease renewal is documented for long jobs.
4. DLQ has an owner, an alert, and a triage runbook.
5. Status is queryable by anyone who needs to know (users, support, operators).
6. Tracing context propagates producer → broker → consumer.
7. Cost-at-scale modeled, including retry-storm cost.
8. Failure-injection tests exist and pass.
9. Compensation, where required, is implemented and tested — not deferred.
10. Concurrency caps protect downstream dependencies.

# Used By

- backend-change-builder
- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `idempotency-retry-design` for repeated side-effect math; `message-queue-design` for queue topology and broker specifics; `event-driven-architecture` for broker/event-flow design; `logging-error-handling` for diagnostic context standards; `data-migration-design` for backfill jobs; `degradation-circuit-breaking` for downstream protection; `observability` and `reliability-observability-gate` for SLO and alerting acceptance; `security-privacy-gate` when payloads contain sensitive data.

# Completion Criteria

The capability is complete when the job can run asynchronously with **safe retries, visible status, bounded failure behavior, recoverable partial failure, tested cancellation/compensation, propagated tracing, owned DLQ, and bounded cost at projected volume** — and when an on-call engineer can diagnose and recover from a failure at 02:00 using only the runbook and the emitted observability.
